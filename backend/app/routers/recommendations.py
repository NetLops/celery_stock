from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from ..database import get_db
from ..schemas import *
from ..services.recommendation_service import RecommendationService
from ..models import StockRecommendation, Stock
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/", response_model=BaseResponse)
async def get_recommendations(
    min_score: float = 0.6,
    risk_levels: Optional[str] = None,
    limit: int = 20,
    db: Session = Depends(get_db)
):
    """获取股票推荐列表"""
    try:
        recommendation_service = RecommendationService()
        
        # 解析风险等级参数
        risk_level_list = None
        if risk_levels:
            risk_level_list = [level.strip() for level in risk_levels.split(",")]
        
        recommendations = recommendation_service.get_recommendations_by_criteria(
            min_score=min_score,
            risk_levels=risk_level_list,
            limit=limit
        )
        
        return BaseResponse(
            data={
                "recommendations": recommendations,
                "criteria": {
                    "min_score": min_score,
                    "risk_levels": risk_level_list,
                    "limit": limit
                },
                "total_count": len(recommendations)
            }
        )
        
    except Exception as e:
        logger.error(f"获取推荐列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/potential", response_model=BaseResponse)
async def get_potential_stocks(
    limit: int = 10,
    db: Session = Depends(get_db)
):
    """获取潜力股票推荐"""
    try:
        recommendation_service = RecommendationService()
        potential_stocks = recommendation_service.find_potential_stocks(limit=limit)
        
        return BaseResponse(
            message=f"找到 {len(potential_stocks)} 只潜力股票",
            data={
                "potential_stocks": potential_stocks,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取潜力股票失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{symbol}/score", response_model=BaseResponse)
async def get_stock_score(symbol: str, db: Session = Depends(get_db)):
    """获取单个股票的综合评分"""
    try:
        recommendation_service = RecommendationService()
        score_data = recommendation_service.generate_stock_score(symbol.upper())
        
        if "error" in score_data:
            raise HTTPException(status_code=404, detail=score_data["error"])
        
        return BaseResponse(data=score_data)
        
    except Exception as e:
        logger.error(f"获取股票评分失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/{symbol}/generate", response_model=BaseResponse)
async def generate_recommendation(symbol: str, db: Session = Depends(get_db)):
    """为指定股票生成推荐"""
    try:
        recommendation_service = RecommendationService()
        
        # 生成评分
        score_data = recommendation_service.generate_stock_score(symbol.upper())
        
        if "error" in score_data:
            raise HTTPException(status_code=404, detail=score_data["error"])
        
        # 保存推荐结果
        success = recommendation_service.save_recommendation(symbol.upper(), score_data)
        
        if not success:
            raise HTTPException(status_code=500, detail="保存推荐失败")
        
        return BaseResponse(
            message="推荐已生成并保存",
            data=score_data
        )
        
    except Exception as e:
        logger.error(f"生成推荐失败 {symbol}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/sectors/analysis", response_model=BaseResponse)
async def get_sector_analysis(db: Session = Depends(get_db)):
    """获取行业板块分析"""
    try:
        # 按行业统计推荐情况
        sector_stats = db.query(
            Stock.sector,
            func.count(StockRecommendation.id).label('recommendation_count'),
            func.avg(StockRecommendation.score).label('avg_score')
        ).join(StockRecommendation).filter(
            StockRecommendation.expires_at > datetime.now()
        ).group_by(Stock.sector).all()
        
        sector_analysis = []
        for sector, count, avg_score in sector_stats:
            if sector:  # 过滤空值
                sector_analysis.append({
                    "sector": sector,
                    "recommendation_count": count,
                    "average_score": round(float(avg_score), 3) if avg_score else 0,
                    "performance_rating": get_sector_rating(float(avg_score) if avg_score else 0)
                })
        
        # 按平均评分排序
        sector_analysis.sort(key=lambda x: x["average_score"], reverse=True)
        
        return BaseResponse(
            data={
                "sector_analysis": sector_analysis,
                "total_sectors": len(sector_analysis),
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取行业分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/risk/analysis", response_model=BaseResponse)
async def get_risk_analysis(db: Session = Depends(get_db)):
    """获取风险分析报告"""
    try:
        # 按风险等级统计
        risk_stats = db.query(
            StockRecommendation.risk_level,
            func.count(StockRecommendation.id).label('count'),
            func.avg(StockRecommendation.score).label('avg_score')
        ).filter(
            StockRecommendation.expires_at > datetime.now()
        ).group_by(StockRecommendation.risk_level).all()
        
        risk_analysis = []
        for risk_level, count, avg_score in risk_stats:
            if risk_level:
                risk_analysis.append({
                    "risk_level": risk_level,
                    "stock_count": count,
                    "average_score": round(float(avg_score), 3) if avg_score else 0
                })
        
        # 获取推荐类型分布
        recommendation_stats = db.query(
            StockRecommendation.recommendation_type,
            func.count(StockRecommendation.id).label('count')
        ).filter(
            StockRecommendation.expires_at > datetime.now()
        ).group_by(StockRecommendation.recommendation_type).all()
        
        recommendation_distribution = [
            {"type": rec_type, "count": count}
            for rec_type, count in recommendation_stats
        ]
        
        return BaseResponse(
            data={
                "risk_analysis": risk_analysis,
                "recommendation_distribution": recommendation_distribution,
                "generated_at": datetime.now().isoformat()
            }
        )
        
    except Exception as e:
        logger.error(f"获取风险分析失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

def get_sector_rating(avg_score: float) -> str:
    """根据平均评分获取行业评级"""
    if avg_score >= 0.8:
        return "优秀"
    elif avg_score >= 0.65:
        return "良好"
    elif avg_score >= 0.5:
        return "一般"
    elif avg_score >= 0.35:
        return "较差"
    else:
        return "差"