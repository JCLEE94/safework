import React, { useState, useEffect } from 'react';
import { Tabs, Tab, Box, Typography, Container } from '@mui/material';
import MedicationManagement from '../components/healthRoom/MedicationManagement';
import VitalSignsManagement from '../components/healthRoom/VitalSignsManagement';
import InBodyManagement from '../components/healthRoom/InBodyManagement';
import VisitRecords from '../components/healthRoom/VisitRecords';
import HealthRoomDashboard from '../components/healthRoom/HealthRoomDashboard';

function TabPanel(props: any) {
  const { children, value, index, ...other } = props;
  return (
    <div role="tabpanel" hidden={value !== index} {...other}>
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

export default function HealthRoom() {
  const [activeTab, setActiveTab] = useState(0);

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setActiveTab(newValue);
  };

  return (
    <Container maxWidth="xl">
      <Typography variant="h4" component="h1" gutterBottom sx={{ mt: 2 }}>
        건강관리실
      </Typography>
      
      <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
        <Tabs value={activeTab} onChange={handleTabChange} aria-label="건강관리실 탭">
          <Tab label="대시보드" />
          <Tab label="투약 관리" />
          <Tab label="생체 신호 측정" />
          <Tab label="인바디 측정" />
          <Tab label="방문 기록" />
        </Tabs>
      </Box>

      <TabPanel value={activeTab} index={0}>
        <HealthRoomDashboard />
      </TabPanel>
      
      <TabPanel value={activeTab} index={1}>
        <MedicationManagement />
      </TabPanel>
      
      <TabPanel value={activeTab} index={2}>
        <VitalSignsManagement />
      </TabPanel>
      
      <TabPanel value={activeTab} index={3}>
        <InBodyManagement />
      </TabPanel>
      
      <TabPanel value={activeTab} index={4}>
        <VisitRecords />
      </TabPanel>
    </Container>
  );
}