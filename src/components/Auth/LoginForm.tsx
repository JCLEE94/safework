import React, { useState } from 'react';
import { Button } from '../common/Button';
import { Card } from '../common/Card';
import { authService } from '../../services/authService';

interface LoginFormProps {
  onLoginSuccess: () => void;
}

export function LoginForm({ onLoginSuccess }: LoginFormProps) {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [showRegister, setShowRegister] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.login(formData);
      onLoginSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : '로그인에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setError('');
    setLoading(true);

    try {
      await authService.register({
        ...formData,
        name: formData.email.split('@')[0], // 이메일에서 이름 추출
      });
      onLoginSuccess();
    } catch (err) {
      setError(err instanceof Error ? err.message : '회원가입에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-gray-50">
      <Card className="w-full max-w-md p-8">
        <div className="text-center mb-8">
          <h1 className="text-2xl font-bold text-gray-900 mb-2">
            SafeWork Pro
          </h1>
          <p className="text-gray-600">
            {showRegister ? '새 계정을 만들어주세요' : '계정에 로그인하세요'}
          </p>
        </div>

        <form onSubmit={showRegister ? handleRegister : handleLogin} className="space-y-6">
          <div>
            <label htmlFor="email" className="block text-sm font-medium text-gray-700 mb-2">
              이메일
            </label>
            <input
              type="email"
              id="email"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          <div>
            <label htmlFor="password" className="block text-sm font-medium text-gray-700 mb-2">
              비밀번호
            </label>
            <input
              type="password"
              id="password"
              value={formData.password}
              onChange={(e) => setFormData({ ...formData, password: e.target.value })}
              className="w-full px-3 py-2 border border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              required
            />
          </div>

          {error && (
            <div className="p-3 bg-red-100 border border-red-400 text-red-700 rounded">
              {error}
            </div>
          )}

          <Button
            type="submit"
            disabled={loading}
            className="w-full"
          >
            {loading ? '처리 중...' : showRegister ? '회원가입' : '로그인'}
          </Button>

          <div className="text-center">
            <button
              type="button"
              onClick={() => setShowRegister(!showRegister)}
              className="text-blue-600 hover:text-blue-800 text-sm"
            >
              {showRegister ? '이미 계정이 있나요? 로그인' : '계정이 없나요? 회원가입'}
            </button>
          </div>
        </form>

        <div className="mt-6 p-4 bg-blue-50 rounded-md">
          <h3 className="font-semibold text-blue-900 mb-2">기본 관리자 계정:</h3>
          <p className="text-sm text-blue-800">
            이메일: admin@safework.local<br />
            비밀번호: admin123!
          </p>
        </div>
      </Card>
    </div>
  );
}