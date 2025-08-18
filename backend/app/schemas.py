from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from decimal import Decimal

# 基础响应模型
class BaseResponse(BaseModel):
    success: bool = True
    message: str = "操作成功"
    data: Optional[Any] = None

# 股票相关模型
class StockBase(BaseModel):
    symbol: str = Field(..., description="股票代码")
    name: Optional[str] = Field(None, description="股票名称")
    exchange: Optional[str] = Field(None, description="交易所")
    sector: Optional[str] = Field(None, description="行业板块")
    industry: Optional[str] = Field(None, description="细分行业")

class StockCreate(StockBase):
    pass

class Stock(StockBase):
    id: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

# 股价数据模型
class StockPriceBase(BaseModel):
    date: date
    open_price: Optional[Decimal]
    high_price: Optional[Decimal]
    low_price: Optional[Decimal]
    close_price: Optional[Decimal]
    volume: Optional[int]
    adj_close: Optional[Decimal]

class StockPrice(StockPriceBase):
    id: int
    stock_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# AI分析模型
class AIAnalysisBase(BaseModel):
    analysis_type: str = Field(..., description="分析类型")
    analysis_content: Dict[str, Any] = Field(..., description="分析内容")
    confidence_score: Optional[Decimal] = Field(None, description="置信度评分")
    tags: Optional[List[str]] = Field(None, description="标签")
    prompt_template: Optional[str] = Field(None, description="提示词模板")
    valid_until: Optional[datetime] = Field(None, description="有效期")

class AIAnalysisCreate(AIAnalysisBase):
    stock_id: int

class AIAnalysis(AIAnalysisBase):
    id: int
    stock_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 任务模型
class AnalysisTaskBase(BaseModel):
    task_type: str = Field(..., description="任务类型")
    symbols: List[str] = Field(..., description="股票代码列表")

class AnalysisTaskCreate(AnalysisTaskBase):
    pass

class AnalysisTask(AnalysisTaskBase):
    id: int
    task_id: str
    status: str
    progress: int
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    
    class Config:
        from_attributes = True

# 推荐模型
class StockRecommendationBase(BaseModel):
    recommendation_type: str = Field(..., description="推荐类型")
    score: Decimal = Field(..., description="推荐评分")
    reasoning: Optional[str] = Field(None, description="推荐理由")
    risk_level: Optional[str] = Field(None, description="风险等级")
    target_price: Optional[Decimal] = Field(None, description="目标价格")
    stop_loss: Optional[Decimal] = Field(None, description="止损价格")
    time_horizon: Optional[str] = Field(None, description="投资时间范围")
    expires_at: Optional[datetime] = Field(None, description="过期时间")

class StockRecommendationCreate(StockRecommendationBase):
    stock_id: int

class StockRecommendation(StockRecommendationBase):
    id: int
    stock_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 用户查询模型
class UserQueryRequest(BaseModel):
    message: str = Field(..., description="用户查询消息")
    session_id: Optional[str] = Field(None, description="会话ID")

class UserQueryResponse(BaseModel):
    analysis: Optional[Dict[str, Any]] = Field(None, description="分析结果")
    chart_data: Optional[Dict[str, Any]] = Field(None, description="K线图数据")
    recommendations: Optional[List[Dict[str, Any]]] = Field(None, description="推荐信息")
    reference_urls: Optional[List[str]] = Field(None, description="参考链接")

# 股票查询请求
class StockAnalysisRequest(BaseModel):
    symbol: str = Field(..., description="股票代码")
    analysis_types: Optional[List[str]] = Field(["technical", "fundamental"], description="分析类型")
    force_refresh: bool = Field(False, description="是否强制刷新")

# 批量任务请求
class BatchAnalysisRequest(BaseModel):
    symbols: List[str] = Field(..., description="股票代码列表")
    analysis_types: Optional[List[str]] = Field(["technical", "fundamental"], description="分析类型")
    priority: Optional[str] = Field("normal", description="任务优先级")