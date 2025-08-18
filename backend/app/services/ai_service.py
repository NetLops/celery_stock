import openai
import json
import re
from typing import Dict, Any, List, Optional
from datetime import datetime
import logging
import os

logger = logging.getLogger(__name__)

class AIAnalysisService:
    """AI分析服务"""
    
    def __init__(self):
        self.client = openai.OpenAI(api_key=os.getenv("OPENAI_API_KEY"), base_url="https://api.gpt.ge/v1")
        self.prompts = self._load_prompts()
    
    def _parse_json_from_response(self, response_text: str) -> Dict[str, Any]:
        """
        从模型响应中解析JSON，处理可能的Markdown代码块标记
        """
        # 去除可能的Markdown代码块标记
        cleaned_text = response_text.strip()
        
        # 使用正则表达式移除开头的```json或```标记和结尾的```标记
        cleaned_text = re.sub(r'^```json\s*', '', cleaned_text)
        cleaned_text = re.sub(r'^```\s*', '', cleaned_text)
        cleaned_text = re.sub(r'\s*```$', '', cleaned_text)
        
        # 清理文本并解析JSON
        cleaned_text = cleaned_text.strip()
        
        try:
            return json.loads(cleaned_text)
        except json.JSONDecodeError as e:
            logger.error(f"JSON解析错误: {e}")
            logger.debug(f"清理后的文本: {cleaned_text}")
            # 返回原始文本作为备用
            return {"raw_text": cleaned_text}
    
    def _load_prompts(self) -> Dict[str, str]:
        """加载分析提示词模板"""
        return {
            "technical": """
你是一位专业的技术分析师。请基于以下股票技术数据进行分析：

股票代码: {symbol}
当前价格: {current_price}
技术指标:
- RSI: {rsi}
- MACD: {macd}
- 移动平均线: {moving_averages}
- 布林带: {bollinger_bands}
- 价格变化: {price_change}% 

请提供以下分析：
1. 技术面总体评价（看涨/看跌/中性）
2. 关键技术指标解读
3. 支撑位和阻力位分析
4. 短期趋势预测（1-7天）
5. 风险提示

请以JSON格式返回，包含：
- overall_sentiment: "bullish"/"bearish"/"neutral"
- key_levels: {"support": 价格, "resistance": 价格}
- short_term_outlook: 文字描述
- risk_factors: [风险因素列表]
- confidence: 0-1之间的置信度

重要：请直接返回JSON格式的响应，不要添加任何Markdown格式标记（如 ```json 或 ```）。
只返回原始JSON数据，没有任何其他文本或格式。
""",
            
            "fundamental": """
你是一位专业的基本面分析师。请基于以下股票基本面数据进行分析：

股票代码: {symbol}
公司名称: {name}
行业: {sector} - {industry}
市值: {market_cap}
市盈率: {pe_ratio}
贝塔系数: {beta}
股息收益率: {dividend_yield}

请提供以下分析：
1. 公司基本面评价
2. 行业地位和竞争优势
3. 财务健康状况
4. 长期投资价值
5. 主要风险因素

请以JSON格式返回，包含：
- fundamental_score: 0-100的评分
- investment_thesis: 投资逻辑
- competitive_advantages: [竞争优势列表]
- risk_factors: [风险因素列表]
- long_term_outlook: 长期前景描述
- confidence: 0-1之间的置信度

重要：请直接返回JSON格式的响应，不要添加任何Markdown格式标记（如 ```json 或 ```）。
只返回原始JSON数据，没有任何其他文本或格式。
""",
            
            "sentiment": """
你是一位专业的市场情绪分析师。请基于当前市场环境和股票表现进行情绪分析：

股票代码: {symbol}
近期表现: {price_change}%
市场环境: {market_context}

请分析：
1. 市场对该股票的整体情绪
2. 投资者信心水平
3. 可能影响情绪的因素
4. 情绪转变的关键催化剂

请以JSON格式返回，包含：
- sentiment_score: -1到1之间（-1极度悲观，1极度乐观）
- confidence_level: "low"/"medium"/"high"
- key_drivers: [影响情绪的关键因素]
- potential_catalysts: [可能的催化剂]
- recommendation: 基于情绪的操作建议

重要：请直接返回JSON格式的响应，不要添加任何Markdown格式标记（如 ```json 或 ```）。
只返回原始JSON数据，没有任何其他文本或格式。
""",
            
            "recommendation": """
你是一位资深投资顾问。请基于综合分析给出投资建议：

股票代码: {symbol}
技术分析结果: {technical_analysis}
基本面分析结果: {fundamental_analysis}
市场情绪分析: {sentiment_analysis}

请提供：
1. 综合投资评级（强烈买入/买入/持有/卖出/强烈卖出）
2. 目标价格区间
3. 投资时间框架建议
4. 风险等级评估
5. 具体操作建议

请以JSON格式返回，包含：
- rating: "strong_buy"/"buy"/"hold"/"sell"/"strong_sell"
- target_price_range: {"low": 价格, "high": 价格}
- time_horizon: "short"/"medium"/"long"
- risk_level: "low"/"medium"/"high"
- action_plan: 具体操作建议
- stop_loss: 建议止损价格
- confidence: 0-1之间的置信度

重要：请直接返回JSON格式的响应，不要添加任何Markdown格式标记（如 ```json 或 ```）。
只返回原始JSON数据，没有任何其他文本或格式。
"""
        }
    
    def analyze_stock(self, symbol: str, analysis_type: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """执行股票分析"""
        try:
            if analysis_type not in self.prompts:
                raise ValueError(f"不支持的分析类型: {analysis_type}")
            
            prompt = self.prompts[analysis_type].format(**data)
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "你是一位专业的股票分析师，请提供准确、客观的分析建议。请直接返回JSON格式的响应，不要添加任何Markdown格式标记。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.3,
                    max_tokens=1500
                )
                
                # 解析AI响应
                ai_response = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API调用失败: {e}")
                # 检查是否返回了字符串而不是对象
                if isinstance(response, str):
                    ai_response = response
                else:
                    raise e
            
            # 尝试解析JSON响应
            try:
                analysis_result = json.loads(ai_response)
            except json.JSONDecodeError:
                # 尝试清理并解析JSON
                analysis_result = self._parse_json_from_response(ai_response)
                
                # 如果仍然无法解析为JSON，包装成标准格式
                if "raw_text" in analysis_result:
                    analysis_result = {
                        "raw_analysis": analysis_result["raw_text"],
                        "analysis_type": analysis_type,
                        "confidence": 0.7
                    }
            
            # 添加元数据
            analysis_result.update({
                "symbol": symbol,
                "analysis_type": analysis_type,
                "generated_at": datetime.now().isoformat(),
                "model_used": "gpt-4.1-mini"
            })
            
            return analysis_result
            
        except Exception as e:
            logger.error(f"AI分析失败 {symbol} - {analysis_type}: {e}")
            return {
                "error": str(e),
                "symbol": symbol,
                "analysis_type": analysis_type,
                "generated_at": datetime.now().isoformat()
            }
    
    def generate_comprehensive_analysis(self, symbol: str, stock_data: Dict[str, Any]) -> Dict[str, Any]:
        """生成综合分析报告"""
        try:
            analyses = {}
            
            # 技术分析
            if "indicators" in stock_data:
                technical_data = {
                    "symbol": symbol,
                    "current_price": stock_data["indicators"].get("current_price", 0),
                    "rsi": stock_data["indicators"].get("rsi", "N/A"),
                    "macd": stock_data["indicators"].get("macd", {}),
                    "moving_averages": stock_data["indicators"].get("moving_averages", {}),
                    "bollinger_bands": stock_data["indicators"].get("bollinger_bands", {}),
                    "price_change": stock_data["indicators"].get("price_change_percent", 0)
                }
                analyses["technical"] = self.analyze_stock(symbol, "technical", technical_data)
            
            # 基本面分析
            if "stock_info" in stock_data:
                fundamental_data = stock_data["stock_info"]
                analyses["fundamental"] = self.analyze_stock(symbol, "fundamental", fundamental_data)
            
            # 市场情绪分析
            sentiment_data = {
                "symbol": symbol,
                "price_change": stock_data.get("indicators", {}).get("price_change_percent", 0),
                "market_context": "当前市场环境"  # 可以从外部API获取
            }
            analyses["sentiment"] = self.analyze_stock(symbol, "sentiment", sentiment_data)
            
            # 综合推荐
            if len(analyses) >= 2:
                recommendation_data = {
                    "symbol": symbol,
                    "technical_analysis": analyses.get("technical", {}),
                    "fundamental_analysis": analyses.get("fundamental", {}),
                    "sentiment_analysis": analyses.get("sentiment", {})
                }
                analyses["recommendation"] = self.analyze_stock(symbol, "recommendation", recommendation_data)
            
            return {
                "symbol": symbol,
                "comprehensive_analysis": analyses,
                "generated_at": datetime.now().isoformat(),
                "analysis_count": len(analyses)
            }
            
        except Exception as e:
            logger.error(f"生成综合分析失败 {symbol}: {e}")
            return {"error": str(e), "symbol": symbol}
    
    def answer_user_query(self, query: str, context_data: Dict[str, Any]) -> Dict[str, Any]:
        """回答用户查询"""
        try:
            # 构建上下文提示词
            context_prompt = f"""
基于以下股票数据回答用户问题：

用户问题: {query}

可用数据:
{json.dumps(context_data, indent=2, ensure_ascii=False)}

请提供：
1. 直接回答用户问题
2. 相关的分析见解
3. 如果需要，提供具体的股票推荐
4. 包含K线图数据的建议
5. 相关参考信息

请以JSON格式返回，包含：
- answer: 主要回答
- analysis: 分析见解
- recommendations: 推荐列表（列表的元素里包含 "symbol"、"action"、"rationale" 三个字段的信息）
- chart_suggestions: K线图建议
- references: 参考信息

重要：请直接返回JSON格式的响应，不要添加任何Markdown格式标记（如 ```json 或 ```）。
只返回原始JSON数据，没有任何其他文本或格式。
"""
            
            try:
                response = self.client.chat.completions.create(
                    model="gpt-4.1-mini",
                    messages=[
                        {"role": "system", "content": "你是一位专业的股票投资顾问，请基于提供的数据回答用户问题。请直接返回JSON格式的响应，不要添加任何Markdown格式标记。"},
                        {"role": "user", "content": context_prompt}
                    ],
                    temperature=0.4,
                    max_tokens=5000
                )
                
                logger.info(f"Debug Info {response}")
                ai_response = response.choices[0].message.content
            except Exception as e:
                logger.error(f"OpenAI API调用失败: {e}")
                # 检查是否返回了字符串而不是对象
                if isinstance(response, str):
                    ai_response = response
                else:
                    raise e
            
            try:
                result = json.loads(ai_response)
            except json.JSONDecodeError:
                # 尝试清理并解析JSON
                result = self._parse_json_from_response(ai_response)
                
                # 如果仍然无法解析为JSON，使用默认结构
                if "raw_text" in result:
                    result = {
                        "answer": result["raw_text"],
                        "analysis": {},
                        "recommendations": [],
                        "chart_suggestions": {},
                        "references": []
                    }
            
            result.update({
                "query": query,
                "generated_at": datetime.now().isoformat(),
                "model_used": "gpt-4.1-mini"
            })
            
            return result
            
        except Exception as e:
            logger.error(f"回答用户查询失败: {e}")
            return {
                "error": str(e),
                "query": query,
                "generated_at": datetime.now().isoformat()
            }