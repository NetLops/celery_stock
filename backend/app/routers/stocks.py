from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from .. import schemas
from ..services.stock_service import StockDataService
from ..services.ai_service import AIAnalysisService
from ..models import Stock, AIAnalysis
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=List[schemas.Stock])
async def get_stocks(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db)
):
    """获取股票列表"""
    stocks = db.query(Stock).offset(skip).limit(limit).all()
    
    # 将SQLAlchemy模型转换为Pydantic模型
    result = []
    for stock in stocks:
        result.append(schemas.Stock(
            id=stock.id,
            symbol=stock.symbol,
            name=stock.name,
            exchange=stock.exchange,
            sector=stock.sector,
            industry=stock.industry,
            created_at=stock.created_at,
            updated_at=stock.updated_at
        ))
    return result

@router.get("/search", response_model=schemas.BaseResponse)
async def search_stock_by_name(name: str):
    """根据股票名称查找股票代码"""
    try:
        stock_service = StockDataService()
        results = stock_service.find_stock_by_name(name)
        
        if not results:
            return schemas.BaseResponse(
                message="未找到匹配的股票",
                data=[]
            )
        
        return schemas.BaseResponse(
            message=f"找到 {len(results)} 个匹配的股票",
            data=results
        )
        
    except Exception as e:
        logger.error(f"查找股票失败 {name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}", response_model=schemas.BaseResponse)
async def get_stock_info(symbol: str, db: Session = Depends(get_db)):
    """获取单个股票信息"""
    try:
        stock_service = StockDataService()
        
        # 从数据库获取股票信息
        stock = db.query(Stock).filter(Stock.symbol == symbol.upper()).first()
        
        if not stock:
            # 如果数据库中没有，尝试从API获取
            stock_info = stock_service.get_stock_info(symbol.upper())
            if not stock_info:
                raise HTTPException(status_code=404, detail="股票不存在")
            
            # 保存到数据库
            stock = Stock(
                symbol=stock_info["symbol"],
                name=stock_info["name"],
                exchange=stock_info["exchange"],
                sector=stock_info["sector"],
                industry=stock_info["industry"]
            )
            db.add(stock)
            db.commit()
            db.refresh(stock)
        
        # 获取最新价格数据
        chart_data = stock_service.get_chart_data(symbol.upper(), "1y")
        
        return schemas.BaseResponse(
            data={
                "stock_info": {
                    "id": stock.id,
                    "symbol": stock.symbol,
                    "name": stock.name,
                    "exchange": stock.exchange,
                    "sector": stock.sector,
                    "industry": stock.industry
                },
                "chart_data": chart_data
            }
        )
        
    except Exception as e:
        logger.error(f"获取股票信息失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze", response_model=schemas.BaseResponse)
async def analyze_stock(
    request: schemas.StockAnalysisRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """分析单个股票"""
    try:
        symbol = request.symbol.upper()
        
        # 检查是否需要强制刷新
        if not request.force_refresh:
            # 查找最近的分析结果
            recent_analysis = db.query(AIAnalysis).join(Stock).filter(
                Stock.symbol == symbol,
                AIAnalysis.created_at >= datetime.now() - timedelta(hours=1)
            ).first()
            
            if recent_analysis:
                return schemas.BaseResponse(
                    message="返回缓存的分析结果",
                    data=recent_analysis.analysis_content
                )
        
        # 添加后台任务进行分析
        background_tasks.add_task(
            perform_stock_analysis,
            symbol,
            request.analysis_types,
            db
        )
        
        return schemas.BaseResponse(
            message="分析任务已提交，请稍后查询结果",
            data={"symbol": symbol, "status": "processing"}
        )
        
    except Exception as e:
        logger.error(f"提交分析任务失败 {request.symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/analysis", response_model=schemas.BaseResponse)
async def get_stock_analysis(
    symbol: str,
    analysis_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """获取股票分析结果"""
    try:
        query = db.query(AIAnalysis).join(Stock).filter(Stock.symbol == symbol.upper())
        
        if analysis_type:
            query = query.filter(AIAnalysis.analysis_type == analysis_type)
        
        analyses = query.order_by(AIAnalysis.created_at.desc()).limit(10).all()
        
        if not analyses:
            raise HTTPException(status_code=404, detail="未找到分析结果")
        
        result = []
        for analysis in analyses:
            result.append({
                "id": analysis.id,
                "analysis_type": analysis.analysis_type,
                "content": analysis.analysis_content,
                "confidence_score": float(analysis.confidence_score) if analysis.confidence_score else None,
                "tags": analysis.tags,
                "created_at": analysis.created_at.isoformat()
            })
        
        return schemas.BaseResponse(data=result)
        
    except Exception as e:
        logger.error(f"获取分析结果失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/chart", response_model=schemas.BaseResponse)
async def get_stock_chart(
    symbol: str,
    period: str = "1y"
):
    """获取股票K线图数据"""
    try:
        stock_service = StockDataService()
        chart_data = stock_service.get_chart_data(symbol.upper(), period)
        
        if not chart_data:
            raise HTTPException(status_code=404, detail="无法获取图表数据")
        
        return schemas.BaseResponse(data=chart_data)
        
    except Exception as e:
        logger.error(f"获取图表数据失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def perform_stock_analysis(symbol: str, analysis_types: List[str], db: Session):
    """执行股票分析的后台任务"""
    try:
        stock_service = StockDataService()
        ai_service = AIAnalysisService()
        
        # 获取股票数据
        stock_info = stock_service.get_stock_info(symbol)
        chart_data = stock_service.get_chart_data(symbol)
        
        if not stock_info or not chart_data:
            logger.error(f"无法获取股票数据: {symbol}")
            return
        
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
        
        # 执行AI分析
        analysis_data = {
            "stock_info": stock_info,
            "indicators": chart_data.get("indicators", {})
        }
        
        comprehensive_analysis = ai_service.generate_comprehensive_analysis(symbol, analysis_data)
        
        # 保存分析结果
        for analysis_type, content in comprehensive_analysis.get("comprehensive_analysis", {}).items():
            if analysis_type in analysis_types:
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
        logger.info(f"股票分析完成: {symbol}")
        
    except Exception as e:
        logger.error(f"执行股票分析失败 {symbol}: {e}")
        db.rollback()