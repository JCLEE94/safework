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
  FormControlLabel,
  Checkbox,
  Card,
  CardContent
} from '@mui/material';
import { Add, Visibility, LocalHospital, MedicalServices } from '@mui/icons-material';
import { healthRoomApi, HealthRoomVisit } from '../../api/healthRoom';
import { workersApi } from '../../api/workers';
import { format } from 'date-fns';

const commonVisitReasons = [
  '두통',
  '복통',
  '근육통',
  '관절통',
  '감기 증상',
  '소화불량',
  '현기증',
  '피로',
  '외상',
  '화상',
  '알레르기',
  '기타'
];

export default function VisitRecords() {
  const [visits, setVisits] = useState<HealthRoomVisit[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [openDetailDialog, setOpenDetailDialog] = useState(false);
  const [selectedVisit, setSelectedVisit] = useState<HealthRoomVisit | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState<Partial<HealthRoomVisit>>({
    worker_id: 0,
    visit_reason: '',
    chief_complaint: '',
    treatment_provided: '',
    medication_given: false,
    measurement_taken: false,
    follow_up_required: false,
    referral_required: false,
    referral_location: '',
    notes: ''
  });

  useEffect(() => {
    fetchVisits();
    fetchWorkers();
  }, []);

  const fetchVisits = async () => {
    try {
      setLoading(true);
      const data = await healthRoomApi.visits.getList({ limit: 100 });
      setVisits(data);
    } catch (error) {
      console.error('방문 기록 조회 실패:', error);
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
      if (!formData.worker_id || !formData.visit_reason) {
        alert('필수 항목을 입력해주세요.');
        return;
      }

      await healthRoomApi.visits.create(formData as HealthRoomVisit);
      setOpenDialog(false);
      resetForm();
      fetchVisits();
      alert('건강관리실 방문 기록이 저장되었습니다.');
    } catch (error) {
      console.error('방문 기록 저장 실패:', error);
      alert('방문 기록 저장에 실패했습니다.');
    }
  };

  const resetForm = () => {
    setFormData({
      worker_id: 0,
      visit_reason: '',
      chief_complaint: '',
      treatment_provided: '',
      medication_given: false,
      measurement_taken: false,
      follow_up_required: false,
      referral_required: false,
      referral_location: '',
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

  const handleOpenDetail = (visit: HealthRoomVisit) => {
    setSelectedVisit(visit);
    setOpenDetailDialog(true);
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">건강관리실 방문 기록</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Add />}
          onClick={handleOpenDialog}
        >
          방문 기록 추가
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>방문일시</TableCell>
              <TableCell>근로자</TableCell>
              <TableCell>방문 사유</TableCell>
              <TableCell>주요 증상</TableCell>
              <TableCell>처치 내용</TableCell>
              <TableCell>투약</TableCell>
              <TableCell>측정</TableCell>
              <TableCell>후속조치</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {visits.map((visit) => (
              <TableRow key={visit.id}>
                <TableCell>
                  {visit.visit_date && format(new Date(visit.visit_date), 'yyyy-MM-dd HH:mm')}
                </TableCell>
                <TableCell>{visit.worker_id}</TableCell>
                <TableCell>{visit.visit_reason}</TableCell>
                <TableCell>{visit.chief_complaint || '-'}</TableCell>
                <TableCell>
                  {visit.treatment_provided ? 
                    (visit.treatment_provided.length > 30 ? 
                      visit.treatment_provided.substring(0, 30) + '...' : 
                      visit.treatment_provided) : '-'
                  }
                </TableCell>
                <TableCell>
                  {visit.medication_given && <Chip label="O" size="small" color="primary" />}
                </TableCell>
                <TableCell>
                  {visit.measurement_taken && <Chip label="O" size="small" color="secondary" />}
                </TableCell>
                <TableCell>
                  {visit.follow_up_required && (
                    <Chip label="추적관찰" size="small" color="warning" />
                  )}
                  {visit.referral_required && (
                    <Chip label="의뢰" size="small" color="error" />
                  )}
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small" onClick={() => handleOpenDetail(visit)}>
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 방문 기록 추가 다이얼로그 */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>건강관리실 방문 기록 추가</DialogTitle>
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

            <Grid item xs={12} md={6}>
              <Autocomplete
                freeSolo
                options={commonVisitReasons}
                value={formData.visit_reason}
                onInputChange={(event, newValue) => {
                  setFormData({ ...formData, visit_reason: newValue });
                }}
                renderInput={(params) => (
                  <TextField {...params} label="방문 사유 *" fullWidth />
                )}
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                label="주요 증상"
                value={formData.chief_complaint}
                onChange={(e) => setFormData({ ...formData, chief_complaint: e.target.value })}
                fullWidth
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                label="제공된 처치"
                value={formData.treatment_provided}
                onChange={(e) => setFormData({ ...formData, treatment_provided: e.target.value })}
                fullWidth
                multiline
                rows={3}
                placeholder="예: 상처 소독 및 드레싱, 냉찜질, 안정 지도 등"
              />
            </Grid>

            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>처치 내용</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.medication_given}
                            onChange={(e) => setFormData({ ...formData, medication_given: e.target.checked })}
                          />
                        }
                        label="투약 실시"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.measurement_taken}
                            onChange={(e) => setFormData({ ...formData, measurement_taken: e.target.checked })}
                          />
                        }
                        label="측정 실시"
                      />
                    </Grid>
                  </Grid>
                </CardContent>
              </Card>
            </Grid>

            <Grid item xs={12}>
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>후속 조치</Typography>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.follow_up_required}
                            onChange={(e) => setFormData({ ...formData, follow_up_required: e.target.checked })}
                          />
                        }
                        label="추적 관찰 필요"
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.referral_required}
                            onChange={(e) => setFormData({ ...formData, referral_required: e.target.checked })}
                          />
                        }
                        label="의료기관 의뢰 필요"
                      />
                    </Grid>
                    {formData.referral_required && (
                      <Grid item xs={12}>
                        <TextField
                          label="의뢰 기관"
                          value={formData.referral_location}
                          onChange={(e) => setFormData({ ...formData, referral_location: e.target.value })}
                          fullWidth
                          placeholder="예: ○○병원 정형외과"
                        />
                      </Grid>
                    )}
                  </Grid>
                </CardContent>
              </Card>
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

      {/* 상세 보기 다이얼로그 */}
      <Dialog 
        open={openDetailDialog} 
        onClose={() => setOpenDetailDialog(false)} 
        maxWidth="sm" 
        fullWidth
      >
        <DialogTitle>
          <Box display="flex" alignItems="center" gap={1}>
            <LocalHospital color="primary" />
            방문 기록 상세
          </Box>
        </DialogTitle>
        <DialogContent>
          {selectedVisit && (
            <Box sx={{ mt: 2 }}>
              <Grid container spacing={2}>
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">방문일시</Typography>
                  <Typography variant="body1">
                    {format(new Date(selectedVisit.visit_date!), 'yyyy년 MM월 dd일 HH:mm')}
                  </Typography>
                </Grid>
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">방문 사유</Typography>
                  <Typography variant="body1">{selectedVisit.visit_reason}</Typography>
                </Grid>
                
                {selectedVisit.chief_complaint && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">주요 증상</Typography>
                    <Typography variant="body1">{selectedVisit.chief_complaint}</Typography>
                  </Grid>
                )}
                
                {selectedVisit.treatment_provided && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">제공된 처치</Typography>
                    <Typography variant="body1">{selectedVisit.treatment_provided}</Typography>
                  </Grid>
                )}
                
                <Grid item xs={12}>
                  <Typography variant="body2" color="textSecondary">처치 내용</Typography>
                  <Box display="flex" gap={1} mt={1}>
                    {selectedVisit.medication_given && (
                      <Chip label="투약 실시" size="small" color="primary" />
                    )}
                    {selectedVisit.measurement_taken && (
                      <Chip label="측정 실시" size="small" color="secondary" />
                    )}
                  </Box>
                </Grid>
                
                {(selectedVisit.follow_up_required || selectedVisit.referral_required) && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">후속 조치</Typography>
                    <Box display="flex" gap={1} mt={1}>
                      {selectedVisit.follow_up_required && (
                        <Chip label="추적 관찰 필요" size="small" color="warning" />
                      )}
                      {selectedVisit.referral_required && (
                        <Chip 
                          label={`의뢰: ${selectedVisit.referral_location || '의료기관'}`} 
                          size="small" 
                          color="error" 
                        />
                      )}
                    </Box>
                  </Grid>
                )}
                
                {selectedVisit.notes && (
                  <Grid item xs={12}>
                    <Typography variant="body2" color="textSecondary">비고</Typography>
                    <Typography variant="body1">{selectedVisit.notes}</Typography>
                  </Grid>
                )}
              </Grid>
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