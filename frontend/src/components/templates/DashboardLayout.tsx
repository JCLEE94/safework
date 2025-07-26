import React, { useState } from 'react';
import { Layout, Menu, Drawer, Grid } from 'antd';
import { MenuOutlined } from '@ant-design/icons';
import styled from 'styled-components';
import { useLocation, useNavigate } from 'react-router-dom';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
`;

const MobileHeader = styled(Header)`
  display: none;
  padding: 0 16px;
  background: #fff;
  box-shadow: 0 2px 8px rgba(0,0,0,0.09);
  
  @media (max-width: 768px) {
    display: flex;
    align-items: center;
    position: fixed;
    top: 0;
    left: 0;
    right: 0;
    z-index: 100;
  }
`;

const StyledContent = styled(Content)`
  padding: 24px;
  background: #f0f2f5;
  
  @media (max-width: 768px) {
    padding: 16px;
    margin-top: 64px;
  }
`;

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const screens = useBreakpoint();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = !screens.md;

  const menuItems = [
    { key: 'dashboard', label: '대시보드' },
    { key: 'workers', label: '작업자 관리' },
    { key: 'health-exam', label: '건강검진 관리' },
    { key: 'incidents', label: '사고 관리' },
    { key: 'compliance', label: '규정 준수' },
  ];

  return (
    <StyledLayout>
      {isMobile && (
        <MobileHeader>
          <MenuOutlined onClick={() => setMobileDrawerVisible(true)} />
          <h2 style={{ margin: '0 0 0 16px' }}>SafeWork Pro</h2>
        </MobileHeader>
      )}
      
      {!isMobile ? (
        <Sider
          collapsible
          collapsed={collapsed}
          onCollapse={setCollapsed}
          theme="light"
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname.split('/')[1] || 'dashboard']}
            items={menuItems}
            onClick={({ key }) => navigate(`/${key}`)}
          />
        </Sider>
      ) : (
        <Drawer
          placement="left"
          open={mobileDrawerVisible}
          onClose={() => setMobileDrawerVisible(false)}
          width={280}
        >
          <Menu
            mode="inline"
            selectedKeys={[location.pathname.split('/')[1] || 'dashboard']}
            items={menuItems}
            onClick={({ key }) => {
              navigate(`/${key}`);
              setMobileDrawerVisible(false);
            }}
          />
        </Drawer>
      )}
      
      <Layout>
        <StyledContent>{children}</StyledContent>
      </Layout>
    </StyledLayout>
  );
};