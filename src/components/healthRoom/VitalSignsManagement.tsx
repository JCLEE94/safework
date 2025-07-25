import React, { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  Typography,
  Chip,
  IconButton,
  Autocomplete,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Card,
  CardContent
} from '@mui/material';
import { Add, FavoriteBorder, Thermostat, Speed, WaterDrop } from '@mui/icons-material';
import { healthRoomApi, VitalSignRecord } from '../../api/healthRoom';
import { workersApi } from '../../api/workers';
import { format } from 'date-fns';

export default function VitalSignsManagement() {
  const [vitalSigns, setVitalSigns] = useState<VitalSignRecord[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState<Partial<VitalSignRecord>>({
    worker_id: 0,
    systolic_bp: undefined,
    diastolic_bp: undefined,
    blood_sugar: undefined,
    blood_sugar_type: undefined,
    heart_rate: undefined,
    body_temperature: undefined,
    oxygen_saturation: undefined,
    measured_by: '',
    notes: ''
  });

  useEffect(() => {
    fetchVitalSigns();
    fetchWorkers();
  }, []);

  const fetchVitalSigns = async () => {
    try {
      setLoading(true);
      const data = await healthRoomApi.vitalSigns.getList({ limit: 100 });
      setVitalSigns(data);
    } catch (error) {
      console.error('생체 신호 측정 기록 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkers = async () => {
    try {
      const data = await workersApi.getAll();
      setWorkers(data);
    } catch (error) {
      console.error('근로자 목록 조회 실패:', error);
    }
  };

  const handleSubmit = async () => {
    try {
      if (!formData.worker_id) {
        alert('근로자를 선택해주세요.');
        return;
      }

      // 최소 하나의 측정값이 있는지 확인
      const hasAnyMeasurement = formData.systolic_bp || formData.diastolic_bp || 
        formData.blood_sugar || formData.heart_rate || 
        formData.body_temperature || formData.oxygen_saturation;

      if (!hasAnyMeasurement) {
        alert('최소 하나 이상의 측정값을 입력해주세요.');
        return;
      }

      await healthRoomApi.vitalSigns.create(formData as VitalSignRecord);
      setOpenDialog(false);
      resetForm();
      fetchVitalSigns();
      alert('생체 신호 측정 기록이 저장되었습니다.');
    } catch (error) {
      console.error('생체 신호 측정 기록 저장 실패:', error);
      alert('측정 기록 저장에 실패했습니다.');
    }
  };

  const resetForm = () => {
    setFormData({
      worker_id: 0,
      systolic_bp: undefined,
      diastolic_bp: undefined,
      blood_sugar: undefined,
      blood_sugar_type: undefined,
      heart_rate: undefined,
      body_temperature: undefined,
      oxygen_saturation: undefined,
      measured_by: '',
      notes: ''
    });
    setSelectedWorker(null);
  };

  const handleOpenDialog = () => {
    setOpenDialog(true);
  };

  const handleCloseDialog = () => {
    setOpenDialog(false);
    resetForm();
  };

  const getStatusColor = (status?: string) => {
    switch (status) {
      case '정상':
        return 'success';
      case '주의':
        return 'warning';
      case '위험':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">생체 신호 측정 관리</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Add />}
          onClick={handleOpenDialog}
        >
          측정 기록 추가
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>측정일시</TableCell>
              <TableCell>근로자</TableCell>
              <TableCell>혈압</TableCell>
              <TableCell>혈당</TableCell>
              <TableCell>심박수</TableCell>
              <TableCell>체온</TableCell>
              <TableCell>산소포화도</TableCell>
              <TableCell>상태</TableCell>
              <TableCell>측정자</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {vitalSigns.map((record) => (
              <TableRow key={record.id}>
                <TableCell>
                  {record.measured_at && format(new Date(record.measured_at), 'yyyy-MM-dd HH:mm')}
                </TableCell>
                <TableCell>{record.worker_id}</TableCell>
                <TableCell>
                  {record.systolic_bp && record.diastolic_bp
                    ? `${record.systolic_bp}/${record.diastolic_bp}`
                    : '-'}
                </TableCell>
                <TableCell>
                  {record.blood_sugar
                    ? `${record.blood_sugar} ${record.blood_sugar_type || ''}`
                    : '-'}
                </TableCell>
                <TableCell>{record.heart_rate || '-'}</TableCell>
                <TableCell>{record.body_temperature ? `${record.body_temperature}°C` : '-'}</TableCell>
                <TableCell>{record.oxygen_saturation ? `${record.oxygen_saturation}%` : '-'}</TableCell>
                <TableCell>
                  {record.status && (
                    <Chip 
                      label={record.status} 
                      color={getStatusColor(record.status) as any}
                      size="small" 
                    />
                  )}
                </TableCell>
                <TableCell>{record.measured_by || '-'}</TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 측정 기록 추가 다이얼로그 */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>생체 신호 측정 기록 추가</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Autocomplete
                options={workers}
                getOptionLabel={(option) => `${option.name} (${option.employee_id})`}
                value={selectedWorker}
                onChange={(event, newValue) => {
                  setSelectedWorker(newValue);
                  setFormData({ ...formData, worker_id: newValue?.id || 0 });
                }}
                renderInput={(params) => (
                  <TextField {...params} label="근로자 *" fullWidth />
                )}
              />
            </Grid>

            {/* 혈압 측정 */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    <FavoriteBorder sx={{ verticalAlign: 'middle', mr: 1 }} />
                    혈압
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="수축기 혈압 (mmHg)"
                        type="number"
                        value={formData.systolic_bp || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          systolic_bp: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 50, max: 300 }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <TextField
                        label="이완기 혈압 (mmHg)"
                        type="number"
                        value={formData.diastolic_bp || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          diastolic_bp: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 30, max: 200 }}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 혈당 측정 */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>
                    <WaterDrop sx={{ verticalAlign: 'middle', mr: 1 }} />
                    혈당
                  </Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={6}>
                      <TextField
                        label="혈당 (mg/dL)"
                        type="number"
                        value={formData.blood_sugar || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          blood_sugar: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 20, max: 600 }}
                      />
                    </Grid>
                    <Grid item xs={6}>
                      <FormControl fullWidth>
                        <InputLabel>측정 시점</InputLabel>
                        <Select
                          value={formData.blood_sugar_type || ''}
                          onChange={(e) => setFormData({ 
                            ...formData, 
                            blood_sugar_type: e.target.value as '공복' | '식후' 
                          })}
                        >
                          <MenuItem value="">선택</MenuItem>
                          <MenuItem value="공복">공복</MenuItem>
                          <MenuItem value="식후">식후</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 기타 측정값 */}
            <Grid item xs={12} md={4}>
              <TextField
                label="심박수 (회/분)"
                type="number"
                value={formData.heart_rate || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  heart_rate: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                fullWidth
                InputProps={{
                  startAdornment: <Speed sx={{ mr: 1, color: 'action.active' }} />
                }}
                inputProps={{ min: 30, max: 300 }}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <TextField
                label="체온 (°C)"
                type="number"
                value={formData.body_temperature || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  body_temperature: e.target.value ? parseFloat(e.target.value) : undefined 
                })}
                fullWidth
                InputProps={{
                  startAdornment: <Thermostat sx={{ mr: 1, color: 'action.active' }} />
                }}
                inputProps={{ min: 30, max: 45, step: 0.1 }}
              />
            </Grid>
            
            <Grid item xs={12} md={4}>
              <TextField
                label="산소포화도 (%)"
                type="number"
                value={formData.oxygen_saturation || ''}
                onChange={(e) => setFormData({ 
                  ...formData, 
                  oxygen_saturation: e.target.value ? parseInt(e.target.value) : undefined 
                })}
                fullWidth
                inputProps={{ min: 50, max: 100 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="측정자"
                value={formData.measured_by}
                onChange={(e) => setFormData({ ...formData, measured_by: e.target.value })}
                fullWidth
              />
            </Grid>
            
            <Grid item xs={12}>
              <TextField
                label="비고"
                value={formData.notes}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={handleCloseDialog}>취소</Button>
          <Button onClick={handleSubmit} variant="contained" color="primary">
            저장
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}