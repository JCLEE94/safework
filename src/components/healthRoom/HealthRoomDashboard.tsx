import React, { useState, useEffect } from 'react';
import {
  Grid,
  Card,
  CardContent,
  Typography,
  CircularProgress,
  Box,
  List,
  ListItem,
  ListItemText,
  Chip,
  Paper,
  Divider
} from '@mui/material';
import {
  LocalHospital,
  Healing,
  Assessment,
  FitnessCenter,
  Warning,
  TrendingUp
} from '@mui/icons-material';
import { healthRoomApi } from '../../api/healthRoom';

interface HealthRoomStats {
  total_visits: number;
  total_medications: number;
  total_measurements: number;
  total_inbody_records: number;
  visits_by_reason: { [key: string]: number };
  common_medications: Array<{ name: string; count: number }>;
  abnormal_vital_signs: number;
  follow_up_required: number;
}

export default function HealthRoomDashboard() {
  const [stats, setStats] = useState<HealthRoomStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    fetchStats();
  }, []);

  const fetchStats = async () => {
    try {
      setLoading(true);
      const data = await healthRoomApi.getStats();
      setStats(data);
    } catch (err) {
      setError('통계 데이터를 불러오는데 실패했습니다.');
      console.error(err);
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

  if (error || !stats) {
    return (
      <Box textAlign="center" py={5}>
        <Typography color="error">{error || '데이터를 불러올 수 없습니다.'}</Typography>
      </Box>
    );
  }

  const statCards = [
    {
      title: '총 방문 건수',
      value: stats.total_visits,
      icon: <LocalHospital />,
      color: '#1976d2'
    },
    {
      title: '투약 건수',
      value: stats.total_medications,
      icon: <Healing />,
      color: '#388e3c'
    },
    {
      title: '측정 건수',
      value: stats.total_measurements,
      icon: <Assessment />,
      color: '#f57c00'
    },
    {
      title: '인바디 측정',
      value: stats.total_inbody_records,
      icon: <FitnessCenter />,
      color: '#7b1fa2'
    }
  ];

  return (
    <Grid container spacing={3}>
      {/* 통계 카드 */}
      {statCards.map((stat, index) => (
        <Grid item xs={12} sm={6} md={3} key={index}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" mb={2}>
                <Box
                  sx={{
                    backgroundColor: stat.color,
                    color: 'white',
                    p: 1,
                    borderRadius: 1,
                    mr: 2
                  }}
                >
                  {stat.icon}
                </Box>
                <Typography color="textSecondary" variant="subtitle2">
                  {stat.title}
                </Typography>
              </Box>
              <Typography variant="h4" component="div">
                {stat.value}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
      ))}

      {/* 경고 상태 */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <Warning color="warning" sx={{ verticalAlign: 'middle', mr: 1 }} />
            주의 필요 현황
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={2}>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h3" color="error">
                  {stats.abnormal_vital_signs}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  이상 측정값
                </Typography>
              </Box>
            </Grid>
            <Grid item xs={6}>
              <Box textAlign="center">
                <Typography variant="h3" color="warning.main">
                  {stats.follow_up_required}
                </Typography>
                <Typography variant="body2" color="textSecondary">
                  추적관찰 필요
                </Typography>
              </Box>
            </Grid>
          </Grid>
        </Paper>
      </Grid>

      {/* 방문 사유 통계 */}
      <Grid item xs={12} md={6}>
        <Paper sx={{ p: 3, height: '100%' }}>
          <Typography variant="h6" gutterBottom>
            <TrendingUp sx={{ verticalAlign: 'middle', mr: 1 }} />
            방문 사유별 통계
          </Typography>
          <Divider sx={{ my: 2 }} />
          <List dense>
            {Object.entries(stats.visits_by_reason)
              .sort(([, a], [, b]) => b - a)
              .slice(0, 5)
              .map(([reason, count]) => (
                <ListItem key={reason}>
                  <ListItemText primary={reason} />
                  <Chip label={count} size="small" color="primary" />
                </ListItem>
              ))}
          </List>
        </Paper>
      </Grid>

      {/* 자주 사용된 약품 */}
      <Grid item xs={12}>
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            <Healing sx={{ verticalAlign: 'middle', mr: 1 }} />
            자주 사용된 약품 TOP 10
          </Typography>
          <Divider sx={{ my: 2 }} />
          <Grid container spacing={2}>
            {stats.common_medications.map((med, index) => (
              <Grid item xs={12} sm={6} md={2.4} key={index}>
                <Box
                  sx={{
                    p: 2,
                    border: '1px solid #e0e0e0',
                    borderRadius: 1,
                    textAlign: 'center'
                  }}
                >
                  <Typography variant="body2" noWrap>
                    {med.name}
                  </Typography>
                  <Typography variant="h6" color="primary">
                    {med.count}회
                  </Typography>
                </Box>
              </Grid>
            ))}
          </Grid>
        </Paper>
      </Grid>
    </Grid>
  );
}