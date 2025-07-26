import axios, { AxiosInstance, AxiosRequestConfig, AxiosResponse, AxiosError } from 'axios';
import { message } from 'antd';

// API 응답 타입
export interface ApiResponse<T = any> {
  data: T;
  message?: string;
  status: 'success' | 'error';
  error?: string;
}

// 페이지네이션 응답 타입
export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  totalPages: number;
}

// 에러 응답 타입
export interface ApiError {
  message: string;
  code?: string;
  details?: any;
}

// API 클라이언트 클래스
class ApiClient {
  private instance: AxiosInstance;

  constructor(baseURL: string = '/api/v1') {
    this.instance = axios.create({
      baseURL,
      timeout: 30000,
      headers: {
        'Content-Type': 'application/json',
      },
    });

    this.setupInterceptors();
  }

  private setupInterceptors(): void {
    // 요청 인터셉터
    this.instance.interceptors.request.use(
      (config) => {
        // 토큰 추가 (있을 경우)
        const token = localStorage.getItem('access_token');
        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // 로깅 (개발 환경)
        if (process.env.NODE_ENV === 'development') {
          console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`, config.data);
        }

        return config;
      },
      (error) => {
        return Promise.reject(error);
      }
    );

    // 응답 인터셉터
    this.instance.interceptors.response.use(
      (response: AxiosResponse) => {
        // 성공 응답 처리
        return response;
      },
      async (error: AxiosError<ApiError>) => {
        // 에러 응답 처리
        const { response } = error;

        if (response) {
          switch (response.status) {
            case 401:
              // 인증 에러 - 로그인 페이지로 리다이렉트
              localStorage.removeItem('access_token');
              window.location.href = '/login';
              message.error('인증이 만료되었습니다. 다시 로그인해주세요.');
              break;
            
            case 403:
              message.error('접근 권한이 없습니다.');
              break;
            
            case 404:
              message.error('요청한 리소스를 찾을 수 없습니다.');
              break;
            
            case 422:
              // 유효성 검증 에러
              const validationError = response.data?.message || '입력값을 확인해주세요.';
              message.error(validationError);
              break;
            
            case 500:
              message.error('서버 오류가 발생했습니다. 잠시 후 다시 시도해주세요.');
              break;
            
            default:
              const errorMessage = response.data?.message || '요청 처리 중 오류가 발생했습니다.';
              message.error(errorMessage);
          }
        } else if (error.request) {
          // 네트워크 에러
          message.error('네트워크 연결을 확인해주세요.');
        } else {
          // 기타 에러
          message.error('요청 처리 중 오류가 발생했습니다.');
        }

        return Promise.reject(error);
      }
    );
  }

  // GET 요청
  async get<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.get<T>(url, config);
    return response.data;
  }

  // POST 요청
  async post<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.post<T>(url, data, config);
    return response.data;
  }

  // PUT 요청
  async put<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.put<T>(url, data, config);
    return response.data;
  }

  // PATCH 요청
  async patch<T = any>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.patch<T>(url, data, config);
    return response.data;
  }

  // DELETE 요청
  async delete<T = any>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.instance.delete<T>(url, config);
    return response.data;
  }

  // 파일 업로드
  async upload<T = any>(url: string, file: File, additionalData?: any): Promise<T> {
    const formData = new FormData();
    formData.append('file', file);

    if (additionalData) {
      Object.keys(additionalData).forEach(key => {
        formData.append(key, additionalData[key]);
      });
    }

    const response = await this.instance.post<T>(url, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    return response.data;
  }

  // 파일 다운로드
  async download(url: string, filename?: string): Promise<void> {
    const response = await this.instance.get(url, {
      responseType: 'blob',
    });

    const blob = new Blob([response.data]);
    const downloadUrl = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = downloadUrl;
    link.download = filename || 'download';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    window.URL.revokeObjectURL(downloadUrl);
  }
}

// 싱글톤 인스턴스
export const apiClient = new ApiClient();

// 편의 함수들
export const api = {
  get: apiClient.get.bind(apiClient),
  post: apiClient.post.bind(apiClient),
  put: apiClient.put.bind(apiClient),
  patch: apiClient.patch.bind(apiClient),
  delete: apiClient.delete.bind(apiClient),
  upload: apiClient.upload.bind(apiClient),
  download: apiClient.download.bind(apiClient),
};

export default api;