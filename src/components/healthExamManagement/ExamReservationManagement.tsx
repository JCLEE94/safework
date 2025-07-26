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
  Tabs,
  Tab,
  Avatar,
  List,
  ListItem,
  ListItemAvatar,
  ListItemText,
  ListItemSecondaryAction,
  Divider,
  FormControlLabel,
  Checkbox,
  Radio,
  RadioGroup,
  FormLabel
} from '@mui/material';
import {
  Add as AddIcon,
  Cancel as CancelIcon,
  CheckCircle as CheckIcon,
  Print as PrintIcon,
  Send as SendIcon,
  Person as PersonIcon,
  CalendarToday as CalendarIcon,
  AccessTime as TimeIcon,
  LocalHospital as HospitalIcon,
  Phone as PhoneIcon,
  Email as EmailIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ko } from 'date-fns/locale';
import { format } from 'date-fns';
import {
  healthExamManagementApi,
  HealthExamReservation,
  HealthExamSchedule,
  ExamCategory,
  ResultDeliveryMethod
} from '../../api/healthExamManagement';
import { workersApi } from '../../api/workers';

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;
  return (
    <div hidden={value !== index} {...other}>
      {value === index && <Box sx={{ pt: 3 }}>{children}</Box>}
    </div>
  );
}

export default function ExamReservationManagement() {
  const [tabValue, setTabValue] = useState(0);
  const [reservations, setReservations] = useState<HealthExamReservation[]>([]);
  const [schedules, setSchedules] = useState<HealthExamSchedule[]>([]);
  const [workers, setWorkers] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [cancelDialogOpen, setCancelDialogOpen] = useState(false);
  const [selectedReservation, setSelectedReservation] = useState<HealthExamReservation | null>(null);
  const [selectedSchedule, setSelectedSchedule] = useState<HealthExamSchedule | null>(null);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [formData, setFormData] = useState<Partial<HealthExamReservation>>({
    schedule_id: 0,
    worker_id: 0,
    reserved_exam_types: [],
    fasting_required: true,
    result_delivery_method: ResultDeliveryMethod.COMPANY_BATCH
  });
  const [cancellationReason, setCancellationReason] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [selectedDate, setSelectedDate] = useState<Date | null>(new Date());

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    fetchReservations();
  }, [selectedDate]);

  const fetchData = async () => {
    try {
      setLoading(true);
      const [schedulesData, workersData] = await Promise.all([
        healthExamManagementApi.schedules.getList({ available_only: true }),
        workersApi.getAll()
      ]);
      setSchedules(schedulesData);
      setWorkers(workersData);
    } catch (err) {
      console.error('데이터 로드 실패:', err);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchReservations = async () => {
    try {
      const data = await healthExamManagementApi.reservations.getList({
        date: selectedDate?.toISOString().split('T')[0]
      });
      setReservations(data);
    } catch (err) {
      console.error('예약 목록 조회 실패:', err);
      setError('예약 목록을 불러오는데 실패했습니다.');
    }
  };

  const handleCreateReservation = () => {
    setFormData({
      schedule_id: 0,
      worker_id: 0,
      reserved_exam_types: [],
      fasting_required: true,
      result_delivery_method: ResultDeliveryMethod.COMPANY_BATCH,
      special_preparations: '검진 전날 밤 10시 이후 금식'
    });
    setSelectedReservation(null);
    setSelectedWorker(null);
    setDialogOpen(true);
  };

  const handleSubmit = async () => {
    if (!formData.schedule_id || !formData.worker_id || !formData.reserved_exam_types?.length) {
      setError('필수 정보를 모두 입력해주세요.');
      return;
    }

    try {
      await healthExamManagementApi.reservations.create({
        schedule_id: formData.schedule_id,
        worker_id: formData.worker_id,
        reserved_exam_types: formData.reserved_exam_types,
        result_delivery_method: formData.result_delivery_method
      });
      setSuccess('예약이 완료되었습니다.');
      setDialogOpen(false);
      fetchReservations();
    } catch (err) {
      console.error('예약 생성 실패:', err);
      setError('예약 생성에 실패했습니다.');
    }
  };

  const handleCheckIn = async (reservationId: number) => {
    try {
      await healthExamManagementApi.reservations.checkIn(reservationId);
      setSuccess('체크인 처리되었습니다.');
      fetchReservations();
    } catch (err) {
      console.error('체크인 실패:', err);
      setError('체크인 처리에 실패했습니다.');
    }
  };

  const handleCancelReservation = async () => {
    if (!selectedReservation || !cancellationReason) {
      setError('취소 사유를 입력해주세요.');
      return;
    }

    try {
      await healthExamManagementApi.reservations.cancel(selectedReservation.id!, cancellationReason);
      setSuccess('예약이 취소되었습니다.');
      setCancelDialogOpen(false);
      setCancellationReason('');
      fetchReservations();
    } catch (err) {
      console.error('예약 취소 실패:', err);
      setError('예약 취소에 실패했습니다.');
    }
  };

  const getStatusChip = (reservation: HealthExamReservation) => {
    if (reservation.is_cancelled) {
      return <Chip label="취소됨" size="small" color="error" />;
    }
    if (reservation.check_out_time) {
      return <Chip label="검진완료" size="small" color="success" />;
    }
    if (reservation.check_in_time) {
      return <Chip label="검진중" size="small" color="info" />;
    }
    return <Chip label="예약완료" size="small" color="default" />;
  };

  const todayReservations = reservations.filter(r => !r.is_cancelled);
  const cancelledReservations = reservations.filter(r => r.is_cancelled);

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
          <DatePicker
            label="예약 날짜"
            value={selectedDate}
            onChange={setSelectedDate}
            sx={{ width: 250 }}
          />
        </LocalizationProvider>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleCreateReservation}
        >
          예약 등록
        </Button>
      </Box>

      <Paper sx={{ mb: 3 }}>
        <Tabs value={tabValue} onChange={(e, val) => setTabValue(val)}>
          <Tab label={`오늘 예약 (${todayReservations.length})`} />
          <Tab label={`취소 내역 (${cancelledReservations.length})`} />
          <Tab label="일정별 현황" />
        </Tabs>
      </Paper>

      <TabPanel value={tabValue} index={0}>
        <TableContainer component={Paper}>
          <Table>
            <TableHead>
              <TableRow>
                <TableCell>예약번호</TableCell>
                <TableCell>근로자</TableCell>
                <TableCell>검진기관</TableCell>
                <TableCell>검진종류</TableCell>
                <TableCell align="center">예약시간</TableCell>
                <TableCell align="center">상태</TableCell>
                <TableCell align="center">작업</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {todayReservations.map((reservation) => (
                <TableRow key={reservation.id}>
                  <TableCell>
                    <Typography variant="body2" fontWeight="bold">
                      {reservation.reservation_number}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" alignItems="center" gap={1}>
                      <Avatar sx={{ width: 32, height: 32 }}>
                        <PersonIcon fontSize="small" />
                      </Avatar>
                      <Box>
                        <Typography variant="body2">
                          {workers.find(w => w.id === reservation.worker_id)?.name || '-'}
                        </Typography>
                        <Typography variant="caption" color="text.secondary">
                          {workers.find(w => w.id === reservation.worker_id)?.employee_id}
                        </Typography>
                      </Box>
                    </Box>
                  </TableCell>
                  <TableCell>
                    <Typography variant="body2">
                      {schedules.find(s => s.id === reservation.schedule_id)?.institution_name || '-'}
                    </Typography>
                  </TableCell>
                  <TableCell>
                    <Box display="flex" flexWrap="wrap" gap={0.5}>
                      {reservation.reserved_exam_types?.map((type, idx) => (
                        <Chip
                          key={idx}
                          label={type.split('_')[0]}
                          size="small"
                          variant="outlined"
                        />
                      ))}
                    </Box>
                  </TableCell>
                  <TableCell align="center">
                    {reservation.reserved_time || '미정'}
                  </TableCell>
                  <TableCell align="center">
                    {getStatusChip(reservation)}
                  </TableCell>
                  <TableCell align="center">
                    {!reservation.check_in_time && (
                      <Tooltip title="체크인">
                        <IconButton
                          size="small"
                          color="primary"
                          onClick={() => handleCheckIn(reservation.id!)}
                        >
                          <CheckIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    {!reservation.check_in_time && (
                      <Tooltip title="예약 취소">
                        <IconButton
                          size="small"
                          color="error"
                          onClick={() => {
                            setSelectedReservation(reservation);
                            setCancelDialogOpen(true);
                          }}
                        >
                          <CancelIcon />
                        </IconButton>
                      </Tooltip>
                    )}
                    <Tooltip title="예약증 출력">
                      <IconButton size="small">
                        <PrintIcon />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
              {todayReservations.length === 0 && (
                <TableRow>
                  <TableCell colSpan={7} align="center">
                    <Typography color="text.secondary" py={3}>
                      예약 내역이 없습니다.
                    </Typography>
                  </TableCell>
                </TableRow>
              )}
            </TableBody>
          </Table>
        </TableContainer>
      </TabPanel>

      <TabPanel value={tabValue} index={1}>
        <List>
          {cancelledReservations.map((reservation) => (
            <React.Fragment key={reservation.id}>
              <ListItem>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: 'error.light' }}>
                    <CancelIcon />
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Box display="flex" alignItems="center" gap={1}>
                      <Typography variant="body2">
                        {reservation.reservation_number}
                      </Typography>
                      <Typography variant="body2" color="text.secondary">
                        {workers.find(w => w.id === reservation.worker_id)?.name || '-'}
                      </Typography>
                    </Box>
                  }
                  secondary={
                    <Box>
                      <Typography variant="caption" display="block">
                        취소일시: {reservation.cancelled_at && format(new Date(reservation.cancelled_at), 'yyyy.MM.dd HH:mm')}
                      </Typography>
                      <Typography variant="caption" color="error">
                        사유: {reservation.cancellation_reason}
                      </Typography>
                    </Box>
                  }
                />
              </ListItem>
              <Divider variant="inset" component="li" />
            </React.Fragment>
          ))}
          {cancelledReservations.length === 0 && (
            <Typography color="text.secondary" align="center" py={3}>
              취소된 예약이 없습니다.
            </Typography>
          )}
        </List>
      </TabPanel>

      <TabPanel value={tabValue} index={2}>
        <Grid container spacing={2}>
          {schedules.map((schedule) => (
            <Grid item xs={12} md={6} key={schedule.id}>
              <Paper sx={{ p: 2 }}>
                <Box display="flex" justifyContent="space-between" alignItems="start" mb={2}>
                  <Box>
                    <Typography variant="h6">{schedule.institution_name}</Typography>
                    <Typography variant="body2" color="text.secondary">
                      {format(new Date(schedule.schedule_date), 'yyyy.MM.dd (EEE)', { locale: ko })}
                      {' '}{schedule.start_time} ~ {schedule.end_time}
                    </Typography>
                  </Box>
                  {schedule.is_full ? (
                    <Chip label="마감" color="error" size="small" />
                  ) : (
                    <Chip label="접수중" color="success" size="small" />
                  )}
                </Box>
                <Box mb={2}>
                  <Box display="flex" justifyContent="space-between" mb={1}>
                    <Typography variant="body2">예약 현황</Typography>
                    <Typography variant="body2">
                      {schedule.reserved_count} / {schedule.total_capacity}
                    </Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate"
                    value={(schedule.reserved_count / schedule.total_capacity) * 100}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
                <Button
                  fullWidth
                  variant="outlined"
                  disabled={schedule.is_full}
                  onClick={() => {
                    setSelectedSchedule(schedule);
                    setFormData({ ...formData, schedule_id: schedule.id! });
                    handleCreateReservation();
                  }}
                >
                  이 일정에 예약하기
                </Button>
              </Paper>
            </Grid>
          ))}
        </Grid>
      </TabPanel>

      {/* 예약 등록 다이얼로그 */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>검진 예약 등록</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>검진 일정</InputLabel>
                <Select
                  value={formData.schedule_id}
                  onChange={(e) => {
                    const schedule = schedules.find(s => s.id === Number(e.target.value));
                    setFormData({ ...formData, schedule_id: Number(e.target.value) });
                    setSelectedSchedule(schedule || null);
                  }}
                  label="검진 일정"
                >
                  {schedules.map(schedule => (
                    <MenuItem key={schedule.id} value={schedule.id}>
                      {format(new Date(schedule.schedule_date), 'MM.dd (EEE)', { locale: ko })} - 
                      {schedule.institution_name} ({schedule.available_slots}명 가능)
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>근로자</InputLabel>
                <Select
                  value={formData.worker_id}
                  onChange={(e) => {
                    const worker = workers.find(w => w.id === Number(e.target.value));
                    setFormData({ ...formData, worker_id: Number(e.target.value) });
                    setSelectedWorker(worker);
                  }}
                  label="근로자"
                >
                  {workers.map(worker => (
                    <MenuItem key={worker.id} value={worker.id}>
                      {worker.name} ({worker.employee_id}) - {worker.department}
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
            </Grid>

            {selectedSchedule && (
              <Grid item xs={12}>
                <Typography variant="subtitle2" gutterBottom>검진 종류 선택</Typography>
                <FormGroup>
                  {selectedSchedule.exam_types?.map(type => (
                    <FormControlLabel
                      key={type}
                      control={
                        <Checkbox
                          checked={formData.reserved_exam_types?.includes(type) || false}
                          onChange={(e) => {
                            const types = formData.reserved_exam_types || [];
                            if (e.target.checked) {
                              setFormData({ ...formData, reserved_exam_types: [...types, type] });
                            } else {
                              setFormData({
                                ...formData,
                                reserved_exam_types: types.filter(t => t !== type)
                              });
                            }
                          }}
                        />
                      }
                      label={type}
                    />
                  ))}
                </FormGroup>
              </Grid>
            )}

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="예약 시간"
                type="time"
                value={formData.reserved_time || ''}
                onChange={(e) => setFormData({ ...formData, reserved_time: e.target.value })}
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="예상 소요시간 (분)"
                type="number"
                value={formData.estimated_duration || 60}
                onChange={(e) => setFormData({ ...formData, estimated_duration: Number(e.target.value) })}
              />
            </Grid>

            <Grid item xs={12}>
              <FormControl>
                <FormLabel>결과 수령 방법</FormLabel>
                <RadioGroup
                  row
                  value={formData.result_delivery_method}
                  onChange={(e) => setFormData({ ...formData, result_delivery_method: e.target.value as ResultDeliveryMethod })}
                >
                  <FormControlLabel value={ResultDeliveryMethod.COMPANY_BATCH} control={<Radio />} label="회사일괄" />
                  <FormControlLabel value={ResultDeliveryMethod.DIRECT} control={<Radio />} label="직접수령" />
                  <FormControlLabel value={ResultDeliveryMethod.POSTAL} control={<Radio />} label="우편발송" />
                  <FormControlLabel value={ResultDeliveryMethod.EMAIL} control={<Radio />} label="이메일" />
                  <FormControlLabel value={ResultDeliveryMethod.MOBILE} control={<Radio />} label="모바일" />
                </RadioGroup>
              </FormControl>
            </Grid>

            {(formData.result_delivery_method === ResultDeliveryMethod.POSTAL ||
              formData.result_delivery_method === ResultDeliveryMethod.EMAIL) && (
              <Grid item xs={12}>
                <TextField
                  fullWidth
                  label={formData.result_delivery_method === ResultDeliveryMethod.EMAIL ? "이메일 주소" : "배송 주소"}
                  value={formData.result_delivery_address || ''}
                  onChange={(e) => setFormData({ ...formData, result_delivery_address: e.target.value })}
                />
              </Grid>
            )}

            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="연락처"
                value={formData.contact_phone || selectedWorker?.phone || ''}
                onChange={(e) => setFormData({ ...formData, contact_phone: e.target.value })}
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <TextField
                fullWidth
                label="이메일"
                value={formData.contact_email || selectedWorker?.email || ''}
                onChange={(e) => setFormData({ ...formData, contact_email: e.target.value })}
              />
            </Grid>

            <Grid item xs={12}>
              <TextField
                fullWidth
                multiline
                rows={2}
                label="특별 준비사항"
                value={formData.special_preparations || ''}
                onChange={(e) => setFormData({ ...formData, special_preparations: e.target.value })}
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>취소</Button>
          <Button variant="contained" onClick={handleSubmit}>
            예약 등록
          </Button>
        </DialogActions>
      </Dialog>

      {/* 예약 취소 다이얼로그 */}
      <Dialog open={cancelDialogOpen} onClose={() => setCancelDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>예약 취소</DialogTitle>
        <DialogContent>
          <Typography variant="body2" gutterBottom>
            예약번호: {selectedReservation?.reservation_number}
          </Typography>
          <TextField
            fullWidth
            multiline
            rows={3}
            label="취소 사유"
            value={cancellationReason}
            onChange={(e) => setCancellationReason(e.target.value)}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCancelDialogOpen(false)}>닫기</Button>
          <Button
            variant="contained"
            color="error"
            onClick={handleCancelReservation}
            disabled={!cancellationReason}
          >
            예약 취소
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}