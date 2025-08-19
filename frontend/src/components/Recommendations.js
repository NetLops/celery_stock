import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Table, 
  Tag, 
  Button, 
  Space, 
  Slider, 
  Select, 
  Row, 
  Col,
  Statistic,
  Progress,
  message,
  Spin
} from 'antd';
import { ReloadOutlined, TrophyOutlined, RiseOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const { Option } = Select;

const Recommendations = () => {
  const [loading, setLoading] = useState(false);
  const [recommendations, setRecommendations] = useState([]);
  const [potentialStocks, setPotentialStocks] = useState([]);
  const [sectorAnalysis, setSectorAnalysis] = useState([]);
  const [riskAnalysis, setRiskAnalysis] = useState({});
  const [filters, setFilters] = useState({
    minScore: 0.6,
    riskLevels: [],
    limit: 20
  });

  useEffect(() => {
    fetchAllData();
  }, []);

  const fetchAllData = async () => {
    setLoading(true);
    try {
      await Promise.all([
        fetchRecommendations(),
        fetchPotentialStocks(),
        fetchSectorAnalysis(),
        fetchRiskAnalysis()
      ]);
    } catch (error) {
      message.error('获取数据失败');
    } finally {
      setLoading(false);
    }
  };

  const fetchRecommendations = async () => {
    try {
      const params = new URLSearchParams({
        min_score: filters.minScore,
        limit: filters.limit
      });
      
      if (filters.riskLevels.length > 0) {
        params.append('risk_levels', filters.riskLevels.join(','));
      }

      const response = await axios.get(`/api/v1/recommendations/?${params}`);
      setRecommendations(response.data.data?.recommendations || []);
    } catch (error) {
      console.error('获取推荐失败:', error);
    }
  };

  const fetchPotentialStocks = async () => {
    try {
      const response = await axios.get('/api/v1/recommendations/potential?limit=10');
      setPotentialStocks(response.data.data?.potential_stocks || []);
    } catch (error) {
      console.error('获取潜力股票失败:', error);
    }
  };

  const fetchSectorAnalysis = async () => {
    try {
      const response = await axios.get('/api/v1/recommendations/sectors/analysis');
      setSectorAnalysis(response.data.data?.sector_analysis || []);
    } catch (error) {
      console.error('获取行业分析失败:', error);
    }
  };

  const fetchRiskAnalysis = async () => {
    try {
      const response = await axios.get('/api/v1/recommendations/risk/analysis');
      setRiskAnalysis(response.data.data || {});
    } catch (error) {
      console.error('获取风险分析失败:', error);
    }
  };

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
  };

  const applyFilters = () => {
    fetchRecommendations();
  };

  const getSectorChartOption = () => {
    return {
      title: {
        text: '行业推荐分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'axis',
        axisPointer: { type: 'shadow' }
      },
      xAxis: {
        type: 'category',
        data: sectorAnalysis.map(item => item.sector),
        axisLabel: { rotate: 45 }
      },
      yAxis: [
        {
          type: 'value',
          name: '推荐数量',
          position: 'left'
        },
        {
          type: 'value',
          name: '平均评分',
          position: 'right',
          max: 1
        }
      ],
      series: [
        {
          name: '推荐数量',
          type: 'bar',
          data: sectorAnalysis.map(item => item.recommendation_count),
          itemStyle: { color: '#1890ff' }
        },
        {
          name: '平均评分',
          type: 'line',
          yAxisIndex: 1,
          data: sectorAnalysis.map(item => item.average_score),
          itemStyle: { color: '#52c41a' }
        }
      ]
    };
  };

  const getRiskChartOption = () => {
    const riskData = riskAnalysis.risk_analysis || [];
    
    return {
      title: {
        text: '风险等级分布',
        left: 'center'
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c} ({d}%)'
      },
      series: [{
        name: '风险分布',
        type: 'pie',
        radius: '50%',
        data: riskData.map(item => ({
          value: item.stock_count,
          name: item.risk_level
        })),
        emphasis: {
          itemStyle: {
            shadowBlur: 10,
            shadowOffsetX: 0,
            shadowColor: 'rgba(0, 0, 0, 0.5)'
          }
        }
      }]
    };
  };

  const recommendationColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Tag color="blue">{symbol}</Tag>
    },
    {
      title: '公司名称',
      dataIndex: 'name',
      key: 'name',
      ellipsis: true
    },
    {
      title: '推荐类型',
      dataIndex: 'recommendation',
      key: 'recommendation',
      render: (rec) => {
        const colorMap = {
          'strong_buy': 'red',
          'buy': 'orange',
          'hold': 'blue',
          'sell': 'purple',
          'strong_sell': 'gray'
        };
        const textMap = {
          'strong_buy': '强烈买入',
          'buy': '买入',
          'hold': '持有',
          'sell': '卖出',
          'strong_sell': '强烈卖出'
        };
        return <Tag color={colorMap[rec] || 'default'}>{textMap[rec] || rec}</Tag>;
      }
    },
    {
      title: '评分',
      dataIndex: 'score',
      key: 'score',
      render: (score) => <Progress percent={Math.round(score * 100)} size="small" />
    },
    {
      title: '风险等级',
      dataIndex: 'risk_level',
      key: 'risk_level',
      render: (risk) => {
        const colorMap = {
          'low': 'green',
          'medium': 'orange',
          'high': 'red'
        };
        const textMap = {
          'low': '低风险',
          'medium': '中风险',
          'high': '高风险'
        };
        return <Tag color={colorMap[risk] || 'default'}>{textMap[risk] || risk}</Tag>;
      }
    },
    {
      title: '推荐理由',
      dataIndex: 'reasoning',
      key: 'reasoning',
      ellipsis: true
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    }
  ];

  const potentialColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Tag color="red">{symbol}</Tag>
    },
    {
      title: '综合评分',
      dataIndex: 'total_score',
      key: 'total_score',
      render: (score) => (
        <div>
          <Progress percent={Math.round(score * 100)} size="small" />
          <span style={{ marginLeft: 8 }}>{(score * 100).toFixed(1)}分</span>
        </div>
      )
    },
    {
      title: '推荐等级',
      dataIndex: 'recommendation',
      key: 'recommendation',
      render: (rec) => {
        const colorMap = {
          'strong_buy': 'red',
          'buy': 'orange'
        };
        const textMap = {
          'strong_buy': '强烈推荐',
          'buy': '推荐'
        };
        return <Tag color={colorMap[rec] || 'blue'}>{textMap[rec] || rec}</Tag>;
      }
    },
    {
      title: '置信度',
      dataIndex: 'confidence',
      key: 'confidence',
      render: (confidence) => `${(confidence * 100).toFixed(1)}%`
    }
  ];

  return (
    <div>
      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={8}>
          <Card>
            <Statistic
              title="推荐股票总数"
              value={recommendations.length}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="潜力股票"
              value={potentialStocks.length}
              prefix={<RiseOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={8}>
          <Card>
            <Statistic
              title="分析行业数"
              value={sectorAnalysis.length}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
      </Row>

      <Card title="筛选条件" style={{ marginBottom: 24 }}>
        <Row gutter={16}>
          <Col span={8}>
            <div>
              <label>最低评分: {filters.minScore}</label>
              <Slider
                min={0}
                max={1}
                step={0.1}
                value={filters.minScore}
                onChange={(value) => handleFilterChange('minScore', value)}
                marks={{
                  0: '0',
                  0.5: '0.5',
                  1: '1.0'
                }}
              />
            </div>
          </Col>
          <Col span={8}>
            <div>
              <label>风险等级:</label>
              <Select
                mode="multiple"
                style={{ width: '100%', marginTop: 8 }}
                placeholder="选择风险等级"
                value={filters.riskLevels}
                onChange={(value) => handleFilterChange('riskLevels', value)}
              >
                <Option value="low">低风险</Option>
                <Option value="medium">中风险</Option>
                <Option value="high">高风险</Option>
              </Select>
            </div>
          </Col>
          <Col span={8}>
            <div>
              <label>显示数量:</label>
              <Select
                style={{ width: '100%', marginTop: 8 }}
                value={filters.limit}
                onChange={(value) => handleFilterChange('limit', value)}
              >
                <Option value={10}>10条</Option>
                <Option value={20}>20条</Option>
                <Option value={50}>50条</Option>
                <Option value={100}>100条</Option>
              </Select>
            </div>
          </Col>
        </Row>
        <div style={{ marginTop: 16 }}>
          <Space>
            <Button type="primary" onClick={applyFilters}>
              应用筛选
            </Button>
            <Button onClick={() => {
              setFilters({ minScore: 0.6, riskLevels: [], limit: 20 });
              fetchRecommendations();
            }}>
              重置
            </Button>
          </Space>
        </div>
      </Card>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="行业分析">
            {sectorAnalysis.length > 0 ? (
              <ReactECharts 
                option={getSectorChartOption()} 
                style={{ height: '300px' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin />
                <p>加载行业数据...</p>
              </div>
            )}
          </Card>
        </Col>
        <Col span={12}>
          <Card title="风险分布">
            {riskAnalysis.risk_analysis?.length > 0 ? (
              <ReactECharts 
                option={getRiskChartOption()} 
                style={{ height: '300px' }}
              />
            ) : (
              <div style={{ textAlign: 'center', padding: '50px' }}>
                <Spin />
                <p>加载风险数据...</p>
              </div>
            )}
          </Card>
        </Col>
      </Row>

      <Card 
        title="潜力股票推荐" 
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchPotentialStocks}>
            刷新
          </Button>
        }
        style={{ marginBottom: 24 }}
      >
        <Table
          columns={potentialColumns}
          dataSource={potentialStocks}
          rowKey="symbol"
          loading={loading}
          pagination={false}
          size="small"
        />
      </Card>

      <Card 
        title="推荐列表" 
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchRecommendations}>
            刷新
          </Button>
        }
      >
        <Table
          columns={recommendationColumns}
          dataSource={recommendations}
          rowKey={(record) => `${record.symbol}-${record.created_at}`}
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 条推荐`
          }}
        />
      </Card>
    </div>
  );
};

export default Recommendations;
