import numpy as np
import pandas as pd
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Stock, AIAnalysis, StockRecommendation, StockPrice
from ..database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class RecommendationService:
    """推荐算法服务"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.weights = {
            "technical_score": 0.3,
            "fundamental_score": 0.4,
            "sentiment_score": 0.2,
            "momentum_score": 0.1
        }
    
    def calculate_technical_score(self, analysis: Dict[str, Any]) -> float:
        """计算技术面评分"""
        try:
            score = 0.5  # 基础分数
            
            # RSI评分
            rsi = analysis.get("rsi")
            if rsi:
                if 30 <= rsi <= 70:
                    score += 0.2  # RSI在正常范围
                elif rsi < 30:
                    score += 0.3  # 超卖，可能反弹
                elif rsi > 70:
                    score -= 0.2  # 超买，风险较高
            
            # MACD评分
            macd_data = analysis.get("macd", {})
            if macd_data.get("histogram", 0) > 0:
                score += 0.15  # MACD柱状图为正
            
            # 移动平均线评分
            ma_data = analysis.get("moving_averages", {})
            current_price = analysis.get("current_price", 0)
            
            if current_price and ma_data:
                ma5 = ma_data.get("MA5", 0)
                ma20 = ma_data.get("MA20", 0)
                
                if ma5 > ma20 and current_price > ma5:
                    score += 0.2  # 短期趋势向上
                elif ma5 < ma20 and current_price < ma5:
                    score -= 0.2  # 短期趋势向下
            
            # 价格动量评分
            price_change = analysis.get("price_change_percent", 0)
            if 0 < price_change <= 5:
                score += 0.15  # 适度上涨
            elif price_change > 5:
                score += 0.1   # 大幅上涨，但可能过热
            elif -5 <= price_change < 0:
                score += 0.05  # 小幅下跌，可能是买入机会
            elif price_change < -5:
                score -= 0.1   # 大幅下跌
            
            return max(0, min(1, score))
            
        except Exception as e:
            logger.error(f"计算技术面评分失败: {e}")
            return 0.5
    
    def calculate_fundamental_score(self, stock_info: Dict[str, Any]) -> float:
        """计算基本面评分"""
        try:
            score = 0.5  # 基础分数
            
            # 市盈率评分
            pe_ratio = stock_info.get("pe_ratio")
            if pe_ratio:
                if 10 <= pe_ratio <= 25:
                    score += 0.2  # 合理估值
                elif pe_ratio < 10:
                    score += 0.3  # 低估值
                elif pe_ratio > 25:
                    score -= 0.1  # 高估值
            
            # 贝塔系数评分
            beta = stock_info.get("beta")
            if beta:
                if 0.8 <= beta <= 1.2:
                    score += 0.1  # 适中风险
                elif beta < 0.8:
                    score += 0.15 # 低风险
                elif beta > 1.5:
                    score -= 0.1  # 高风险
            
            # 股息收益率评分
            dividend_yield = stock_info.get("dividend_yield")
            if dividend_yield and dividend_yield > 0:
                if dividend_yield >= 0.02:  # 2%以上
                    score += 0.15
                else:
                    score += 0.05
            
            # 市值评分（大盘股相对稳定）
            market_cap = stock_info.get("market_cap")
            if market_cap:
                if market_cap > 100_000_000_000:  # 1000亿以上
                    score += 0.1
                elif market_cap > 10_000_000_000:  # 100亿以上
                    score += 0.05
            
            return max(0, min(1, score))
            
        except Exception as e:
            logger.error(f"计算基本面评分失败: {e}")
            return 0.5
    
    def calculate_sentiment_score(self, sentiment_analysis: Dict[str, Any]) -> float:
        """计算情绪面评分"""
        try:
            sentiment_score = sentiment_analysis.get("sentiment_score", 0)
            confidence_level = sentiment_analysis.get("confidence_level", "medium")
            
            # 将情绪分数转换为0-1范围
            base_score = (sentiment_score + 1) / 2  # -1到1转换为0到1
            
            # 根据置信度调整
            confidence_multiplier = {
                "low": 0.7,
                "medium": 1.0,
                "high": 1.2
            }.get(confidence_level, 1.0)
            
            return max(0, min(1, base_score * confidence_multiplier))
            
        except Exception as e:
            logger.error(f"计算情绪面评分失败: {e}")
            return 0.5
    
    def calculate_momentum_score(self, symbol: str) -> float:
        """计算动量评分"""
        try:
            # 获取最近的价格数据
            stock = self.session.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return 0.5
            
            recent_prices = self.session.query(StockPrice).filter(
                StockPrice.stock_id == stock.id
            ).order_by(StockPrice.date.desc()).limit(30).all()
            
            if len(recent_prices) < 10:
                return 0.5
            
            # 计算不同时间段的收益率
            prices = [float(p.close_price) for p in reversed(recent_prices)]
            
            # 1周、2周、1月收益率
            returns = {}
            periods = {"1w": 5, "2w": 10, "1m": 20}
            
            for period, days in periods.items():
                if len(prices) > days:
                    returns[period] = (prices[-1] - prices[-days-1]) / prices[-days-1]
            
            # 计算动量评分
            score = 0.5
            
            # 短期动量
            if "1w" in returns:
                if returns["1w"] > 0.02:  # 1周涨幅超过2%
                    score += 0.2
                elif returns["1w"] < -0.02:  # 1周跌幅超过2%
                    score -= 0.1
            
            # 中期动量
            if "1m" in returns:
                if returns["1m"] > 0.05:  # 1月涨幅超过5%
                    score += 0.3
                elif returns["1m"] < -0.05:  # 1月跌幅超过5%
                    score -= 0.2
            
            return max(0, min(1, score))
            
        except Exception as e:
            logger.error(f"计算动量评分失败 {symbol}: {e}")
            return 0.5
    
    def generate_stock_score(self, symbol: str) -> Dict[str, Any]:
        """生成股票综合评分"""
        try:
            # 获取最新的AI分析结果
            stock = self.session.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return {"error": "股票不存在"}
            
            recent_analyses = self.session.query(AIAnalysis).filter(
                AIAnalysis.stock_id == stock.id,
                AIAnalysis.created_at >= datetime.now() - timedelta(days=1)
            ).all()
            
            # 组织分析数据
            analysis_data = {}
            for analysis in recent_analyses:
                analysis_data[analysis.analysis_type] = analysis.analysis_content
            
            # 计算各项评分
            scores = {}
            
            # 技术面评分
            if "technical" in analysis_data:
                scores["technical_score"] = self.calculate_technical_score(
                    analysis_data["technical"]
                )
            else:
                scores["technical_score"] = 0.5
            
            # 基本面评分
            if "fundamental" in analysis_data:
                scores["fundamental_score"] = self.calculate_fundamental_score(
                    analysis_data["fundamental"]
                )
            else:
                scores["fundamental_score"] = 0.5
            
            # 情绪面评分
            if "sentiment" in analysis_data:
                scores["sentiment_score"] = self.calculate_sentiment_score(
                    analysis_data["sentiment"]
                )
            else:
                scores["sentiment_score"] = 0.5
            
            # 动量评分
            scores["momentum_score"] = self.calculate_momentum_score(symbol)
            
            # 计算综合评分
            total_score = sum(
                scores[key] * self.weights[key] 
                for key in scores if key in self.weights
            )
            
            # 生成推荐等级
            if total_score >= 0.8:
                recommendation = "strong_buy"
                risk_level = "medium"
            elif total_score >= 0.65:
                recommendation = "buy"
                risk_level = "medium"
            elif total_score >= 0.45:
                recommendation = "hold"
                risk_level = "medium"
            elif total_score >= 0.3:
                recommendation = "sell"
                risk_level = "high"
            else:
                recommendation = "strong_sell"
                risk_level = "high"
            
            return {
                "symbol": symbol,
                "total_score": round(total_score, 3),
                "component_scores": scores,
                "recommendation": recommendation,
                "risk_level": risk_level,
                "confidence": min(0.9, total_score + 0.1),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"生成股票评分失败 {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    def find_potential_stocks(self, limit: int = 10) -> List[Dict[str, Any]]:
        """寻找潜力股票"""
        try:
            # 获取所有有分析数据的股票
            stocks_with_analysis = self.session.query(Stock).join(AIAnalysis).filter(
                AIAnalysis.created_at >= datetime.now() - timedelta(days=1)
            ).distinct().all()
            
            stock_scores = []
            
            for stock in stocks_with_analysis:
                score_data = self.generate_stock_score(stock.symbol)
                if "error" not in score_data:
                    stock_scores.append(score_data)
            
            # 按评分排序
            stock_scores.sort(key=lambda x: x["total_score"], reverse=True)
            
            # 返回前N只股票
            return stock_scores[:limit]
            
        except Exception as e:
            logger.error(f"寻找潜力股票失败: {e}")
            return []
    
    def save_recommendation(self, symbol: str, recommendation_data: Dict[str, Any]) -> bool:
        """保存推荐结果到数据库"""
        try:
            stock = self.session.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                return False
            
            # 删除旧的推荐
            self.session.query(StockRecommendation).filter(
                StockRecommendation.stock_id == stock.id
            ).delete()
            
            # 创建新推荐
            recommendation = StockRecommendation(
                stock_id=stock.id,
                recommendation_type=recommendation_data.get("recommendation"),
                score=recommendation_data.get("total_score", 0),
                reasoning=f"综合评分: {recommendation_data.get('total_score', 0):.3f}",
                risk_level=recommendation_data.get("risk_level"),
                time_horizon="medium",
                expires_at=datetime.now() + timedelta(days=1)
            )
            
            self.session.add(recommendation)
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存推荐失败 {symbol}: {e}")
            self.session.rollback()
            return False
    
    def get_recommendations_by_criteria(self, 
                                      min_score: float = 0.6,
                                      risk_levels: List[str] = None,
                                      limit: int = 20) -> List[Dict[str, Any]]:
        """根据条件获取推荐"""
        try:
            query = self.session.query(StockRecommendation).join(Stock).filter(
                StockRecommendation.score >= min_score,
                StockRecommendation.expires_at > datetime.now()
            )
            
            if risk_levels:
                query = query.filter(StockRecommendation.risk_level.in_(risk_levels))
            
            recommendations = query.order_by(
                StockRecommendation.score.desc()
            ).limit(limit).all()
            
            result = []
            for rec in recommendations:
                result.append({
                    "symbol": rec.stock.symbol,
                    "name": rec.stock.name,
                    "recommendation": rec.recommendation_type,
                    "score": float(rec.score),
                    "risk_level": rec.risk_level,
                    "reasoning": rec.reasoning,
                    "created_at": rec.created_at.isoformat()
                })
            
            return result
            
        except Exception as e:
            logger.error(f"获取推荐失败: {e}")
            return []
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()
