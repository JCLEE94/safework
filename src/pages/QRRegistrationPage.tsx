import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
// Temporary UI components replacement
const Card = ({ children, className = "" }: any) => <div className={`bg-white rounded-lg shadow-md ${className}`}>{children}</div>;
const CardContent = ({ children, className = "" }: any) => <div className={`p-6 ${className}`}>{children}</div>;
const CardDescription = ({ children, className = "" }: any) => <p className={`text-gray-600 text-sm ${className}`}>{children}</p>;
const CardHeader = ({ children, className = "" }: any) => <div className={`p-6 pb-2 ${className}`}>{children}</div>;
const CardTitle = ({ children, className = "" }: any) => <h3 className={`text-lg font-semibold ${className}`}>{children}</h3>;
const Button = ({ children, className = "", type = "button", disabled = false, size = "", ...props }: any) => (
  <button type={type} disabled={disabled} className={`px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50 ${className}`} {...props}>{children}</button>
);
const Input = ({ className = "", ...props }: any) => <input className={`border rounded px-3 py-2 w-full ${className}`} {...props} />;
const Label = ({ children, className = "", htmlFor }: any) => <label htmlFor={htmlFor} className={`block text-sm font-medium mb-1 ${className}`}>{children}</label>;
const Select = ({ children, value, onValueChange }: any) => <div className="relative">{children}</div>;
const SelectContent = ({ children }: any) => <div>{children}</div>;
const SelectItem = ({ children, value }: any) => <option value={value}>{children}</option>;
const SelectTrigger = ({ children }: any) => <div className="border rounded px-3 py-2 w-full bg-white">{children}</div>;
const SelectValue = ({ placeholder }: any) => <span className="text-gray-400">{placeholder}</span>;
const Alert = ({ children, variant, className = "" }: any) => <div className={`p-4 rounded border ${variant === 'destructive' ? 'bg-red-50 border-red-200' : 'bg-blue-50 border-blue-200'} ${className}`}>{children}</div>;
const AlertDescription = ({ children }: any) => <div>{children}</div>;
const AlertTitle = ({ children }: any) => <div className="font-semibold mb-1">{children}</div>;
const Badge = ({ children, variant, className = "" }: any) => <span className={`px-2 py-1 text-xs rounded ${variant === 'outline' ? 'border' : 'bg-gray-200'} ${className}`}>{children}</span>;
import { 
  QrCode, 
  CheckCircle2, 
  AlertCircle, 
  User,
  Building,
  Clock,
  Phone,
  Mail,
  Calendar
} from 'lucide-react';
// Temporary toast replacement
const toast = ({ title, description, variant }: any) => {
  console.log(`Toast: ${title} - ${description}`);
  alert(`${title}: ${description}`);
};

// API 설정
const API_BASE = '/api/v1/qr-registration';

// 타입 정의
interface TokenInfo {
  id: string;
  department: string;
  position: string;
  worker_data: {
    name?: string;
    phone?: string;
    email?: string;
    emergency_contact?: string;
    [key: string]: any;
  };
  expires_at: string;
  status: string;
}

interface WorkerFormData {
  name: string;
  phone: string;
  email: string;
  birth_date: string;
  gender: string;
  address: string;
  emergency_contact: string;
  emergency_relationship: string;
  work_type: string;
  employment_type: string;
  hire_date: string;
  health_status: string;
}

export function QRRegistrationPage() {
  const { token } = useParams<{ token: string }>();
  const [searchParams] = useSearchParams();
  
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [tokenInfo, setTokenInfo] = useState<TokenInfo | null>(null);
  const [isValid, setIsValid] = useState(false);
  const [completed, setCompleted] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [formData, setFormData] = useState<WorkerFormData>({
    name: '',
    phone: '',
    email: '',
    birth_date: '',
    gender: '',
    address: '',
    emergency_contact: '',
    emergency_relationship: '',
    work_type: '',
    employment_type: 'regular',
    hire_date: new Date().toISOString().split('T')[0],
    health_status: 'normal'
  });

  // 토큰 검증
  useEffect(() => {
    if (token) {
      validateToken();
    } else {
      setError('유효하지 않은 QR 코드입니다.');
      setLoading(false);
    }
  }, [token]);

  const validateToken = async () => {
    try {
      const response = await fetch(`${API_BASE}/validate/${token}`);
      const data = await response.json();
      
      if (data.valid && data.token_info) {
        setIsValid(true);
        setTokenInfo(data.token_info);
        
        // 기존 데이터로 폼 초기화
        const workerData = data.token_info.worker_data || {};
        setFormData(prev => ({
          ...prev,
          name: workerData.name || '',
          phone: workerData.phone || '',
          email: workerData.email || '',
          emergency_contact: workerData.emergency_contact || ''
        }));
      } else {
        setError(data.message || '유효하지 않은 토큰입니다.');
      }
    } catch (err) {
      setError('토큰 검증 중 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);

    try {
      const response = await fetch(`${API_BASE}/complete`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          token: token,
          worker_data: formData
        }),
      });

      const data = await response.json();

      if (response.ok && data.success) {
        setCompleted(true);
        toast({
          title: "등록 완료",
          description: "근로자 등록이 성공적으로 완료되었습니다.",
        });
      } else {
        throw new Error(data.detail || '등록 처리 중 오류가 발생했습니다.');
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : '등록 중 오류가 발생했습니다.');
      toast({
        title: "등록 실패",
        description: err instanceof Error ? err.message : '등록 중 오류가 발생했습니다.',
        variant: "destructive",
      });
    } finally {
      setSubmitting(false);
    }
  };

  const handleInputChange = (field: keyof WorkerFormData, value: string) => {
    setFormData(prev => ({
      ...prev,
      [field]: value
    }));
  };

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardContent className="pt-6">
            <div className="flex items-center justify-center space-x-2">
              <QrCode className="h-6 w-6 animate-pulse" />
              <span>QR 코드 확인 중...</span>
            </div>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (error || !isValid) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-red-50 to-pink-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <AlertCircle className="h-6 w-6 text-red-500" />
              <CardTitle className="text-red-700">QR 코드 오류</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertTitle>등록할 수 없습니다</AlertTitle>
              <AlertDescription>{error}</AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  if (completed) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-100 flex items-center justify-center p-4">
        <Card className="w-full max-w-md">
          <CardHeader>
            <div className="flex items-center space-x-2">
              <CheckCircle2 className="h-6 w-6 text-green-500" />
              <CardTitle className="text-green-700">등록 완료</CardTitle>
            </div>
          </CardHeader>
          <CardContent>
            <Alert>
              <CheckCircle2 className="h-4 w-4" />
              <AlertTitle>환영합니다!</AlertTitle>
              <AlertDescription>
                근로자 등록이 성공적으로 완료되었습니다. 
                곧 관리자로부터 계정 정보를 받으실 수 있습니다.
              </AlertDescription>
            </Alert>
          </CardContent>
        </Card>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-100 p-4">
      <div className="max-w-2xl mx-auto">
        <Card>
          <CardHeader>
            <div className="flex items-center space-x-2">
              <User className="h-6 w-6 text-blue-600" />
              <CardTitle>근로자 등록</CardTitle>
            </div>
            <CardDescription>
              QR 코드를 통한 근로자 정보 등록을 진행합니다.
            </CardDescription>
          </CardHeader>
          <CardContent>
            {/* 토큰 정보 표시 */}
            <div className="mb-6 p-4 bg-blue-50 rounded-lg">
              <div className="flex items-center justify-between mb-2">
                <h3 className="font-semibold text-blue-800">등록 정보</h3>
                <Badge variant="outline">{tokenInfo?.status}</Badge>
              </div>
              <div className="grid grid-cols-2 gap-4 text-sm">
                <div className="flex items-center space-x-2">
                  <Building className="h-4 w-4 text-blue-600" />
                  <span>부서: {tokenInfo?.department}</span>
                </div>
                <div className="flex items-center space-x-2">
                  <User className="h-4 w-4 text-blue-600" />
                  <span>직급: {tokenInfo?.position}</span>
                </div>
                <div className="flex items-center space-x-2 col-span-2">
                  <Clock className="h-4 w-4 text-blue-600" />
                  <span>만료: {tokenInfo ? new Date(tokenInfo.expires_at).toLocaleString('ko-KR') : ''}</span>
                </div>
              </div>
            </div>

            {/* 등록 폼 */}
            <form onSubmit={handleSubmit} className="space-y-6">
              {/* 기본 정보 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">기본 정보</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="name">성명 *</Label>
                    <Input
                      id="name"
                      value={formData.name}
                      onChange={(e) => handleInputChange('name', e.target.value)}
                      placeholder="성명을 입력하세요"
                      required
                    />
                  </div>
                  
                  <div>
                    <Label htmlFor="phone">연락처 *</Label>
                    <Input
                      id="phone"
                      value={formData.phone}
                      onChange={(e) => handleInputChange('phone', e.target.value)}
                      placeholder="010-0000-0000"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="email">이메일</Label>
                    <Input
                      id="email"
                      type="email"
                      value={formData.email}
                      onChange={(e) => handleInputChange('email', e.target.value)}
                      placeholder="이메일을 입력하세요"
                    />
                  </div>

                  <div>
                    <Label htmlFor="birth_date">생년월일 *</Label>
                    <Input
                      id="birth_date"
                      type="date"
                      value={formData.birth_date}
                      onChange={(e) => handleInputChange('birth_date', e.target.value)}
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="gender">성별 *</Label>
                    <Select
                      value={formData.gender}
                      onValueChange={(value) => handleInputChange('gender', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="성별 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="male">남성</SelectItem>
                        <SelectItem value="female">여성</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="work_type">업무 유형 *</Label>
                    <Select
                      value={formData.work_type}
                      onValueChange={(value) => handleInputChange('work_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="업무 유형 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="construction">건설</SelectItem>
                        <SelectItem value="electrical">전기</SelectItem>
                        <SelectItem value="plumbing">배관</SelectItem>
                        <SelectItem value="painting">도장</SelectItem>
                        <SelectItem value="welding">용접</SelectItem>
                        <SelectItem value="rebar">철근</SelectItem>
                        <SelectItem value="concrete">콘크리트</SelectItem>
                        <SelectItem value="masonry">조적</SelectItem>
                        <SelectItem value="tiling">타일</SelectItem>
                        <SelectItem value="waterproofing">방수</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>

                <div>
                  <Label htmlFor="address">주소</Label>
                  <Input
                    id="address"
                    value={formData.address}
                    onChange={(e) => handleInputChange('address', e.target.value)}
                    placeholder="주소를 입력하세요"
                  />
                </div>
              </div>

              {/* 비상 연락처 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">비상 연락처</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="emergency_contact">비상 연락처 *</Label>
                    <Input
                      id="emergency_contact"
                      value={formData.emergency_contact}
                      onChange={(e) => handleInputChange('emergency_contact', e.target.value)}
                      placeholder="010-0000-0000"
                      required
                    />
                  </div>

                  <div>
                    <Label htmlFor="emergency_relationship">관계</Label>
                    <Select
                      value={formData.emergency_relationship}
                      onValueChange={(value) => handleInputChange('emergency_relationship', value)}
                    >
                      <SelectTrigger>
                        <SelectValue placeholder="관계 선택" />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="parent">부모</SelectItem>
                        <SelectItem value="spouse">배우자</SelectItem>
                        <SelectItem value="sibling">형제/자매</SelectItem>
                        <SelectItem value="child">자녀</SelectItem>
                        <SelectItem value="friend">친구</SelectItem>
                        <SelectItem value="other">기타</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>
                </div>
              </div>

              {/* 고용 정보 */}
              <div className="space-y-4">
                <h3 className="text-lg font-semibold">고용 정보</h3>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div>
                    <Label htmlFor="employment_type">고용 형태 *</Label>
                    <Select
                      value={formData.employment_type}
                      onValueChange={(value) => handleInputChange('employment_type', value)}
                    >
                      <SelectTrigger>
                        <SelectValue />
                      </SelectTrigger>
                      <SelectContent>
                        <SelectItem value="regular">정규직</SelectItem>
                        <SelectItem value="contract">계약직</SelectItem>
                        <SelectItem value="temporary">임시직</SelectItem>
                        <SelectItem value="daily">일용직</SelectItem>
                      </SelectContent>
                    </Select>
                  </div>

                  <div>
                    <Label htmlFor="hire_date">입사일 *</Label>
                    <Input
                      id="hire_date"
                      type="date"
                      value={formData.hire_date}
                      onChange={(e) => handleInputChange('hire_date', e.target.value)}
                      required
                    />
                  </div>
                </div>
              </div>

              {/* 제출 버튼 */}
              <div className="pt-4">
                <Button 
                  type="submit" 
                  className="w-full" 
                  size="lg"
                  disabled={submitting || !formData.name || !formData.phone || !formData.gender || !formData.work_type}
                >
                  {submitting ? (
                    <>
                      <Clock className="mr-2 h-4 w-4 animate-spin" />
                      등록 처리 중...
                    </>
                  ) : (
                    <>
                      <CheckCircle2 className="mr-2 h-4 w-4" />
                      등록 완료
                    </>
                  )}
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}