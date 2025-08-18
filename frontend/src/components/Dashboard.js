import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Row, 
  Col, 
  Statistic, 
  Table, 
  Tag, 
  Progress,
  Alert,
  Spin
} from 'antd';
import { 
  StockOutlined, 
  AnalysisOutlined, 
  TasksOutlined,
  TrophyOutlined,
  ArrowUpOutlined,
  ArrowDownOutlined
} from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const Dashboard = () => {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState({
    stats: {},
    recentTasks: [],
    topRecommendations: [],
    marketOverview: {}
  });

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    setLoading(true);
    try {
      // 获取推荐数据
      const recommendationsResponse = await axios.get('/api/v1/recommendations/potential?limit=5');
      
      // 获取任务数据
      const tasksResponse = await axios.get('/api/v1/tasks?limit=5');
      
      // 模拟统计数据
      const stats = {
        totalStocks: 150,
        analysisCount: 1250,
        activeTasks: 8,
        recommendations: recommendationsResponse.data.data?.potential_stocks?.length || 0
      };

      setDashboardData({
        stats,
        recentTasks: tasksResponse.data.data || [],
        topRecommendations: recommendationsResponse.data.data?.potential_stocks || [],
        marketOverview: generateMarketOverview()
      });

    } catch (error) {
      console.error('获取仪表板数据失败:', error);
    } finally {
      setLoading(false);
    }
  };

  const generateMarketOverview = () => {
    return {
      sectors: [
        { name: '科技', value: 35, change: 2.5 },
        { name: '金融', value: 20, change: -1.2 },
        { name: '医疗', value: 15, change: 1.8 },
        { name: '消费', value: 18, change: 0.5 },
        { name: '能源', value: 12, change: -0.8 }
      ]
    };
  };

  const getMarketChartOption = () => {
    const sectors = dashboardData.marketOverview.sectors || [];
    
    return {
      title: {
        text: '行业分布',
        left: 'center',
        textStyle: { fontSize: 16 }
      },
      tooltip: {
        trigger: 'item',
        formatter: '{a} <br/>{b}: {c}% ({d}%)'
      },
      series: [{
        name: '行业占比',
        type: 'pie',
        radius: ['40%', '70%'],
        data: sectors.map(sector => ({
          value: sector.value,
          name: sector.name
        }))
      }]
    };
  };

  const taskColumns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      render: (id) => id.substring(0, 8) + '...'
    },
    {
      title: '类型',
      dataIndex: 'task_type',
      key: 'task_type',
      render: (type) => {
        const typeMap = {
          'batch_stocks': { text: '批量分析', color: 'blue' },
          'market_scan': { text: '市场扫描', color: 'green' }
        };
        const config = typeMap[type] || { text: type, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '状态',
      dataIndex: 'status',
      key: 'status',
      render: (status) => {
        const statusMap = {
          'pending': { text: '等待中', color: 'orange' },
          'running': { text: '运行中', color: 'blue' },
          'completed': { text: '已完成', color: 'green' },
          'failed': { text: '失败', color: 'red' }
        };
        const config = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    }
  ];

  const recommendationColumns = [
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
      render: (symbol) => <Tag color="blue">{symbol}</Tag>
    },
    {
      title: '评分',
      dataIndex: 'total_score',
      key: 'total_score',
      render: (score) => <Progress percent={Math.round(score * 100)} size="small" />
    },
    {
      title: '推荐',
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
        return <Tag color={colorMap[rec] || 'default'}>{rec}</Tag>;
      }
    }
  ];

  if (loading) {
    return (
      <div style={{ textAlign: 'center', padding: '50px' }}>
        <Spin size="large" />
        <p style={{ marginTop: 16 }}>加载仪表板数据...</p>
      </div>
    );
  }

  return (
    <div>
      <Alert
        message="欢迎使用智能股票分析系统"
        description="基于AI的股票分析平台，提供技术分析、基本面分析和智能推荐功能"
        type="info"
        showIcon
        style={{ marginBottom: 24 }}
      />

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={6}>
          <Card>
            <Statistic
              title="总股票数"
              value={dashboardData.stats.totalStocks}
              prefix={<StockOutlined />}
              valueStyle={{ color: '#1890ff' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="分析次数"
              value={dashboardData.stats.analysisCount}
              prefix={<AnalysisOutlined />}
              valueStyle={{ color: '#52c41a' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="活跃任务"
              value={dashboardData.stats.activeTasks}
              prefix={<TasksOutlined />}
              valueStyle={{ color: '#faad14' }}
            />
          </Card>
        </Col>
        <Col span={6}>
          <Card>
            <Statistic
              title="推荐股票"
              value={dashboardData.stats.recommendations}
              prefix={<TrophyOutlined />}
              valueStyle={{ color: '#f5222d' }}
            />
          </Card>
        </Col>
      </Row>

      <Row gutter={16} style={{ marginBottom: 24 }}>
        <Col span={12}>
          <Card title="市场概览">
            <ReactECharts 
              option={getMarketChartOption()} 
              style={{ height: '300px' }}
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="行业涨跌">
            {dashboardData.marketOverview.sectors?.map(sector => (
              <div key={sector.name} style={{ 
                display: 'flex', 
                justifyContent: 'space-between', 
                alignItems: 'center',
                padding: '8px 0',
                borderBottom: '1px solid #f0f0f0'
              }}>
                <span>{sector.name}</span>
                <span style={{ 
                  color: sector.change >= 0 ? '#52c41a' : '#f5222d',
                  fontWeight: 'bold'
                }}>
                  {sector.change >= 0 ? <ArrowUpOutlined /> : <ArrowDownOutlined />}
                  {Math.abs(sector.change)}%
                </span>
              </div>
            ))}
          </Card>
        </Col>
      </Row>

      <Row gutter={16}>
        <Col span={12}>
          <Card title="最近任务">
            <Table
              columns={taskColumns}
              dataSource={dashboardData.recentTasks}
              rowKey="task_id"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
        <Col span={12}>
          <Card title="热门推荐">
            <Table
              columns={recommendationColumns}
              dataSource={dashboardData.topRecommendations}
              rowKey="symbol"
              pagination={false}
              size="small"
            />
          </Card>
        </Col>
      </Row>
    </div>
  );
};

export default Dashboard;