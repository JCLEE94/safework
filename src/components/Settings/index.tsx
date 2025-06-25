import React, { useState, useEffect } from 'react';
import { Save, User, Building, Shield, Bell, Database, FileText, Globe, RefreshCw } from 'lucide-react';
import { Card, Button, Badge } from '../common';
import { useApi } from '../../hooks/useApi';

interface SystemSettings {
  company_name: string;
  company_address: string;
  company_phone: string;
  company_registration_number: string;
  business_type: string;
  total_employees: number;
  safety_manager: string;
  health_manager: string;
  representative_name: string;
  auto_backup_enabled: boolean;
  backup_frequency: 'daily' | 'weekly' | 'monthly';
  notification_enabled: boolean;
  email_notifications: boolean;
  sms_notifications: boolean;
  report_language: 'korean' | 'english' | 'both';
  data_retention_period: number; // months
  audit_log_enabled: boolean;
  password_policy_enabled: boolean;
  session_timeout: number; // minutes
  api_access_enabled: boolean;
  maintenance_mode: boolean;
}

interface UserSettings {
  user_name: string;
  user_email: string;
  user_phone: string;
  user_role: string;
  department: string;
  notification_preferences: {
    accidents: boolean;
    health_exams: boolean;
    education_reminders: boolean;
    report_deadlines: boolean;
    system_updates: boolean;
  };
  dashboard_layout: 'default' | 'compact' | 'detailed';
  theme: 'light' | 'dark' | 'auto';
  language: 'korean' | 'english';
  timezone: string;
}

export function Settings() {
  const [activeTab, setActiveTab] = useState<'system' | 'user' | 'security' | 'backup'>('system');
  const [systemSettings, setSystemSettings] = useState<SystemSettings | null>(null);
  const [userSettings, setUserSettings] = useState<UserSettings | null>(null);
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const { fetchApi } = useApi();

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      setLoading(true);
      
      // 시스템 설정 더미 데이터
      const systemData: SystemSettings = {
        company_name: "안전건설 주식회사",
        company_address: "서울특별시 강남구 테헤란로 123",
        company_phone: "02-1234-5678",
        company_registration_number: "123-45-67890",
        business_type: "건설업",
        total_employees: 150,
        safety_manager: "이안전",
        health_manager: "김보건",
        representative_name: "박대표",
        auto_backup_enabled: true,
        backup_frequency: 'daily',
        notification_enabled: true,
        email_notifications: true,
        sms_notifications: false,
        report_language: 'korean',
        data_retention_period: 36,
        audit_log_enabled: true,
        password_policy_enabled: true,
        session_timeout: 120,
        api_access_enabled: false,
        maintenance_mode: false
      };

      // 사용자 설정 더미 데이터
      const userData: UserSettings = {
        user_name: "관리자",
        user_email: "admin@company.com",
        user_phone: "010-1234-5678",
        user_role: "시스템 관리자",
        department: "안전관리팀",
        notification_preferences: {
          accidents: true,
          health_exams: true,
          education_reminders: true,
          report_deadlines: true,
          system_updates: false
        },
        dashboard_layout: 'default',
        theme: 'light',
        language: 'korean',
        timezone: 'Asia/Seoul'
      };

      setSystemSettings(systemData);
      setUserSettings(userData);
    } catch (error) {
      console.error('설정 조회 실패:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleSaveSettings = async () => {
    try {
      setSaving(true);
      // 설정 저장 로직
      console.log('설정 저장:', { systemSettings, userSettings });
      
      // 임시로 성공 시뮬레이션
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      alert('설정이 저장되었습니다.');
    } catch (error) {
      console.error('설정 저장 실패:', error);
      alert('설정 저장에 실패했습니다.');
    } finally {
      setSaving(false);
    }
  };

  const handleSystemSettingChange = (key: keyof SystemSettings, value: any) => {
    if (systemSettings) {
      setSystemSettings({
        ...systemSettings,
        [key]: value
      });
    }
  };

  const handleUserSettingChange = (key: keyof UserSettings, value: any) => {
    if (userSettings) {
      setUserSettings({
        ...userSettings,
        [key]: value
      });
    }
  };

  const handleNotificationPreferenceChange = (key: keyof UserSettings['notification_preferences'], value: boolean) => {
    if (userSettings) {
      setUserSettings({
        ...userSettings,
        notification_preferences: {
          ...userSettings.notification_preferences,
          [key]: value
        }
      });
    }
  };

  if (loading) {
    return (
      <div className="p-6 space-y-6">
        <h1 className="text-2xl font-bold text-gray-800">설정</h1>
        <Card>
          <p className="text-gray-600">설정을 불러오는 중...</p>
        </Card>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex justify-between items-center">
        <h1 className="text-2xl font-bold text-gray-800">시스템 설정</h1>
        <Button 
          onClick={handleSaveSettings} 
          disabled={saving}
          className="flex items-center gap-2"
        >
          <Save className="w-4 h-4" />
          {saving ? '저장 중...' : '설정 저장'}
        </Button>
      </div>

      {/* 탭 네비게이션 */}
      <Card>
        <div className="flex space-x-1 border-b">
          {[
            { id: 'system', label: '시스템 정보', icon: Building },
            { id: 'user', label: '사용자 설정', icon: User },
            { id: 'security', label: '보안 설정', icon: Shield },
            { id: 'backup', label: '백업 및 알림', icon: Database }
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setActiveTab(tab.id as any)}
              className={`flex items-center gap-2 px-4 py-2 rounded-t-lg transition-colors ${
                activeTab === tab.id
                  ? 'bg-blue-50 text-blue-600 border-b-2 border-blue-600'
                  : 'text-gray-600 hover:text-gray-800 hover:bg-gray-50'
              }`}
            >
              <tab.icon className="w-4 h-4" />
              {tab.label}
            </button>
          ))}
        </div>
      </Card>

      {/* 시스템 정보 탭 */}
      {activeTab === 'system' && systemSettings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Building className="w-5 h-5" />
                회사 정보
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">회사명</label>
                  <input
                    type="text"
                    value={systemSettings.company_name}
                    onChange={(e) => handleSystemSettingChange('company_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">주소</label>
                  <input
                    type="text"
                    value={systemSettings.company_address}
                    onChange={(e) => handleSystemSettingChange('company_address', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">전화번호</label>
                  <input
                    type="text"
                    value={systemSettings.company_phone}
                    onChange={(e) => handleSystemSettingChange('company_phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">사업자등록번호</label>
                  <input
                    type="text"
                    value={systemSettings.company_registration_number}
                    onChange={(e) => handleSystemSettingChange('company_registration_number', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">업종</label>
                  <select
                    value={systemSettings.business_type}
                    onChange={(e) => handleSystemSettingChange('business_type', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="건설업">건설업</option>
                    <option value="제조업">제조업</option>
                    <option value="서비스업">서비스업</option>
                    <option value="기타">기타</option>
                  </select>
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <User className="w-5 h-5" />
                관리자 정보
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">대표자명</label>
                  <input
                    type="text"
                    value={systemSettings.representative_name}
                    onChange={(e) => handleSystemSettingChange('representative_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">안전관리자</label>
                  <input
                    type="text"
                    value={systemSettings.safety_manager}
                    onChange={(e) => handleSystemSettingChange('safety_manager', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">보건관리자</label>
                  <input
                    type="text"
                    value={systemSettings.health_manager}
                    onChange={(e) => handleSystemSettingChange('health_manager', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">총 근로자 수</label>
                  <input
                    type="number"
                    value={systemSettings.total_employees}
                    onChange={(e) => handleSystemSettingChange('total_employees', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">보고서 언어</label>
                  <select
                    value={systemSettings.report_language}
                    onChange={(e) => handleSystemSettingChange('report_language', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="korean">한국어</option>
                    <option value="english">영어</option>
                    <option value="both">한국어/영어</option>
                  </select>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* 사용자 설정 탭 */}
      {activeTab === 'user' && userSettings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <User className="w-5 h-5" />
                개인 정보
              </h3>
              
              <div className="space-y-4">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">사용자명</label>
                  <input
                    type="text"
                    value={userSettings.user_name}
                    onChange={(e) => handleUserSettingChange('user_name', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">이메일</label>
                  <input
                    type="email"
                    value={userSettings.user_email}
                    onChange={(e) => handleUserSettingChange('user_email', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">전화번호</label>
                  <input
                    type="text"
                    value={userSettings.user_phone}
                    onChange={(e) => handleUserSettingChange('user_phone', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">역할</label>
                  <input
                    type="text"
                    value={userSettings.user_role}
                    onChange={(e) => handleUserSettingChange('user_role', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">부서</label>
                  <input
                    type="text"
                    value={userSettings.department}
                    onChange={(e) => handleUserSettingChange('department', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
              </div>
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Bell className="w-5 h-5" />
                알림 설정
              </h3>
              
              <div className="space-y-3">
                {Object.entries({
                  accidents: '사고 발생',
                  health_exams: '건강진단 일정',
                  education_reminders: '교육 알림',
                  report_deadlines: '보고서 제출 기한',
                  system_updates: '시스템 업데이트'
                }).map(([key, label]) => (
                  <label key={key} className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={userSettings.notification_preferences[key as keyof typeof userSettings.notification_preferences]}
                      onChange={(e) => handleNotificationPreferenceChange(key as keyof typeof userSettings.notification_preferences, e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">{label}</span>
                  </label>
                ))}
              </div>
              
              <div className="pt-4 border-t">
                <div className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">테마</label>
                    <select
                      value={userSettings.theme}
                      onChange={(e) => handleUserSettingChange('theme', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="light">라이트</option>
                      <option value="dark">다크</option>
                      <option value="auto">자동</option>
                    </select>
                  </div>
                  
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-1">대시보드 레이아웃</label>
                    <select
                      value={userSettings.dashboard_layout}
                      onChange={(e) => handleUserSettingChange('dashboard_layout', e.target.value)}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                    >
                      <option value="default">기본</option>
                      <option value="compact">컴팩트</option>
                      <option value="detailed">상세</option>
                    </select>
                  </div>
                </div>
              </div>
            </div>
          </Card>
        </div>
      )}

      {/* 보안 설정 탭 */}
      {activeTab === 'security' && systemSettings && (
        <Card>
          <div className="space-y-6">
            <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
              <Shield className="w-5 h-5" />
              보안 설정
            </h3>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="space-y-4">
                <h4 className="font-medium text-gray-800">인증 설정</h4>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={systemSettings.password_policy_enabled}
                    onChange={(e) => handleSystemSettingChange('password_policy_enabled', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">강력한 비밀번호 정책 사용</span>
                </label>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">세션 타임아웃 (분)</label>
                  <input
                    type="number"
                    value={systemSettings.session_timeout}
                    onChange={(e) => handleSystemSettingChange('session_timeout', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                </div>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={systemSettings.api_access_enabled}
                    onChange={(e) => handleSystemSettingChange('api_access_enabled', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">API 접근 허용</span>
                </label>
              </div>
              
              <div className="space-y-4">
                <h4 className="font-medium text-gray-800">감사 로그</h4>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={systemSettings.audit_log_enabled}
                    onChange={(e) => handleSystemSettingChange('audit_log_enabled', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">감사 로그 기록</span>
                </label>
                
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">데이터 보존 기간 (개월)</label>
                  <input
                    type="number"
                    value={systemSettings.data_retention_period}
                    onChange={(e) => handleSystemSettingChange('data_retention_period', parseInt(e.target.value))}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                  />
                  <p className="text-xs text-gray-500 mt-1">법적 요구사항: 최소 36개월</p>
                </div>
                
                <label className="flex items-center gap-3">
                  <input
                    type="checkbox"
                    checked={systemSettings.maintenance_mode}
                    onChange={(e) => handleSystemSettingChange('maintenance_mode', e.target.checked)}
                    className="rounded"
                  />
                  <span className="text-sm text-gray-700">유지보수 모드</span>
                </label>
              </div>
            </div>
          </div>
        </Card>
      )}

      {/* 백업 및 알림 탭 */}
      {activeTab === 'backup' && systemSettings && (
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Database className="w-5 h-5" />
                백업 설정
              </h3>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={systemSettings.auto_backup_enabled}
                  onChange={(e) => handleSystemSettingChange('auto_backup_enabled', e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">자동 백업 활성화</span>
              </label>
              
              {systemSettings.auto_backup_enabled && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">백업 주기</label>
                  <select
                    value={systemSettings.backup_frequency}
                    onChange={(e) => handleSystemSettingChange('backup_frequency', e.target.value)}
                    className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500"
                  >
                    <option value="daily">매일</option>
                    <option value="weekly">매주</option>
                    <option value="monthly">매월</option>
                  </select>
                </div>
              )}
              
              <div className="pt-4 border-t">
                <Button
                  variant="outline"
                  onClick={() => console.log('수동 백업 실행')}
                  className="flex items-center gap-2"
                >
                  <RefreshCw className="w-4 h-4" />
                  수동 백업 실행
                </Button>
              </div>
            </div>
          </Card>

          <Card>
            <div className="space-y-4">
              <h3 className="text-lg font-semibold text-gray-800 flex items-center gap-2">
                <Bell className="w-5 h-5" />
                시스템 알림
              </h3>
              
              <label className="flex items-center gap-3">
                <input
                  type="checkbox"
                  checked={systemSettings.notification_enabled}
                  onChange={(e) => handleSystemSettingChange('notification_enabled', e.target.checked)}
                  className="rounded"
                />
                <span className="text-sm text-gray-700">시스템 알림 활성화</span>
              </label>
              
              {systemSettings.notification_enabled && (
                <div className="space-y-3 pl-6">
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={systemSettings.email_notifications}
                      onChange={(e) => handleSystemSettingChange('email_notifications', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">이메일 알림</span>
                  </label>
                  
                  <label className="flex items-center gap-3">
                    <input
                      type="checkbox"
                      checked={systemSettings.sms_notifications}
                      onChange={(e) => handleSystemSettingChange('sms_notifications', e.target.checked)}
                      className="rounded"
                    />
                    <span className="text-sm text-gray-700">SMS 알림</span>
                  </label>
                </div>
              )}
            </div>
          </Card>
        </div>
      )}

      {/* 시스템 상태 정보 */}
      <Card>
        <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
          <div className="flex items-start gap-3">
            <div className="w-5 h-5 bg-blue-500 rounded-full flex items-center justify-center mt-0.5">
              <div className="w-2 h-2 bg-white rounded-full"></div>
            </div>
            <div>
              <h4 className="font-medium text-blue-900 mb-1">시스템 정보</h4>
              <div className="text-sm text-blue-700 space-y-1">
                <p>• 버전: SafeWork Pro v2.0.1</p>
                <p>• 빌드: 2024.06.25.001</p>
                <p>• 데이터베이스: PostgreSQL 15.3</p>
                <p>• 마지막 백업: 2024-06-25 02:00:00</p>
                <p>• 시스템 상태: <Badge className="bg-green-100 text-green-800">정상</Badge></p>
              </div>
            </div>
          </div>
        </div>
      </Card>
    </div>
  );
}