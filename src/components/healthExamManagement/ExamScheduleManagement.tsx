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
  LinearProgress,
  Card,
  CardContent,
  FormControlLabel,
  Checkbox,
  FormGroup
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  People as PeopleIcon,
  LocationOn as LocationIcon,
  Phone as PhoneIcon,
  CalendarMonth as CalendarIcon,
  Schedule as ScheduleIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { TimePicker } from '@mui/x-date-pickers/TimePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ko } from 'date-fns/locale';
import { format, parse } from 'date-fns';
import {
  healthExamManagementApi,
  HealthExamSchedule,
  HealthExamPlan,
  ExamCategory
} from '../../api/healthExamManagement';

export default function ExamScheduleManagement() {
  const [schedules, setSchedules] = useState<HealthExamSchedule[]>([]);
  const [plans, setPlans] = useState<HealthExamPlan[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [selectedSchedule, setSelectedSchedule] = useState<HealthExamSchedule | null>(null);
  const [selectedPlanId, setSelectedPlanId] = useState<number | null>(null);
  const [formData, setFormData] = useState<Partial<HealthExamSchedule>>({
    plan_id: 0,
    schedule_date: new Date().toISOString().split('T')[0],
    start_time: '09:00',
    end_time: '17:00',
    institution_name: '',
    institution_address: '',
    institution_contact: '',
    exam_types: [],
    total_capacity: 50,
    special_requirements: ''
  });
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedPlanId) {
      fetchSchedules();
    }
  }, [selectedPlanId]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const plansData = await healthExamManagementApi.plans.getList();
      setPlans(plansData);
      if (plansData.length > 0) {
        setSelectedPlanId(plansData[0].id!);
      }
    } catch (err) {
      console.error('데이터 로드 실패:', err);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchSchedules = async () => {
    if (!selectedPlanId) return;
    
    try {
      const data = await healthExamManagementApi.schedules.getList({ plan_id: selectedPlanId });
      setSchedules(data);
    } catch (err) {
      console.error('일정 목록 조회 실패:', err);
      setError('일정 목록을 불러오는데 실패했습니다.');
    }
  };

  const handleCreateSchedule = () => {
    setFormData({
      plan_id: selectedPlanId || 0,
      schedule_date: new Date().toISOString().split('T')[0],
      start_time: '09:00',
      end_time: '17:00',
      institution_name: '',
      institution_address: '',
      institution_contact: '',
      exam_types: [ExamCategory.GENERAL_REGULAR],
      total_capacity: 50,
      special_requirements: '검진 전 8시간 이상 금식 필요'
    });
    setSelectedSchedule(null);
    setDialogOpen(true);
  };

  const handleEditSchedule = (schedule: HealthExamSchedule) => {
    setFormData(schedule);
    setSelectedSchedule(schedule);
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    try {
      if (selectedSchedule) {
        await healthExamManagementApi.schedules.update(selectedSchedule.id!, formData);
        setSuccess('검진 일정이 수정되었습니다.');
      } else {
        await healthExamManagementApi.schedules.create(formData as any);
        setSuccess('검진 일정이 생성되었습니다.');
      }
      setDialogOpen(false);
      fetchSchedules();
    } catch (err) {
      console.error('일정 저장 실패:', err);
      setError('일정 저장에 실패했습니다.');
    }
  };

  const getOccupancyColor = (reserved: number, total: number) => {
    const rate = (reserved / total) * 100;
    if (rate >= 90) return 'error';
    if (rate >= 70) return 'warning';
    return 'success';
  };

  const examTypeOptions = [
    { value: ExamCategory.GENERAL_REGULAR, label: '일반건강진단(정기)' },
    { value: ExamCategory.GENERAL_TEMPORARY, label: '일반건강진단(임시)' },
    { value: ExamCategory.SPECIAL_REGULAR, label: '특수건강진단(정기)' },
    { value: ExamCategory.SPECIAL_TEMPORARY, label: '특수건강진단(임시)' },
    { value: ExamCategory.PRE_PLACEMENT, label: '배치전건강진단' },
    { value: ExamCategory.JOB_CHANGE, label: '직무전환건강진단' },
    { value: ExamCategory.NIGHT_WORK, label: '야간작업건강진단' }
  ];

  const institutionOptions = [
    '서울대학교병원 건강검진센터',
    '삼성서울병원 건강의학센터',
    '세브란스병원 체크업',
    '서울아산병원 건강증진센터',
    '강북삼성병원 종합건진센터'
  ];

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <FormControl sx={{ minWidth: 300 }}>
          <InputLabel>검진 계획 선택</InputLabel>
          <Select
            value={selectedPlanId || ''}
            onChange={(e) => setSelectedPlanId(Number(e.target.value))}
            label="검진 계획 선택"
          >
            {plans.map(plan => (
              <MenuItem key={plan.id} value={plan.id}>
                {plan.plan_name} ({plan.plan_year}년)
              </MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateSchedule}
          disabled={!selectedPlanId}
        >
          일정 추가
        </Button>
      </Box>

      {/* 월별 일정 요약 */}
      <Grid container spacing={2} sx={{ mb: 3 }}>
        {[0, 1, 2].map(monthOffset => {
          const targetDate = new Date();
          targetDate.setMonth(targetDate.getMonth() + monthOffset);
          const monthSchedules = schedules.filter(s => {
            const scheduleDate = new Date(s.schedule_date);
            return scheduleDate.getMonth() === targetDate.getMonth() &&
                   scheduleDate.getFullYear() === targetDate.getFullYear();
          });
          
          return (
            <Grid item xs={12} md={4} key={monthOffset}>
              <Card>
                <CardContent>
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
                    <Typography variant="h6">
                      {format(targetDate, 'yyyy년 M월', { locale: ko })}
                    </Typography>
                    <CalendarIcon color="action" />
                  </Box>
                  <Typography variant="body2" color="text.secondary">
                    일정 수: {monthSchedules.length}건
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    총 정원: {monthSchedules.reduce((sum, s) => sum + s.total_capacity, 0)}명
                  </Typography>
                  <Typography variant="body2" color="text.secondary">
                    예약률: {monthSchedules.length > 0
                      ? Math.round(
                          monthSchedules.reduce((sum, s) => sum + s.reserved_count, 0) /
                          monthSchedules.reduce((sum, s) => sum + s.total_capacity, 0) * 100
                        )
                      : 0}%
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          );
        })}
      </Grid>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>날짜</TableCell>
              <TableCell>시간</TableCell>
              <TableCell>검진기관</TableCell>
              <TableCell>검진 종류</TableCell>
              <TableCell align="center">정원</TableCell>
              <TableCell align="center">예약 현황</TableCell>
              <TableCell align="center">상태</TableCell>
              <TableCell align="center">작업</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {schedules.map((schedule) => (
              <TableRow key={schedule.id}>
                <TableCell>
                  <Typography variant="body2">
                    {format(new Date(schedule.schedule_date), 'yyyy.MM.dd (EEE)', { locale: ko })}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2">
                    {schedule.start_time} ~ {schedule.end_time}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Box>
                    <Typography variant="body2">{schedule.institution_name}</Typography>
                    {schedule.institution_contact && (
                      <Typography variant="caption" color="text.secondary">
                        <PhoneIcon sx={{ fontSize: 12, mr: 0.5 }} />
                        {schedule.institution_contact}
                      </Typography>
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Box display="flex" flexWrap="wrap" gap={0.5}>
                    {schedule.exam_types?.slice(0, 2).map((type, idx) => (
                      <Chip
                        key={idx}
                        label={type.split('_')[0]}
                        size="small"
                        variant="outlined"
                      />
                    ))}
                    {schedule.exam_types && schedule.exam_types.length > 2 && (
                      <Chip
                        label={`+${schedule.exam_types.length - 2}`}
                        size="small"
                        variant="outlined"
                      />
                    )}
                  </Box>
                </TableCell>
                <TableCell align="center">{schedule.total_capacity}</TableCell>
                <TableCell align="center">
                  <Box>
                    <Typography variant="body2">
                      {schedule.reserved_count}/{schedule.total_capacity}
                    </Typography>
                    <LinearProgress
                      variant="determinate"
                      value={(schedule.reserved_count / schedule.total_capacity) * 100}
                      color={getOccupancyColor(schedule.reserved_count, schedule.total_capacity)}
                      sx={{ mt: 1, height: 6, borderRadius: 3 }}
                    />
                  </Box>
                </TableCell>
                <TableCell align="center">
                  {schedule.is_full ? (
                    <Chip label="마감" size="small" color="error" />
                  ) : schedule.is_active ? (
                    <Chip label="접수중" size="small" color="success" />
                  ) : (
                    <Chip label="비활성" size="small" />
                  )}
                </TableCell>
                <TableCell align="center">
                  <Tooltip title="수정">
                    <IconButton size="small" onClick={() => handleEditSchedule(schedule)}>
                      <EditIcon />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="예약 목록">
                    <IconButton size="small">
                      <PeopleIcon />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {schedules.length === 0 && (
              <TableRow>
                <TableCell colSpan={8} align="center">
                  <Typography color="text.secondary" py={3}>
                    등록된 일정이 없습니다.
                  </Typography>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      {/* 일정 생성/수정 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {selectedSchedule ? '검진 일정 수정' : '검진 일정 추가'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <DatePicker
                  label="검진 날짜"
                  value={formData.schedule_date ? new Date(formData.schedule_date) : null}
                  onChange={(date) => setFormData({
                    ...formData,
                    schedule_date: date?.toISOString().split('T')[0]
                  })}
                  sx={{ width: '100%' }}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12} md={3}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <TimePicker
                  label="시작 시간"
                  value={formData.start_time ? parse(formData.start_time, 'HH:mm', new Date()) : null}
                  onChange={(time) => setFormData({
                    ...formData,
                    start_time: time ? format(time, 'HH:mm') : ''
                  })}
                  sx={{ width: '100%' }}
                />
              </LocalizationProvider>
            </Grid>
            <Grid item xs={12} md={3}>
              <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                <TimePicker
                  label="종료 시간"
                  value={formData.end_time ? parse(formData.end_time, 'HH:mm', new Date()) : null}
                  onChange={(time) => setFormData({
                    ...formData,
                    end_time: time ? format(time, 'HH:mm') : ''
                  })}
                  sx={{ width: '100%' }}
                />
              </LocalizationProvider>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>검진기관</InputLabel>
                <Select
                  value={formData.institution_name}
                  onChange={(e) => setFormData({ ...formData, institution_name: e.target.value })}
                  label="검진기관"
                >
                  {institutionOptions.map(inst => (
                    <MenuItem key={inst} value={inst}>{inst}</MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12} md={8}>
              <TextField
                fullWidth
                label="기관 주소"
                value={formData.institution_address || ''}
                onChange={(e) => setFormData({ ...formData, institution_address: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={4}>
              <TextField
                fullWidth
                label="연락처"
                value={formData.institution_contact || ''}
                onChange={(e) => setFormData({ ...formData, institution_contact: e.target.value })}
                placeholder="02-1234-5678"
              />
            </Grid>

            <Grid item xs={12}>
              <Typography variant="subtitle2" gutterBottom>가능한 검진 종류</Typography>
              <FormGroup row>
                {examTypeOptions.map(option => (
                  <FormControlLabel
                    key={option.value}
                    control={
                      <Checkbox
                        checked={formData.exam_types?.includes(option.value) || false}
                        onChange={(e) => {
                          const types = formData.exam_types || [];
                          if (e.target.checked) {
                            setFormData({ ...formData, exam_types: [...types, option.value] });
                          } else {
                            setFormData({ 
                              ...formData, 
                              exam_types: types.filter(t => t !== option.value) 
                            });
                          }
                        }}
                      />
                    }
                    label={option.label}
                  />
                ))}
              </FormGroup>
            </Grid>

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="총 정원"
                type="number"
                value={formData.total_capacity}
                onChange={(e) => setFormData({ ...formData, total_capacity: Number(e.target.value) })}
                InputProps={{ inputProps: { min: 1, max: 500 } }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="그룹 코드"
                value={formData.group_code || ''}
                onChange={(e) => setFormData({ ...formData, group_code: e.target.value })}
                placeholder="부서/팀별 그룹 예약용"
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={3}
                label="특별 요구사항"
                value={formData.special_requirements || ''}
                onChange={(e) => setFormData({ ...formData, special_requirements: e.target.value })}
                placeholder="예: 검진 전 8시간 이상 금식 필요, 당뇨약 복용자는 검진 당일 복용 금지"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSubmit}>
            {selectedSchedule ? '수정' : '생성'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}