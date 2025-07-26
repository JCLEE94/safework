import React, { useState } from 'react';
import { 
  Box, 
  Paper, 
  Tabs, 
  Tab, 
  Typography,
  Container
} from '@mui/material';
import ExamPlanManagement from '../components/healthExamManagement/ExamPlanManagement';
import ExamScheduleManagement from '../components/healthExamManagement/ExamScheduleManagement';
import ExamReservationManagement from '../components/healthExamManagement/ExamReservationManagement';
import ExamChartManagement from '../components/healthExamManagement/ExamChartManagement';
import ExamResultManagement from '../components/healthExamManagement/ExamResultManagement';
import ExamDashboard from '../components/healthExamManagement/ExamDashboard';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`exam-tabpanel-${index}`}
      aria-labelledby={`exam-tab-${index}`}
      {...other}
    >
      {value === index && (
        <Box sx={{ py: 3 }}>
          {children}
        </Box>
      )}
    </div>
  );
}

export default function HealthExamManagement() {
  const [value, setValue] = useState(0);

  const handleChange = (event: React.SyntheticEvent, newValue: number) => {
    setValue(newValue);
  };

  return (
    <Container maxWidth="xl">
      <Box sx={{ mb: 3 }}>
        <Typography variant="h4" component="h1" gutterBottom>
          건강검진 통합관리
        </Typography>
        <Typography variant="body1" color="text.secondary">
          건강검진 계획 수립부터 결과 관리까지 체계적으로 관리합니다.
        </Typography>
      </Box>

      <Paper sx={{ width: '100%' }}>
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={value} 
            onChange={handleChange} 
            aria-label="건강검진 관리 탭"
            variant="scrollable"
            scrollButtons="auto"
          >
            <Tab label="대시보드" />
            <Tab label="검진계획 수립" />
            <Tab label="검진일정 관리" />
            <Tab label="예약관리" />
            <Tab label="문진표 관리" />
            <Tab label="결과관리" />
          </Tabs>
        </Box>

        <TabPanel value={value} index={0}>
          <ExamDashboard />
        </TabPanel>
        <TabPanel value={value} index={1}>
          <ExamPlanManagement />
        </TabPanel>
        <TabPanel value={value} index={2}>
          <ExamScheduleManagement />
        </TabPanel>
        <TabPanel value={value} index={3}>
          <ExamReservationManagement />
        </TabPanel>
        <TabPanel value={value} index={4}>
          <ExamChartManagement />
        </TabPanel>
        <TabPanel value={value} index={5}>
          <ExamResultManagement />
        </TabPanel>
      </Paper>
    </Container>
  );
}