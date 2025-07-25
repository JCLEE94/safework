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
  FormControlLabel,
  Checkbox,
  Typography,
  Chip,
  IconButton,
  Autocomplete
} from '@mui/material';
import { Add, Edit, Visibility } from '@mui/icons-material';
import { healthRoomApi, MedicationRecord } from '../../api/healthRoom';
import { workersApi } from '../../api/workers';
import { format } from 'date-fns';

export default function MedicationManagement() {
  const [medications, setMedications] = useState<MedicationRecord[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [openDialog, setOpenDialog] = useState(false);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState<Partial<MedicationRecord>>({
    worker_id: 0,
    medication_name: '',
    dosage: '',
    quantity: 1,
    purpose: '',
    symptoms: '',
    administered_by: '',
    notes: '',
    follow_up_required: false
  });

  useEffect(() => {
    fetchMedications();
    fetchWorkers();
  }, []);

  const fetchMedications = async () => {
    try {
      setLoading(true);
      const data = await healthRoomApi.medications.getList({ limit: 100 });
      setMedications(data);
    } catch (error) {
      console.error('투약 기록 조회 실패:', error);
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
      if (!formData.worker_id || !formData.medication_name || !formData.dosage) {
        alert('필수 항목을 입력해주세요.');
        return;
      }

      await healthRoomApi.medications.create(formData as MedicationRecord);
      setOpenDialog(false);
      resetForm();
      fetchMedications();
      alert('투약 기록이 저장되었습니다.');
    } catch (error) {
      console.error('투약 기록 저장 실패:', error);
      alert('투약 기록 저장에 실패했습니다.');
    }
  };

  const resetForm = () => {
    setFormData({
      worker_id: 0,
      medication_name: '',
      dosage: '',
      quantity: 1,
      purpose: '',
      symptoms: '',
      administered_by: '',
      notes: '',
      follow_up_required: false
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

  const commonMedications = [
    '타이레놀 500mg',
    '부루펜 400mg',
    '게보린',
    '아스피린 100mg',
    '후시딘 연고',
    '마데카솔 연고',
    '베아로반 연고',
    '소화제',
    '제산제',
    '지사제'
  ];

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">투약 관리</Typography>
        <Button
          variant="contained"
          color="primary"
          startIcon={<Add />}
          onClick={handleOpenDialog}
        >
          투약 기록 추가
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>투약일시</TableCell>
              <TableCell>근로자</TableCell>
              <TableCell>약품명</TableCell>
              <TableCell>용량</TableCell>
              <TableCell>수량</TableCell>
              <TableCell>증상</TableCell>
              <TableCell>투약자</TableCell>
              <TableCell>추적관찰</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {medications.map((med) => (
              <TableRow key={med.id}>
                <TableCell>
                  {med.administered_at && format(new Date(med.administered_at), 'yyyy-MM-dd HH:mm')}
                </TableCell>
                <TableCell>{med.worker_id}</TableCell>
                <TableCell>{med.medication_name}</TableCell>
                <TableCell>{med.dosage}</TableCell>
                <TableCell>{med.quantity}</TableCell>
                <TableCell>{med.symptoms || '-'}</TableCell>
                <TableCell>{med.administered_by || '-'}</TableCell>
                <TableCell>
                  {med.follow_up_required && (
                    <Chip label="필요" color="warning" size="small" />
                  )}
                </TableCell>
                <TableCell align="center">
                  <IconButton size="small">
                    <Visibility />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 투약 기록 추가 다이얼로그 */}
      <Dialog open={openDialog} onClose={handleCloseDialog} maxWidth="md" fullWidth>
        <DialogTitle>투약 기록 추가</DialogTitle>
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
                options={commonMedications}
                value={formData.medication_name}
                onInputChange={(event, newValue) => {
                  setFormData({ ...formData, medication_name: newValue });
                }}
                renderInput={(params) => (
                  <TextField {...params} label="약품명 *" fullWidth />
                )}
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                label="용량 *"
                value={formData.dosage}
                onChange={(e) => setFormData({ ...formData, dosage: e.target.value })}
                fullWidth
                placeholder="예: 500mg"
              />
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                label="수량 *"
                type="number"
                value={formData.quantity}
                onChange={(e) => setFormData({ ...formData, quantity: parseInt(e.target.value) || 1 })}
                fullWidth
                inputProps={{ min: 1 }}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="증상"
                value={formData.symptoms}
                onChange={(e) => setFormData({ ...formData, symptoms: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="투약 목적"
                value={formData.purpose}
                onChange={(e) => setFormData({ ...formData, purpose: e.target.value })}
                fullWidth
                multiline
                rows={2}
              />
            </Grid>
            
            <Grid item xs={12} md={6}>
              <TextField
                label="투약자"
                value={formData.administered_by}
                onChange={(e) => setFormData({ ...formData, administered_by: e.target.value })}
                fullWidth
              />
            </Grid>
            
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