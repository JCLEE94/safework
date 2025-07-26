import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  Box,
  LinearProgress,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Chip,
  Alert,
  CircularProgress,
  Button,
  Divider
} from '@mui/material';
import {
  People as PeopleIcon,
  CheckCircle as CheckCircleIcon,
  Schedule as ScheduleIcon,
  Warning as WarningIcon,
  Assessment as AssessmentIcon,
  CalendarToday as CalendarIcon,
  Assignment as AssignmentIcon,
  LocalHospital as LocalHospitalIcon
} from '@mui/icons-material';
import { healthExamManagementApi } from '../../api/healthExamManagement';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';

interface StatCard {
  title: string;
  value: number | string;
  subtitle?: string;
  icon: React.ReactNode;
  color: string;
  progress?: number;
}

export default function ExamDashboard() {
  const [loading, setLoading] = useState(true);
  const [dashboardData, setDashboardData] = useState<any>(null);
  const [yearStats, setYearStats] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchDashboardData();
  }, []);

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      const [dashboard, stats] = await Promise.all([
        healthExamManagementApi.stats.getOverallStats(),
        healthExamManagementApi.stats.getOverallStats(new Date().getFullYear())
      ]);
      setDashboardData(dashboard);
      setYearStats(stats);
    } catch (err) {
      console.error('대시보드 데이터 로드 실패:', err);
      setError('대시보드 데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight={400}>
        <CircularProgress />
      </Box>
    );
  }

  if (error) {
    return <Alert severity="error">{error}</Alert>;
  }

  const statCards: StatCard[] = [
    {
      title: '전체 대상자',
      value: dashboardData?.total_targets || 0,
      subtitle: `${new Date().getFullYear()}년 검진 대상`,
      icon: <PeopleIcon />,
      color: '#1976d2'
    },
    {
      title: '검진 완료',
      value: dashboardData?.completed_count || 0,
      subtitle: `완료율 ${dashboardData?.completion_rate?.toFixed(1) || 0}%`,
      icon: <CheckCircleIcon />,
      color: '#4caf50',
      progress: dashboardData?.completion_rate || 0
    },
    {
      title: '검진 예정',
      value: dashboardData?.pending_count || 0,
      subtitle: '미검진자',
      icon: <ScheduleIcon />,
      color: '#ff9800'
    },
    {
      title: '유소견자',
      value: dashboardData?.abnormal_count || 0,
      subtitle: `유소견율 ${dashboardData?.abnormal_rate?.toFixed(1) || 0}%`,
      icon: <WarningIcon />,
      color: '#f44336'
    }
  ];

  const getResultChipColor = (result: string) => {
    switch (result) {
      case 'A': return 'success';
      case 'B': return 'info';
      case 'C': return 'warning';
      case 'D': case 'R': return 'error';
      default: return 'default';
    }
  };

  return (
    <Box>
      {/* 통계 카드 */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        {statCards.map((stat, index) => (
          <Grid item xs={12} sm={6} md={3} key={index}>
            <Card sx={{ height: '100%' }}>
              <CardContent>
                <Box display="flex" alignItems="center" mb={2}>
                  <Box
                    sx={{
                      backgroundColor: `${stat.color}20`,
                      borderRadius: 2,
                      p: 1,
                      mr: 2
                    }}
                  >
                    <Box sx={{ color: stat.color }}>{stat.icon}</Box>
                  </Box>
                  <Typography color="text.secondary" variant="body2">
                    {stat.title}
                  </Typography>
                </Box>
                <Typography variant="h4" gutterBottom>
                  {stat.value}
                </Typography>
                {stat.subtitle && (
                  <Typography variant="body2" color="text.secondary">
                    {stat.subtitle}
                  </Typography>
                )}
                {stat.progress !== undefined && (
                  <Box mt={2}>
                    <LinearProgress
                      variant="determinate"
                      value={stat.progress}
                      sx={{
                        height: 8,
                        borderRadius: 4,
                        backgroundColor: `${stat.color}20`,
                        '& .MuiLinearProgress-bar': {
                          backgroundColor: stat.color
                        }
                      }}
                    />
                  </Box>
                )}
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Grid container spacing={3}>
        {/* 월별 검진 일정 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">월별 검진 일정</Typography>
                <CalendarIcon color="action" />
              </Box>
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Box
                    sx={{
                      p: 2,
                      backgroundColor: 'primary.light',
                      borderRadius: 2,
                      textAlign: 'center'
                    }}
                  >
                    <Typography variant="h4" color="primary.contrastText">
                      {dashboardData?.this_month_scheduled || 0}
                    </Typography>
                    <Typography variant="body2" color="primary.contrastText">
                      이번달 예정
                    </Typography>
                  </Box>
                </Grid>
                <Grid item xs={6}>
                  <Box
                    sx={{
                      p: 2,
                      backgroundColor: 'grey.200',
                      borderRadius: 2,
                      textAlign: 'center'
                    }}
                  >
                    <Typography variant="h4">
                      {dashboardData?.next_month_scheduled || 0}
                    </Typography>
                    <Typography variant="body2" color="text.secondary">
                      다음달 예정
                    </Typography>
                  </Box>
                </Grid>
              </Grid>
            </CardContent>
          </Card>
        </Grid>

        {/* 검진 결과 분포 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">검진 결과 분포</Typography>
                <AssessmentIcon color="action" />
              </Box>
              <Box display="flex" justifyContent="space-around">
                {['A', 'B', 'C', 'D', 'R'].map((grade) => (
                  <Box key={grade} textAlign="center">
                    <Chip
                      label={grade}
                      color={getResultChipColor(grade)}
                      sx={{ mb: 1, fontWeight: 'bold' }}
                    />
                    <Typography variant="h6">
                      {yearStats?.[`result_${grade.toLowerCase()}_count`] || 0}
                    </Typography>
                    <Typography variant="caption" color="text.secondary">
                      {grade}급
                    </Typography>
                  </Box>
                ))}
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* 미검진자 목록 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">미검진자 현황</Typography>
                <Button size="small" variant="text">
                  전체보기
                </Button>
              </Box>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>사번</TableCell>
                      <TableCell>이름</TableCell>
                      <TableCell>검진 예정일</TableCell>
                      <TableCell>경과일</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {dashboardData?.overdue_workers?.slice(0, 5).map((worker: any, index: number) => (
                      <TableRow key={index}>
                        <TableCell>{worker.employee_id}</TableCell>
                        <TableCell>{worker.name}</TableCell>
                        <TableCell>{worker.due_date}</TableCell>
                        <TableCell>
                          <Chip
                            size="small"
                            label={`${worker.overdue_days}일 경과`}
                            color={worker.overdue_days > 30 ? 'error' : 'warning'}
                          />
                        </TableCell>
                      </TableRow>
                    )) || (
                      <TableRow>
                        <TableCell colSpan={4} align="center">
                          미검진자가 없습니다
                        </TableCell>
                      </TableRow>
                    )}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* 최근 알림 */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
                <Typography variant="h6">최근 알림</Typography>
                <AssignmentIcon color="action" />
              </Box>
              <Box>
                {dashboardData?.recent_alerts?.map((alert: any, index: number) => (
                  <Box key={index}>
                    <Box display="flex" alignItems="center" py={1}>
                      <LocalHospitalIcon
                        fontSize="small"
                        sx={{ mr: 1, color: alert.type === 'urgent' ? 'error.main' : 'action.active' }}
                      />
                      <Box flex={1}>
                        <Typography variant="body2">{alert.message}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {format(new Date(alert.created_at), 'MM월 dd일 HH:mm', { locale: ko })}
                        </Typography>
                      </Box>
                    </Box>
                    {index < (dashboardData?.recent_alerts?.length - 1) && <Divider />}
                  </Box>
                )) || (
                  <Typography variant="body2" color="text.secondary" align="center">
                    최근 알림이 없습니다
                  </Typography>
                )}
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
}