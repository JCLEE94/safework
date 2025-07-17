/**
 * API 설정 및 URL 관리
 * 환경변수 기반으로 API 엔드포인트를 중앙 관리
 */

// 환경변수에서 API 베이스 URL 가져오기
const getApiBaseUrl = (): string => {
  // Vite 환경변수는 VITE_ 접두사 필요
  const envApiUrl = import.meta.env.VITE_API_BASE_URL;
  
  if (envApiUrl) {
    return envApiUrl;
  }
  
  // 기본값: 현재 호스트의 API 경로
  const protocol = window.location.protocol;
  const host = window.location.host;
  return `${protocol}//${host}`;
};

// WebSocket URL 생성
const getWebSocketUrl = (): string => {
  const envWsUrl = import.meta.env.VITE_WS_BASE_URL;
  
  if (envWsUrl) {
    return envWsUrl;
  }
  
  // 기본값: HTTP를 WebSocket으로 변경
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  const host = window.location.host;
  return `${protocol}//${host}`;
};

export const API_CONFIG = {
  BASE_URL: getApiBaseUrl(),
  WS_BASE_URL: getWebSocketUrl(),
  
  // API 버전
  VERSION: '/api/v1',
  
  // 전체 API URL
  get API_URL() {
    return `${this.BASE_URL}${this.VERSION}`;
  },
  
  // WebSocket API URL
  get WS_API_URL() {
    return `${this.WS_BASE_URL}${this.VERSION}`;
  }
};

// 편의 함수들
export const apiUrl = (endpoint: string): string => {
  return `${API_CONFIG.API_URL}${endpoint}`;
};

export const wsUrl = (endpoint: string): string => {
  return `${API_CONFIG.WS_API_URL}${endpoint}`;
};

// 개발 환경 확인
export const isDevelopment = import.meta.env.DEV;
export const isProduction = import.meta.env.PROD;

// 간단한 API 클라이언트
export const api = {
  get: async (endpoint: string) => {
    const response = await fetch(apiUrl(endpoint));
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  },
  
  post: async (endpoint: string, data?: any) => {
    const response = await fetch(apiUrl(endpoint), {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  },
  
  put: async (endpoint: string, data?: any) => {
    const response = await fetch(apiUrl(endpoint), {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: data ? JSON.stringify(data) : undefined,
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  },
  
  delete: async (endpoint: string) => {
    const response = await fetch(apiUrl(endpoint), {
      method: 'DELETE',
    });
    if (!response.ok) {
      throw new Error(`API Error: ${response.status}`);
    }
    return response.json();
  }
};

console.log('🔗 API Configuration:', {
  baseUrl: API_CONFIG.BASE_URL,
  apiUrl: API_CONFIG.API_URL,
  wsUrl: API_CONFIG.WS_BASE_URL,
  environment: isDevelopment ? 'development' : 'production'
});