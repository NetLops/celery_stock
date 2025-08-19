import json
import os
from typing import Dict, List, Optional, Tuple
import logging
from sqlalchemy.orm import Session
from ..models import StockNameMapping
from ..database import SessionLocal

logger = logging.getLogger(__name__)

class StockMappingService:
    """股票名称映射服务，提供中英文股票名称映射"""
    
    def __init__(self):
        self.session = SessionLocal()
        self.ensure_default_mappings()
    
    def ensure_default_mappings(self):
        """确保默认映射数据存在于数据库中"""
        try:
            # 检查数据库中是否已有映射数据
            count = self.session.query(StockNameMapping).count()
            
            if count == 0:
                logger.info("数据库中没有映射数据，正在导入默认映射...")
                default_mappings = self.get_default_mapping()
                
                # 将默认映射导入数据库
                for chinese_name, data in default_mappings.items():
                    mapping = StockNameMapping(
                        chinese_name=chinese_name,
                        english_name=data["en_name"],
                        symbol=data["symbol"]
                    )
                    self.session.add(mapping)
                
                self.session.commit()
                logger.info(f"成功导入 {len(default_mappings)} 条默认映射数据")
        except Exception as e:
            logger.error(f"确保默认映射数据失败: {e}")
            self.session.rollback()
    
    def get_default_mapping(self) -> Dict[str, Dict[str, str]]:
        """获取默认的股票名称映射数据"""
        # 返回常见美股公司的中英文名称映射
        return {
            # 科技公司
            "苹果": {"en_name": "Apple Inc.", "symbol": "AAPL"},
            "谷歌": {"en_name": "Alphabet Inc.", "symbol": "GOOGL"},
            "微软": {"en_name": "Microsoft Corporation", "symbol": "MSFT"},
            "亚马逊": {"en_name": "Amazon.com Inc.", "symbol": "AMZN"},
            "特斯拉": {"en_name": "Tesla, Inc.", "symbol": "TSLA"},
            "英伟达": {"en_name": "NVIDIA Corporation", "symbol": "NVDA"},
            "脸书": {"en_name": "Meta Platforms, Inc.", "symbol": "META"},
            "网飞": {"en_name": "Netflix, Inc.", "symbol": "NFLX"},
            "甲骨文": {"en_name": "Oracle Corporation", "symbol": "ORCL"},
            "英特尔": {"en_name": "Intel Corporation", "symbol": "INTC"},
            "高通": {"en_name": "Qualcomm Incorporated", "symbol": "QCOM"},
            "思科": {"en_name": "Cisco Systems, Inc.", "symbol": "CSCO"},
            "Adobe": {"en_name": "Adobe Inc.", "symbol": "ADBE"},
            "赛富时": {"en_name": "Salesforce, Inc.", "symbol": "CRM"},
            "推特": {"en_name": "Twitter, Inc.", "symbol": "TWTR"},
            "优步": {"en_name": "Uber Technologies, Inc.", "symbol": "UBER"},
            "爱彼迎": {"en_name": "Airbnb, Inc.", "symbol": "ABNB"},
            "Zoom": {"en_name": "Zoom Video Communications, Inc.", "symbol": "ZM"},
            
            # 金融公司
            "摩根大通": {"en_name": "JPMorgan Chase & Co.", "symbol": "JPM"},
            "美国银行": {"en_name": "Bank of America Corporation", "symbol": "BAC"},
            "花旗集团": {"en_name": "Citigroup Inc.", "symbol": "C"},
            "富国银行": {"en_name": "Wells Fargo & Company", "symbol": "WFC"},
            "高盛": {"en_name": "The Goldman Sachs Group, Inc.", "symbol": "GS"},
            "摩根士丹利": {"en_name": "Morgan Stanley", "symbol": "MS"},
            "美国运通": {"en_name": "American Express Company", "symbol": "AXP"},
            "万事达卡": {"en_name": "Mastercard Incorporated", "symbol": "MA"},
            "维萨": {"en_name": "Visa Inc.", "symbol": "V"},
            "贝宝": {"en_name": "PayPal Holdings, Inc.", "symbol": "PYPL"},
            
            # 零售和消费品公司
            "沃尔玛": {"en_name": "Walmart Inc.", "symbol": "WMT"},
            "家得宝": {"en_name": "The Home Depot, Inc.", "symbol": "HD"},
            "麦当劳": {"en_name": "McDonald's Corporation", "symbol": "MCD"},
            "星巴克": {"en_name": "Starbucks Corporation", "symbol": "SBUX"},
            "耐克": {"en_name": "NIKE, Inc.", "symbol": "NKE"},
            "可口可乐": {"en_name": "The Coca-Cola Company", "symbol": "KO"},
            "百事可乐": {"en_name": "PepsiCo, Inc.", "symbol": "PEP"},
            "宝洁": {"en_name": "The Procter & Gamble Company", "symbol": "PG"},
            "强生": {"en_name": "Johnson & Johnson", "symbol": "JNJ"},
            "辉瑞": {"en_name": "Pfizer Inc.", "symbol": "PFE"},
            "默克": {"en_name": "Merck & Co., Inc.", "symbol": "MRK"},
            
            # 工业和能源公司
            "通用电气": {"en_name": "General Electric Company", "symbol": "GE"},
            "波音": {"en_name": "The Boeing Company", "symbol": "BA"},
            "卡特彼勒": {"en_name": "Caterpillar Inc.", "symbol": "CAT"},
            "埃克森美孚": {"en_name": "Exxon Mobil Corporation", "symbol": "XOM"},
            "雪佛龙": {"en_name": "Chevron Corporation", "symbol": "CVX"},
            
            # 中国公司（在美上市）
            "阿里巴巴": {"en_name": "Alibaba Group Holding Limited", "symbol": "BABA"},
            "腾讯": {"en_name": "Tencent Holdings Limited", "symbol": "TCEHY"},
            "百度": {"en_name": "Baidu, Inc.", "symbol": "BIDU"},
            "京东": {"en_name": "JD.com, Inc.", "symbol": "JD"},
            "拼多多": {"en_name": "Pinduoduo Inc.", "symbol": "PDD"},
            "网易": {"en_name": "NetEase, Inc.", "symbol": "NTES"},
            "哔哩哔哩": {"en_name": "Bilibili Inc.", "symbol": "BILI"},
            "小鹏汽车": {"en_name": "XPeng Inc.", "symbol": "XPEV"},
            "蔚来": {"en_name": "NIO Inc.", "symbol": "NIO"},
            "理想汽车": {"en_name": "Li Auto Inc.", "symbol": "LI"}
        }
    
    def get_english_name(self, chinese_name: str) -> Optional[str]:
        """根据中文名称获取英文名称"""
        mapping = self.session.query(StockNameMapping).filter(
            StockNameMapping.chinese_name == chinese_name
        ).first()
        
        if mapping:
            return mapping.english_name
        return None
    
    def get_symbol(self, chinese_name: str) -> Optional[str]:
        """根据中文名称直接获取股票代码"""
        mapping = self.session.query(StockNameMapping).filter(
            StockNameMapping.chinese_name == chinese_name
        ).first()
        
        if mapping:
            return mapping.symbol
        return None
    
    def search_by_chinese_name(self, name_part: str) -> List[Dict[str, str]]:
        """根据中文名称片段搜索匹配的股票"""
        results = []
        mappings = self.session.query(StockNameMapping).filter(
            StockNameMapping.chinese_name.like(f"%{name_part}%")
        ).all()
        
        for mapping in mappings:
            results.append({
                "chinese_name": mapping.chinese_name,
                "english_name": mapping.english_name,
                "symbol": mapping.symbol
            })
        return results
    
    def get_all_mappings(self, skip: int = 0, limit: int = 100) -> List[Dict[str, str]]:
        """获取所有映射数据"""
        mappings = self.session.query(StockNameMapping).offset(skip).limit(limit).all()
        
        results = []
        for mapping in mappings:
            results.append({
                "id": mapping.id,
                "chinese_name": mapping.chinese_name,
                "english_name": mapping.english_name,
                "symbol": mapping.symbol,
                "created_at": mapping.created_at.isoformat(),
                "updated_at": mapping.updated_at.isoformat()
            })
        return results
    
    def get_mapping_by_id(self, mapping_id: int) -> Optional[Dict[str, str]]:
        """根据ID获取映射"""
        mapping = self.session.query(StockNameMapping).filter(
            StockNameMapping.id == mapping_id
        ).first()
        
        if mapping:
            return {
                "id": mapping.id,
                "chinese_name": mapping.chinese_name,
                "english_name": mapping.english_name,
                "symbol": mapping.symbol,
                "created_at": mapping.created_at.isoformat(),
                "updated_at": mapping.updated_at.isoformat()
            }
        return None
    
    def add_mapping(self, chinese_name: str, english_name: str, symbol: str) -> Optional[Dict[str, str]]:
        """添加新的映射"""
        try:
            # 检查是否已存在
            existing = self.session.query(StockNameMapping).filter(
                StockNameMapping.chinese_name == chinese_name
            ).first()
            
            if existing:
                return None
            
            # 创建新映射
            mapping = StockNameMapping(
                chinese_name=chinese_name,
                english_name=english_name,
                symbol=symbol
            )
            self.session.add(mapping)
            self.session.commit()
            self.session.refresh(mapping)
            
            return {
                "id": mapping.id,
                "chinese_name": mapping.chinese_name,
                "english_name": mapping.english_name,
                "symbol": mapping.symbol,
                "created_at": mapping.created_at.isoformat(),
                "updated_at": mapping.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"添加映射失败: {e}")
            self.session.rollback()
            return None
    
    def update_mapping(self, mapping_id: int, chinese_name: str = None, english_name: str = None, symbol: str = None) -> Optional[Dict[str, str]]:
        """更新现有映射"""
        try:
            mapping = self.session.query(StockNameMapping).filter(
                StockNameMapping.id == mapping_id
            ).first()
            
            if not mapping:
                return None
            
            if chinese_name:
                # 检查新的中文名称是否已被使用
                if chinese_name != mapping.chinese_name:
                    existing = self.session.query(StockNameMapping).filter(
                        StockNameMapping.chinese_name == chinese_name
                    ).first()
                    if existing:
                        return None
                mapping.chinese_name = chinese_name
            
            if english_name:
                mapping.english_name = english_name
            
            if symbol:
                mapping.symbol = symbol
            
            self.session.commit()
            self.session.refresh(mapping)
            
            return {
                "id": mapping.id,
                "chinese_name": mapping.chinese_name,
                "english_name": mapping.english_name,
                "symbol": mapping.symbol,
                "created_at": mapping.created_at.isoformat(),
                "updated_at": mapping.updated_at.isoformat()
            }
        except Exception as e:
            logger.error(f"更新映射失败: {e}")
            self.session.rollback()
            return None
    
    def delete_mapping(self, mapping_id: int) -> bool:
        """删除映射"""
        try:
            mapping = self.session.query(StockNameMapping).filter(
                StockNameMapping.id == mapping_id
            ).first()
            
            if not mapping:
                return False
            
            self.session.delete(mapping)
            self.session.commit()
            return True
        except Exception as e:
            logger.error(f"删除映射失败: {e}")
            self.session.rollback()
            return False
    
    def __del__(self):
        if hasattr(self, 'session'):
            self.session.close()