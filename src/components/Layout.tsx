import React from 'react';
import { 
  AppBar, 
  Toolbar, 
  Typography, 
  Drawer, 
  List, 
  ListItem, 
  ListItemIcon, 
  ListItemText, 
  Box,
  IconButton,
  Divider,
  ListItemButton
} from '@mui/material';
import {
  Dashboard,
  People,
  LocalHospital,
  Assignment,
  School,
  Science,
  Warning,
  Description,
  Assessment,
  Settings as SettingsIcon,
  Menu as MenuIcon,
  QrCode,
  MedicalServices,
  Logout
} from '@mui/icons-material';

interface LayoutProps {
  children: React.ReactNode;
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  activeMenu: string;
  setActiveMenu: (menu: string) => void;
  onLogout: () => void;
}

export function Layout({ 
  children, 
  sidebarOpen, 
  setSidebarOpen, 
  activeMenu, 
  setActiveMenu,
  onLogout 
}: LayoutProps) {
  const menuItems = [
    { id: 'dashboard', label: '대시보드', icon: <Dashboard /> },
    { id: 'workers', label: '근로자 관리', icon: <People /> },
    { id: 'health', label: '건강검진', icon: <LocalHospital /> },
    { id: 'appointments', label: '검진 예약', icon: <Assignment /> },
    { id: 'health-room', label: '건강관리실', icon: <MedicalServices /> },
    { id: 'environment', label: '작업환경 측정', icon: <Assessment /> },
    { id: 'education', label: '보건교육', icon: <School /> },
    { id: 'chemicals', label: '화학물질 관리', icon: <Science /> },
    { id: 'accidents', label: '산업재해', icon: <Warning /> },
    { id: 'unified-documents', label: '통합문서', icon: <Description /> },
    { id: 'integrated-documents', label: '문서관리', icon: <Description /> },
    { id: 'reports', label: '보고서', icon: <Assessment /> },
    { id: 'monitoring', label: '모니터링', icon: <Assessment /> },
    { id: 'qr-registration', label: 'QR 등록', icon: <QrCode /> },
    { id: 'common-qr', label: '공통 QR', icon: <QrCode /> },
    { id: 'confined-space', label: '밀폐공간', icon: <Warning /> },
    { id: 'settings', label: '설정', icon: <SettingsIcon /> }
  ];

  const drawerWidth = 240;

  return (
    <Box sx={{ display: 'flex' }}>
      <AppBar position="fixed" sx={{ zIndex: (theme) => theme.zIndex.drawer + 1 }}>
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            aria-label="menu"
            onClick={() => setSidebarOpen(!sidebarOpen)}
            sx={{ mr: 2 }}
          >
            <MenuIcon />
          </IconButton>
          <Typography variant="h6" noWrap component="div" sx={{ flexGrow: 1 }}>
            SafeWork Pro - 건설업 보건관리 시스템
          </Typography>
          <IconButton color="inherit" onClick={onLogout}>
            <Logout />
          </IconButton>
        </Toolbar>
      </AppBar>
      
      <Drawer
        variant="persistent"
        anchor="left"
        open={sidebarOpen}
        sx={{
          width: drawerWidth,
          flexShrink: 0,
          '& .MuiDrawer-paper': {
            width: drawerWidth,
            boxSizing: 'border-box',
          },
        }}
      >
        <Toolbar />
        <Box sx={{ overflow: 'auto' }}>
          <List>
            {menuItems.map((item) => (
              <ListItem key={item.id} disablePadding>
                <ListItemButton
                  selected={activeMenu === item.id}
                  onClick={() => setActiveMenu(item.id)}
                >
                  <ListItemIcon>{item.icon}</ListItemIcon>
                  <ListItemText primary={item.label} />
                </ListItemButton>
              </ListItem>
            ))}
          </List>
        </Box>
      </Drawer>
      
      <Box
        component="main"
        sx={{
          flexGrow: 1,
          p: 3,
          width: { sm: `calc(100% - ${drawerWidth}px)` },
          ml: sidebarOpen ? `${drawerWidth}px` : 0,
          transition: 'margin 0.3s',
        }}
      >
        <Toolbar />
        {children}
      </Box>
    </Box>
  );
}