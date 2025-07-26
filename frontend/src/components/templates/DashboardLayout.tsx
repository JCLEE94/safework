import React, { useState, useMemo } from 'react';
import { Layout, Menu, Drawer, Grid, Avatar, Space, Badge, Dropdown, Input, Typography } from 'antd';
import { 
  MenuOutlined, 
  BellOutlined, 
  UserOutlined, 
  SearchOutlined,
  LogoutOutlined,
  SettingOutlined,
} from '@ant-design/icons';
import styled from 'styled-components';
import { useLocation, useNavigate } from 'react-router-dom';
import { navigationMenus } from '../../constants/navigation';
import { designTokens } from '../../styles/theme';

const { Header, Sider, Content } = Layout;
const { useBreakpoint } = Grid;
const { Text } = Typography;

const StyledLayout = styled(Layout)`
  min-height: 100vh;
  background: ${designTokens.colors.neutral[50]};
`;

const StyledHeader = styled(Header)`
  background: #ffffff;
  padding: 0 ${designTokens.spacing.lg}px;
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  box-shadow: ${designTokens.shadows.sm};
  position: sticky;
  top: 0;
  z-index: 100;
  
  @media (max-width: ${designTokens.breakpoints.md}px) {
    padding: 0 ${designTokens.spacing.md}px;
  }
`;

const Logo = styled.div<{ collapsed?: boolean }>`
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: ${designTokens.spacing.md}px;
  border-bottom: 1px solid ${designTokens.colors.neutral[200]};
  transition: all ${designTokens.transitions.base};
  
  img {
    height: 32px;
    transition: all ${designTokens.transitions.base};
  }
  
  h1 {
    margin: 0 0 0 ${designTokens.spacing.sm}px;
    font-size: ${designTokens.typography.fontSize.xl}px;
    font-weight: ${designTokens.typography.fontWeight.bold};
    color: ${designTokens.colors.primary[600]};
    transition: all ${designTokens.transitions.base};
    opacity: ${props => props.collapsed ? 0 : 1};
    width: ${props => props.collapsed ? 0 : 'auto'};
    overflow: hidden;
  }
`;

const SearchBar = styled(Input)`
  max-width: 400px;
  
  @media (max-width: ${designTokens.breakpoints.md}px) {
    display: none;
  }
`;

const HeaderActions = styled(Space)`
  .ant-badge {
    cursor: pointer;
  }
`;

const StyledSider = styled(Sider)`
  background: #ffffff;
  box-shadow: ${designTokens.shadows.sm};
  
  .ant-layout-sider-trigger {
    background: #ffffff;
    color: ${designTokens.colors.neutral[600]};
    border-top: 1px solid ${designTokens.colors.neutral[200]};
  }
  
  .ant-menu {
    border-right: none;
  }
  
  .ant-menu-item {
    margin: 4px 8px;
    border-radius: ${designTokens.borderRadius.base}px;
  }
  
  .ant-menu-submenu {
    .ant-menu-submenu-title {
      margin: 4px 8px;
      border-radius: ${designTokens.borderRadius.base}px;
    }
  }
`;

const MobileMenuButton = styled.div`
  display: none;
  font-size: 20px;
  cursor: pointer;
  
  @media (max-width: ${designTokens.breakpoints.md}px) {
    display: block;
  }
`;

const StyledContent = styled(Content)`
  margin: ${designTokens.spacing.lg}px;
  
  @media (max-width: ${designTokens.breakpoints.md}px) {
    margin: ${designTokens.spacing.md}px;
  }
`;

const UserInfo = styled.div`
  display: flex;
  align-items: center;
  gap: ${designTokens.spacing.sm}px;
  cursor: pointer;
  padding: ${designTokens.spacing.xs}px ${designTokens.spacing.sm}px;
  border-radius: ${designTokens.borderRadius.base}px;
  transition: all ${designTokens.transitions.fast};
  
  &:hover {
    background: ${designTokens.colors.neutral[50]};
  }
  
  @media (max-width: ${designTokens.breakpoints.sm}px) {
    .user-name {
      display: none;
    }
  }
`;

export const DashboardLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [collapsed, setCollapsed] = useState(false);
  const [mobileDrawerVisible, setMobileDrawerVisible] = useState(false);
  const screens = useBreakpoint();
  const location = useLocation();
  const navigate = useNavigate();

  const isMobile = !screens.md;

  // 현재 경로에 맞는 선택된 메뉴 키 찾기
  const selectedKeys = useMemo(() => {
    const pathname = location.pathname;
    const findSelectedKey = (items: typeof navigationMenus): string[] => {
      for (const item of items) {
        if ('path' in item && item.path === pathname) {
          return [item.key as string];
        }
        if ('children' in item && item.children) {
          const childKey = findSelectedKey(item.children);
          if (childKey.length > 0) {
            return childKey;
          }
        }
      }
      return [];
    };
    return findSelectedKey(navigationMenus);
  }, [location.pathname]);

  // 사용자 메뉴 아이템
  const userMenuItems = [
    {
      key: 'profile',
      label: '내 정보',
      icon: <UserOutlined />,
    },
    {
      key: 'settings',
      label: '설정',
      icon: <SettingOutlined />,
    },
    {
      type: 'divider' as const,
    },
    {
      key: 'logout',
      label: '로그아웃',
      icon: <LogoutOutlined />,
      danger: true,
    },
  ];

  const handleMenuClick = ({ keyPath }: { keyPath: string[] }) => {
    const item = navigationMenus.find(menu => {
      if (menu.key === keyPath[keyPath.length - 1]) return true;
      if ('children' in menu && menu.children) {
        return menu.children.find(child => child.key === keyPath[0]);
      }
      return false;
    });
    
    if (item && 'children' in item && item.children) {
      const child = item.children.find(c => c.key === keyPath[0]);
      if (child && 'path' in child && child.path) {
        navigate(child.path);
      }
    } else if (item && 'path' in item && item.path) {
      navigate(item.path);
    }
    
    if (isMobile) {
      setMobileDrawerVisible(false);
    }
  };

  return (
    <StyledLayout>
      <StyledSider
        collapsible
        collapsed={collapsed}
        onCollapse={setCollapsed}
        trigger={!isMobile ? undefined : null}
        width={256}
        collapsedWidth={80}
        breakpoint="md"
        style={{ display: isMobile ? 'none' : 'block' }}
      >
        <Logo collapsed={collapsed}>
          <img src="/logo.png" alt="SafeWork Pro" />
          <h1>SafeWork Pro</h1>
        </Logo>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={navigationMenus.map(item => item.key)}
          items={navigationMenus as any}
          onClick={handleMenuClick as any}
          style={{ borderRight: 0 }}
        />
      </StyledSider>
      
      <Layout>
        <StyledHeader>
          <div style={{ display: 'flex', alignItems: 'center', gap: designTokens.spacing.md }}>
            <MobileMenuButton onClick={() => setMobileDrawerVisible(true)}>
              <MenuOutlined />
            </MobileMenuButton>
            {isMobile && <h2 style={{ margin: 0, fontSize: 18 }}>SafeWork Pro</h2>}
            {!isMobile && (
              <SearchBar
                placeholder="검색어를 입력하세요"
                prefix={<SearchOutlined />}
                allowClear
              />
            )}
          </div>
          
          <HeaderActions size="middle">
            <Badge count={5} size="small">
              <BellOutlined style={{ fontSize: 20 }} />
            </Badge>
            
            <Dropdown menu={{ items: userMenuItems as any }} placement="bottomRight">
              <UserInfo>
                <Avatar icon={<UserOutlined />} />
                <div className="user-name">
                  <Text strong>홍길동</Text>
                  <br />
                  <Text type="secondary" style={{ fontSize: 12 }}>보건관리자</Text>
                </div>
              </UserInfo>
            </Dropdown>
          </HeaderActions>
        </StyledHeader>
        
        <StyledContent>{children}</StyledContent>
      </Layout>
      
      <Drawer
        placement="left"
        open={mobileDrawerVisible}
        onClose={() => setMobileDrawerVisible(false)}
        width={280}
        bodyStyle={{ padding: 0 }}
      >
        <Logo>
          <img src="/logo.png" alt="SafeWork Pro" />
          <h1>SafeWork Pro</h1>
        </Logo>
        <Menu
          mode="inline"
          selectedKeys={selectedKeys}
          defaultOpenKeys={[]}
          items={navigationMenus as any}
          onClick={handleMenuClick as any}
          style={{ borderRight: 0 }}
        />
      </Drawer>
    </StyledLayout>
  );
};