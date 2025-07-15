"""
고급 로깅 시스템
Advanced logging system for health management application
"""

import json
import logging
import logging.handlers
import sys
import traceback
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional


class JSONFormatter(logging.Formatter):
    """JSON 형태로 로그를 포맷하는 클래스"""

    def format(self, record):
        log_obj = {
            "timestamp": datetime.fromtimestamp(record.created).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # 추가 필드들
        if hasattr(record, "user_id"):
            log_obj["user_id"] = record.user_id
        if hasattr(record, "request_id"):
            log_obj["request_id"] = record.request_id
        if hasattr(record, "duration"):
            log_obj["duration_ms"] = record.duration
        if hasattr(record, "status_code"):
            log_obj["status_code"] = record.status_code
        if hasattr(record, "endpoint"):
            log_obj["endpoint"] = record.endpoint

        # 예외 정보
        if record.exc_info:
            log_obj["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
            }

        return json.dumps(log_obj, ensure_ascii=False)


class HealthLogger:
    """건설업 보건관리 시스템 전용 로거"""

    def __init__(self, name: str = "health_system"):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)

        # 핸들러가 이미 있으면 중복 추가 방지
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """로그 핸들러 설정"""
        # 로그 디렉토리 생성
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # 콘솔 핸들러 (개발 환경)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        console_handler.setFormatter(console_formatter)
        self.logger.addHandler(console_handler)

        # 파일 핸들러 (운영 환경) - 일별 로테이션
        file_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "health_system.log",
            when="midnight",
            interval=1,
            backupCount=30,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(file_handler)

        # 에러 전용 핸들러
        error_handler = logging.handlers.TimedRotatingFileHandler(
            log_dir / "errors.log",
            when="midnight",
            interval=1,
            backupCount=90,
            encoding="utf-8",
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(JSONFormatter())
        self.logger.addHandler(error_handler)

    def info(self, message: str, **kwargs):
        """정보 로그"""
        self.logger.info(message, extra=kwargs)

    def warning(self, message: str, **kwargs):
        """경고 로그"""
        self.logger.warning(message, extra=kwargs)

    def error(self, message: str, error: Optional[Exception] = None, **kwargs):
        """에러 로그"""
        if error:
            self.logger.error(message, exc_info=True, extra=kwargs)
        else:
            self.logger.error(message, extra=kwargs)

    def debug(self, message: str, **kwargs):
        """디버그 로그"""
        self.logger.debug(message, extra=kwargs)

    @contextmanager
    def performance_log(self, operation: str, **context):
        """성능 측정 컨텍스트 매니저"""
        start_time = datetime.now()
        try:
            yield
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.info(
                f"Performance: {operation} completed",
                duration=duration,
                operation=operation,
                **context,
            )
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            self.error(
                f"Performance: {operation} failed",
                error=e,
                duration=duration,
                operation=operation,
                **context,
            )
            raise

    def api_request(
        self,
        method: str,
        endpoint: str,
        status_code: int,
        duration_ms: float,
        user_id: str = None,
        **kwargs,
    ):
        """API 요청 로그"""
        self.info(
            f"API {method} {endpoint} - {status_code}",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration=duration_ms,
            user_id=user_id,
            **kwargs,
        )

    def security_event(
        self, event_type: str, details: Dict[str, Any], severity: str = "warning"
    ):
        """보안 이벤트 로그"""
        log_method = getattr(self.logger, severity.lower(), self.logger.warning)
        log_method(
            f"Security Event: {event_type}",
            extra={
                "event_type": event_type,
                "security_details": details,
                "severity": severity,
            },
        )

    def database_operation(
        self, operation: str, table: str, duration_ms: float = None, **kwargs
    ):
        """데이터베이스 작업 로그"""
        self.info(
            f"DB Operation: {operation} on {table}",
            db_operation=operation,
            table=table,
            duration=duration_ms,
            **kwargs,
        )

    def pdf_generation(
        self,
        form_type: str,
        success: bool,
        file_size: int = None,
        duration_ms: float = None,
        **kwargs,
    ):
        """PDF 생성 로그"""
        status = "success" if success else "failed"
        self.info(
            f"PDF Generation: {form_type} - {status}",
            form_type=form_type,
            success=success,
            file_size_bytes=file_size,
            duration=duration_ms,
            **kwargs,
        )


# 전역 로거 인스턴스
logger = HealthLogger()


class ErrorHandler:
    """통합 에러 핸들러"""

    @staticmethod
    def handle_database_error(error: Exception, operation: str, table: str = None):
        """데이터베이스 에러 처리"""
        error_details = {
            "operation": operation,
            "table": table,
            "error_type": type(error).__name__,
            "error_message": str(error),
        }

        logger.error(f"Database error during {operation}", error=error, **error_details)

        # 사용자 친화적 메시지 반환
        if "duplicate key" in str(error).lower():
            return "이미 존재하는 데이터입니다."
        elif "foreign key" in str(error).lower():
            return "관련된 데이터가 존재하여 작업을 완료할 수 없습니다."
        elif "timeout" in str(error).lower():
            return "데이터베이스 응답 시간이 초과되었습니다."
        else:
            return "데이터베이스 작업 중 오류가 발생했습니다."

    @staticmethod
    def handle_validation_error(error: Exception, data: Dict[str, Any] = None):
        """검증 에러 처리"""
        logger.warning(
            "Validation error",
            error=error,
            validation_data=data,
            error_type=type(error).__name__,
        )
        return f"입력 데이터 검증 실패: {str(error)}"

    @staticmethod
    def handle_pdf_error(error: Exception, form_type: str, data: Dict[str, Any] = None):
        """PDF 생성 에러 처리"""
        logger.error(
            f"PDF generation failed for {form_type}",
            error=error,
            form_type=form_type,
            form_data=data,
        )
        return "PDF 생성 중 오류가 발생했습니다."

    @staticmethod
    def handle_api_error(error: Exception, endpoint: str, method: str = None):
        """API 에러 처리"""
        logger.error(
            f"API error at {endpoint}", error=error, endpoint=endpoint, method=method
        )

        if hasattr(error, "status_code"):
            return error
        else:
            return "서버 내부 오류가 발생했습니다."


# 데코레이터
def log_performance(operation_name: str):
    """성능 로깅 데코레이터"""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with logger.performance_log(operation_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_api_call(func):
    """API 호출 로깅 데코레이터"""

    def wrapper(*args, **kwargs):
        start_time = datetime.now()
        try:
            result = func(*args, **kwargs)
            duration = (datetime.now() - start_time).total_seconds() * 1000

            # FastAPI 요청 객체에서 정보 추출
            if hasattr(args[0], "method") and hasattr(args[0], "url"):
                request = args[0]
                logger.api_request(
                    method=request.method,
                    endpoint=str(request.url.path),
                    status_code=200,
                    duration_ms=duration,
                )

            return result
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds() * 1000
            logger.error(
                f"API call failed: {func.__name__}", error=e, duration=duration
            )
            raise

    return wrapper
