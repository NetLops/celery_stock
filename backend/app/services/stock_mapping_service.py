import json
import os
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)

class StockMappingService:
    """股票名称映射服务，提供中英文股票名称映射"""
    
    def __init__(self):
        self.mapping_data = {}
        self.load_mapping_data()
    
    def load_mapping_data(self):
        """加载映射数据"""
        try:
            # 获取映射文件路径
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mapping_file = os.path.join(current_dir, '../data/stock_name_mapping.json')
            
            # 如果文件存在，加载数据
            if os.path.exists(mapping_file):
                with open(mapping_file, 'r', encoding='utf-8') as f:
                    self.mapping_data = json.load(f)
                logger.info(f"成功加载股票名称映射数据，共 {len(self.mapping_data)} 条记录")
            else:
                # 如果文件不存在，初始化基础映射数据
                self.mapping_data = self.get_default_mapping()
                
                # 确保目录存在
                os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
                
                # 保存默认映射数据
                with open(mapping_file, 'w', encoding='utf-8') as f:
                    json.dump(self.mapping_data, f, ensure_ascii=False, indent=2)
                logger.info(f"创建默认股票名称映射数据，共 {len(self.mapping_data)} 条记录")
        except Exception as e:
            logger.error(f"加载股票名称映射数据失败: {e}")
            # 如果加载失败，使用默认映射
            self.mapping_data = self.get_default_mapping()
    
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
        if chinese_name in self.mapping_data:
            return self.mapping_data[chinese_name]["en_name"]
        return None
    
    def get_symbol(self, chinese_name: str) -> Optional[str]:
        """根据中文名称直接获取股票代码"""
        if chinese_name in self.mapping_data:
            return self.mapping_data[chinese_name]["symbol"]
        return None
    
    def search_by_chinese_name(self, name_part: str) -> List[Dict[str, str]]:
        """根据中文名称片段搜索匹配的股票"""
        results = []
        for cn_name, data in self.mapping_data.items():
            if name_part.lower() in cn_name.lower():
                results.append({
                    "chinese_name": cn_name,
                    "english_name": data["en_name"],
                    "symbol": data["symbol"]
                })
        return results
    
    def add_mapping(self, chinese_name: str, english_name: str, symbol: str) -> bool:
        """添加新的映射"""
        try:
            self.mapping_data[chinese_name] = {
                "en_name": english_name,
                "symbol": symbol
            }
            
            # 保存到文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mapping_file = os.path.join(current_dir, '../data/stock_name_mapping.json')
            
            # 确保目录存在
            os.makedirs(os.path.dirname(mapping_file), exist_ok=True)
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"添加映射失败: {e}")
            return False
    
    def update_mapping(self, chinese_name: str, english_name: str = None, symbol: str = None) -> bool:
        """更新现有映射"""
        if chinese_name not in self.mapping_data:
            return False
        
        try:
            if english_name:
                self.mapping_data[chinese_name]["en_name"] = english_name
            if symbol:
                self.mapping_data[chinese_name]["symbol"] = symbol
            
            # 保存到文件
            current_dir = os.path.dirname(os.path.abspath(__file__))
            mapping_file = os.path.join(current_dir, '../data/stock_name_mapping.json')
            
            with open(mapping_file, 'w', encoding='utf-8') as f:
                json.dump(self.mapping_data, f, ensure_ascii=False, indent=2)
            
            return True
        except Exception as e:
            logger.error(f"更新映射失败: {e}")
            return False