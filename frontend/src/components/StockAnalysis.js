import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Input, 
  Button, 
  Table, 
  Tag, 
  Space, 
  message, 
  Spin,
  Row,
  Col,
  Statistic,
  Progress
} from 'antd';
import { SearchOutlined, AnalysisOutlined, LineChartOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const { Search } = Input;

const StockAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [analysisData, setAnalysisData] = useState([]);
  const [chartData, setChartData] = useState(null);

  const handleSearch = async (symbol) => {
    if (!symbol) {
      message.error('请输入股票代码');
      return;
    }

    setLoading(true);
    try {
      // 获取股票基本信息
      const stockResponse = await axios.get(`/api/v1/stocks/${symbol}`);
      setStockData(stockResponse.data.data);

      // 获取分析结果
      const analysisResponse = await axios.get(`/api/v1/stocks/${symbol}/analysis`);
      setAnalysisData(analysisResponse.data.data || []);

      // 获取图表数据
      const chartResponse = await axios.get(`/api/v1/stocks/${symbol}/chart`);
      setChartData(chartResponse.data.data);

    } catch (error) {
      message.error('获取数据失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleAnalyze = async (symbol) => {
    setLoading(true);
    try {
      await axios.post('/api/v1/stocks/analyze', {
        symbol: symbol,
        analysis_types: ['technical', 'fundamental', 'sentiment'],
        force_refresh: true
      });
      message.success('分析任务已提交，请稍后查看结果');
      
      // 延迟刷新分析结果
      setTimeout(() => {
        handleSearch(symbol);
      }, 3000);
      
    } catch (error) {
      message.error('提交分析失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const getChartOption = () => {
    if (!chartData || !chartData.data) return {};

    const data = chartData.data.map(item => [
      item.date,
      item.open,
      item.close,
      item.low,
      item.high,
      item.volume
    ]);

    return {
      title: {
        text: `${chartData.symbol} 股价走势`,
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: {
          type: 'cross'
        }
      },
      legend: {
        data: ['K线', '成交量'],
        top: 30
      },
      grid: [
        {
          left: '10%',
          right: '8%',
          height: '50%'
        },
        {
          left: '10%',
          right: '8%',
          top: '70%',
          height: '16%'
        }
      ],
      xAxis: [
        {
          type: 'category',
          data: chartData.data.map(item => item.date),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          splitLine: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        },
        {
          type: 'category',
          gridIndex: 1,
          data: chartData.data.map(item => item.date),
          scale: true,
          boundaryGap: false,
          axisLine: { onZero: false },
          axisTick: { show: false },
          splitLine: { show: false },
          axisLabel: { show: false },
          min: 'dataMin',
          max: 'dataMax'
        }
      ],
      yAxis: [
        {
          scale: true,
          splitArea: {
            show: true
          }
        },
        {
          scale: true,
          gridIndex: 1,
          splitNumber: 2,
          axisLabel: { show: false },
          axisLine: { show: false },
          axisTick: { show: false },
          splitLine: { show: false }
        }
      ],
      dataZoom: [
        {
          type: 'inside',
          xAxisIndex: [0, 1],
          start: 70,
          end: 100
        },
        {
          show: true,
          xAxisIndex: [0, 1],
          type: 'slider',
          top: '85%',
          start: 70,
          end: 100
        }
      ],
      series: [
        {
          name: 'K线',
          type: 'candlestick',
          data: data.map(item => [item[1], item[2], item[3], item[4]]),
          itemStyle: {
            color: '#ec0000',
            color0: '#00da3c',
            borderColor: '#8A0000',
            borderColor0: '#008F28'
          }
        },
        {
          name: '成交量',
          type: 'bar',
          xAxisIndex: 1,
          yAxisIndex: 1,
          data: data.map(item => item[5])
        }
      ]
    };
  };

  const analysisColumns = [
    {
      title: '分析类型',
      dataIndex: 'analysis_type',
      key: 'analysis_type',
      render: (type) => {
        const typeMap = {
          'technical': { text: '技术分析', color: 'blue' },
          'fundamental': { text: '基本面分析', color: 'green' },
          'sentiment': { text: '情绪分析', color: 'orange' },
          'recommendation': { text: '投资建议', color: 'red' }
        };
        const config = typeMap[type] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '置信度',
      dataIndex: 'confidence_score',
      key: 'confidence_score',
      render: (score) => score ? <Progress percent={Math.round(score * 100)} size="small" /> : '-'
    },
    {
      title: '分析时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Button 
          type="link" 
          onClick={() => {
            // 显示详细分析内容
            console.log('分析详情:', record.content);
          }}
        >
          查看详情
        </Button>
      )
    }
  ];

  return (
    <div>
      <Card title="股票分析" style={{ marginBottom: 24 }}>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Search
            placeholder="请输入股票代码 (如: AAPL, GOOGL)"
            allowClear
            enterButton={<SearchOutlined />}
            size="large"
            onSearch={handleSearch}
            loading={loading}
          />
          
          {stockData && (
            <Row gutter={16} style={{ marginTop: 16 }}>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="股票代码"
                    value={stockData.stock_info.symbol}
                    valueStyle={{ color: '#1890ff' }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="公司名称"
                    value={stockData.stock_info.name}
                    valueStyle={{ fontSize: 14 }}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="交易所"
                    value={stockData.stock_info.exchange}
                  />
                </Card>
              </Col>
              <Col span={6}>
                <Card size="small">
                  <Statistic
                    title="行业"
                    value={stockData.stock_info.sector}
                  />
                </Card>
              </Col>
            </Row>
          )}

          {stockData && (
            <Space>
              <Button 
                type="primary" 
                icon={<AnalysisOutlined />}
                onClick={() => handleAnalyze(stockData.stock_info.symbol)}
                loading={loading}
              >
                开始分析
              </Button>
              <Button 
                icon={<LineChartOutlined />}
                onClick={() => handleSearch(stockData.stock_info.symbol)}
              >
                刷新数据
              </Button>
            </Space>
          )}
        </Space>
      </Card>

      {chartData && (
        <Card title="价格走势图" style={{ marginBottom: 24 }}>
          <ReactECharts 
            option={getChartOption()} 
            style={{ height: '400px' }}
            notMerge={true}
            lazyUpdate={true}
          />
        </Card>
      )}

      {analysisData.length > 0 && (
        <Card title="分析结果">
          <Table
            columns={analysisColumns}
            dataSource={analysisData}
            rowKey="id"
            pagination={false}
            loading={loading}
          />
        </Card>
      )}

      {loading && (
        <div style={{ textAlign: 'center', padding: '50px' }}>
          <Spin size="large" />
          <p style={{ marginTop: 16 }}>正在获取数据...</p>
        </div>
      )}
    </div>
  );
};

export default StockAnalysis;