import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Stock, StockPrice
from ..database import SessionLocal
import logging

logger = logging.getLogger(__name__)

class StockDataService:
    """股票数据服务"""
    
    def __init__(self):
        self.session = SessionLocal()
    
    def get_stock_info(self, symbol: str) -> Optional[Dict[str, Any]]:
        """获取股票基本信息"""
        try:
            ticker = yf.Ticker(symbol)
            info = ticker.info
            
            return {
                "symbol": symbol,
                "name": info.get("longName", ""),
                "exchange": info.get("exchange", ""),
                "sector": info.get("sector", ""),
                "industry": info.get("industry", ""),
                "market_cap": info.get("marketCap"),
                "pe_ratio": info.get("trailingPE"),
                "dividend_yield": info.get("dividendYield"),
                "beta": info.get("beta"),
                "52_week_high": info.get("fiftyTwoWeekHigh"),
                "52_week_low": info.get("fiftyTwoWeekLow"),
                "current_price": info.get("currentPrice")
            }
        except Exception as e:
            logger.error(f"获取股票信息失败 {symbol}: {e}")
            return None
    
    def get_historical_data(self, symbol: str, period: str = "1y") -> Optional[pd.DataFrame]:
        """获取历史价格数据"""
        try:
            ticker = yf.Ticker(symbol)
            data = ticker.history(period=period)
            return data
        except Exception as e:
            logger.error(f"获取历史数据失败 {symbol}: {e}")
            return None
    
    def save_stock_data(self, symbol: str, data: pd.DataFrame) -> bool:
        """保存股票数据到数据库"""
        try:
            # 获取或创建股票记录
            stock = self.session.query(Stock).filter(Stock.symbol == symbol).first()
            if not stock:
                stock_info = self.get_stock_info(symbol)
                if stock_info:
                    stock = Stock(
                        symbol=symbol,
                        name=stock_info.get("name"),
                        exchange=stock_info.get("exchange"),
                        sector=stock_info.get("sector"),
                        industry=stock_info.get("industry")
                    )
                    self.session.add(stock)
                    self.session.commit()
                else:
                    return False
            
            # 保存价格数据
            for date, row in data.iterrows():
                existing = self.session.query(StockPrice).filter(
                    StockPrice.stock_id == stock.id,
                    StockPrice.date == date.date()
                ).first()
                
                if not existing:
                    price_record = StockPrice(
                        stock_id=stock.id,
                        date=date.date(),
                        open_price=float(row['Open']),
                        high_price=float(row['High']),
                        low_price=float(row['Low']),
                        close_price=float(row['Close']),
                        volume=int(row['Volume']),
                        adj_close=float(row['Close'])
                    )
                    self.session.add(price_record)
            
            self.session.commit()
            return True
            
        except Exception as e:
            logger.error(f"保存股票数据失败 {symbol}: {e}")
            self.session.rollback()
            return False
    
    def calculate_technical_indicators(self, data: pd.DataFrame) -> Dict[str, Any]:
        """计算技术指标"""
        try:
            # 移动平均线
            data['MA5'] = data['Close'].rolling(window=5).mean()
            data['MA10'] = data['Close'].rolling(window=10).mean()
            data['MA20'] = data['Close'].rolling(window=20).mean()
            data['MA50'] = data['Close'].rolling(window=50).mean()
            
            # RSI
            delta = data['Close'].diff()
            gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
            loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
            rs = gain / loss
            data['RSI'] = 100 - (100 / (1 + rs))
            
            # MACD
            exp1 = data['Close'].ewm(span=12).mean()
            exp2 = data['Close'].ewm(span=26).mean()
            data['MACD'] = exp1 - exp2
            data['MACD_signal'] = data['MACD'].ewm(span=9).mean()
            data['MACD_histogram'] = data['MACD'] - data['MACD_signal']
            
            # 布林带
            data['BB_middle'] = data['Close'].rolling(window=20).mean()
            bb_std = data['Close'].rolling(window=20).std()
            data['BB_upper'] = data['BB_middle'] + (bb_std * 2)
            data['BB_lower'] = data['BB_middle'] - (bb_std * 2)
            
            # 获取最新值
            latest = data.iloc[-1]
            
            return {
                "moving_averages": {
                    "MA5": float(latest['MA5']) if not pd.isna(latest['MA5']) else None,
                    "MA10": float(latest['MA10']) if not pd.isna(latest['MA10']) else None,
                    "MA20": float(latest['MA20']) if not pd.isna(latest['MA20']) else None,
                    "MA50": float(latest['MA50']) if not pd.isna(latest['MA50']) else None,
                },
                "rsi": float(latest['RSI']) if not pd.isna(latest['RSI']) else None,
                "macd": {
                    "macd": float(latest['MACD']) if not pd.isna(latest['MACD']) else None,
                    "signal": float(latest['MACD_signal']) if not pd.isna(latest['MACD_signal']) else None,
                    "histogram": float(latest['MACD_histogram']) if not pd.isna(latest['MACD_histogram']) else None,
                },
                "bollinger_bands": {
                    "upper": float(latest['BB_upper']) if not pd.isna(latest['BB_upper']) else None,
                    "middle": float(latest['BB_middle']) if not pd.isna(latest['BB_middle']) else None,
                    "lower": float(latest['BB_lower']) if not pd.isna(latest['BB_lower']) else None,
                },
                "current_price": float(latest['Close']),
                "volume": int(latest['Volume']),
                "price_change": float(latest['Close'] - data['Close'].iloc[-2]) if len(data) > 1 else 0,
                "price_change_percent": float((latest['Close'] - data['Close'].iloc[-2]) / data['Close'].iloc[-2] * 100) if len(data) > 1 else 0
            }
            
        except Exception as e:
            logger.error(f"计算技术指标失败: {e}")
            return {}
    
    def get_chart_data(self, symbol: str, period: str = "1y") -> Dict[str, Any]:
        """获取K线图数据"""
        try:
            data = self.get_historical_data(symbol, period)
            if data is None or data.empty:
                return {}
            
            # 转换为前端需要的格式
            chart_data = []
            for date, row in data.iterrows():
                chart_data.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "open": float(row['Open']),
                    "high": float(row['High']),
                    "low": float(row['Low']),
                    "close": float(row['Close']),
                    "volume": int(row['Volume'])
                })
            
            # 计算技术指标
            indicators = self.calculate_technical_indicators(data.copy())
            
            return {
                "symbol": symbol,
                "period": period,
                "data": chart_data,
                "indicators": indicators,
                "total_records": len(chart_data)
            }
            
        except Exception as e:
            logger.error(f"获取K线图数据失败 {symbol}: {e}")
            return {}
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()