from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Text, JSON, Boolean, Date, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime

Base = declarative_base()

class Stock(Base):
    __tablename__ = "stocks"
    
    id = Column(Integer, primary_key=True, index=True)
    symbol = Column(String(20), unique=True, index=True, nullable=False)
    name = Column(String(100))
    exchange = Column(String(50))
    sector = Column(String(100))
    industry = Column(String(100))
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)
    
    prices = relationship("StockPrice", back_populates="stock")
    analyses = relationship("AIAnalysis", back_populates="stock")
    recommendations = relationship("StockRecommendation", back_populates="stock")

class StockPrice(Base):
    __tablename__ = "stock_prices"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    date = Column(Date, index=True)
    open_price = Column(Numeric(10, 2))
    high_price = Column(Numeric(10, 2))
    low_price = Column(Numeric(10, 2))
    close_price = Column(Numeric(10, 2))
    volume = Column(Integer)
    adj_close = Column(Numeric(10, 2))
    created_at = Column(DateTime, default=datetime.now)
    
    stock = relationship("Stock", back_populates="prices")

class AIAnalysis(Base):
    __tablename__ = "ai_analyses"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    analysis_type = Column(String(50), index=True)
    analysis_content = Column(JSON)
    confidence_score = Column(Numeric(3, 2))
    tags = Column(JSON)
    prompt_template = Column(Text)
    valid_until = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    stock = relationship("Stock", back_populates="analyses")

class StockRecommendation(Base):
    __tablename__ = "stock_recommendations"
    
    id = Column(Integer, primary_key=True, index=True)
    stock_id = Column(Integer, ForeignKey("stocks.id"))
    recommendation_type = Column(String(50))
    score = Column(Numeric(3, 2))
    reasoning = Column(Text)
    risk_level = Column(String(20))
    target_price = Column(Numeric(10, 2))
    stop_loss = Column(Numeric(10, 2))
    time_horizon = Column(String(50))
    expires_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.now)
    
    stock = relationship("Stock", back_populates="recommendations")

class AnalysisTask(Base):
    __tablename__ = "analysis_tasks"
    
    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String(50), unique=True, index=True)
    task_type = Column(String(50))
    symbols = Column(JSON)
    status = Column(String(20), default="pending")
    progress = Column(Integer, default=0)
    result = Column(JSON)
    error_message = Column(Text)
    created_at = Column(DateTime, default=datetime.now)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)

class UserQuery(Base):
    __tablename__ = "user_queries"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(50), index=True)
    query_message = Column(Text)
    response_data = Column(JSON)
    query_type = Column(String(50))
    created_at = Column(DateTime, default=datetime.now)

class StockNameMapping(Base):
    __tablename__ = "stock_name_mappings"
    
    id = Column(Integer, primary_key=True, index=True)
    chinese_name = Column(String(100), unique=True, index=True)
    english_name = Column(String(200))
    symbol = Column(String(20), index=True)
    created_at = Column(DateTime, default=datetime.now)
    updated_at = Column(DateTime, default=datetime.now, onupdate=datetime.now)