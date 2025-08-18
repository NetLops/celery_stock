from celery import Celery
from .celery_app import celery_app
from .database import SessionLocal
from .models import AnalysisTask, Stock, AIAnalysis, StockPrice
from .services.stock_service import StockDataService
from .services.ai_service import AIAnalysisService
from .services.recommendation_service import RecommendationService
from datetime import datetime, timedelta
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)

@celery_app.task(bind=True)
def analyze_batch_stocks(self, task_id: str, symbols: List[str], analysis_types: List[str], priority: str = "normal"):
    """批量分析股票任务"""
    db = SessionLocal()
    
    try:
        # 更新任务状态
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            logger.error(f"任务不存在: {task_id}")
            return
        
        task.status = "running"
        task.started_at = datetime.now()
        db.commit()
        
        stock_service = StockDataService()
        ai_service = AIAnalysisService()
        
        results = {}
        total_symbols = len(symbols)
        
        for i, symbol in enumerate(symbols):
            try:
                # 更新进度
                progress = int((i / total_symbols) * 100)
                task.progress = progress
                db.commit()
                
                # 获取股票数据
                stock_info = stock_service.get_stock_info(symbol)
                if not stock_info:
                    results[symbol] = {"error": "无法获取股票信息"}
                    continue
                
                # 获取或创建股票记录
                stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                if not stock:
                    stock = Stock(
                        symbol=symbol,
                        name=stock_info["name"],
                        exchange=stock_info["exchange"],
                        sector=stock_info["sector"],
                        industry=stock_info["industry"]
                    )
                    db.add(stock)
                    db.commit()
                    db.refresh(stock)
                
                # 获取历史数据并保存
                historical_data = stock_service.get_historical_data(symbol, "1y")
                if historical_data is not None:
                    stock_service.save_stock_data(symbol, historical_data)
                
                # 执行AI分析
                chart_data = stock_service.get_chart_data(symbol)
                analysis_data = {
                    "stock_info": stock_info,
                    "indicators": chart_data.get("indicators", {})
                }
                
                comprehensive_analysis = ai_service.generate_comprehensive_analysis(symbol, analysis_data)
                
                # 保存分析结果
                for analysis_type in analysis_types:
                    if analysis_type in comprehensive_analysis.get("comprehensive_analysis", {}):
                        content = comprehensive_analysis["comprehensive_analysis"][analysis_type]
                        
                        # 删除旧的分析结果
                        db.query(AIAnalysis).filter(
                            AIAnalysis.stock_id == stock.id,
                            AIAnalysis.analysis_type == analysis_type
                        ).delete()
                        
                        # 创建新的分析结果
                        analysis = AIAnalysis(
                            stock_id=stock.id,
                            analysis_type=analysis_type,
                            analysis_content=content,
                            confidence_score=content.get("confidence", 0.7),
                            tags=content.get("tags", []),
                            valid_until=datetime.now() + timedelta(hours=24)
                        )
                        db.add(analysis)
                
                db.commit()
                results[symbol] = {"status": "completed", "analyses": len(analysis_types)}
                
            except Exception as e:
                logger.error(f"分析股票失败 {symbol}: {e}")
                results[symbol] = {"error": str(e)}
                continue
        
        # 完成任务
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.now()
        task.result = results
        db.commit()
        
        logger.info(f"批量分析任务完成: {task_id}")
        
    except Exception as e:
        logger.error(f"批量分析任务失败 {task_id}: {e}")
        task.status = "failed"
        task.error_message = str(e)
        task.completed_at = datetime.now()
        db.commit()
        
    finally:
        db.close()

@celery_app.task(bind=True)
def scan_market_opportunities(self, task_id: str, sector: Optional[str] = None, market_cap_min: Optional[float] = None):
    """扫描市场机会任务"""
    db = SessionLocal()
    
    try:
        task = db.query(AnalysisTask).filter(AnalysisTask.task_id == task_id).first()
        if not task:
            return
        
        task.status = "running"
        task.started_at = datetime.now()
        db.commit()
        
        # 示例股票列表
        market_symbols = ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA", "META", "NVDA"]
        
        recommendation_service = RecommendationService()
        opportunities = []
        
        for i, symbol in enumerate(market_symbols):
            try:
                task.progress = int((i / len(market_symbols)) * 100)
                db.commit()
                
                score_data = recommendation_service.generate_stock_score(symbol)
                
                if "error" not in score_data and score_data.get("total_score", 0) >= 0.7:
                    opportunities.append({
                        "symbol": symbol,
                        "score": score_data.get("total_score", 0),
                        "recommendation": score_data.get("recommendation"),
                        "risk_level": score_data.get("risk_level")
                    })
                
            except Exception as e:
                logger.error(f"扫描股票失败 {symbol}: {e}")
                continue
        
        opportunities.sort(key=lambda x: x["score"], reverse=True)
        
        task.status = "completed"
        task.progress = 100
        task.completed_at = datetime.now()
        task.result = {"opportunities": opportunities[:10]}
        db.commit()
        
    except Exception as e:
        logger.error(f"市场扫描失败 {task_id}: {e}")
        task.status = "failed"
        task.error_message = str(e)
        db.commit()
        
    finally:
        db.close()

@celery_app.task
def update_market_data():
    """定时更新市场数据"""
    db = SessionLocal()
    try:
        stocks = db.query(Stock).all()
        stock_service = StockDataService()
        
        for stock in stocks:
            try:
                historical_data = stock_service.get_historical_data(stock.symbol, "5d")
                if historical_data is not None:
                    stock_service.save_stock_data(stock.symbol, historical_data)
            except Exception as e:
                logger.error(f"更新失败 {stock.symbol}: {e}")
                
        logger.info("市场数据更新完成")
    finally:
        db.close()

@celery_app.task
def cleanup_expired_analysis():
    """清理过期数据"""
    db = SessionLocal()
    try:
        expired_count = db.query(AIAnalysis).filter(
            AIAnalysis.valid_until < datetime.now()
        ).delete()
        db.commit()
        logger.info(f"清理了 {expired_count} 条过期分析")
    finally:
        db.close()