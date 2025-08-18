import React, { useState, useEffect } from 'react';
import { 
  Card, 
  Form, 
  Input, 
  Button, 
  Table, 
  Tag, 
  Space, 
  message, 
  Modal,
  Progress,
  Select,
  Divider
} from 'antd';
import { PlusOutlined, ReloadOutlined, DeleteOutlined, EyeOutlined } from '@ant-design/icons';
import axios from 'axios';

const { TextArea } = Input;
const { Option } = Select;

const BatchTasks = () => {
  const [form] = Form.useForm();
  const [loading, setLoading] = useState(false);
  const [tasks, setTasks] = useState([]);
  const [modalVisible, setModalVisible] = useState(false);
  const [selectedTask, setSelectedTask] = useState(null);

  useEffect(() => {
    fetchTasks();
  }, []);

  const fetchTasks = async () => {
    setLoading(true);
    try {
      const response = await axios.get('/api/v1/tasks/?limit=50');
      setTasks(response.data.data || []);
    } catch (error) {
      message.error('获取任务列表失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateBatchTask = async (values) => {
    setLoading(true);
    try {
      const symbols = values.symbols.split(/[,\s\n]+/).filter(s => s.trim());
      
      const response = await axios.post('/api/v1/tasks/batch-analysis', {
        symbols: symbols,
        analysis_types: values.analysis_types,
        priority: values.priority || 'normal'
      });

      message.success('批量分析任务创建成功');
      form.resetFields();
      fetchTasks();
      
    } catch (error) {
      message.error('创建任务失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCreateMarketScan = async () => {
    setLoading(true);
    try {
      const response = await axios.post('/api/v1/tasks/market-scan');
      message.success('市场扫描任务创建成功');
      fetchTasks();
    } catch (error) {
      message.error('创建扫描任务失败: ' + (error.response?.data?.detail || error.message));
    } finally {
      setLoading(false);
    }
  };

  const handleCancelTask = async (taskId) => {
    try {
      await axios.delete(`/api/v1/tasks/${taskId}`);
      message.success('任务已取消');
      fetchTasks();
    } catch (error) {
      message.error('取消任务失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewTaskDetail = async (taskId) => {
    try {
      const response = await axios.get(`/api/v1/tasks/${taskId}`);
      setSelectedTask(response.data.data);
      setModalVisible(true);
    } catch (error) {
      message.error('获取任务详情失败: ' + (error.response?.data?.detail || error.message));
    }
  };

  const columns = [
    {
      title: '任务ID',
      dataIndex: 'task_id',
      key: 'task_id',
      render: (id) => (
        <Button type="link" onClick={() => handleViewTaskDetail(id)}>
          {id.substring(0, 8)}...
        </Button>
      )
    },
    {
      title: '任务类型',
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
      title: '股票数量',
      dataIndex: 'symbols_count',
      key: 'symbols_count',
      render: (count) => count || '-'
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
          'failed': { text: '失败', color: 'red' },
          'cancelled': { text: '已取消', color: 'gray' }
        };
        const config = statusMap[status] || { text: status, color: 'default' };
        return <Tag color={config.color}>{config.text}</Tag>;
      }
    },
    {
      title: '进度',
      dataIndex: 'progress',
      key: 'progress',
      render: (progress) => <Progress percent={progress} size="small" />
    },
    {
      title: '创建时间',
      dataIndex: 'created_at',
      key: 'created_at',
      render: (time) => new Date(time).toLocaleString()
    },
    {
      title: '完成时间',
      dataIndex: 'completed_at',
      key: 'completed_at',
      render: (time) => time ? new Date(time).toLocaleString() : '-'
    },
    {
      title: '操作',
      key: 'action',
      render: (_, record) => (
        <Space>
          <Button 
            type="link" 
            icon={<EyeOutlined />}
            onClick={() => handleViewTaskDetail(record.task_id)}
          >
            详情
          </Button>
          {['pending', 'running'].includes(record.status) && (
            <Button 
              type="link" 
              danger
              icon={<DeleteOutlined />}
              onClick={() => handleCancelTask(record.task_id)}
            >
              取消
            </Button>
          )}
        </Space>
      )
    }
  ];

  return (
    <div>
      <Card title="创建批量任务" style={{ marginBottom: 24 }}>
        <Form
          form={form}
          layout="vertical"
          onFinish={handleCreateBatchTask}
        >
          <Form.Item
            name="symbols"
            label="股票代码"
            rules={[{ required: true, message: '请输入股票代码' }]}
          >
            <TextArea
              rows={4}
              placeholder="请输入股票代码，支持多种分隔符（逗号、空格、换行）&#10;例如：AAPL, GOOGL, MSFT&#10;或：AAPL GOOGL MSFT&#10;或每行一个代码"
            />
          </Form.Item>

          <Form.Item
            name="analysis_types"
            label="分析类型"
            rules={[{ required: true, message: '请选择分析类型' }]}
            initialValue={['technical', 'fundamental']}
          >
            <Select mode="multiple" placeholder="选择分析类型">
              <Option value="technical">技术分析</Option>
              <Option value="fundamental">基本面分析</Option>
              <Option value="sentiment">情绪分析</Option>
              <Option value="recommendation">投资建议</Option>
            </Select>
          </Form.Item>

          <Form.Item
            name="priority"
            label="任务优先级"
            initialValue="normal"
          >
            <Select>
              <Option value="low">低</Option>
              <Option value="normal">普通</Option>
              <Option value="high">高</Option>
            </Select>
          </Form.Item>

          <Form.Item>
            <Space>
              <Button type="primary" htmlType="submit" loading={loading} icon={<PlusOutlined />}>
                创建批量分析任务
              </Button>
              <Button onClick={handleCreateMarketScan} loading={loading}>
                创建市场扫描任务
              </Button>
            </Space>
          </Form.Item>
        </Form>
      </Card>

      <Card 
        title="任务列表" 
        extra={
          <Button icon={<ReloadOutlined />} onClick={fetchTasks} loading={loading}>
            刷新
          </Button>
        }
      >
        <Table
          columns={columns}
          dataSource={tasks}
          rowKey="task_id"
          loading={loading}
          pagination={{
            pageSize: 10,
            showSizeChanger: true,
            showQuickJumper: true,
            showTotal: (total) => `共 ${total} 个任务`
          }}
        />
      </Card>

      <Modal
        title="任务详情"
        visible={modalVisible}
        onCancel={() => setModalVisible(false)}
        footer={null}
        width={800}
      >
        {selectedTask && (
          <div>
            <p><strong>任务ID:</strong> {selectedTask.task_id}</p>
            <p><strong>任务类型:</strong> {selectedTask.task_type}</p>
            <p><strong>状态:</strong> 
              <Tag color={
                selectedTask.status === 'completed' ? 'green' :
                selectedTask.status === 'failed' ? 'red' :
                selectedTask.status === 'running' ? 'blue' : 'orange'
              }>
                {selectedTask.status}
              </Tag>
            </p>
            <p><strong>进度:</strong> <Progress percent={selectedTask.progress} /></p>
            <p><strong>股票列表:</strong></p>
            <div style={{ marginBottom: 16 }}>
              {selectedTask.symbols?.map(symbol => (
                <Tag key={symbol} color="blue">{symbol}</Tag>
              ))}
            </div>
            
            {selectedTask.result && (
              <>
                <Divider>任务结果</Divider>
                <pre style={{ 
                  background: '#f5f5f5', 
                  padding: 16, 
                  borderRadius: 4,
                  maxHeight: 300,
                  overflow: 'auto'
                }}>
                  {JSON.stringify(selectedTask.result, null, 2)}
                </pre>
              </>
            )}

            {selectedTask.error_message && (
              <>
                <Divider>错误信息</Divider>
                <div style={{ color: 'red', background: '#fff2f0', padding: 16, borderRadius: 4 }}>
                  {selectedTask.error_message}
                </div>
              </>
            )}
          </div>
        )}
      </Modal>
    </div>
  );
};

export default BatchTasks;