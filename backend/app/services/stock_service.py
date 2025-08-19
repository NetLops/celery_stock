import yfinance as yf
import pandas as pd
import numpy as np
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..models import Stock, StockPrice
from ..database import SessionLocal
import logging
import re
from .stock_mapping_service import StockMappingService

logger = logging.getLogger(__name__)

class StockDataService:
    """股票数据服务"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.mapping_service = StockMappingService()
    
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
    
    def find_stock_by_name(self, name: str) -> List[Dict[str, str]]:
        """根据股票名称查找股票代码
        
        Args:
            name: 股票名称（中文或英文）
            
        Returns:
            匹配的股票列表，每个元素包含 symbol 和 name
        """
        try:
            results = []
            
            # 1. 首先检查是否是中文名称，如果是，尝试使用映射服务
            if re.search(r'[\u4e00-\u9fff]', name):
                # 直接查找完全匹配
                symbol = self.mapping_service.get_symbol(name)
                if symbol:
                    stock_info = self.get_stock_info(symbol)
                    if stock_info:
                        results.append({
                            "symbol": symbol,
                            "name": stock_info.get("name", name),
                            "exchange": stock_info.get("exchange", "")
                        })
                
                # 查找部分匹配
                mapping_results = self.mapping_service.search_by_chinese_name(name)
                for item in mapping_results:
                    if not any(r["symbol"] == item["symbol"] for r in results):
                        results.append({
                            "symbol": item["symbol"],
                            "name": item["english_name"],
                            "exchange": ""  # 可以通过 yfinance 获取，但为了性能这里先不获取
                        })
            
            # 2. 在数据库中查找
            query = self.session.query(Stock)
            
            # 如果输入是中文，尝试模糊匹配名称
            if re.search(r'[\u4e00-\u9fff]', name):
                stocks = query.filter(Stock.name.like(f"%{name}%")).all()
            else:
                # 英文名称可能是部分匹配
                stocks = query.filter(Stock.name.ilike(f"%{name}%")).all()
            
            for stock in stocks:
                if not any(r["symbol"] == stock.symbol for r in results):
                    results.append({
                        "symbol": stock.symbol,
                        "name": stock.name,
                        "exchange": stock.exchange
                    })
            
            # 3. 如果数据库中没有找到，尝试使用 yfinance 搜索
            if not results and not re.search(r'[\u4e00-\u9fff]', name):
                # 对于英文名称，尝试直接使用名称的首字母缩写
                words = name.split()
                if len(words) > 1:
                    acronym = ''.join(word[0].upper() for word in words if word)
                    try:
                        ticker = yf.Ticker(acronym)
                        info = ticker.info
                        if info and 'longName' in info:
                            results.append({
                                "symbol": acronym,
                                "name": info.get("longName", ""),
                                "exchange": info.get("exchange", "")
                            })
                    except:
                        pass
                
                # 尝试使用名称的前几个字母
                name_no_space = ''.join(name.split()).upper()
                if len(name_no_space) >= 2:
                    possible_symbols = [name_no_space[:i] for i in range(2, min(5, len(name_no_space) + 1))]
                    for symbol in possible_symbols:
                        try:
                            ticker = yf.Ticker(symbol)
                            info = ticker.info
                            if info and 'longName' in info:
                                if not any(r["symbol"] == symbol for r in results):
                                    results.append({
                                        "symbol": symbol,
                                        "name": info.get("longName", ""),
                                        "exchange": info.get("exchange", "")
                                    })
                        except:
                            pass
            
            # 4. 如果是中文名称但没有找到匹配，尝试将中文转为英文再搜索
            if not results and re.search(r'[\u4e00-\u9fff]', name):
                # 这里可以集成翻译服务，但为简单起见，我们只使用映射表中的英文名称
                en_name = self.mapping_service.get_english_name(name)
                if en_name:
                    # 尝试使用英文名称搜索
                    words = en_name.split()
                    if len(words) > 1:
                        acronym = ''.join(word[0].upper() for word in words if word and not word.lower() in ['inc', 'corp', 'co', 'ltd', 'limited'])
                        try:
                            ticker = yf.Ticker(acronym)
                            info = ticker.info
                            if info and 'longName' in info:
                                results.append({
                                    "symbol": acronym,
                                    "name": info.get("longName", ""),
                                    "exchange": info.get("exchange", "")
                                })
                        except:
                            pass
            
            return results
            
        except Exception as e:
            logger.error(f"根据名称查找股票失败 {name}: {e}")
            return []
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()