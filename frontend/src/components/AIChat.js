import React, { useState, useEffect, useRef } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  List, 
  Avatar, 
  Space, 
  Tag, 
  Spin,
  message,
  Divider,
  Typography
} from 'antd';
import { SendOutlined, RobotOutlined, UserOutlined, ReloadOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Text, Paragraph } = Typography;

const AIChat = () => {
  const [messages, setMessages] = useState([]);
  const [inputValue, setInputValue] = useState('');
  const [loading, setLoading] = useState(false);
  const [sessionId, setSessionId] = useState(null);
  const messagesEndRef = useRef(null);

  useEffect(() => {
    // 生成会话ID
    setSessionId(generateSessionId());
    
    // 添加欢迎消息
    setMessages([{
      id: 'welcome',
      type: 'ai',
      content: '您好！我是AI股票分析助手。您可以询问我关于股票分析、投资建议、市场趋势等问题。',
      timestamp: new Date().toISOString(),
      suggestions: [
        '分析苹果公司的股票',
        '推荐一些科技股',
        '当前市场趋势如何？',
        '什么是技术分析？'
      ]
    }]);
  }, []);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const generateSessionId = () => {
    return 'session_' + Date.now() + '_' + Math.random().toString(36).substr(2, 9);
  };

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const handleSendMessage = async () => {
    if (!inputValue.trim()) {
      message.warning('请输入您的问题');
      return;
    }

    const userMessage = {
      id: Date.now().toString(),
      type: 'user',
      content: inputValue,
      timestamp: new Date().toISOString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputValue('');
    setLoading(true);

    try {
      const response = await axios.post('/api/v1/analysis/query', {
        message: inputValue,
        session_id: sessionId
      });

      const aiMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: response.data.data.answer,
        timestamp: new Date().toISOString(),
        analysis: response.data.data.response?.analysis,
        recommendations: response.data.data.response?.recommendations,
        chartData: response.data.data.response?.chart_data,
        references: response.data.data.response?.reference_urls,
        contextSymbols: response.data.data.context_symbols
      };

      setMessages(prev => [...prev, aiMessage]);

    } catch (error) {
      message.error('发送消息失败: ' + (error.response?.data?.detail || error.message));
      
      const errorMessage = {
        id: (Date.now() + 1).toString(),
        type: 'ai',
        content: '抱歉，我暂时无法回答您的问题。请稍后再试。',
        timestamp: new Date().toISOString(),
        isError: true
      };

      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleSuggestionClick = (suggestion) => {
    setInputValue(suggestion);
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSendMessage();
    }
  };

  const loadChatHistory = async () => {
    if (!sessionId) return;

    try {
      const response = await axios.get(`/api/v1/analysis/history/${sessionId}`);
      const history = response.data.data || [];
      
      const historyMessages = history.flatMap(item => [
        {
          id: `user_${item.id}`,
          type: 'user',
          content: item.message,
          timestamp: item.created_at
        },
        {
          id: `ai_${item.id}`,
          type: 'ai',
          content: item.response?.answer || '无响应内容',
          timestamp: item.created_at,
          analysis: item.response?.analysis,
          recommendations: item.response?.recommendations,
          chartData: item.response?.chart_data,
          references: item.response?.reference_urls
        }
      ]);

      setMessages(prev => [...historyMessages, ...prev]);
    } catch (error) {
      console.error('加载聊天历史失败:', error);
    }
  };

  const renderMessage = (msg) => {
    const isUser = msg.type === 'user';
    
    return (
      <List.Item key={msg.id} style={{ border: 'none', padding: '12px 0' }}>
        <div style={{ 
          display: 'flex', 
          flexDirection: isUser ? 'row-reverse' : 'row',
          width: '100%',
          alignItems: 'flex-start'
        }}>
          <Avatar 
            icon={isUser ? <UserOutlined /> : <RobotOutlined />}
            style={{ 
              backgroundColor: isUser ? '#1890ff' : '#52c41a',
              margin: isUser ? '0 0 0 12px' : '0 12px 0 0'
            }}
          />
          
          <div style={{ 
            maxWidth: '70%',
            backgroundColor: isUser ? '#e6f7ff' : '#f6ffed',
            padding: '12px 16px',
            borderRadius: '12px',
            border: `1px solid ${isUser ? '#91d5ff' : '#b7eb8f'}`
          }}>
            <Paragraph style={{ margin: 0, whiteSpace: 'pre-wrap' }}>
              {msg.content}
            </Paragraph>
            
            {msg.contextSymbols && msg.contextSymbols.length > 0 && (
              <div style={{ marginTop: 8 }}>
                <Text type="secondary">相关股票: </Text>
                {msg.contextSymbols.map(symbol => (
                  <Tag key={symbol} color="red">{symbol}</Tag>
                ))}
              </div>
            )}

            {msg.recommendations && msg.recommendations.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Divider style={{ margin: '8px 0' }}>推荐信息</Divider>
                {msg.recommendations.map((rec, index) => (
                  <div key={index} style={{ marginBottom: 8 }}>
                    <Tag color="orange">{rec.symbol || '推荐'}</Tag>
                    <Text>{rec.rationale || rec}</Text>
                    <Tag color='blue'>{rec.action || '推荐买入' }</Tag>
                  </div>
                ))}
              </div>
            )}

            {/* {msg.references && msg.references.length > 0 && (
              <div style={{ marginTop: 12 }}>
                <Divider style={{ margin: '8px 0' }}>参考链接</Divider>
                {msg.references.map((ref, index) => (
                  <div key={index}>
                    <a href={ref} target="_blank" rel="noopener noreferrer">
                      {ref}
                    </a>
                  </div>
                ))}
              </div>
            )} */}

            {msg.suggestions && (
              <div style={{ marginTop: 12 }}>
                <Text type="secondary">您可以尝试问:</Text>
                <div style={{ marginTop: 8 }}>
                  {msg.suggestions.map((suggestion, index) => (
                    <Tag 
                      key={index}
                      style={{ 
                        cursor: 'pointer', 
                        marginBottom: 4,
                        backgroundColor: '#f0f0f0',
                        border: '1px dashed #d9d9d9'
                      }}
                      onClick={() => handleSuggestionClick(suggestion)}
                    >
                      {suggestion}
                    </Tag>
                  ))}
                </div>
              </div>
            )}

            <div style={{ marginTop: 8, textAlign: isUser ? 'left' : 'right' }}>
              <Text type="secondary" style={{ fontSize: '12px' }}>
                {new Date(msg.timestamp).toLocaleTimeString()}
              </Text>
            </div>
          </div>
        </div>
      </List.Item>
    );
  };

  return (
    <div style={{ height: 'calc(100vh - 200px)', display: 'flex', flexDirection: 'column' }}>
      <Card 
        title="AI股票分析助手" 
        extra={
          <Button 
            icon={<ReloadOutlined />} 
            onClick={loadChatHistory}
            size="small"
          >
            加载历史
          </Button>
        }
        style={{ flex: 1, display: 'flex', flexDirection: 'column' }}
        bodyStyle={{ flex: 1, display: 'flex', flexDirection: 'column', padding: 0 }}
      >
        <div style={{ 
          flex: 1, 
          overflowY: 'auto', 
          padding: '16px',
          backgroundColor: '#fafafa'
        }}>
          <List
            dataSource={messages}
            renderItem={renderMessage}
            style={{ backgroundColor: 'transparent' }}
          />
          {loading && (
            <div style={{ textAlign: 'center', padding: '20px' }}>
              <Spin />
              <Text style={{ marginLeft: 8 }}>AI正在思考中...</Text>
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        <div style={{ 
          padding: '16px', 
          borderTop: '1px solid #f0f0f0',
          backgroundColor: '#fff'
        }}>
          <Space.Compact style={{ width: '100%' }}>
            <TextArea
              value={inputValue}
              onChange={(e) => setInputValue(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="请输入您的问题... (Shift+Enter换行，Enter发送)"
              autoSize={{ minRows: 1, maxRows: 4 }}
              disabled={loading}
            />
            <Button 
              type="primary" 
              icon={<SendOutlined />}
              onClick={handleSendMessage}
              loading={loading}
              disabled={!inputValue.trim()}
            >
              发送
            </Button>
          </Space.Compact>
        </div>
      </Card>
    </div>
  );
};

export default AIChat;