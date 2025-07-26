import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Chip,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  Grid,
  MenuItem,
  FormControl,
  InputLabel,
  Select,
  Alert,
  Tooltip,
  Card,
  CardContent,
  Divider,
  FormControlLabel,
  Checkbox
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  CheckCircle as CheckIcon,
  Cancel as CancelIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ko } from 'date-fns/locale';
import { format } from 'date-fns';
import { healthExamManagementApi, HealthExamPlan, ExamPlanStatus } from '../../api/healthExamManagement';

export default function ExamPlanManagement() {
  const [plans, setPlans] = useState<HealthExamPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [viewDialogOpen, setViewDialogOpen] = useState(false);
  const [selectedPlan, setSelectedPlan] = useState<HealthExamPlan | null>(null);
  const [formData, setFormData] = useState<Partial<HealthExamPlan>>({
    plan_year: new Date().getFullYear(),
    plan_name: '',
    total_workers: 0,
    general_exam_targets: 0,
    special_exam_targets: 0,
    night_work_targets: 0,
    primary_institution: '',
    estimated_budget: 0,
    harmful_factors: []
  });
  const [selectedYear, setSelectedYear] = useState(new Date().getFullYear());
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchPlans();
  }, [selectedYear]);

  const fetchPlans = async () => {
    try {
      setLoading(true);
      const data = await healthExamManagementApi.plans.getList({ year: selectedYear });
      setPlans(data);
    } catch (err) {
      console.error('계획 목록 조회 실패:', err);
      setError('계획 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleCreatePlan = () => {
    setFormData({
      plan_year: new Date().getFullYear(),
      plan_name: `${new Date().getFullYear()}년 정기건강검진 계획`,
      total_workers: 0,
      general_exam_targets: 0,
      special_exam_targets: 0,
      night_work_targets: 0,
      primary_institution: '',
      estimated_budget: 0,
      harmful_factors: []
    });
    setSelectedPlan(null);
    setDialogOpen(true);
  };

  const handleEditPlan = (plan: HealthExamPlan) => {
    setFormData(plan);
    setSelectedPlan(plan);
    setDialogOpen(true);
  };

  const handleViewPlan = (plan: HealthExamPlan) => {
    setSelectedPlan(plan);
    setViewDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (selectedPlan) {
        await healthExamManagementApi.plans.update(selectedPlan.id!, formData);
        setSuccess('검진 계획이 수정되었습니다.');
      } else {
        await healthExamManagementApi.plans.create(formData as any);
        setSuccess('검진 계획이 생성되었습니다.');
      }
      setDialogOpen(false);
      fetchPlans();
    } catch (err) {
      console.error('계획 저장 실패:', err);
      setError('계획 저장에 실패했습니다.');
    }
  };

  const handleApprovePlan = async (planId: number) => {
    if (!window.confirm('이 계획을 승인하시겠습니까?')) return;
    
    try {
      await healthExamManagementApi.plans.approve(planId);
      setSuccess('계획이 승인되었습니다.');
      fetchPlans();
    } catch (err) {
      console.error('계획 승인 실패:', err);
      setError('계획 승인에 실패했습니다.');
    }
  };

  const getStatusChip = (status?: ExamPlanStatus) => {
    const statusConfig = {
      [ExamPlanStatus.DRAFT]: { label: '초안', color: 'default' as const },
      [ExamPlanStatus.APPROVED]: { label: '승인됨', color: 'success' as const },
      [ExamPlanStatus.IN_PROGRESS]: { label: '진행중', color: 'info' as const },
      [ExamPlanStatus.COMPLETED]: { label: '완료', color: 'primary' as const },
      [ExamPlanStatus.CANCELLED]: { label: '취소', color: 'error' as const }
    };

    const config = status ? statusConfig[status] : statusConfig[ExamPlanStatus.DRAFT];
    return <Chip size="small" label={config.label} color={config.color} />;
  };

  const harmfulFactorOptions = [
    '소음', '분진', '화학물질', '중금속', '유기용제',
    '방사선', '진동', '고온', '저온', '이상기압'
  ];

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box display="flex" alignItems="center" gap={2}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>연도</InputLabel>
            <Select
              value={selectedYear}
              onChange={(e) => setSelectedYear(Number(e.target.value))}
              label="연도"
            >
              {[0, 1, 2].map(offset => (
                <MenuItem key={offset} value={new Date().getFullYear() - offset}>
                  {new Date().getFullYear() - offset}년
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreatePlan}
        >
          계획 수립
        </Button>
      </Box>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>계획명</TableCell>
              <TableCell align="center">상태</TableCell>
              <TableCell align="center">총 대상자</TableCell>
              <TableCell align="center">일반검진</TableCell>
              <TableCell align="center">특수검진</TableCell>
              <TableCell align="center">야간작업</TableCell>
              <TableCell align="center">예산</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {plans.map((plan) => (
              <TableRow key={plan.id}>
                <TableCell>
                  <Typography variant="body2">{plan.plan_name}</Typography>
                  {plan.plan_start_date && plan.plan_end_date && (
                    <Typography variant="caption" color="text.secondary">
                      {format(new Date(plan.plan_start_date), 'yyyy.MM.dd')} ~ 
                      {format(new Date(plan.plan_end_date), 'yyyy.MM.dd')}
                    </Typography>
                  )}
                </TableCell>
                <TableCell align="center">{getStatusChip(plan.plan_status)}</TableCell>
                <TableCell align="center">{plan.total_workers}</TableCell>
                <TableCell align="center">{plan.general_exam_targets}</TableCell>
                <TableCell align="center">{plan.special_exam_targets}</TableCell>
                <TableCell align="center">{plan.night_work_targets}</TableCell>
                <TableCell align="center">
                  {plan.estimated_budget ? `${(plan.estimated_budget / 10000).toFixed(0)}만원` : '-'}
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="상세보기">
                    <IconButton size="small" onClick={() => handleViewPlan(plan)}>
                      <ViewIcon />
                    </IconButton>
                  </Tooltip>
                  {plan.plan_status === ExamPlanStatus.DRAFT && (
                    <>
                      <Tooltip title="수정">
                        <IconButton size="small" onClick={() => handleEditPlan(plan)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="승인">
                        <IconButton
                          size="small"
                          color="success"
                          onClick={() => handleApprovePlan(plan.id!)}
                        >
                          <CheckIcon />
                        </IconButton>
                      </Tooltip>
                    </>
                  )}
                </TableCell>
              </TableRow>
            ))}
            {plans.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" py={3}>
                    등록된 계획이 없습니다.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 계획 생성/수정 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedPlan ? '검진 계획 수정' : '검진 계획 수립'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="계획 연도"
                type="number"
                value={formData.plan_year}
                onChange={(e) => setFormData({ ...formData, plan_year: Number(e.target.value) })}
                disabled={!!selectedPlan}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="계획명"
                value={formData.plan_name}
                onChange={(e) => setFormData({ ...formData, plan_name: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <DatePicker
                  label="시작일"
                  value={formData.plan_start_date ? new Date(formData.plan_start_date) : null}
                  onChange={(date) => setFormData({ ...formData, plan_start_date: date?.toISOString().split('T')[0] })}
                  sx={{ width: '100%' }}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <DatePicker
                  label="종료일"
                  value={formData.plan_end_date ? new Date(formData.plan_end_date) : null}
                  onChange={(date) => setFormData({ ...formData, plan_end_date: date?.toISOString().split('T')[0] })}
                  sx={{ width: '100%' }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>대상자 정보</Typography>
            </Grid>
            
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="전체 근로자"
                type="number"
                value={formData.total_workers}
                onChange={(e) => setFormData({ ...formData, total_workers: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="일반검진 대상"
                type="number"
                value={formData.general_exam_targets}
                onChange={(e) => setFormData({ ...formData, general_exam_targets: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="특수검진 대상"
                type="number"
                value={formData.special_exam_targets}
                onChange={(e) => setFormData({ ...formData, special_exam_targets: Number(e.target.value) })}
              />
            </Grid>
            <Grid item xs={12} md={3}>
              <TextField
                fullWidth
                label="야간작업 대상"
                type="number"
                value={formData.night_work_targets}
                onChange={(e) => setFormData({ ...formData, night_work_targets: Number(e.target.value) })}
              />
            </Grid>

            <Grid item xs={12}>
              <Divider sx={{ my: 2 }} />
              <Typography variant="subtitle2" gutterBottom>검진기관 및 예산</Typography>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="주 검진기관"
                value={formData.primary_institution}
                onChange={(e) => setFormData({ ...formData, primary_institution: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="예상 예산 (원)"
                type="number"
                value={formData.estimated_budget}
                onChange={(e) => setFormData({ ...formData, estimated_budget: Number(e.target.value) })}
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>특수검진 유해인자</Typography>
              <Box display="flex" flexWrap="wrap" gap={1}>
                {harmfulFactorOptions.map(factor => (
                  <FormControlLabel
                    key={factor}
                    control={
                      <Checkbox
                        checked={formData.harmful_factors?.includes(factor) || false}
                        onChange={(e) => {
                          const factors = formData.harmful_factors || [];
                          if (e.target.checked) {
                            setFormData({ ...formData, harmful_factors: [...factors, factor] });
                          } else {
                            setFormData({ ...formData, harmful_factors: factors.filter(f => f !== factor) });
                          }
                        }}
                      />
                    }
                    label={factor}
                  />
                ))}
              </Box>
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="비고"
                value={formData.notes || ''}
                onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSubmit}>
            {selectedPlan ? '수정' : '생성'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* 계획 상세보기 다이얼로그 */}
      <Dialog open={viewDialogOpen} onClose={() => setViewDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>검진 계획 상세</DialogTitle>
        <DialogContent>
          {selectedPlan && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Card variant="outlined">
                  <CardContent>
                    <Typography variant="h6" gutterBottom>{selectedPlan.plan_name}</Typography>
                    <Box display="flex" gap={2} mb={2}>
                      {getStatusChip(selectedPlan.plan_status)}
                      {selectedPlan.approved_by && (
                        <Typography variant="caption" color="text.secondary">
                          승인자: {selectedPlan.approved_by} ({format(new Date(selectedPlan.approved_at!), 'yyyy.MM.dd')})
                        </Typography>
                      )}
                    </Box>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">기간</Typography>
                        <Typography variant="body1">
                          {selectedPlan.plan_start_date && selectedPlan.plan_end_date
                            ? `${format(new Date(selectedPlan.plan_start_date), 'yyyy.MM.dd')} ~ ${format(new Date(selectedPlan.plan_end_date), 'yyyy.MM.dd')}`
                            : '미정'}
                        </Typography>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="body2" color="text.secondary">주 검진기관</Typography>
                        <Typography variant="body1">{selectedPlan.primary_institution || '-'}</Typography>
                      </Grid>
                      <Grid item xs={12}>
                        <Divider sx={{ my: 1 }} />
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2" color="text.secondary">전체 대상</Typography>
                        <Typography variant="h6">{selectedPlan.total_workers}명</Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2" color="text.secondary">일반검진</Typography>
                        <Typography variant="h6">{selectedPlan.general_exam_targets}명</Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2" color="text.secondary">특수검진</Typography>
                        <Typography variant="h6">{selectedPlan.special_exam_targets}명</Typography>
                      </Grid>
                      <Grid item xs={3}>
                        <Typography variant="body2" color="text.secondary">야간작업</Typography>
                        <Typography variant="h6">{selectedPlan.night_work_targets}명</Typography>
                      </Grid>
                      {selectedPlan.harmful_factors && selectedPlan.harmful_factors.length > 0 && (
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary" gutterBottom>유해인자</Typography>
                          <Box display="flex" flexWrap="wrap" gap={1}>
                            {selectedPlan.harmful_factors.map(factor => (
                              <Chip key={factor} label={factor} size="small" />
                            ))}
                          </Box>
                        </Grid>
                      )}
                      <Grid item xs={12}>
                        <Typography variant="body2" color="text.secondary">예산</Typography>
                        <Typography variant="h6">
                          {selectedPlan.estimated_budget
                            ? `${(selectedPlan.estimated_budget / 10000).toFixed(0)}만원 (1인당 ${(selectedPlan.budget_per_person || 0).toLocaleString()}원)`
                            : '미정'}
                        </Typography>
                      </Grid>
                      {selectedPlan.notes && (
                        <Grid item xs={12}>
                          <Typography variant="body2" color="text.secondary">비고</Typography>
                          <Typography variant="body1">{selectedPlan.notes}</Typography>
                        </Grid>
                      )}
                    </Grid>
                  </CardContent>
                </Card>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setViewDialogOpen(false)}>닫기</Button>
          {selectedPlan?.plan_status === ExamPlanStatus.APPROVED && (
            <Button
              variant="contained"
              startIcon={<PeopleIcon />}
              onClick={() => {
                // TODO: 대상자 생성 기능 구현
                alert('대상자 생성 기능은 구현 예정입니다.');
              }}
            >
              대상자 생성
            </Button>
          )}
        </DialogActions>
      </Dialog>
    </Box>
  );
}