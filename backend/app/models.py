from sqlalchemy import Column, Integer, String, DateTime, Text, Boolean, Date, BigInteger, ARRAY
from decimal import Decimal
from sqlalchemy.types import DECIMAL
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from sqlalchemy import ForeignKey
from .database import Base

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(200))
    exchange = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(100))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    # 关联关系
    prices = relationship("StockPrice", back_populates="stock")
    analyses = relationship("AIAnalysis", back_populates="stock")
    recommendations = relationship("StockRecommendation", back_populates="stock")

class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    date = Column(Date, nullable=False)
    open_price = Column(DECIMAL(10, 4))
    high_price = Column(DECIMAL(10, 4))
    low_price = Column(DECIMAL(10, 4))
    close_price = Column(DECIMAL(10, 4))
    volume = Column(BigInteger)
    adj_close = Column(DECIMAL(10, 4))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关联关系
    stock = relationship("Stock", back_populates="prices")

class AIAnalysis(Base):
    __tablename__ = "ai_analysis"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    analysis_type = Column(String(50), nullable=False)  # 'technical', 'fundamental', 'sentiment', 'recommendation'
    analysis_content = Column(JSONB, nullable=False)
    confidence_score = Column(DECIMAL(3, 2))  # 0.00 to 1.00
    tags = Column(ARRAY(Text))  # 用于分类标识
    prompt_template = Column(String(500))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    valid_until = Column(DateTime(timezone=True))  # 分析有效期
    
    # 关联关系
    stock = relationship("Stock", back_populates="analyses")

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(100), unique=True, nullable=False)
    task_type = Column(String(50), nullable=False)  # 'single_stock', 'batch_stocks', 'market_scan'
    symbols = Column(ARRAY(Text), nullable=False)
    status = Column(String(20), default='pending')  # 'pending', 'running', 'completed', 'failed'
    progress = Column(Integer, default=0)
    result = Column(JSONB)
    error_message = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    started_at = Column(DateTime(timezone=True))
    completed_at = Column(DateTime(timezone=True))

class UserQuery(Base):
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100))
    query_message = Column(Text, nullable=False)
    response_data = Column(JSONB, nullable=False)
    query_type = Column(String(50))  # 'analysis', 'recommendation', 'chart_data'
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class StockRecommendation(Base):
    __tablename__ = "stock_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"), nullable=False)
    recommendation_type = Column(String(50))  # 'buy', 'sell', 'hold'
    score = Column(DECIMAL(3, 2))  # 推荐评分 0.00-1.00
    reasoning = Column(Text)
    risk_level = Column(String(20))  # 'low', 'medium', 'high'
    target_price = Column(DECIMAL(10, 4))
    stop_loss = Column(DECIMAL(10, 4))
    time_horizon = Column(String(20))  # 'short', 'medium', 'long'
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    expires_at = Column(DateTime(timezone=True))
    
    # 关联关系
    stock = relationship("Stock", back_populates="recommendations")