import { API_CONFIG } from '../config/api';

interface LoginRequest {
  email: string;
  password: string;
}

interface LoginResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
}

interface RegisterRequest {
  email: string;
  password: string;
  name: string;
  role?: string;
}

class AuthService {
  private tokenKey = 'safework_token';
  private userKey = 'safework_user';

  async login(credentials: LoginRequest): Promise<LoginResponse> {
    try {
      const response = await fetch(`${API_CONFIG.API_URL}/auth/login`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(credentials),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '로그인에 실패했습니다');
      }

      const data: LoginResponse = await response.json();
      
      // 토큰 저장
      this.setToken(data.access_token);
      
      // JWT 토큰에서 사용자 정보 추출
      const userInfo = this.parseTokenForUser(data.access_token);
      if (userInfo) {
        this.setUser(userInfo);
      }
      
      return data;
    } catch (error) {
      console.error('로그인 오류:', error);
      throw error;
    }
  }

  async register(userData: RegisterRequest): Promise<LoginResponse> {
    try {
      const response = await fetch(`${API_CONFIG.API_URL}/auth/register`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(userData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || '회원가입에 실패했습니다');
      }

      const data: LoginResponse = await response.json();
      
      // 토큰 저장
      this.setToken(data.access_token);
      
      // JWT 토큰에서 사용자 정보 추출
      const userInfo = this.parseTokenForUser(data.access_token);
      if (userInfo) {
        this.setUser(userInfo);
      }
      
      return data;
    } catch (error) {
      console.error('회원가입 오류:', error);
      throw error;
    }
  }

  async logout(): Promise<void> {
    try {
      const token = this.getToken();
      if (token) {
        await fetch(`${API_CONFIG.API_URL}/auth/logout`, {
          method: 'POST',
          headers: {
            'Authorization': `Bearer ${token}`,
          },
        });
      }
    } catch (error) {
      console.error('로그아웃 오류:', error);
    } finally {
      this.clearAuth();
    }
  }

  getToken(): string | null {
    return localStorage.getItem(this.tokenKey);
  }

  setToken(token: string): void {
    localStorage.setItem(this.tokenKey, token);
  }

  getUser(): any {
    const userStr = localStorage.getItem(this.userKey);
    return userStr ? JSON.parse(userStr) : null;
  }

  setUser(user: any): void {
    localStorage.setItem(this.userKey, JSON.stringify(user));
  }

  clearAuth(): void {
    localStorage.removeItem(this.tokenKey);
    localStorage.removeItem(this.userKey);
  }

  isAuthenticated(): boolean {
    return !!this.getToken();
  }

  // API 요청용 헤더 생성
  getAuthHeaders(): Record<string, string> {
    const token = this.getToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }

  // JWT 토큰에서 사용자 정보 추출
  private parseTokenForUser(token: string): any {
    try {
      const payload = JSON.parse(atob(token.split('.')[1]));
      return {
        id: payload.sub,
        email: payload.email,
        name: payload.email && payload.email.includes('@') ? payload.email.split('@')[0] : payload.email, // 이메일 또는 사용자명에서 이름 추출
        role: payload.role || 'user'
      };
    } catch (error) {
      console.error('토큰 파싱 오류:', error);
      return null;
    }
  }
}

export const authService = new AuthService();