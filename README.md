# 智能股票分析系统

基于AI的股票分析平台，提供技术分析、基本面分析、情绪分析和智能推荐功能。

## 🚀 功能特性

### 核心功能
1. **单股分析** - 结合AI进行深度分析，结果同步到数据库
2. **批量任务** - 定向抓取多只股票的分析内容
3. **智能推荐** - AI自动选取潜力股票
4. **智能问答** - 基于用户消息和数据库内容的AI助手

### 技术特点
- **RESTful API** - 标准化接口设计
- **JSON序列化** - 统一数据交互格式
- **前后端分离** - React + Python FastAPI
- **Docker部署** - 一键快速部署
- **AI集成** - OpenAI GPT-4 智能分析
- **异步任务** - Celery处理批量分析

## 🏗️ 架构设计

### 系统架构
```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   前端 (React)   │────│  API Gateway    │────│  后端服务群      │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐    ┌─────────────────┐
                       │  PostgreSQL     │────│   Redis Cache   │
                       └─────────────────┘    └─────────────────┘
                                │
                       ┌─────────────────┐
                       │  Celery Worker  │
                       └─────────────────┘
```

### 核心组件
- **Stock Service**: 股票数据获取和技术指标计算
- **AI Service**: OpenAI集成，智能分析生成
- **Recommendation Service**: 推荐算法和评分系统
- **Task Queue**: 异步任务处理
- **Database**: PostgreSQL存储，支持JSON字段

## 📊 推荐算法原理

### 综合评分模型
```python
总评分 = 技术面评分 × 0.3 + 基本面评分 × 0.4 + 情绪面评分 × 0.2 + 动量评分 × 0.1
```

### 评分维度
1. **技术面评分** (30%)
   - RSI指标: 超卖区间加分，超买区间减分
   - MACD: 金叉信号加分，死叉信号减分
   - 移动平均线: 多头排列加分
   - 价格动量: 适度上涨最优

2. **基本面评分** (40%)
   - 市盈率: 10-25倍为合理区间
   - 贝塔系数: 0.8-1.2为适中风险
   - 股息收益率: 有分红加分
   - 市值规模: 大盘股相对稳定

3. **情绪面评分** (20%)
   - 市场情绪指数: -1到1转换为0到1
   - 置信度调整: 高置信度乘以1.2倍

4. **动量评分** (10%)
   - 短期动量: 1周涨幅2%以上加分
   - 中期动量: 1月涨幅5%以上加分

### 推荐等级
- **强烈买入** (≥0.8): 综合评分优秀
- **买入** (0.65-0.8): 综合评分良好
- **持有** (0.45-0.65): 综合评分一般
- **卖出** (0.3-0.45): 综合评分较差
- **强烈卖出** (<0.3): 综合评分差

## 🛠️ 快速开始

### 环境要求
- Docker & Docker Compose
- OpenAI API Key

### 部署步骤

1. **克隆项目**
```bash
git clone <repository-url>
cd stock-analysis-system
```

2. **配置环境变量**
```bash
cp .env.example .env
# 编辑 .env 文件，设置 OPENAI_API_KEY
```

3. **启动服务**
```bash
docker-compose up -d
```

4. **访问应用**
- 前端: http://localhost:3000
- API文档: http://localhost:8000/docs
- 数据库: localhost:5432

### API接口

#### 股票分析
```bash
# 获取股票信息
GET /api/v1/stocks/{symbol}

# 分析股票
POST /api/v1/stocks/analyze
{
  "symbol": "AAPL",
  "analysis_types": ["technical", "fundamental"],
  "force_refresh": false
}

# 获取分析结果
GET /api/v1/stocks/{symbol}/analysis

# 获取K线图数据
GET /api/v1/stocks/{symbol}/chart?period=1y
```

#### 批量任务
```bash
# 创建批量分析任务
POST /api/v1/tasks/batch-analysis
{
  "symbols": ["AAPL", "GOOGL", "MSFT"],
  "analysis_types": ["technical", "fundamental"],
  "priority": "normal"
}

# 获取任务状态
GET /api/v1/tasks/{task_id}
```

#### 推荐系统
```bash
# 获取推荐列表
GET /api/v1/recommendations?min_score=0.6&limit=20

# 获取潜力股票
GET /api/v1/recommendations/potential?limit=10

# 获取股票评分
GET /api/v1/recommendations/{symbol}/score
```

#### AI问答
```bash
# 用户查询
POST /api/v1/analysis/query
{
  "message": "帮我分析一下苹果公司的股票",
  "session_id": "optional-session-id"
}
```

## 🎯 设计原理

### 为什么选择这种架构？

1. **微服务架构**
   - ✅ 模块化设计，便于维护和扩展
   - ✅ 服务独立部署，提高可用性
   - ✅ 技术栈灵活，可针对性优化

2. **PostgreSQL + Redis**
   - ✅ PostgreSQL支持JSON字段，适合复杂数据
   - ✅ Redis提供高性能缓存，提升响应速度
   - ✅ 数据持久化和缓存分离，架构清晰

3. **Celery异步任务**
   - ✅ 批量分析不阻塞主线程
   - ✅ 任务队列支持优先级和重试
   - ✅ 水平扩展，支持多Worker

4. **AI集成策略**
   - ✅ 标准化提示词模板，保证分析质量
   - ✅ 分类标签系统，便于数据检索
   - ✅ 置信度评分，量化分析可靠性

### 是否为最优解？

**优势:**
- 架构清晰，职责分明
- 技术栈成熟，生态完善
- 部署简单，运维友好
- 扩展性强，支持高并发

**可优化点:**
- 可考虑引入消息队列(RabbitMQ)替代Redis作为任务队列
- 可添加API网关(Kong/Nginx)进行负载均衡
- 可引入时序数据库(InfluxDB)存储股价数据
- 可添加监控系统(Prometheus+Grafana)

**适用场景:**
- 中小型股票分析平台
- 个人投资决策工具
- 量化交易辅助系统
- 金融数据分析研究

## 📈 使用示例

### 1. 单股分析
```python
# 分析苹果公司股票
curl -X POST "http://localhost:8000/api/v1/stocks/analyze" \
  -H "Content-Type: application/json" \
  -d '{
    "symbol": "AAPL",
    "analysis_types": ["technical", "fundamental", "sentiment"],
    "force_refresh": true
  }'
```

### 2. 批量分析
```python
# 批量分析科技股
curl -X POST "http://localhost:8000/api/v1/tasks/batch-analysis" \
  -H "Content-Type: application/json" \
  -d '{
    "symbols": ["AAPL", "GOOGL", "MSFT", "AMZN", "TSLA"],
    "analysis_types": ["technical", "fundamental"],
    "priority": "high"
  }'
```

### 3. 获取推荐
```python
# 获取高评分推荐
curl "http://localhost:8000/api/v1/recommendations?min_score=0.7&limit=10"
```

## 🔧 开发指南

### 添加新的分析类型
1. 在 `ai_service.py` 中添加提示词模板
2. 在 `recommendation_service.py` 中添加评分逻辑
3. 更新数据库模型和API接口

### 自定义推荐算法
1. 修改 `RecommendationService` 中的权重配置
2. 添加新的评分维度计算方法
3. 调整推荐等级阈值

### 扩展数据源
1. 在 `StockDataService` 中添加新的数据提供商
2. 统一数据格式和接口
3. 更新缓存策略

## 📝 许可证

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请通过 GitHub Issues 联系。