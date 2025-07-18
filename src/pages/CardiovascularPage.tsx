import React, { useState, useEffect } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Alert, AlertDescription, AlertTitle } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Calendar } from "@/components/ui/calendar";
import { Checkbox } from "@/components/ui/checkbox";
import { 
  Activity, 
  Heart, 
  AlertCircle, 
  Calendar as CalendarIcon,
  Clock,
  User,
  FileText,
  CheckCircle2,
  XCircle,
  BookOpen,
  Stethoscope,
  AlertTriangle,
  TrendingUp
} from 'lucide-react';
import { format } from 'date-fns';
import { ko } from 'date-fns/locale';
import { toast } from "@/components/ui/use-toast";

// API 설정
const API_BASE = '/api/v1/cardiovascular';

// 타입 정의
interface RiskCalculationRequest {
  age: number;
  gender: string;
  systolic_bp: number;
  cholesterol: number;
  smoking: boolean;
  diabetes: boolean;
  hypertension: boolean;
}

interface RiskCalculationResponse {
  risk_score: number;
  risk_level: string;
  ten_year_risk: number;
  recommendations: string[];
  next_assessment_months: number;
}

interface CardiovascularAssessment {
  id: string;
  worker_id: string;
  assessment_date: string;
  age: number;
  gender: string;
  smoking: boolean;
  diabetes: boolean;
  hypertension: boolean;
  family_history: boolean;
  obesity: boolean;
  systolic_bp: number;
  diastolic_bp: number;
  cholesterol: number;
  ldl_cholesterol?: number;
  hdl_cholesterol?: number;
  triglycerides?: number;
  blood_sugar?: number;
  bmi?: number;
  risk_score: number;
  risk_level: string;
  ten_year_risk: number;
  recommendations: string[];
  follow_up_date?: string;
  assessed_by: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

interface MonitoringSchedule {
  id: string;
  worker_id: string;
  monitoring_type: string;
  scheduled_date: string;
  actual_date?: string;
  systolic_bp?: number;
  diastolic_bp?: number;
  heart_rate?: number;
  is_completed: boolean;
  is_normal?: boolean;
  abnormal_findings?: string;
  action_required: boolean;
  monitored_by?: string;
  location?: string;
  equipment_used?: string;
  notes?: string;
  next_monitoring_date?: string;
  created_at: string;
  updated_at: string;
}

interface PreventionEducation {
  id: string;
  title: string;
  description?: string;
  target_audience?: string;
  education_type?: string;
  scheduled_date: string;
  duration_minutes?: number;
  location?: string;
  curriculum?: string[];
  materials?: string[];
  learning_objectives?: string[];
  target_participants?: number;
  actual_participants?: number;
  participant_list?: string[];
  instructor?: string;
  organizer?: string;
  is_completed: boolean;
  effectiveness_score?: number;
  created_at: string;
  updated_at: string;
}

interface Statistics {
  total_assessments: number;
  high_risk_count: number;
  moderate_risk_count: number;
  low_risk_count: number;
  active_monitoring: number;
  overdue_monitoring: number;
  completed_this_month: number;
  emergency_cases_this_month: number;
  emergency_response_time_avg?: number;
  scheduled_education: number;
  completed_education: number;
  education_effectiveness_avg?: number;
  by_risk_level: Record<string, number>;
}

const CardiovascularPage: React.FC = () => {
  // 상태 관리
  const [activeTab, setActiveTab] = useState('risk-calculator');
  const [loading, setLoading] = useState(false);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [assessments, setAssessments] = useState<CardiovascularAssessment[]>([]);
  const [monitoringSchedules, setMonitoringSchedules] = useState<MonitoringSchedule[]>([]);
  const [educationPrograms, setEducationPrograms] = useState<PreventionEducation[]>([]);
  
  // 위험도 계산 폼 상태
  const [riskForm, setRiskForm] = useState<RiskCalculationRequest>({
    age: 40,
    gender: 'male',
    systolic_bp: 120,
    cholesterol: 180,
    smoking: false,
    diabetes: false,
    hypertension: false
  });
  
  const [calculationResult, setCalculationResult] = useState<RiskCalculationResponse | null>(null);

  // 평가 생성 폼 상태
  const [assessmentForm, setAssessmentForm] = useState({
    worker_id: '',
    age: 40,
    gender: 'male',
    smoking: false,
    diabetes: false,
    hypertension: false,
    family_history: false,
    obesity: false,
    systolic_bp: 120,
    diastolic_bp: 80,
    cholesterol: 180,
    ldl_cholesterol: 100,
    hdl_cholesterol: 50,
    triglycerides: 150,
    blood_sugar: 90,
    bmi: 23,
    notes: ''
  });

  // 모니터링 폼 상태
  const [monitoringForm, setMonitoringForm] = useState({
    worker_id: '',
    monitoring_type: '혈압측정',
    scheduled_date: new Date(),
    systolic_bp: 120,
    diastolic_bp: 80,
    heart_rate: 70,
    location: '보건관리실',
    equipment_used: '',
    notes: ''
  });

  // 교육 프로그램 폼 상태
  const [educationForm, setEducationForm] = useState({
    title: '',
    description: '',
    target_audience: '전체 근로자',
    education_type: '집합교육',
    scheduled_date: new Date(),
    duration_minutes: 60,
    location: '교육실',
    instructor: '',
    organizer: '',
    learning_objectives: ['']
  });

  // 데이터 로딩
  useEffect(() => {
    loadStatistics();
    loadAssessments();
    loadMonitoringSchedules();
    loadEducationPrograms();
  }, []);

  // API 함수들
  const loadStatistics = async () => {
    try {
      const response = await fetch(`${API_BASE}/statistics`);
      if (response.ok) {
        const data = await response.json();
        setStatistics(data);
      }
    } catch (error) {
      console.error('통계 로딩 실패:', error);
    }
  };

  const loadAssessments = async () => {
    try {
      const response = await fetch(`${API_BASE}/assessments/`);
      if (response.ok) {
        const data = await response.json();
        setAssessments(data);
      }
    } catch (error) {
      console.error('평가 목록 로딩 실패:', error);
    }
  };

  const loadMonitoringSchedules = async () => {
    try {
      const response = await fetch(`${API_BASE}/monitoring/`);
      if (response.ok) {
        const data = await response.json();
        setMonitoringSchedules(data);
      }
    } catch (error) {
      console.error('모니터링 스케줄 로딩 실패:', error);
    }
  };

  const loadEducationPrograms = async () => {
    try {
      const response = await fetch(`${API_BASE}/education/`);
      if (response.ok) {
        const data = await response.json();
        setEducationPrograms(data);
      }
    } catch (error) {
      console.error('교육 프로그램 로딩 실패:', error);
    }
  };

  // 위험도 계산
  const calculateRisk = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/risk-calculation`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(riskForm)
      });

      if (response.ok) {
        const data = await response.json();
        setCalculationResult(data);
        toast({
          title: "위험도 계산 완료",
          description: `위험도 수준: ${data.risk_level} (10년 위험도: ${data.ten_year_risk}%)`,
        });
      } else {
        toast({
          title: "계산 실패",
          description: "위험도 계산 중 오류가 발생했습니다.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('위험도 계산 오류:', error);
      toast({
        title: "오류 발생",
        description: "서버 연결에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 평가 생성
  const createAssessment = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/assessments/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(assessmentForm)
      });

      if (response.ok) {
        toast({
          title: "평가 생성 완료",
          description: "뇌심혈관계 위험도 평가가 생성되었습니다.",
        });
        loadAssessments();
        loadStatistics();
        // 폼 초기화
        setAssessmentForm({
          ...assessmentForm,
          worker_id: '',
          notes: ''
        });
      } else {
        toast({
          title: "생성 실패",
          description: "평가 생성 중 오류가 발생했습니다.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('평가 생성 오류:', error);
      toast({
        title: "오류 발생",
        description: "서버 연결에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 모니터링 스케줄 생성
  const createMonitoringSchedule = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/monitoring/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...monitoringForm,
          scheduled_date: monitoringForm.scheduled_date.toISOString()
        })
      });

      if (response.ok) {
        toast({
          title: "모니터링 예약 완료",
          description: "모니터링 일정이 등록되었습니다.",
        });
        loadMonitoringSchedules();
        // 폼 초기화
        setMonitoringForm({
          ...monitoringForm,
          worker_id: '',
          notes: ''
        });
      } else {
        toast({
          title: "예약 실패",
          description: "모니터링 예약 중 오류가 발생했습니다.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('모니터링 예약 오류:', error);
      toast({
        title: "오류 발생",
        description: "서버 연결에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 교육 프로그램 생성
  const createEducationProgram = async () => {
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE}/education/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          ...educationForm,
          scheduled_date: educationForm.scheduled_date.toISOString(),
          learning_objectives: educationForm.learning_objectives.filter(obj => obj.length > 0)
        })
      });

      if (response.ok) {
        toast({
          title: "교육 프로그램 생성 완료",
          description: "예방 교육 프로그램이 등록되었습니다.",
        });
        loadEducationPrograms();
        // 폼 초기화
        setEducationForm({
          ...educationForm,
          title: '',
          description: '',
          learning_objectives: ['']
        });
      } else {
        toast({
          title: "생성 실패",
          description: "교육 프로그램 생성 중 오류가 발생했습니다.",
          variant: "destructive",
        });
      }
    } catch (error) {
      console.error('교육 프로그램 생성 오류:', error);
      toast({
        title: "오류 발생",
        description: "서버 연결에 실패했습니다.",
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  };

  // 위험도 수준별 색상 반환
  const getRiskLevelColor = (level: string) => {
    switch (level) {
      case '낮음': return 'text-green-600 bg-green-50';
      case '보통': return 'text-yellow-600 bg-yellow-50';
      case '높음': return 'text-orange-600 bg-orange-50';
      case '매우높음': return 'text-red-600 bg-red-50';
      default: return 'text-gray-600 bg-gray-50';
    }
  };

  // 위험도 수준별 아이콘 반환
  const getRiskLevelIcon = (level: string) => {
    switch (level) {
      case '낮음': return <CheckCircle2 className="w-5 h-5" />;
      case '보통': return <AlertCircle className="w-5 h-5" />;
      case '높음': return <AlertTriangle className="w-5 h-5" />;
      case '매우높음': return <XCircle className="w-5 h-5" />;
      default: return <AlertCircle className="w-5 h-5" />;
    }
  };

  return (
    <div className="container mx-auto p-6">
      <div className="mb-6">
        <h1 className="text-3xl font-bold flex items-center gap-2">
          <Heart className="w-8 h-8 text-red-500" />
          뇌심혈관계 관리
        </h1>
        <p className="text-gray-600 mt-2">
          근로자의 심혈관 건강을 체계적으로 관리하고 예방합니다
        </p>
      </div>

      {/* 통계 대시보드 */}
      {statistics && (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">전체 평가</CardTitle>
              <Activity className="h-4 w-4 text-muted-foreground" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.total_assessments}</div>
              <p className="text-xs text-muted-foreground">
                총 위험도 평가 건수
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">고위험군</CardTitle>
              <AlertTriangle className="h-4 w-4 text-red-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-red-600">
                {statistics.high_risk_count}
              </div>
              <p className="text-xs text-muted-foreground">
                즉시 관리 필요
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">진행중 모니터링</CardTitle>
              <Stethoscope className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.active_monitoring}</div>
              <p className="text-xs text-muted-foreground">
                지연: {statistics.overdue_monitoring}건
              </p>
            </CardContent>
          </Card>

          <Card>
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium">예방 교육</CardTitle>
              <BookOpen className="h-4 w-4 text-green-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold">{statistics.scheduled_education}</div>
              <p className="text-xs text-muted-foreground">
                완료: {statistics.completed_education}건
              </p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* 메인 탭 */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5">
          <TabsTrigger value="risk-calculator">위험도 계산</TabsTrigger>
          <TabsTrigger value="assessments">평가 관리</TabsTrigger>
          <TabsTrigger value="monitoring">모니터링</TabsTrigger>
          <TabsTrigger value="education">예방 교육</TabsTrigger>
          <TabsTrigger value="emergency">응급 대응</TabsTrigger>
        </TabsList>

        {/* 위험도 계산 탭 */}
        <TabsContent value="risk-calculator">
          <Card>
            <CardHeader>
              <CardTitle>심혈관 위험도 계산기</CardTitle>
              <CardDescription>
                Framingham Risk Score 기반 10년 심혈관 질환 위험도 평가
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div className="space-y-4">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="age">나이</Label>
                      <Input
                        id="age"
                        type="number"
                        value={riskForm.age}
                        onChange={(e) => setRiskForm({...riskForm, age: parseInt(e.target.value)})}
                        min="20"
                        max="80"
                      />
                    </div>
                    <div>
                      <Label htmlFor="gender">성별</Label>
                      <Select
                        value={riskForm.gender}
                        onValueChange={(value) => setRiskForm({...riskForm, gender: value})}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem value="male">남성</SelectItem>
                          <SelectItem value="female">여성</SelectItem>
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <Label htmlFor="systolic_bp">수축기 혈압 (mmHg)</Label>
                      <Input
                        id="systolic_bp"
                        type="number"
                        value={riskForm.systolic_bp}
                        onChange={(e) => setRiskForm({...riskForm, systolic_bp: parseInt(e.target.value)})}
                        min="90"
                        max="200"
                      />
                    </div>
                    <div>
                      <Label htmlFor="cholesterol">총 콜레스테롤 (mg/dL)</Label>
                      <Input
                        id="cholesterol"
                        type="number"
                        value={riskForm.cholesterol}
                        onChange={(e) => setRiskForm({...riskForm, cholesterol: parseInt(e.target.value)})}
                        min="150"
                        max="300"
                      />
                    </div>
                  </div>

                  <div className="space-y-3">
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="smoking"
                        checked={riskForm.smoking}
                        onCheckedChange={(checked) => setRiskForm({...riskForm, smoking: checked as boolean})}
                      />
                      <Label htmlFor="smoking">흡연</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="diabetes"
                        checked={riskForm.diabetes}
                        onCheckedChange={(checked) => setRiskForm({...riskForm, diabetes: checked as boolean})}
                      />
                      <Label htmlFor="diabetes">당뇨병</Label>
                    </div>
                    <div className="flex items-center space-x-2">
                      <Checkbox
                        id="hypertension"
                        checked={riskForm.hypertension}
                        onCheckedChange={(checked) => setRiskForm({...riskForm, hypertension: checked as boolean})}
                      />
                      <Label htmlFor="hypertension">고혈압</Label>
                    </div>
                  </div>

                  <Button 
                    onClick={calculateRisk} 
                    disabled={loading}
                    className="w-full"
                  >
                    위험도 계산
                  </Button>
                </div>

                {/* 계산 결과 */}
                <div>
                  {calculationResult && (
                    <Alert className={getRiskLevelColor(calculationResult.risk_level)}>
                      <div className="flex items-start gap-2">
                        {getRiskLevelIcon(calculationResult.risk_level)}
                        <div className="flex-1">
                          <AlertTitle className="text-lg mb-2">
                            위험도 평가 결과
                          </AlertTitle>
                          <AlertDescription>
                            <div className="space-y-3">
                              <div>
                                <p className="font-semibold">위험도 수준: {calculationResult.risk_level}</p>
                                <p>위험도 점수: {calculationResult.risk_score}점</p>
                                <p className="text-lg font-bold mt-2">
                                  10년 내 심혈관 질환 발생 위험도: {calculationResult.ten_year_risk}%
                                </p>
                              </div>
                              
                              <div>
                                <p className="font-semibold mb-1">권고사항:</p>
                                <ul className="list-disc list-inside space-y-1">
                                  {calculationResult.recommendations.map((rec, idx) => (
                                    <li key={idx}>{rec}</li>
                                  ))}
                                </ul>
                              </div>
                              
                              <div className="pt-2 border-t">
                                <p className="text-sm">
                                  다음 평가 예정: {calculationResult.next_assessment_months}개월 후
                                </p>
                              </div>
                            </div>
                          </AlertDescription>
                        </div>
                      </div>
                    </Alert>
                  )}
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>

        {/* 평가 관리 탭 */}
        <TabsContent value="assessments">
          <div className="space-y-6">
            {/* 새 평가 생성 폼 */}
            <Card>
              <CardHeader>
                <CardTitle>새 위험도 평가 등록</CardTitle>
                <CardDescription>
                  근로자의 심혈관 위험도를 종합적으로 평가합니다
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="worker_id">근로자 ID</Label>
                    <Input
                      id="worker_id"
                      value={assessmentForm.worker_id}
                      onChange={(e) => setAssessmentForm({...assessmentForm, worker_id: e.target.value})}
                      placeholder="근로자 ID 입력"
                    />
                  </div>
                  <div>
                    <Label htmlFor="age">나이</Label>
                    <Input
                      id="age"
                      type="number"
                      value={assessmentForm.age}
                      onChange={(e) => setAssessmentForm({...assessmentForm, age: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label htmlFor="gender">성별</Label>
                    <Select
                      value={assessmentForm.gender}
                      onValueChange={(value) => setAssessmentForm({...assessmentForm, gender: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">남성</SelectItem>
                        <SelectItem value="female">여성</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div>
                    <Label>수축기 혈압</Label>
                    <Input
                      type="number"
                      value={assessmentForm.systolic_bp}
                      onChange={(e) => setAssessmentForm({...assessmentForm, systolic_bp: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>이완기 혈압</Label>
                    <Input
                      type="number"
                      value={assessmentForm.diastolic_bp}
                      onChange={(e) => setAssessmentForm({...assessmentForm, diastolic_bp: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>총 콜레스테롤</Label>
                    <Input
                      type="number"
                      value={assessmentForm.cholesterol}
                      onChange={(e) => setAssessmentForm({...assessmentForm, cholesterol: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>BMI</Label>
                    <Input
                      type="number"
                      step="0.1"
                      value={assessmentForm.bmi}
                      onChange={(e) => setAssessmentForm({...assessmentForm, bmi: parseFloat(e.target.value)})}
                    />
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mt-4">
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={assessmentForm.smoking}
                      onCheckedChange={(checked) => setAssessmentForm({...assessmentForm, smoking: checked as boolean})}
                    />
                    <Label>흡연</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={assessmentForm.diabetes}
                      onCheckedChange={(checked) => setAssessmentForm({...assessmentForm, diabetes: checked as boolean})}
                    />
                    <Label>당뇨병</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={assessmentForm.hypertension}
                      onCheckedChange={(checked) => setAssessmentForm({...assessmentForm, hypertension: checked as boolean})}
                    />
                    <Label>고혈압</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={assessmentForm.family_history}
                      onCheckedChange={(checked) => setAssessmentForm({...assessmentForm, family_history: checked as boolean})}
                    />
                    <Label>가족력</Label>
                  </div>
                  <div className="flex items-center space-x-2">
                    <Checkbox
                      checked={assessmentForm.obesity}
                      onCheckedChange={(checked) => setAssessmentForm({...assessmentForm, obesity: checked as boolean})}
                    />
                    <Label>비만</Label>
                  </div>
                </div>

                <div className="mt-4">
                  <Label htmlFor="notes">특이사항</Label>
                  <Input
                    id="notes"
                    value={assessmentForm.notes}
                    onChange={(e) => setAssessmentForm({...assessmentForm, notes: e.target.value})}
                    placeholder="특이사항 입력"
                  />
                </div>

                <Button 
                  onClick={createAssessment} 
                  disabled={loading || !assessmentForm.worker_id}
                  className="mt-4"
                >
                  평가 등록
                </Button>
              </CardContent>
            </Card>

            {/* 평가 목록 */}
            <Card>
              <CardHeader>
                <CardTitle>최근 평가 내역</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {assessments.map((assessment) => (
                    <div key={assessment.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-4 mb-2">
                            <p className="font-semibold">근로자 ID: {assessment.worker_id}</p>
                            <Badge className={getRiskLevelColor(assessment.risk_level)}>
                              {assessment.risk_level}
                            </Badge>
                            <span className="text-sm text-gray-500">
                              {format(new Date(assessment.assessment_date), 'yyyy-MM-dd', { locale: ko })}
                            </span>
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500">나이/성별</p>
                              <p>{assessment.age}세 / {assessment.gender === 'male' ? '남성' : '여성'}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">혈압</p>
                              <p>{assessment.systolic_bp}/{assessment.diastolic_bp} mmHg</p>
                            </div>
                            <div>
                              <p className="text-gray-500">콜레스테롤</p>
                              <p>{assessment.cholesterol} mg/dL</p>
                            </div>
                            <div>
                              <p className="text-gray-500">10년 위험도</p>
                              <p className="font-semibold">{assessment.ten_year_risk}%</p>
                            </div>
                          </div>
                          {assessment.recommendations && assessment.recommendations.length > 0 && (
                            <div className="mt-2">
                              <p className="text-sm text-gray-500">권고사항:</p>
                              <p className="text-sm">{assessment.recommendations.join(', ')}</p>
                            </div>
                          )}
                        </div>
                        <div className="text-right">
                          <TrendingUp className="w-5 h-5 text-gray-400" />
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 모니터링 탭 */}
        <TabsContent value="monitoring">
          <div className="space-y-6">
            {/* 새 모니터링 예약 */}
            <Card>
              <CardHeader>
                <CardTitle>모니터링 일정 등록</CardTitle>
                <CardDescription>
                  정기적인 건강 모니터링 일정을 예약합니다
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                  <div>
                    <Label htmlFor="monitoring_worker_id">근로자 ID</Label>
                    <Input
                      id="monitoring_worker_id"
                      value={monitoringForm.worker_id}
                      onChange={(e) => setMonitoringForm({...monitoringForm, worker_id: e.target.value})}
                      placeholder="근로자 ID 입력"
                    />
                  </div>
                  <div>
                    <Label htmlFor="monitoring_type">모니터링 유형</Label>
                    <Select
                      value={monitoringForm.monitoring_type}
                      onValueChange={(value) => setMonitoringForm({...monitoringForm, monitoring_type: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="혈압측정">혈압측정</SelectItem>
                        <SelectItem value="심박수">심박수</SelectItem>
                        <SelectItem value="심전도">심전도</SelectItem>
                        <SelectItem value="혈액검사">혈액검사</SelectItem>
                        <SelectItem value="스트레스검사">스트레스검사</SelectItem>
                        <SelectItem value="상담">상담</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                  <div>
                    <Label>예정일</Label>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal"
                      onClick={() => {/* Calendar picker implementation */}}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {format(monitoringForm.scheduled_date, 'yyyy-MM-dd')}
                    </Button>
                  </div>
                </div>

                <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4">
                  <div>
                    <Label>장소</Label>
                    <Input
                      value={monitoringForm.location}
                      onChange={(e) => setMonitoringForm({...monitoringForm, location: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>사용 장비</Label>
                    <Input
                      value={monitoringForm.equipment_used}
                      onChange={(e) => setMonitoringForm({...monitoringForm, equipment_used: e.target.value})}
                      placeholder="선택사항"
                    />
                  </div>
                  <div className="col-span-2">
                    <Label>특이사항</Label>
                    <Input
                      value={monitoringForm.notes}
                      onChange={(e) => setMonitoringForm({...monitoringForm, notes: e.target.value})}
                      placeholder="선택사항"
                    />
                  </div>
                </div>

                <Button 
                  onClick={createMonitoringSchedule} 
                  disabled={loading || !monitoringForm.worker_id}
                  className="mt-4"
                >
                  모니터링 예약
                </Button>
              </CardContent>
            </Card>

            {/* 모니터링 목록 */}
            <Card>
              <CardHeader>
                <CardTitle>모니터링 일정</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {monitoringSchedules.map((schedule) => (
                    <div key={schedule.id} className="border rounded-lg p-4">
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-4 mb-2">
                            <p className="font-semibold">근로자 ID: {schedule.worker_id}</p>
                            <Badge variant={schedule.is_completed ? "default" : "outline"}>
                              {schedule.monitoring_type}
                            </Badge>
                            {schedule.is_completed ? (
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                            ) : (
                              <Clock className="w-4 h-4 text-gray-400" />
                            )}
                          </div>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500">예정일</p>
                              <p>{format(new Date(schedule.scheduled_date), 'yyyy-MM-dd')}</p>
                            </div>
                            {schedule.actual_date && (
                              <div>
                                <p className="text-gray-500">실시일</p>
                                <p>{format(new Date(schedule.actual_date), 'yyyy-MM-dd')}</p>
                              </div>
                            )}
                            <div>
                              <p className="text-gray-500">장소</p>
                              <p>{schedule.location || '-'}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">상태</p>
                              <p>{schedule.is_completed ? '완료' : '예정'}</p>
                            </div>
                          </div>
                          {schedule.abnormal_findings && (
                            <Alert className="mt-2">
                              <AlertTriangle className="h-4 w-4" />
                              <AlertDescription>
                                이상 소견: {schedule.abnormal_findings}
                              </AlertDescription>
                            </Alert>
                          )}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 예방 교육 탭 */}
        <TabsContent value="education">
          <div className="space-y-6">
            {/* 새 교육 프로그램 생성 */}
            <Card>
              <CardHeader>
                <CardTitle>예방 교육 프로그램 등록</CardTitle>
                <CardDescription>
                  심혈관 질환 예방을 위한 교육 프로그램을 관리합니다
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="education_title">교육명</Label>
                    <Input
                      id="education_title"
                      value={educationForm.title}
                      onChange={(e) => setEducationForm({...educationForm, title: e.target.value})}
                      placeholder="교육 프로그램 제목"
                    />
                  </div>
                  <div>
                    <Label htmlFor="education_type">교육 유형</Label>
                    <Select
                      value={educationForm.education_type}
                      onValueChange={(value) => setEducationForm({...educationForm, education_type: value})}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="집합교육">집합교육</SelectItem>
                        <SelectItem value="온라인교육">온라인교육</SelectItem>
                        <SelectItem value="개별상담">개별상담</SelectItem>
                        <SelectItem value="워크샵">워크샵</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div>
                    <Label>예정일</Label>
                    <Button
                      variant="outline"
                      className="w-full justify-start text-left font-normal"
                      onClick={() => {/* Calendar picker implementation */}}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {format(educationForm.scheduled_date, 'yyyy-MM-dd')}
                    </Button>
                  </div>
                  <div>
                    <Label>교육시간 (분)</Label>
                    <Input
                      type="number"
                      value={educationForm.duration_minutes}
                      onChange={(e) => setEducationForm({...educationForm, duration_minutes: parseInt(e.target.value)})}
                    />
                  </div>
                  <div>
                    <Label>장소</Label>
                    <Input
                      value={educationForm.location}
                      onChange={(e) => setEducationForm({...educationForm, location: e.target.value})}
                    />
                  </div>
                </div>

                <div className="mt-4">
                  <Label htmlFor="education_description">교육 설명</Label>
                  <Input
                    id="education_description"
                    value={educationForm.description}
                    onChange={(e) => setEducationForm({...educationForm, description: e.target.value})}
                    placeholder="교육 내용 및 목적"
                  />
                </div>

                <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mt-4">
                  <div>
                    <Label>대상자</Label>
                    <Input
                      value={educationForm.target_audience}
                      onChange={(e) => setEducationForm({...educationForm, target_audience: e.target.value})}
                    />
                  </div>
                  <div>
                    <Label>강사</Label>
                    <Input
                      value={educationForm.instructor}
                      onChange={(e) => setEducationForm({...educationForm, instructor: e.target.value})}
                      placeholder="강사명"
                    />
                  </div>
                  <div>
                    <Label>주관자</Label>
                    <Input
                      value={educationForm.organizer}
                      onChange={(e) => setEducationForm({...educationForm, organizer: e.target.value})}
                      placeholder="주관 부서/담당자"
                    />
                  </div>
                </div>

                <Button 
                  onClick={createEducationProgram} 
                  disabled={loading || !educationForm.title}
                  className="mt-4"
                >
                  교육 프로그램 등록
                </Button>
              </CardContent>
            </Card>

            {/* 교육 프로그램 목록 */}
            <Card>
              <CardHeader>
                <CardTitle>교육 프로그램 일정</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {educationPrograms.map((program) => (
                    <div key={program.id} className="border rounded-lg p-4">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center gap-4 mb-2">
                            <p className="font-semibold">{program.title}</p>
                            <Badge variant={program.is_completed ? "default" : "outline"}>
                              {program.education_type}
                            </Badge>
                            {program.is_completed && (
                              <CheckCircle2 className="w-4 h-4 text-green-500" />
                            )}
                          </div>
                          <p className="text-sm text-gray-600 mb-2">{program.description}</p>
                          <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                            <div>
                              <p className="text-gray-500">예정일</p>
                              <p>{format(new Date(program.scheduled_date), 'yyyy-MM-dd')}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">교육시간</p>
                              <p>{program.duration_minutes}분</p>
                            </div>
                            <div>
                              <p className="text-gray-500">대상</p>
                              <p>{program.target_audience}</p>
                            </div>
                            <div>
                              <p className="text-gray-500">장소</p>
                              <p>{program.location}</p>
                            </div>
                          </div>
                          {program.is_completed && program.effectiveness_score && (
                            <div className="mt-2">
                              <p className="text-sm text-gray-500">효과성 평가</p>
                              <Progress value={program.effectiveness_score * 20} className="w-32" />
                            </div>
                          )}
                        </div>
                        <BookOpen className="w-5 h-5 text-gray-400" />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        {/* 응급 대응 탭 */}
        <TabsContent value="emergency">
          <Card>
            <CardHeader>
              <CardTitle>응급상황 대응 체계</CardTitle>
              <CardDescription>
                심혈관 응급상황 발생 시 대응 절차 및 기록 관리
              </CardDescription>
            </CardHeader>
            <CardContent>
              <Alert>
                <AlertTriangle className="h-4 w-4" />
                <AlertTitle>응급상황 대응 절차</AlertTitle>
                <AlertDescription>
                  <ol className="list-decimal list-inside space-y-2 mt-2">
                    <li>119 신고 및 응급실 연락</li>
                    <li>기본 응급처치 시행 (CPR, AED 사용)</li>
                    <li>생체징후 모니터링 및 기록</li>
                    <li>병원 이송 준비 및 동행</li>
                    <li>사고 경위 및 대응 내용 상세 기록</li>
                    <li>후속 조치 계획 수립</li>
                  </ol>
                </AlertDescription>
              </Alert>

              <div className="mt-6">
                <h3 className="text-lg font-semibold mb-4">최근 응급상황 대응 기록</h3>
                {statistics && statistics.emergency_cases_this_month > 0 ? (
                  <div className="space-y-4">
                    <Alert className="border-red-200">
                      <AlertCircle className="h-4 w-4 text-red-600" />
                      <AlertTitle>이달 응급상황 발생</AlertTitle>
                      <AlertDescription>
                        <p>발생 건수: {statistics.emergency_cases_this_month}건</p>
                        {statistics.emergency_response_time_avg && (
                          <p>평균 대응시간: {statistics.emergency_response_time_avg}분</p>
                        )}
                      </AlertDescription>
                    </Alert>
                  </div>
                ) : (
                  <p className="text-gray-500 text-center py-8">
                    이달 응급상황 발생 기록이 없습니다
                  </p>
                )}
              </div>

              <div className="mt-6 p-4 bg-gray-50 rounded-lg">
                <h4 className="font-semibold mb-2">응급 연락처</h4>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                  <div>
                    <p className="text-gray-600">응급실</p>
                    <p className="font-medium">119</p>
                  </div>
                  <div>
                    <p className="text-gray-600">산업보건의</p>
                    <p className="font-medium">내선 1234</p>
                  </div>
                  <div>
                    <p className="text-gray-600">보건관리자</p>
                    <p className="font-medium">010-1234-5678</p>
                  </div>
                  <div>
                    <p className="text-gray-600">협력병원</p>
                    <p className="font-medium">02-1234-5678</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
};

export default CardiovascularPage;