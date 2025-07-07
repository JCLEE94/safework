import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertTriangle, RefreshCw, Bug, Send } from 'lucide-react';
import { apiUrl } from '../../config/api';

interface Props {
  children: ReactNode;
  fallback?: ReactNode;
}

interface State {
  hasError: boolean;
  error: Error | null;
  errorInfo: ErrorInfo | null;
  isReporting: boolean;
  reportSent: boolean;
}

class ErrorBoundary extends Component<Props, State> {
  private errorId: string = '';

  constructor(props: Props) {
    super(props);

    this.state = {
      hasError: false,
      error: null,
      errorInfo: null,
      isReporting: false,
      reportSent: false,
    };
  }

  static getDerivedStateFromError(error: Error): State {
    return {
      hasError: true,
      error,
      errorInfo: null,
      isReporting: false,
      reportSent: false,
    };
  }

  componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    this.setState({
      error,
      errorInfo,
    });

    // 자동으로 에러 리포트 전송
    this.reportError(error, errorInfo);
  }

  reportError = async (error: Error, errorInfo: ErrorInfo) => {
    this.setState({ isReporting: true });
    
    try {
      const errorReport = {
        message: error.message,
        name: error.name,
        stack: error.stack || 'No stack trace available',
        filename: this.extractFilename(error.stack),
        url: window.location.href,
        userAgent: navigator.userAgent,
        severity: 'error',
        component: 'frontend',
        customData: {
          componentStack: errorInfo.componentStack,
          timestamp: new Date().toISOString(),
          userId: this.getCurrentUserId(),
        }
      };

      const response = await fetch(apiUrl('/error-reporting/frontend-error'), {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(errorReport),
      });

      if (response.ok) {
        const result = await response.json();
        this.errorId = result.error_id;
        this.setState({ reportSent: true });
        console.log('Error report sent successfully:', result);
      } else {
        console.error('Failed to send error report:', response.statusText);
      }
    } catch (reportingError) {
      console.error('Error while reporting error:', reportingError);
    } finally {
      this.setState({ isReporting: false });
    }
  };

  extractFilename = (stack?: string): string => {
    if (!stack) return 'unknown';
    
    const matches = stack.match(/https?:\/\/[^)]+/);
    if (matches && matches[0]) {
      return matches[0].split('/').pop() || 'unknown';
    }
    return 'unknown';
  };

  getCurrentUserId = (): string | undefined => {
    // 로컬 스토리지나 세션에서 사용자 ID 추출
    try {
      const user = localStorage.getItem('user');
      if (user) {
        return JSON.parse(user).id;
      }
    } catch {
      // 무시
    }
    return undefined;
  };

  handleReload = () => {
    window.location.reload();
  };

  handleReset = () => {
    this.setState({
      hasError: false,
      error: null,
      errorInfo: null,
      isReporting: false,
      reportSent: false,
    });
  };

  render() {
    if (this.state.hasError) {
      if (this.props.fallback) {
        return this.props.fallback;
      }

      return (
        <div className="min-h-screen bg-gray-50 flex flex-col justify-center items-center px-4">
          <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
            {/* 에러 아이콘 */}
            <div className="flex justify-center mb-6">
              <div className="bg-red-100 rounded-full p-4">
                <AlertTriangle className="h-12 w-12 text-red-600" />
              </div>
            </div>

            {/* 제목 */}
            <h1 className="text-2xl font-bold text-gray-900 mb-4">
              앗! 문제가 발생했습니다
            </h1>

            {/* 설명 */}
            <p className="text-gray-600 mb-6">
              예상치 못한 오류가 발생했습니다. 불편을 드려 죄송합니다.
              {this.state.reportSent && (
                <span className="block mt-2 text-sm text-green-600">
                  ✅ 오류가 개발팀에 자동으로 보고되었습니다 (ID: {this.errorId})
                </span>
              )}
            </p>

            {/* 에러 세부 정보 (개발 환경에서만) */}
            {process.env.NODE_ENV === 'development' && this.state.error && (
              <div className="bg-gray-100 rounded-lg p-4 mb-6 text-left">
                <h3 className="font-semibold text-gray-900 mb-2">개발자 정보:</h3>
                <p className="text-sm text-gray-700 font-mono break-all">
                  {this.state.error.message}
                </p>
                {this.state.error.stack && (
                  <details className="mt-2">
                    <summary className="text-sm text-gray-600 cursor-pointer">
                      스택 트레이스 보기
                    </summary>
                    <pre className="text-xs text-gray-600 mt-2 overflow-auto max-h-32">
                      {this.state.error.stack}
                    </pre>
                  </details>
                )}
              </div>
            )}

            {/* 액션 버튼들 */}
            <div className="space-y-3">
              <button
                onClick={this.handleReload}
                className="w-full bg-blue-600 text-white px-6 py-3 rounded-lg hover:bg-blue-700 transition-colors flex items-center justify-center"
              >
                <RefreshCw className="h-5 w-5 mr-2" />
                페이지 새로고침
              </button>

              <button
                onClick={this.handleReset}
                className="w-full bg-gray-600 text-white px-6 py-3 rounded-lg hover:bg-gray-700 transition-colors"
              >
                다시 시도
              </button>

              {/* 수동 리포트 버튼 */}
              {!this.state.reportSent && (
                <button
                  onClick={() => this.reportError(this.state.error!, this.state.errorInfo!)}
                  disabled={this.state.isReporting}
                  className="w-full bg-orange-600 text-white px-6 py-3 rounded-lg hover:bg-orange-700 transition-colors flex items-center justify-center disabled:bg-gray-400"
                >
                  {this.state.isReporting ? (
                    <>
                      <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white mr-2" />
                      리포트 전송 중...
                    </>
                  ) : (
                    <>
                      <Bug className="h-5 w-5 mr-2" />
                      에러 리포트 보내기
                    </>
                  )}
                </button>
              )}
            </div>

            {/* 추가 도움말 */}
            <div className="mt-8 pt-6 border-t border-gray-200">
              <p className="text-sm text-gray-500">
                문제가 계속 발생하면{' '}
                <a
                  href="mailto:support@safework.com"
                  className="text-blue-600 hover:underline"
                >
                  고객지원팀
                </a>
                에 문의하세요.
              </p>
            </div>
          </div>
        </div>
      );
    }

    return this.props.children;
  }
}

export default ErrorBoundary;