import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { Layout, Menu, Typography } from 'antd';
import { 
  DashboardOutlined, 
  StockOutlined, 
  AnalysisOutlined, 
  StarOutlined,
  AppstoreAddOutlined 
} from '@ant-design/icons';
import Dashboard from './components/Dashboard';
import StockAnalysis from './components/StockAnalysis';
import BatchTasks from './components/BatchTasks';
import Recommendations from './components/Recommendations';
import AIChat from './components/AIChat';
import './App.css';

const { Header, Sider, Content } = Layout;
const { Title } = Typography;

function App() {
  const [collapsed, setCollapsed] = React.useState(false);

  const menuItems = [
    {
      key: '/',
      icon: <DashboardOutlined />,
      label: '仪表板',
    },
    {
      key: '/analysis',
      icon: <StockOutlined />,
      label: '股票分析',
    },
    {
      key: '/tasks',
      icon: <AppstoreAddOutlined />,
      label: '批量任务',
    },
    {
      key: '/recommendations',
      icon: <StarOutlined />,
      label: '推荐系统',
    },
    {
      key: '/chat',
      icon: <AnalysisOutlined />,
      label: 'AI助手',
    },
  ];

  return (
    <Router>
      <Layout style={{ minHeight: '100vh' }}>
        <Sider 
          collapsible 
          collapsed={collapsed} 
          onCollapse={setCollapsed}
          theme="dark"
        >
          <div className="logo" style={{ 
            height: 32, 
            margin: 16, 
            background: 'rgba(255, 255, 255, 0.3)',
            borderRadius: 6,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: 'white',
            fontWeight: 'bold'
          }}>
            {collapsed ? 'SA' : '股票分析系统'}
          </div>
          <Menu
            theme="dark"
            defaultSelectedKeys={['/']}
            mode="inline"
            items={menuItems}
            onClick={({ key }) => {
              window.location.pathname = key;
            }}
          />
        </Sider>
        
        <Layout>
          <Header style={{ 
            padding: '0 24px', 
            background: '#fff',
            display: 'flex',
            alignItems: 'center'
          }}>
            <Title level={3} style={{ margin: 0, color: '#1890ff' }}>
              智能股票分析平台
            </Title>
          </Header>
          
          <Content style={{ 
            margin: '24px 16px',
            padding: 24,
            background: '#fff',
            minHeight: 280,
            borderRadius: 6
          }}>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/analysis" element={<StockAnalysis />} />
              <Route path="/tasks" element={<BatchTasks />} />
              <Route path="/recommendations" element={<Recommendations />} />
              <Route path="/chat" element={<AIChat />} />
            </Routes>
          </Content>
        </Layout>
      </Layout>
    </Router>
  );
}

export default App;