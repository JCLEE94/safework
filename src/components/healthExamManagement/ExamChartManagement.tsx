import React, { useState, useEffect } from 'react';
import {
  Box,
  Paper,
  Typography,
  Button,
  TextField,
  Grid,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Alert,
  Card,
  CardContent,
  Divider,
  FormGroup,
  FormControlLabel,
  Checkbox,
  Radio,
  RadioGroup,
  FormLabel,
  Chip,
  IconButton,
  Stepper,
  Step,
  StepLabel,
  StepContent,
  List,
  ListItem,
  ListItemText,
  ListItemIcon
} from '@mui/material';
import {
  Save as SaveIcon,
  Print as PrintIcon,
  CheckCircle as CheckIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  SmokingRooms as SmokingIcon,
  LocalBar as DrinkingIcon,
  FitnessCenter as ExerciseIcon,
  Hotel as SleepIcon,
  Healing as HealthIcon,
  Work as WorkIcon
} from '@mui/icons-material';
import { DatePicker } from '@mui/x-date-pickers/DatePicker';
import { LocalizationProvider } from '@mui/x-date-pickers/LocalizationProvider';
import { AdapterDateFns } from '@mui/x-date-pickers/AdapterDateFns';
import { ko } from 'date-fns/locale';
import { format } from 'date-fns';
import {
  healthExamManagementApi,
  HealthExamChart,
  MedicalHistoryInfo,
  LifestyleHabitsInfo
} from '../../api/healthExamManagement';
import { workersApi } from '../../api/workers';

export default function ExamChartManagement() {
  const [activeStep, setActiveStep] = useState(0);
  const [selectedWorker, setSelectedWorker] = useState<any>(null);
  const [workers, setWorkers] = useState<any[]>([]);
  const [charts, setCharts] = useState<HealthExamChart[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  
  const [formData, setFormData] = useState<Partial<HealthExamChart>>({
    worker_id: 0,
    exam_date: new Date().toISOString().split('T')[0],
    exam_type: '일반건강진단',
    medical_history: {
      past_diseases: [],
      current_medications: [],
      family_history: [],
      allergies: [],
      surgeries: []
    },
    lifestyle_habits: {
      smoking: { status: 'never', amount: '', years: 0 },
      drinking: { frequency: 'never', amount: '' },
      exercise: { frequency: 'never', type: '' },
      sleep: { hours: 7, quality: 'normal' }
    },
    symptoms: {
      general: [],
      respiratory: [],
      cardiovascular: [],
      musculoskeletal: [],
      neurological: []
    },
    work_environment: {
      harmful_factors: [],
      ppe_usage: {},
      work_hours: { day: 8, overtime: 0 },
      shift_work: false
    }
  });

  useEffect(() => {
    fetchWorkers();
  }, []);

  useEffect(() => {
    if (selectedWorker) {
      fetchWorkerCharts(selectedWorker.id);
    }
  }, [selectedWorker]);

  const fetchWorkers = async () => {
    try {
      setLoading(true);
      const data = await workersApi.getAll();
      setWorkers(data);
    } catch (err) {
      console.error('근로자 목록 조회 실패:', err);
      setError('근로자 목록을 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const fetchWorkerCharts = async (workerId: number) => {
    try {
      const data = await healthExamManagementApi.charts.getByWorkerId(workerId);
      setCharts(data);
    } catch (err) {
      console.error('문진표 조회 실패:', err);
    }
  };

  const handleWorkerSelect = (workerId: number) => {
    const worker = workers.find(w => w.id === workerId);
    setSelectedWorker(worker);
    setFormData({ ...formData, worker_id: workerId });
  };

  const handleSubmit = async () => {
    try {
      await healthExamManagementApi.charts.create(formData as any);
      setSuccess('문진표가 저장되었습니다.');
      setActiveStep(0);
      fetchWorkerCharts(formData.worker_id);
    } catch (err) {
      console.error('문진표 저장 실패:', err);
      setError('문진표 저장에 실패했습니다.');
    }
  };

  const updateMedicalHistory = (field: keyof MedicalHistoryInfo, value: string[]) => {
    setFormData({
      ...formData,
      medical_history: {
        ...formData.medical_history!,
        [field]: value
      }
    });
  };

  const updateLifestyleHabits = (field: keyof LifestyleHabitsInfo, value: any) => {
    setFormData({
      ...formData,
      lifestyle_habits: {
        ...formData.lifestyle_habits!,
        [field]: value
      }
    });
  };

  const updateSymptoms = (category: string, symptoms: string[]) => {
    setFormData({
      ...formData,
      symptoms: {
        ...formData.symptoms!,
        [category]: symptoms
      }
    });
  };

  const updateWorkEnvironment = (field: string, value: any) => {
    setFormData({
      ...formData,
      work_environment: {
        ...formData.work_environment!,
        [field]: value
      }
    });
  };

  const steps = [
    '기본 정보',
    '과거 병력',
    '생활 습관',
    '증상 확인',
    '작업 환경',
    '확인 및 제출'
  ];

  const diseaseOptions = [
    '고혈압', '당뇨병', '고지혈증', '심장질환', '뇌졸중',
    '암', '간질환', '신장질환', '갑상선질환', '천식',
    '결핵', '간염', '빈혈', '위장질환', '기타'
  ];

  const symptomOptions = {
    general: ['피로감', '체중감소', '체중증가', '발열', '오한', '식욕부진'],
    respiratory: ['기침', '가래', '호흡곤란', '흉통', '객혈'],
    cardiovascular: ['가슴통증', '심계항진', '부종', '현기증'],
    musculoskeletal: ['요통', '관절통', '근육통', '운동제한'],
    neurological: ['두통', '어지러움', '손발저림', '시야장애']
  };

  const harmfulFactorOptions = [
    '소음', '분진', '화학물질', '중금속', '유기용제',
    '방사선', '진동', '고온', '저온', '이상기압'
  ];

  return (
    <Box>
      {error && <Alert severity="error" sx={{ mb: 2 }} onClose={() => setError(null)}>{error}</Alert>}
      {success && <Alert severity="success" sx={{ mb: 2 }} onClose={() => setSuccess(null)}>{success}</Alert>}

      <Grid container spacing={3}>
        {/* 근로자 선택 */}
        <Grid item xs={12} md={4}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>근로자 선택</Typography>
            <FormControl fullWidth sx={{ mb: 2 }}>
              <InputLabel>근로자</InputLabel>
              <Select
                value={formData.worker_id || ''}
                onChange={(e) => handleWorkerSelect(Number(e.target.value))}
                label="근로자"
              >
                {workers.map(worker => (
                  <MenuItem key={worker.id} value={worker.id}>
                    {worker.name} ({worker.employee_id})
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {selectedWorker && (
              <Card variant="outlined">
                <CardContent>
                  <Typography variant="subtitle2" gutterBottom>선택된 근로자</Typography>
                  <Typography variant="body2">{selectedWorker.name}</Typography>
                  <Typography variant="caption" color="text.secondary">
                    {selectedWorker.department} / {selectedWorker.position}
                  </Typography>
                  
                  {charts.length > 0 && (
                    <>
                      <Divider sx={{ my: 2 }} />
                      <Typography variant="subtitle2" gutterBottom>이전 문진표</Typography>
                      <List dense>
                        {charts.slice(0, 3).map((chart) => (
                          <ListItem key={chart.id} button>
                            <ListItemText
                              primary={format(new Date(chart.exam_date), 'yyyy.MM.dd')}
                              secondary={chart.exam_type}
                            />
                          </ListItem>
                        ))}
                      </List>
                    </>
                  )}
                </CardContent>
              </Card>
            )}
          </Paper>
        </Grid>

        {/* 문진표 작성 */}
        <Grid item xs={12} md={8}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>건강검진 문진표</Typography>
            
            <Stepper activeStep={activeStep} orientation="vertical">
              {/* Step 1: 기본 정보 */}
              <Step>
                <StepLabel>기본 정보</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <LocalizationProvider dateAdapter={AdapterDateFns} adapterLocale={ko}>
                        <DatePicker
                          label="검진 날짜"
                          value={formData.exam_date ? new Date(formData.exam_date) : null}
                          onChange={(date) => setFormData({
                            ...formData,
                            exam_date: date?.toISOString().split('T')[0]
                          })}
                          sx={{ width: '100%' }}
                        />
                      </LocalizationProvider>
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <FormControl fullWidth>
                        <InputLabel>검진 종류</InputLabel>
                        <Select
                          value={formData.exam_type}
                          onChange={(e) => setFormData({ ...formData, exam_type: e.target.value })}
                          label="검진 종류"
                        >
                          <MenuItem value="일반건강진단">일반건강진단</MenuItem>
                          <MenuItem value="특수건강진단">특수건강진단</MenuItem>
                          <MenuItem value="배치전건강진단">배치전건강진단</MenuItem>
                          <MenuItem value="야간작업건강진단">야간작업건강진단</MenuItem>
                        </Select>
                      </FormControl>
                    </Grid>
                  </Grid>
                  <Box mt={2}>
                    <Button variant="contained" onClick={() => setActiveStep(1)}>
                      다음
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 2: 과거 병력 */}
              <Step>
                <StepLabel>과거 병력</StepLabel>
                <StepContent>
                  <Typography variant="subtitle2" gutterBottom>과거 질병</Typography>
                  <FormGroup row sx={{ mb: 2 }}>
                    {diseaseOptions.map(disease => (
                      <FormControlLabel
                        key={disease}
                        control={
                          <Checkbox
                            checked={formData.medical_history?.past_diseases?.includes(disease) || false}
                            onChange={(e) => {
                              const diseases = formData.medical_history?.past_diseases || [];
                              if (e.target.checked) {
                                updateMedicalHistory('past_diseases', [...diseases, disease]);
                              } else {
                                updateMedicalHistory('past_diseases', diseases.filter(d => d !== disease));
                              }
                            }}
                          />
                        }
                        label={disease}
                      />
                    ))}
                  </FormGroup>

                  <Typography variant="subtitle2" gutterBottom>현재 복용 약물</Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    placeholder="복용 중인 약물명을 입력하세요"
                    value={formData.medical_history?.current_medications?.join(', ') || ''}
                    onChange={(e) => updateMedicalHistory(
                      'current_medications',
                      e.target.value.split(',').map(s => s.trim()).filter(s => s)
                    )}
                    sx={{ mb: 2 }}
                  />

                  <Typography variant="subtitle2" gutterBottom>가족력</Typography>
                  <TextField
                    fullWidth
                    multiline
                    rows={2}
                    placeholder="가족 중 주요 질병력을 입력하세요"
                    value={formData.medical_history?.family_history?.join(', ') || ''}
                    onChange={(e) => updateMedicalHistory(
                      'family_history',
                      e.target.value.split(',').map(s => s.trim()).filter(s => s)
                    )}
                  />

                  <Box mt={2} display="flex" gap={1}>
                    <Button onClick={() => setActiveStep(0)}>이전</Button>
                    <Button variant="contained" onClick={() => setActiveStep(2)}>
                      다음
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 3: 생활 습관 */}
              <Step>
                <StepLabel>생활 습관</StepLabel>
                <StepContent>
                  <Grid container spacing={2}>
                    {/* 흡연 */}
                    <Grid item xs={12}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <SmokingIcon />
                        <Typography variant="subtitle2">흡연</Typography>
                      </Box>
                      <FormControl>
                        <RadioGroup
                          row
                          value={formData.lifestyle_habits?.smoking?.status || 'never'}
                          onChange={(e) => updateLifestyleHabits('smoking', {
                            ...formData.lifestyle_habits?.smoking,
                            status: e.target.value
                          })}
                        >
                          <FormControlLabel value="never" control={<Radio />} label="비흡연" />
                          <FormControlLabel value="past" control={<Radio />} label="과거흡연" />
                          <FormControlLabel value="current" control={<Radio />} label="현재흡연" />
                        </RadioGroup>
                      </FormControl>
                      {formData.lifestyle_habits?.smoking?.status === 'current' && (
                        <Box display="flex" gap={2} mt={1}>
                          <TextField
                            label="하루 흡연량"
                            size="small"
                            value={formData.lifestyle_habits?.smoking?.amount || ''}
                            onChange={(e) => updateLifestyleHabits('smoking', {
                              ...formData.lifestyle_habits?.smoking,
                              amount: e.target.value
                            })}
                          />
                          <TextField
                            label="흡연 기간(년)"
                            type="number"
                            size="small"
                            value={formData.lifestyle_habits?.smoking?.years || ''}
                            onChange={(e) => updateLifestyleHabits('smoking', {
                              ...formData.lifestyle_habits?.smoking,
                              years: Number(e.target.value)
                            })}
                          />
                        </Box>
                      )}
                    </Grid>

                    {/* 음주 */}
                    <Grid item xs={12}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <DrinkingIcon />
                        <Typography variant="subtitle2">음주</Typography>
                      </Box>
                      <FormControl fullWidth>
                        <Select
                          value={formData.lifestyle_habits?.drinking?.frequency || 'never'}
                          onChange={(e) => updateLifestyleHabits('drinking', {
                            ...formData.lifestyle_habits?.drinking,
                            frequency: e.target.value
                          })}
                          size="small"
                        >
                          <MenuItem value="never">전혀 안함</MenuItem>
                          <MenuItem value="monthly">월 1회 이하</MenuItem>
                          <MenuItem value="weekly">주 1-2회</MenuItem>
                          <MenuItem value="frequent">주 3-4회</MenuItem>
                          <MenuItem value="daily">거의 매일</MenuItem>
                        </Select>
                      </FormControl>
                      {formData.lifestyle_habits?.drinking?.frequency !== 'never' && (
                        <TextField
                          fullWidth
                          label="1회 음주량"
                          size="small"
                          value={formData.lifestyle_habits?.drinking?.amount || ''}
                          onChange={(e) => updateLifestyleHabits('drinking', {
                            ...formData.lifestyle_habits?.drinking,
                            amount: e.target.value
                          })}
                          sx={{ mt: 1 }}
                        />
                      )}
                    </Grid>

                    {/* 운동 */}
                    <Grid item xs={12}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <ExerciseIcon />
                        <Typography variant="subtitle2">운동</Typography>
                      </Box>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <FormControl fullWidth>
                            <InputLabel>운동 빈도</InputLabel>
                            <Select
                              value={formData.lifestyle_habits?.exercise?.frequency || 'never'}
                              onChange={(e) => updateLifestyleHabits('exercise', {
                                ...formData.lifestyle_habits?.exercise,
                                frequency: e.target.value
                              })}
                              label="운동 빈도"
                              size="small"
                            >
                              <MenuItem value="never">전혀 안함</MenuItem>
                              <MenuItem value="monthly">월 1-2회</MenuItem>
                              <MenuItem value="weekly">주 1-2회</MenuItem>
                              <MenuItem value="frequent">주 3-4회</MenuItem>
                              <MenuItem value="daily">거의 매일</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="운동 종류"
                            size="small"
                            value={formData.lifestyle_habits?.exercise?.type || ''}
                            onChange={(e) => updateLifestyleHabits('exercise', {
                              ...formData.lifestyle_habits?.exercise,
                              type: e.target.value
                            })}
                          />
                        </Grid>
                      </Grid>
                    </Grid>

                    {/* 수면 */}
                    <Grid item xs={12}>
                      <Box display="flex" alignItems="center" gap={1} mb={1}>
                        <SleepIcon />
                        <Typography variant="subtitle2">수면</Typography>
                      </Box>
                      <Grid container spacing={2}>
                        <Grid item xs={6}>
                          <TextField
                            fullWidth
                            label="평균 수면시간"
                            type="number"
                            size="small"
                            value={formData.lifestyle_habits?.sleep?.hours || 7}
                            onChange={(e) => updateLifestyleHabits('sleep', {
                              ...formData.lifestyle_habits?.sleep,
                              hours: Number(e.target.value)
                            })}
                            InputProps={{ inputProps: { min: 1, max: 24 } }}
                          />
                        </Grid>
                        <Grid item xs={6}>
                          <FormControl fullWidth>
                            <InputLabel>수면의 질</InputLabel>
                            <Select
                              value={formData.lifestyle_habits?.sleep?.quality || 'normal'}
                              onChange={(e) => updateLifestyleHabits('sleep', {
                                ...formData.lifestyle_habits?.sleep,
                                quality: e.target.value
                              })}
                              label="수면의 질"
                              size="small"
                            >
                              <MenuItem value="good">좋음</MenuItem>
                              <MenuItem value="normal">보통</MenuItem>
                              <MenuItem value="poor">나쁨</MenuItem>
                              <MenuItem value="insomnia">불면증</MenuItem>
                            </Select>
                          </FormControl>
                        </Grid>
                      </Grid>
                    </Grid>
                  </Grid>

                  <Box mt={2} display="flex" gap={1}>
                    <Button onClick={() => setActiveStep(1)}>이전</Button>
                    <Button variant="contained" onClick={() => setActiveStep(3)}>
                      다음
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 4: 증상 확인 */}
              <Step>
                <StepLabel>증상 확인</StepLabel>
                <StepContent>
                  {Object.entries(symptomOptions).map(([category, symptoms]) => (
                    <Box key={category} mb={2}>
                      <Typography variant="subtitle2" gutterBottom>
                        {category === 'general' ? '일반 증상' :
                         category === 'respiratory' ? '호흡기 증상' :
                         category === 'cardiovascular' ? '심혈관 증상' :
                         category === 'musculoskeletal' ? '근골격계 증상' :
                         '신경계 증상'}
                      </Typography>
                      <FormGroup row>
                        {symptoms.map(symptom => (
                          <FormControlLabel
                            key={symptom}
                            control={
                              <Checkbox
                                checked={formData.symptoms?.[category]?.includes(symptom) || false}
                                onChange={(e) => {
                                  const currentSymptoms = formData.symptoms?.[category] || [];
                                  if (e.target.checked) {
                                    updateSymptoms(category, [...currentSymptoms, symptom]);
                                  } else {
                                    updateSymptoms(category, currentSymptoms.filter(s => s !== symptom));
                                  }
                                }}
                              />
                            }
                            label={symptom}
                          />
                        ))}
                      </FormGroup>
                    </Box>
                  ))}

                  <Box mt={2} display="flex" gap={1}>
                    <Button onClick={() => setActiveStep(2)}>이전</Button>
                    <Button variant="contained" onClick={() => setActiveStep(4)}>
                      다음
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 5: 작업 환경 */}
              <Step>
                <StepLabel>작업 환경</StepLabel>
                <StepContent>
                  <Typography variant="subtitle2" gutterBottom>노출 유해인자</Typography>
                  <FormGroup row sx={{ mb: 2 }}>
                    {harmfulFactorOptions.map(factor => (
                      <FormControlLabel
                        key={factor}
                        control={
                          <Checkbox
                            checked={formData.work_environment?.harmful_factors?.includes(factor) || false}
                            onChange={(e) => {
                              const factors = formData.work_environment?.harmful_factors || [];
                              if (e.target.checked) {
                                updateWorkEnvironment('harmful_factors', [...factors, factor]);
                              } else {
                                updateWorkEnvironment('harmful_factors', factors.filter(f => f !== factor));
                              }
                            }}
                          />
                        }
                        label={factor}
                      />
                    ))}
                  </FormGroup>

                  <Grid container spacing={2}>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="일일 근무시간"
                        type="number"
                        value={formData.work_environment?.work_hours?.day || 8}
                        onChange={(e) => updateWorkEnvironment('work_hours', {
                          ...formData.work_environment?.work_hours,
                          day: Number(e.target.value)
                        })}
                      />
                    </Grid>
                    <Grid item xs={12} md={6}>
                      <TextField
                        fullWidth
                        label="주간 초과근무 시간"
                        type="number"
                        value={formData.work_environment?.work_hours?.overtime || 0}
                        onChange={(e) => updateWorkEnvironment('work_hours', {
                          ...formData.work_environment?.work_hours,
                          overtime: Number(e.target.value)
                        })}
                      />
                    </Grid>
                    <Grid item xs={12}>
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={formData.work_environment?.shift_work || false}
                            onChange={(e) => updateWorkEnvironment('shift_work', e.target.checked)}
                          />
                        }
                        label="교대근무 여부"
                      />
                    </Grid>
                  </Grid>

                  <Box mt={2} display="flex" gap={1}>
                    <Button onClick={() => setActiveStep(3)}>이전</Button>
                    <Button variant="contained" onClick={() => setActiveStep(5)}>
                      다음
                    </Button>
                  </Box>
                </StepContent>
              </Step>

              {/* Step 6: 확인 및 제출 */}
              <Step>
                <StepLabel>확인 및 제출</StepLabel>
                <StepContent>
                  <Card variant="outlined" sx={{ mb: 2 }}>
                    <CardContent>
                      <Typography variant="h6" gutterBottom>문진표 요약</Typography>
                      
                      <Grid container spacing={2}>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" color="text.secondary">검진일</Typography>
                          <Typography variant="body2" gutterBottom>
                            {formData.exam_date && format(new Date(formData.exam_date), 'yyyy년 MM월 dd일')}
                          </Typography>
                        </Grid>
                        <Grid item xs={12} md={6}>
                          <Typography variant="subtitle2" color="text.secondary">검진 종류</Typography>
                          <Typography variant="body2" gutterBottom>{formData.exam_type}</Typography>
                        </Grid>
                      </Grid>

                      <Divider sx={{ my: 2 }} />

                      {/* 과거 병력 요약 */}
                      {formData.medical_history?.past_diseases?.length! > 0 && (
                        <Box mb={2}>
                          <Typography variant="subtitle2" color="text.secondary">과거 질병</Typography>
                          <Box display="flex" flexWrap="wrap" gap={0.5} mt={1}>
                            {formData.medical_history?.past_diseases?.map(disease => (
                              <Chip key={disease} label={disease} size="small" />
                            ))}
                          </Box>
                        </Box>
                      )}

                      {/* 생활습관 요약 */}
                      <Grid container spacing={1}>
                        <Grid item xs={6} md={3}>
                          <Typography variant="caption" color="text.secondary">흡연</Typography>
                          <Typography variant="body2">
                            {formData.lifestyle_habits?.smoking?.status === 'never' ? '비흡연' :
                             formData.lifestyle_habits?.smoking?.status === 'past' ? '과거흡연' : '현재흡연'}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="caption" color="text.secondary">음주</Typography>
                          <Typography variant="body2">
                            {formData.lifestyle_habits?.drinking?.frequency === 'never' ? '안함' :
                             formData.lifestyle_habits?.drinking?.frequency}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="caption" color="text.secondary">운동</Typography>
                          <Typography variant="body2">
                            {formData.lifestyle_habits?.exercise?.frequency === 'never' ? '안함' :
                             formData.lifestyle_habits?.exercise?.frequency}
                          </Typography>
                        </Grid>
                        <Grid item xs={6} md={3}>
                          <Typography variant="caption" color="text.secondary">수면</Typography>
                          <Typography variant="body2">
                            {formData.lifestyle_habits?.sleep?.hours}시간
                          </Typography>
                        </Grid>
                      </Grid>
                    </CardContent>
                  </Card>

                  <Alert severity="info" sx={{ mb: 2 }}>
                    작성하신 문진표는 건강검진 시 참고자료로 활용됩니다.
                    정확한 정보를 기입해 주시기 바랍니다.
                  </Alert>

                  <Box display="flex" gap={1}>
                    <Button onClick={() => setActiveStep(4)}>이전</Button>
                    <Button
                      variant="contained"
                      startIcon={<SaveIcon />}
                      onClick={handleSubmit}
                    >
                      문진표 저장
                    </Button>
                    <Button
                      variant="outlined"
                      startIcon={<PrintIcon />}
                      onClick={() => window.print()}
                    >
                      출력
                    </Button>
                  </Box>
                </StepContent>
              </Step>
            </Stepper>
          </Paper>
        </Grid>
      </Grid>
    </Box>
  );
}