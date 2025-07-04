/**
 * 프론트엔드 에러 리포팅 서비스
 * Frontend error reporting service
 */

import { API_BASE_URL } from '../config/api';

interface ErrorReport {
  message: string;
  name?: string;
  stack?: string;
  filename?: string;
  lineno?: number;
  colno?: number;
  url?: string;
  userAgent?: string;
  userId?: string;
  severity?: 'warning' | 'error' | 'critical';
  component?: string;
  customData?: Record<string, any>;
}

interface ManualReport {
  title: string;
  description: string;
  steps_to_reproduce?: string;
  expected_behavior?: string;
  actual_behavior?: string;
  severity?: 'warning' | 'error' | 'critical';
  component?: string;
  environment?: string;
  browser_info?: string;
  user_id?: string;
}

class ErrorReportingService {
  private isEnabled: boolean = true;
  private reportQueue: ErrorReport[] = [];
  private isProcessing: boolean = false;

  constructor() {
    this.setupGlobalErrorHandlers();
  }

  /**
   * 전역 에러 핸들러 설정
   */
  private setupGlobalErrorHandlers() {
    // JavaScript 에러 캐치
    window.addEventListener('error', (event) => {
      this.reportError({
        message: event.message,
        filename: event.filename,
        lineno: event.lineno,
        colno: event.colno,
        stack: event.error?.stack,
        severity: 'error',
        component: 'frontend'
      });
    });

    // Promise rejection 에러 캐치
    window.addEventListener('unhandledrejection', (event) => {
      this.reportError({
        message: `Unhandled Promise Rejection: ${event.reason}`,
        stack: event.reason?.stack || String(event.reason),
        severity: 'error',
        component: 'frontend'
      });
    });

    // API 에러 인터셉트 (fetch 래퍼 사용시)
    this.interceptFetchErrors();
  }

  /**
   * Fetch API 에러 인터셉트
   */
  private interceptFetchErrors() {
    const originalFetch = window.fetch;
    
    window.fetch = async (...args) => {
      try {
        const response = await originalFetch(...args);
        
        // HTTP 에러 상태 체크
        if (!response.ok && response.status >= 500) {
          this.reportError({
            message: `API Error: ${response.status} ${response.statusText}`,
            url: args[0] as string,
            severity: 'error',
            component: 'api',
            customData: {
              status: response.status,
              statusText: response.statusText,
              requestUrl: args[0]
            }
          });
        }
        
        return response;
      } catch (error) {
        // 네트워크 에러 등
        this.reportError({
          message: `Network Error: ${error}`,
          url: args[0] as string,
          severity: 'critical',
          component: 'api',
          customData: {
            requestUrl: args[0],
            errorType: 'network'
          }
        });
        throw error;
      }
    };
  }

  /**
   * 에러 리포트 전송
   */
  async reportError(errorData: Partial<ErrorReport>): Promise<void> {
    if (!this.isEnabled) return;

    const report: ErrorReport = {
      message: errorData.message || 'Unknown error',
      name: errorData.name || 'Error',
      stack: errorData.stack,
      filename: errorData.filename,
      lineno: errorData.lineno,
      colno: errorData.colno,
      url: errorData.url || window.location.href,
      userAgent: errorData.userAgent || navigator.userAgent,
      userId: errorData.userId || this.getCurrentUserId(),
      severity: errorData.severity || 'error',
      component: errorData.component || 'frontend',
      customData: {
        ...errorData.customData,
        timestamp: new Date().toISOString(),
        pathname: window.location.pathname,
        search: window.location.search,
        userAgent: navigator.userAgent,
        language: navigator.language,
        platform: navigator.platform,
        viewport: {
          width: window.innerWidth,
          height: window.innerHeight
        }
      }
    };

    // 큐에 추가하고 처리
    this.reportQueue.push(report);
    this.processQueue();
  }

  /**
   * 수동 버그 리포트 전송
   */
  async submitManualReport(reportData: ManualReport): Promise<boolean> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/error-reporting/manual-report`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...reportData,
          browser_info: this.getBrowserInfo(),
          user_id: reportData.user_id || this.getCurrentUserId()
        }),
      });

      if (response.ok) {
        const result = await response.json();
        console.log('Manual report submitted:', result);
        return true;
      } else {
        console.error('Failed to submit manual report:', response.statusText);
        return false;
      }
    } catch (error) {
      console.error('Error submitting manual report:', error);
      return false;
    }
  }

  /**
   * 리포트 큐 처리
   */
  private async processQueue() {
    if (this.isProcessing || this.reportQueue.length === 0) return;
    
    this.isProcessing = true;

    while (this.reportQueue.length > 0) {
      const report = this.reportQueue.shift()!;
      
      try {
        await this.sendReport(report);
        await this.delay(100); // API 부하 방지
      } catch (error) {
        console.error('Failed to send error report:', error);
        // 중요한 에러는 다시 큐에 추가 (최대 3회까지)
        if (report.severity === 'critical' && !report.customData?.retryCount) {
          report.customData = report.customData || {};
          report.customData.retryCount = (report.customData.retryCount || 0) + 1;
          if (report.customData.retryCount < 3) {
            this.reportQueue.push(report);
          }
        }
      }
    }

    this.isProcessing = false;
  }

  /**
   * 실제 리포트 전송
   */
  private async sendReport(report: ErrorReport): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/v1/error-reporting/frontend-error`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(report),
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}: ${response.statusText}`);
    }

    const result = await response.json();
    console.log('Error report sent:', result);
  }

  /**
   * 현재 사용자 ID 가져오기
   */
  private getCurrentUserId(): string | undefined {
    try {
      const user = localStorage.getItem('user');
      if (user) {
        return JSON.parse(user).id;
      }
    } catch {
      // 무시
    }
    return undefined;
  }

  /**
   * 브라우저 정보 수집
   */
  private getBrowserInfo(): string {
    const info = {
      userAgent: navigator.userAgent,
      language: navigator.language,
      platform: navigator.platform,
      cookieEnabled: navigator.cookieEnabled,
      onLine: navigator.onLine,
      viewport: {
        width: window.innerWidth,
        height: window.innerHeight
      },
      screen: {
        width: screen.width,
        height: screen.height,
        colorDepth: screen.colorDepth
      },
      timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      url: window.location.href
    };

    return JSON.stringify(info, null, 2);
  }

  /**
   * 지연 함수
   */
  private delay(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * 에러 리포팅 활성화/비활성화
   */
  setEnabled(enabled: boolean) {
    this.isEnabled = enabled;
  }

  /**
   * 리포팅 상태 확인
   */
  async getStatus(): Promise<any> {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/error-reporting/status`);
      if (response.ok) {
        return await response.json();
      }
    } catch (error) {
      console.error('Failed to get reporting status:', error);
    }
    return null;
  }
}

// 싱글톤 인스턴스
export const errorReporting = new ErrorReportingService();

// 편의 함수들
export const reportError = (error: Error | string, context?: Record<string, any>) => {
  const errorData = typeof error === 'string' 
    ? { message: error, customData: context }
    : { 
        message: error.message, 
        name: error.name, 
        stack: error.stack, 
        customData: context 
      };
  
  errorReporting.reportError(errorData);
};

export const reportWarning = (message: string, context?: Record<string, any>) => {
  errorReporting.reportError({
    message,
    severity: 'warning',
    customData: context
  });
};

export const reportCritical = (error: Error | string, context?: Record<string, any>) => {
  const errorData = typeof error === 'string' 
    ? { message: error, severity: 'critical' as const, customData: context }
    : { 
        message: error.message, 
        name: error.name, 
        stack: error.stack, 
        severity: 'critical' as const, 
        customData: context 
      };
  
  errorReporting.reportError(errorData);
};

export default errorReporting;