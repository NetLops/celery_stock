from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any
from ..database import get_db
from .. import schemas
from ..services.ai_service import AIAnalysisService
from ..services.stock_service import StockDataService
from ..models import Stock, AIAnalysis, UserQuery
from datetime import datetime
import uuid
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/query", response_model=schemas.BaseResponse)
async def handle_user_query(
    request: schemas.UserQueryRequest,
    db: Session = Depends(get_db)
):
    """处理用户查询"""
    try:
        ai_service = AIAnalysisService()
        stock_service = StockDataService()
        
        # 生成会话ID
        session_id = request.session_id or str(uuid.uuid4())
        
        # 分析查询内容，提取可能的股票代码
        query_text = request.message.upper()
        potential_symbols = extract_stock_symbols(query_text)
        
        # 收集相关数据
        context_data = {}
        
        if potential_symbols:
            for symbol in potential_symbols[:3]:  # 限制最多3只股票
                # 获取股票基本信息
                stock_info = stock_service.get_stock_info(symbol)
                if stock_info:
                    context_data[symbol] = {
                        "stock_info": stock_info,
                        "chart_data": stock_service.get_chart_data(symbol, "3mo")
                    }
                    
                    # 获取最新分析结果
                    stock = db.query(Stock).filter(Stock.symbol == symbol).first()
                    if stock:
                        recent_analyses = db.query(AIAnalysis).filter(
                            AIAnalysis.stock_id == stock.id
                        ).order_by(AIAnalysis.created_at.desc()).limit(5).all()
                        
                        context_data[symbol]["analyses"] = [
                            {
                                "type": a.analysis_type,
                                "content": a.analysis_content,
                                "created_at": a.created_at.isoformat()
                            }
                            for a in recent_analyses
                        ]
        
        # 如果没有找到具体股票，提供市场概览
        if not context_data:
            context_data = await get_market_overview(db)
        
        # 使用AI回答用户问题
        ai_response = ai_service.answer_user_query(request.message, context_data)
        
        # 构建响应数据
        response_data = schemas.UserQueryResponse(
            analysis=ai_response.get("analysis", {}),
            chart_data=ai_response.get("chart_suggestions", {}),
            recommendations=ai_response.get("recommendations", []),
            reference_urls=ai_response.get("references", [])
        )
        
        # 保存查询历史
        user_query = UserQuery(
            session_id=session_id,
            query_message=request.message,
            response_data=response_data.dict(),
            query_type="general"
        )
        db.add(user_query)
        db.commit()
        
        return schemas.BaseResponse(
            data={
                "session_id": session_id,
                "answer": ai_response.get("answer", ""),
                "response": response_data.dict(),
                "context_symbols": list(context_data.keys())
            }
        )
        
    except Exception as e:
        logger.error(f"处理用户查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{session_id}", response_model=schemas.BaseResponse)
async def get_query_history(
    session_id: str,
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取查询历史"""
    try:
        queries = db.query(UserQuery).filter(
            UserQuery.session_id == session_id
        ).order_by(UserQuery.created_at.desc()).limit(limit).all()
        
        history = []
        for query in queries:
            history.append({
                "id": query.id,
                "message": query.query_message,
                "response": query.response_data,
                "created_at": query.created_at.isoformat()
            })
        
        return schemas.BaseResponse(data=history)
        
    except Exception as e:
        logger.error(f"获取查询历史失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare", response_model=schemas.BaseResponse)
async def compare_stocks(
    symbols: List[str],
    db: Session = Depends(get_db)
):
    """比较多只股票"""
    try:
        if len(symbols) > 5:
            raise HTTPException(status_code=400, detail="最多只能比较5只股票")
        
        stock_service = StockDataService()
        ai_service = AIAnalysisService()
        
        comparison_data = {}
        
        for symbol in symbols:
            symbol = symbol.upper()
            
            # 获取股票数据
            stock_info = stock_service.get_stock_info(symbol)
            chart_data = stock_service.get_chart_data(symbol, "6m")
            
            if stock_info and chart_data:
                comparison_data[symbol] = {
                    "basic_info": stock_info,
                    "technical_indicators": chart_data.get("indicators", {}),
                    "performance": calculate_performance_metrics(chart_data)
                }
        
        if not comparison_data:
            raise HTTPException(status_code=404, detail="无法获取股票数据")
        
        # 使用AI进行比较分析
        comparison_prompt = f"""
请比较以下股票的投资价值：

{json.dumps(comparison_data, indent=2, ensure_ascii=False)}

请提供：
1. 各股票的优缺点分析
2. 风险收益比较
3. 投资建议排序
4. 适合的投资策略

请以JSON格式返回比较结果。
"""
        
        ai_response = ai_service.client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "你是专业的股票分析师，请提供客观的比较分析。"},
                {"role": "user", "content": comparison_prompt}
            ],
            temperature=0.3
        )
        
        try:
            comparison_result = json.loads(ai_response.choices[0].message.content)
        except:
            comparison_result = {"analysis": ai_response.choices[0].message.content}
        
        return schemas.BaseResponse(
            data={
                "symbols": symbols,
                "comparison_data": comparison_data,
                "ai_analysis": comparison_result,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"股票比较失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def extract_stock_symbols(text: str) -> List[str]:
    """从文本中提取股票代码"""
    import re
    
    # 常见股票代码模式
    patterns = [
        r'\b[A-Z]{1,5}\b',  # 美股代码
        r'\b\d{6}\b',       # A股代码
        r'\b[A-Z]{2,4}\d{1,3}\b'  # 港股代码
    ]
    
    symbols = []
    for pattern in patterns:
        matches = re.findall(pattern, text)
        symbols.extend(matches)
    
    # 过滤常见非股票代码的词汇
    exclude_words = {'THE', 'AND', 'FOR', 'ARE', 'BUT', 'NOT', 'YOU', 'ALL', 'CAN', 'HER', 'WAS', 'ONE', 'OUR', 'HAD', 'BY'}
    symbols = [s for s in symbols if s not in exclude_words]
    
    return list(set(symbols))  # 去重

async def get_market_overview(db: Session) -> Dict[str, Any]:
    """获取市场概览数据"""
    try:
        # 获取最近分析的股票
        recent_stocks = db.query(Stock).join(AIAnalysis).order_by(
            AIAnalysis.created_at.desc()
        ).limit(10).all()
        
        market_data = {}
        for stock in recent_stocks:
            market_data[stock.symbol] = {
                "name": stock.name,
                "sector": stock.sector,
                "industry": stock.industry
            }
        
        return {"market_overview": market_data}
        
    except Exception as e:
        logger.error(f"获取市场概览失败: {e}")
        return {}

def calculate_performance_metrics(chart_data: Dict[str, Any]) -> Dict[str, Any]:
    """计算股票表现指标"""
    try:
        data = chart_data.get("data", [])
        if len(data) < 2:
            return {}
        
        # 计算收益率
        first_price = data[0]["close"]
        last_price = data[-1]["close"]
        total_return = (last_price - first_price) / first_price * 100
        
        # 计算波动率
        prices = [d["close"] for d in data]
        returns = [(prices[i] - prices[i-1]) / prices[i-1] for i in range(1, len(prices))]
        volatility = np.std(returns) * np.sqrt(252) * 100  # 年化波动率
        
        # 计算最大回撤
        peak = prices[0]
        max_drawdown = 0
        for price in prices:
            if price > peak:
                peak = price
            drawdown = (peak - price) / peak
            if drawdown > max_drawdown:
                max_drawdown = drawdown
        
        return {
            "total_return": round(total_return, 2),
            "volatility": round(volatility, 2),
            "max_drawdown": round(max_drawdown * 100, 2),
            "sharpe_ratio": round(total_return / volatility if volatility > 0 else 0, 2)
        }
        
    except Exception as e:
        logger.error(f"计算表现指标失败: {e}")
        return {}