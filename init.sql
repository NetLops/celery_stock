-- 创建数据库表结构

-- 股票基本信息表
CREATE TABLE IF NOT EXISTS stocks (
    id SERIAL PRIMARY KEY,
    symbol VARCHAR(20) UNIQUE NOT NULL,
    name VARCHAR(200),
    exchange VARCHAR(50),
    sector VARCHAR(100),
    industry VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 股票价格数据表
CREATE TABLE IF NOT EXISTS stock_prices (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    date DATE NOT NULL,
    open_price DECIMAL(10,4),
    high_price DECIMAL(10,4),
    low_price DECIMAL(10,4),
    close_price DECIMAL(10,4),
    volume BIGINT,
    adj_close DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(stock_id, date)
);

-- AI分析结果表
CREATE TABLE IF NOT EXISTS ai_analysis (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    analysis_type VARCHAR(50) NOT NULL, -- 'technical', 'fundamental', 'sentiment', 'recommendation'
    analysis_content JSONB NOT NULL,
    confidence_score DECIMAL(3,2), -- 0.00 to 1.00
    tags TEXT[], -- 用于分类标识
    prompt_template VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    valid_until TIMESTAMP -- 分析有效期
);

-- 任务队列表
CREATE TABLE IF NOT EXISTS analysis_tasks (
    id SERIAL PRIMARY KEY,
    task_id VARCHAR(100) UNIQUE NOT NULL,
    task_type VARCHAR(50) NOT NULL, -- 'single_stock', 'batch_stocks', 'market_scan'
    symbols TEXT[] NOT NULL,
    status VARCHAR(20) DEFAULT 'pending', -- 'pending', 'running', 'completed', 'failed'
    progress INTEGER DEFAULT 0,
    result JSONB,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP
);

-- 用户查询历史表
CREATE TABLE IF NOT EXISTS user_queries (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(100),
    query_message TEXT NOT NULL,
    response_data JSONB NOT NULL,
    query_type VARCHAR(50), -- 'analysis', 'recommendation', 'chart_data'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 推荐股票表
CREATE TABLE IF NOT EXISTS stock_recommendations (
    id SERIAL PRIMARY KEY,
    stock_id INTEGER REFERENCES stocks(id),
    recommendation_type VARCHAR(50), -- 'buy', 'sell', 'hold'
    score DECIMAL(3,2), -- 推荐评分 0.00-1.00
    reasoning TEXT,
    risk_level VARCHAR(20), -- 'low', 'medium', 'high'
    target_price DECIMAL(10,4),
    stop_loss DECIMAL(10,4),
    time_horizon VARCHAR(20), -- 'short', 'medium', 'long'
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    expires_at TIMESTAMP
);

-- 创建索引优化查询性能
CREATE INDEX IF NOT EXISTS idx_stock_prices_symbol_date ON stock_prices(stock_id, date DESC);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_stock_type ON ai_analysis(stock_id, analysis_type);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_tags ON ai_analysis USING GIN(tags);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON analysis_tasks(status);
CREATE INDEX IF NOT EXISTS idx_recommendations_score ON stock_recommendations(score DESC);

-- 插入一些示例数据
INSERT INTO stocks (symbol, name, exchange, sector, industry) VALUES
('AAPL', 'Apple Inc.', 'NASDAQ', 'Technology', 'Consumer Electronics'),
('GOOGL', 'Alphabet Inc.', 'NASDAQ', 'Technology', 'Internet Content & Information'),
('MSFT', 'Microsoft Corporation', 'NASDAQ', 'Technology', 'Software'),
('TSLA', 'Tesla, Inc.', 'NASDAQ', 'Consumer Cyclical', 'Auto Manufacturers'),
('AMZN', 'Amazon.com, Inc.', 'NASDAQ', 'Consumer Cyclical', 'Internet Retail')
ON CONFLICT (symbol) DO NOTHING;