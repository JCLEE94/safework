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
  IconButton,
  Autocomplete,
  Card,
  CardContent,
  Divider,
  LinearProgress
} from '@mui/material';
import { Add, Visibility, Assessment } from '@mui/icons-material';
import { healthRoomApi, InBodyRecord } from '../../api/healthRoom';
import { workersApi } from '../../api/workers';
import { format } from 'date-fns';

export default function InBodyManagement() {
  const [inbodyRecords, setInbodyRecords] = useState<InBodyRecord[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openDetailDialog, setOpenDetailDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState<InBodyRecord | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState<Partial<InBodyRecord>>({
    worker_id: 0,
    height: 0,
    weight: 0,
    bmi: 0,
    body_fat_mass: undefined,
    body_fat_percentage: undefined,
    muscle_mass: undefined,
    lean_body_mass: undefined,
    total_body_water: undefined,
    visceral_fat_level: undefined,
    basal_metabolic_rate: undefined,
    body_age: undefined,
    device_model: '',
    evaluation: '',
    recommendations: ''
  });

  useEffect(() => {
    fetchInBodyRecords();
    fetchWorkers();
  }, []);

  const fetchInBodyRecords = async () => {
    try {
      setLoading(true);
      const data = await healthRoomApi.inbody.getList({ limit: 100 });
      setInbodyRecords(data);
    } catch (error) {
      console.error('인바디 측정 기록 조회 실패:', error);
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

  const calculateBMI = (height: number, weight: number) => {
    if (height && weight) {
      return Number((weight / ((height / 100) ** 2)).toFixed(1));
    }
    return 0;
  };

  const handleHeightWeightChange = (field: 'height' | 'weight', value: number) => {
    const newData = { ...formData, [field]: value };
    
    if (newData.height && newData.weight) {
      newData.bmi = calculateBMI(newData.height, newData.weight);
    }
    
    setFormData(newData);
  };

  const handleSubmit = async () => {
    try {
      if (!formData.worker_id || !formData.height || !formData.weight) {
        alert('필수 항목을 입력해주세요.');
        return;
      }

      await healthRoomApi.inbody.create(formData as InBodyRecord);
      setOpenDialog(false);
      resetForm();
      fetchInBodyRecords();
      alert('인바디 측정 기록이 저장되었습니다.');
    } catch (error) {
      console.error('인바디 측정 기록 저장 실패:', error);
      alert('측정 기록 저장에 실패했습니다.');
    }
  };

  const resetForm = () => {
    setFormData({
      worker_id: 0,
      height: 0,
      weight: 0,
      bmi: 0,
      body_fat_mass: undefined,
      body_fat_percentage: undefined,
      muscle_mass: undefined,
      lean_body_mass: undefined,
      total_body_water: undefined,
      visceral_fat_level: undefined,
      basal_metabolic_rate: undefined,
      body_age: undefined,
      device_model: '',
      evaluation: '',
      recommendations: ''
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

  const handleOpenDetail = (record: InBodyRecord) => {
    setSelectedRecord(record);
    setOpenDetailDialog(true);
  };

  const getBMIStatus = (bmi: number) => {
    if (bmi < 18.5) return { text: '저체중', color: '#2196f3' };
    if (bmi < 23) return { text: '정상', color: '#4caf50' };
    if (bmi < 25) return { text: '과체중', color: '#ff9800' };
    if (bmi < 30) return { text: '비만', color: '#f44336' };
    return { text: '고도비만', color: '#d32f2f' };
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">인바디 측정 관리</Typography>
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
              <TableCell>신장(cm)</TableCell>
              <TableCell>체중(kg)</TableCell>
              <TableCell>BMI</TableCell>
              <TableCell>체지방률</TableCell>
              <TableCell>근육량</TableCell>
              <TableCell>내장지방</TableCell>
              <TableCell>체성분나이</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {inbodyRecords.map((record) => (
              <TableRow key={record.id}>
                <TableCell>
                  {record.measured_at && format(new Date(record.measured_at), 'yyyy-MM-dd HH:mm')}
                </TableCell>
                <TableCell>{record.worker_id}</TableCell>
                <TableCell>{record.height}</TableCell>
                <TableCell>{record.weight}</TableCell>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <span>{record.bmi.toFixed(1)}</span>
                    <Typography 
                      variant="caption" 
                      sx={{ 
                        color: getBMIStatus(record.bmi).color,
                        fontWeight: 'bold'
                      }}
                    >
                      ({getBMIStatus(record.bmi).text})
                    </Typography>
                  </Box>
                </TableCell>
                <TableCell>
                  {record.body_fat_percentage ? `${record.body_fat_percentage}%` : '-'}
                </TableCell>
                <TableCell>
                  {record.muscle_mass ? `${record.muscle_mass}kg` : '-'}
                </TableCell>
                <TableCell>
                  {record.visceral_fat_level || '-'}
                </TableCell>
                <TableCell>
                  {record.body_age || '-'}
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small" onClick={() => handleOpenDetail(record)}>
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 측정 기록 추가 다이얼로그 */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="lg" fullWidth>
        <DialogTitle>인바디 측정 기록 추가</DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
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

            {/* 기본 측정값 */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>기본 측정값</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="신장 (cm) *"
                        type="number"
                        value={formData.height || ''}
                        onChange={(e) => handleHeightWeightChange('height', parseFloat(e.target.value) || 0)}
                        fullWidth
                        inputProps={{ min: 100, max: 250, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="체중 (kg) *"
                        type="number"
                        value={formData.weight || ''}
                        onChange={(e) => handleHeightWeightChange('weight', parseFloat(e.target.value) || 0)}
                        fullWidth
                        inputProps={{ min: 20, max: 300, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="BMI"
                        value={formData.bmi || ''}
                        fullWidth
                        disabled
                        InputProps={{
                          endAdornment: formData.bmi ? (
                            <Typography variant="caption" color={getBMIStatus(formData.bmi).color}>
                              {getBMIStatus(formData.bmi).text}
                            </Typography>
                          ) : null
                        }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="측정 장비"
                        value={formData.device_model}
                        onChange={(e) => setFormData({ ...formData, device_model: e.target.value })}
                        fullWidth
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 체성분 분석 */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>체성분 분석</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="체지방량 (kg)"
                        type="number"
                        value={formData.body_fat_mass || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          body_fat_mass: e.target.value ? parseFloat(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 0, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="체지방률 (%)"
                        type="number"
                        value={formData.body_fat_percentage || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          body_fat_percentage: e.target.value ? parseFloat(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 0, max: 60, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="근육량 (kg)"
                        type="number"
                        value={formData.muscle_mass || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          muscle_mass: e.target.value ? parseFloat(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 0, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="제지방량 (kg)"
                        type="number"
                        value={formData.lean_body_mass || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          lean_body_mass: e.target.value ? parseFloat(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 0, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="체수분 (L)"
                        type="number"
                        value={formData.total_body_water || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          total_body_water: e.target.value ? parseFloat(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 0, step: 0.1 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="내장지방 레벨"
                        type="number"
                        value={formData.visceral_fat_level || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          visceral_fat_level: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 1, max: 20 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="기초대사량 (kcal)"
                        type="number"
                        value={formData.basal_metabolic_rate || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          basal_metabolic_rate: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 500 }}
                      />
                    </Grid>
                    <Grid item xs={12} md={3}>
                      <TextField
                        label="체성분 나이"
                        type="number"
                        value={formData.body_age || ''}
                        onChange={(e) => setFormData({ 
                          ...formData, 
                          body_age: e.target.value ? parseInt(e.target.value) : undefined 
                        })}
                        fullWidth
                        inputProps={{ min: 10, max: 100 }}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            {/* 평가 및 권고사항 */}
            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle1" gutterBottom>평가 및 권고사항</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12}>
                      <TextField
                        label="종합 평가"
                        value={formData.evaluation}
                        onChange={(e) => setFormData({ ...formData, evaluation: e.target.value })}
                        fullWidth
                        multiline
                        rows={3}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <TextField
                        label="권고사항"
                        value={formData.recommendations}
                        onChange={(e) => setFormData({ ...formData, recommendations: e.target.value })}
                        fullWidth
                        multiline
                        rows={3}
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
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

      {/* 상세 보기 다이얼로그 */}
      <Dialog 
        open={openDetailDialog} 
        onClose={() => setOpenDetailDialog(false)} 
        maxWidth="md" 
        fullWidth
      >
        <DialogTitle>인바디 측정 상세 정보</DialogTitle>
        <DialogContent>
          {selectedRecord && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="h6" gutterBottom>
                측정일: {format(new Date(selectedRecord.measured_at!), 'yyyy년 MM월 dd일 HH:mm')}
              </Typography>
              
              <Divider sx={{ my: 2 }} />
              
              <Grid container spacing={2}>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">신장</Typography>
                  <Typography variant="body1">{selectedRecord.height} cm</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">체중</Typography>
                  <Typography variant="body1">{selectedRecord.weight} kg</Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">BMI</Typography>
                  <Typography variant="body1">
                    {selectedRecord.bmi.toFixed(1)} ({getBMIStatus(selectedRecord.bmi).text})
                  </Typography>
                </Grid>
                <Grid item xs={6}>
                  <Typography variant="body2" color="textSecondary">체지방률</Typography>
                  <Typography variant="body1">
                    {selectedRecord.body_fat_percentage ? `${selectedRecord.body_fat_percentage}%` : '-'}
                  </Typography>
                </Grid>
              </Grid>

              {selectedRecord.evaluation && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>종합 평가</Typography>
                  <Typography variant="body2">{selectedRecord.evaluation}</Typography>
                </Box>
              )}

              {selectedRecord.recommendations && (
                <Box sx={{ mt: 3 }}>
                  <Typography variant="subtitle1" gutterBottom>권고사항</Typography>
                  <Typography variant="body2">{selectedRecord.recommendations}</Typography>
                </Box>
              )}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setOpenDetailDialog(false)}>닫기</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}