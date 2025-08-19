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
  Progress,
  Modal,
  Typography,
  Divider,
  List,
  Select,
  AutoComplete,
  Tooltip,
  Form,
  Popconfirm
} from 'antd';
import { SearchOutlined, FileSearchOutlined, LineChartOutlined, InfoCircleOutlined, PlusOutlined, EditOutlined, DeleteOutlined } from '@ant-design/icons';
import ReactECharts from 'echarts-for-react';
import axios from 'axios';

const { Search } = Input;
const { Title, Paragraph, Text } = Typography;
const { Option } = Select;

const StockAnalysis = () => {
  const [loading, setLoading] = useState(false);
  const [stockData, setStockData] = useState(null);
  const [analysisData, setAnalysisData] = useState([]);
  const [chartData, setChartData] = useState(null);
  const [detailModalVisible, setDetailModalVisible] = useState(false);
  const [currentAnalysis, setCurrentAnalysis] = useState(null);
  const [searchMode, setSearchMode] = useState('symbol'); // 'symbol' 或 'name'
  const [searchValue, setSearchValue] = useState('');
  const [stockOptions, setStockOptions] = useState([]);
  const [searchLoading, setSearchLoading] = useState(false);
  
  // 映射表相关状态
  const [mappingModalVisible, setMappingModalVisible] = useState(false);
  const [mappingData, setMappingData] = useState([]);
  const [mappingLoading, setMappingLoading] = useState(false);
  const [mappingPagination, setMappingPagination] = useState({
    current: 1,
    pageSize: 10,
    total: 0
  });
  const [mappingFormVisible, setMappingFormVisible] = useState(false);
  const [editingMapping, setEditingMapping] = useState(null);
  const [mappingForm] = Form.useForm();

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

  const searchStockByName = async (name) => {
    if (!name || name.length < 2) {
      setStockOptions([]);
      return;
    }

    setSearchLoading(true);
    try {
      const response = await axios.get(`/api/v1/stocks/search?name=${encodeURIComponent(name)}`);
      const results = response.data.data || [];
      
      const options = results.map(stock => ({
        value: stock.symbol,
        label: (
          <div>
            <div><b>{stock.symbol}</b> - {stock.name}</div>
            <div style={{ fontSize: '12px', color: '#888' }}>{stock.exchange || '未知交易所'}</div>
          </div>
        )
      }));
      
      setStockOptions(options);
    } catch (error) {
      console.error('搜索股票失败:', error);
    } finally {
      setSearchLoading(false);
    }
  };

  const handleSearchModeChange = (mode) => {
    setSearchMode(mode);
    setSearchValue('');
    setStockOptions([]);
  };

  const handleSearchInputChange = (value) => {
    setSearchValue(value);
    if (searchMode === 'name') {
      searchStockByName(value);
    }
  };

  const handleSearchSubmit = (value) => {
    if (searchMode === 'symbol') {
      handleSearch(value);
    } else if (value) {
      handleSearch(value);
    }
  };

  // 映射表相关函数
  const loadMappingData = async (page = 1, pageSize = 10) => {
    setMappingLoading(true);
    try {
      const skip = (page - 1) * pageSize;
      const response = await axios.get(`/api/v1/stocks/mappings?skip=${skip}&limit=${pageSize}`);
      const { items, total } = response.data.data;
      
      setMappingData(items);
      setMappingPagination({
        current: page,
        pageSize: pageSize,
        total: total
      });
    } catch (error) {
      console.error('获取股票名称映射失败:', error);
      message.error('获取股票名称映射失败');
    } finally {
      setMappingLoading(false);
    }
  };

  const handleMappingTableChange = (pagination) => {
    loadMappingData(pagination.current, pagination.pageSize);
  };

  const showMappingModal = () => {
    setMappingModalVisible(true);
    loadMappingData();
  };

  const showAddMappingForm = () => {
    setEditingMapping(null);
    mappingForm.resetFields();
    setMappingFormVisible(true);
  };

  const showEditMappingForm = (record) => {
    setEditingMapping(record);
    mappingForm.setFieldsValue({
      chinese_name: record.chinese_name,
      english_name: record.english_name,
      symbol: record.symbol
    });
    setMappingFormVisible(true);
  };

  const handleMappingFormSubmit = async () => {
    try {
      const values = await mappingForm.validateFields();
      
      if (editingMapping) {
        // 更新映射
        await axios.put(`/api/v1/stocks/mappings/${editingMapping.id}`, values);
        message.success('更新映射成功');
      } else {
        // 添加映射
        await axios.post('/api/v1/stocks/mappings', values);
        message.success('添加映射成功');
      }
      
      setMappingFormVisible(false);
      loadMappingData(mappingPagination.current, mappingPagination.pageSize);
    } catch (error) {
      console.error('保存映射失败:', error);
      message.error('保存映射失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleDeleteMapping = async (id) => {
    try {
      await axios.delete(`/api/v1/stocks/mappings/${id}`);
      message.success('删除映射成功');
      loadMappingData(mappingPagination.current, mappingPagination.pageSize);
    } catch (error) {
      console.error('删除映射失败:', error);
      message.error('删除映射失败: ' + (error.response?.data?.detail || error.message));
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
            setCurrentAnalysis(record);
            setDetailModalVisible(true);
          }}
        >
          查看详情
        </Button>
      )
    }
  ];

  const mappingColumns = [
    {
      title: '中文名称',
      dataIndex: 'chinese_name',
      key: 'chinese_name',
    },
    {
      title: '英文名称',
      dataIndex: 'english_name',
      key: 'english_name',
    },
    {
      title: '股票代码',
      dataIndex: 'symbol',
      key: 'symbol',
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space size="small">
          <Button 
            type="text" 
            icon={<EditOutlined />} 
            onClick={() => showEditMappingForm(record)}
          />
          <Popconfirm
            title="确定要删除这条映射吗？"
            onConfirm={() => handleDeleteMapping(record.id)}
            okText="确定"
            cancelText="取消"
          >
            <Button 
              type="text" 
              danger 
              icon={<DeleteOutlined />} 
            />
          </Popconfirm>
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card title="股票分析" style={{ marginBottom: 24 }} extra={
        <Tooltip title="查看股票名称映射表">
          <Button 
            type="text" 
            icon={<InfoCircleOutlined />} 
            onClick={showMappingModal}
          >
            股票名称映射表
          </Button>
        </Tooltip>
      }>
        <Space direction="vertical" style={{ width: '100%' }}>
          <Input.Group compact>
            <Select 
              defaultValue="symbol" 
              value={searchMode}
              onChange={handleSearchModeChange}
              style={{ width: '120px' }}
            >
              <Option value="symbol">股票代码</Option>
              <Option value="name">股票名称</Option>
            </Select>
            
            {searchMode === 'symbol' ? (
              <Search
                placeholder="请输入股票代码 (如: AAPL, GOOGL)"
                allowClear
                enterButton={<SearchOutlined />}
                size="large"
                style={{ width: 'calc(100% - 120px)' }}
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                onSearch={handleSearchSubmit}
                loading={loading}
              />
            ) : (
              <AutoComplete
                placeholder="请输入股票名称 (如: 苹果, 谷歌)"
                allowClear
                style={{ width: 'calc(100% - 120px)' }}
                value={searchValue}
                onChange={handleSearchInputChange}
                onSelect={handleSearchSubmit}
                options={stockOptions}
                loading={searchLoading}
              >
                <Input 
                  size="large"
                  suffix={
                    <Button 
                      type="primary" 
                      icon={<SearchOutlined />} 
                      loading={loading || searchLoading}
                      onClick={() => searchValue && handleSearchSubmit(searchValue)}
                    />
                  }
                />
              </AutoComplete>
            )}
          </Input.Group>
          
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
                icon={<FileSearchOutlined />}
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

      {/* 分析详情弹窗 */}
      <Modal
        title={
          currentAnalysis ? 
          `${currentAnalysis.analysis_type === 'technical' ? '技术分析' : 
            currentAnalysis.analysis_type === 'fundamental' ? '基本面分析' : 
            currentAnalysis.analysis_type === 'sentiment' ? '情绪分析' : 
            currentAnalysis.analysis_type === 'recommendation' ? '投资建议' : 
            '分析'} 详情` : '分析详情'
        }
        open={detailModalVisible}
        onCancel={() => setDetailModalVisible(false)}
        width={800}
        footer={[
          <Button key="close" onClick={() => setDetailModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        {currentAnalysis && (
          <div className="analysis-detail">
            <Row gutter={[0, 16]}>
              <Col span={24}>
                <Card>
                  <Statistic 
                    title="分析类型" 
                    value={
                      currentAnalysis.analysis_type === 'technical' ? '技术分析' : 
                      currentAnalysis.analysis_type === 'fundamental' ? '基本面分析' : 
                      currentAnalysis.analysis_type === 'sentiment' ? '情绪分析' : 
                      currentAnalysis.analysis_type === 'recommendation' ? '投资建议' : 
                      currentAnalysis.analysis_type
                    } 
                  />
                </Card>
              </Col>
              
              <Col span={12}>
                <Card>
                  <Statistic 
                    title="置信度" 
                    value={`${Math.round(currentAnalysis.confidence_score * 100)}%`} 
                    valueStyle={{ color: currentAnalysis.confidence_score > 0.7 ? '#3f8600' : 
                                 currentAnalysis.confidence_score > 0.4 ? '#faad14' : '#cf1322' }}
                  />
                </Card>
              </Col>
              
              <Col span={12}>
                <Card>
                  <Statistic 
                    title="分析时间" 
                    value={new Date(currentAnalysis.created_at).toLocaleString()} 
                  />
                </Card>
              </Col>
            </Row>
            
            <Divider orientation="left">分析内容</Divider>
            
            <Typography>
              {currentAnalysis.content && typeof currentAnalysis.content === 'object' ? (
                <div>
                  {Object.entries(currentAnalysis.content).map(([key, value]) => (
                    <div key={key} style={{ marginBottom: '16px' }}>
                      <Title level={5}>{key.replace(/_/g, ' ').toUpperCase()}</Title>
                      {typeof value === 'object' ? (
                        <List
                          bordered
                          dataSource={Object.entries(value)}
                          renderItem={([subKey, subValue]) => (
                            <List.Item>
                              <Text strong>{subKey.replace(/_/g, ' ')}:</Text> {subValue}
                            </List.Item>
                          )}
                        />
                      ) : (
                        <Paragraph>{value}</Paragraph>
                      )}
                    </div>
                  ))}
                </div>
              ) : (
                <Paragraph>{currentAnalysis.content || '无详细内容'}</Paragraph>
              )}
            </Typography>
          </div>
        )}
      </Modal>

      {/* 股票名称映射表弹窗 */}
      <Modal
        title="股票名称映射表"
        open={mappingModalVisible}
        onCancel={() => setMappingModalVisible(false)}
        width={800}
        footer={[
          <Button 
            key="add" 
            type="primary" 
            icon={<PlusOutlined />} 
            onClick={showAddMappingForm}
          >
            添加映射
          </Button>,
          <Button key="close" onClick={() => setMappingModalVisible(false)}>
            关闭
          </Button>
        ]}
      >
        <div style={{ marginBottom: 16 }}>
          <Text>此表提供了常见股票的中英文名称映射，方便通过中文名称查找股票代码。您可以添加、编辑或删除映射。</Text>
        </div>
        <Table
          columns={mappingColumns}
          dataSource={mappingData}
          loading={mappingLoading}
          pagination={mappingPagination}
          onChange={handleMappingTableChange}
          rowKey="id"
          size="small"
        />
      </Modal>

      {/* 映射表编辑弹窗 */}
      <Modal
        title={editingMapping ? "编辑映射" : "添加映射"}
        open={mappingFormVisible}
        onCancel={() => setMappingFormVisible(false)}
        onOk={handleMappingFormSubmit}
        confirmLoading={mappingLoading}
      >
        <Form
          form={mappingForm}
          layout="vertical"
        >
          <Form.Item
            name="chinese_name"
            label="中文名称"
            rules={[{ required: true, message: '请输入中文名称' }]}
          >
            <Input placeholder="请输入中文名称，如：苹果" />
          </Form.Item>
          <Form.Item
            name="english_name"
            label="英文名称"
            rules={[{ required: true, message: '请输入英文名称' }]}
          >
            <Input placeholder="请输入英文名称，如：Apple Inc." />
          </Form.Item>
          <Form.Item
            name="symbol"
            label="股票代码"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <Input placeholder="请输入股票代码，如：AAPL" />
          </Form.Item>
        </Form>
      </Modal>
    </div>
  );
};

export default StockAnalysis;