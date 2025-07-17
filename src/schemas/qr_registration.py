"""
QR코드 등록 스키마

이 모듈은 QR코드 기반 근로자 등록을 위한 Pydantic 스키마를 정의합니다.
- 요청/응답 데이터 검증
- 타입 안정성 보장
- API 문서 자동 생성

외부 패키지:
- pydantic: 데이터 검증 (https://docs.pydantic.dev/)

예시 입력:
- QRRegistrationRequest: 등록 요청 데이터
- WorkerRegistrationData: 근로자 기본 정보

예시 출력:
- QRRegistrationResponse: 생성된 QR코드 정보
- RegistrationStatusResponse: 등록 상태 정보
"""

from datetime import datetime
from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field, validator
from enum import Enum


class RegistrationStatus(str, Enum):
    """등록 상태"""
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    EXPIRED = "expired"
    CANCELLED = "cancelled"


class WorkerRegistrationData(BaseModel):
    """근로자 등록 기본 정보"""
    
    name: str = Field(..., min_length=1, max_length=50, description="성명")
    employee_id: Optional[str] = Field(None, max_length=20, description="사번")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    gender: Optional[str] = Field(None, max_length=10, description="성별")
    phone: Optional[str] = Field(None, max_length=20, description="연락처")
    email: Optional[str] = Field(None, max_length=100, description="이메일")
    address: Optional[str] = Field(None, description="주소")
    
    # 고용정보
    employment_type: str = Field(..., max_length=20, description="고용형태")
    work_type: str = Field(..., max_length=20, description="작업분류")
    hire_date: Optional[str] = Field(None, description="입사일 (YYYY-MM-DD)")
    
    # 건강정보
    blood_type: Optional[str] = Field(None, max_length=5, description="혈액형")
    emergency_contact: Optional[str] = Field(None, max_length=100, description="비상연락처")
    
    # 특수건강진단 정보
    is_special_exam_target: bool = Field(False, description="특수건강진단 대상여부")
    harmful_factors: Optional[List[str]] = Field(None, description="유해인자 목록")
    
    @validator('phone')
    def validate_phone(cls, v):
        if v and not v.replace('-', '').replace(' ', '').isdigit():
            raise ValueError('올바른 전화번호 형식이 아닙니다')
        return v
    
    @validator('email')
    def validate_email(cls, v):
        if v and '@' not in v:
            raise ValueError('올바른 이메일 형식이 아닙니다')
        return v


class QRRegistrationRequest(BaseModel):
    """QR코드 등록 요청"""
    
    worker_data: WorkerRegistrationData = Field(..., description="근로자 기본 정보")
    department: str = Field(..., min_length=1, max_length=100, description="부서")
    position: Optional[str] = Field(None, max_length=50, description="직급")
    expires_in_hours: int = Field(24, ge=1, le=168, description="유효시간 (시간, 최대 7일)")
    notes: Optional[str] = Field(None, description="비고")
    
    class Config:
        json_schema_extra = {
            "example": {
                "worker_data": {
                    "name": "홍길동",
                    "employee_id": "EMP001",
                    "phone": "010-1234-5678",
                    "email": "hong@example.com",
                    "employment_type": "정규직",
                    "work_type": "건설업",
                    "birth_date": "1990-01-01",
                    "blood_type": "A",
                    "is_special_exam_target": False
                },
                "department": "건설부",
                "position": "대리",
                "expires_in_hours": 24,
                "notes": "신규 입사자 등록"
            }
        }


class QRRegistrationResponse(BaseModel):
    """QR코드 등록 응답"""
    
    token_id: str = Field(..., description="토큰 ID")
    token: str = Field(..., description="등록 토큰")
    qr_code: str = Field(..., description="QR코드 이미지 (base64)")
    registration_url: str = Field(..., description="등록 URL")
    expires_at: datetime = Field(..., description="만료 시간")
    department: str = Field(..., description="부서")
    worker_data: Dict[str, Any] = Field(..., description="근로자 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token_id": "123e4567-e89b-12d3-a456-426614174000",
                "token": "abc123def456ghi789jkl012mno345pqr678stu901",
                "qr_code": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAA...",
                "registration_url": "https://safework.jclee.me/register?token=abc123...",
                "expires_at": "2025-01-18T15:30:00Z",
                "department": "건설부",
                "worker_data": {
                    "name": "홍길동",
                    "employee_id": "EMP001",
                    "department": "건설부"
                }
            }
        }


class RegistrationStatusResponse(BaseModel):
    """등록 상태 응답"""
    
    token_id: str = Field(..., description="토큰 ID")
    status: RegistrationStatus = Field(..., description="등록 상태")
    department: str = Field(..., description="부서")
    position: Optional[str] = Field(None, description="직급")
    expires_at: datetime = Field(..., description="만료 시간")
    is_expired: bool = Field(..., description="만료 여부")
    worker_data: Dict[str, Any] = Field(..., description="근로자 정보")
    registered_worker_id: Optional[int] = Field(None, description="등록된 근로자 ID")
    registered_at: Optional[datetime] = Field(None, description="등록 완료 시간")
    registered_by: Optional[str] = Field(None, description="등록 처리자")
    created_at: datetime = Field(..., description="생성 시간")


class PendingRegistrationResponse(BaseModel):
    """대기 중인 등록 응답"""
    
    token_id: str = Field(..., description="토큰 ID")
    token: str = Field(..., description="등록 토큰")
    department: str = Field(..., description="부서")
    position: Optional[str] = Field(None, description="직급")
    worker_data: Dict[str, Any] = Field(..., description="근로자 정보")
    expires_at: datetime = Field(..., description="만료 시간")
    created_by: str = Field(..., description="생성자")
    created_at: datetime = Field(..., description="생성 시간")


class PendingRegistrationListResponse(BaseModel):
    """대기 중인 등록 목록 응답"""
    
    registrations: List[PendingRegistrationResponse] = Field(..., description="등록 목록")
    total: int = Field(..., description="총 개수")
    
    class Config:
        json_schema_extra = {
            "example": {
                "registrations": [
                    {
                        "token_id": "123e4567-e89b-12d3-a456-426614174000",
                        "token": "abc123def456ghi789jkl012mno345pqr678stu901",
                        "department": "건설부",
                        "position": "대리",
                        "worker_data": {
                            "name": "홍길동",
                            "employee_id": "EMP001"
                        },
                        "expires_at": "2025-01-18T15:30:00Z",
                        "created_by": "admin",
                        "created_at": "2025-01-17T15:30:00Z"
                    }
                ],
                "total": 1
            }
        }


class WorkerRegistrationFormData(BaseModel):
    """근로자 등록 폼 데이터 (간소화된 버전)"""
    
    name: str = Field(..., min_length=1, max_length=50, description="성명")
    employee_id: str = Field(..., min_length=1, max_length=20, description="사번") 
    department: str = Field(..., min_length=1, max_length=100, description="부서")
    position: Optional[str] = Field(None, max_length=50, description="직급")
    phone: Optional[str] = Field(None, max_length=20, description="연락처")
    email: Optional[str] = Field(None, max_length=100, description="이메일")
    birth_date: Optional[str] = Field(None, description="생년월일 (YYYY-MM-DD)")
    address: Optional[str] = Field(None, description="주소")
    emergency_contact: Optional[str] = Field(None, max_length=100, description="비상연락처 이름")
    emergency_phone: Optional[str] = Field(None, max_length=20, description="비상연락처 전화번호")


class CompleteRegistrationRequest(BaseModel):
    """등록 완료 요청"""
    
    token: str = Field(..., description="등록 토큰")
    worker_data: Optional[WorkerRegistrationFormData] = Field(None, description="근로자 등록 정보")
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456ghi789jkl012mno345pqr678stu901",
                "worker_data": {
                    "name": "홍길동",
                    "employee_id": "EMP001",
                    "department": "건설부",
                    "position": "사원",
                    "phone": "010-1234-5678",
                    "email": "hong@company.com"
                }
            }
        }


class CompleteRegistrationResponse(BaseModel):
    """등록 완료 응답"""
    
    success: bool = Field(..., description="성공 여부")
    worker_id: Optional[int] = Field(None, description="등록된 근로자 ID")
    message: str = Field(..., description="결과 메시지")
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "worker_id": 123,
                "message": "근로자 등록이 완료되었습니다"
            }
        }


class QRRegistrationStatistics(BaseModel):
    """QR코드 등록 통계"""
    
    total_generated: int = Field(..., description="총 생성 수")
    pending_count: int = Field(..., description="대기 중인 수")
    completed_count: int = Field(..., description="완료된 수")
    expired_count: int = Field(..., description="만료된 수")
    departments: Dict[str, int] = Field(..., description="부서별 통계")
    
    class Config:
        json_schema_extra = {
            "example": {
                "total_generated": 100,
                "pending_count": 15,
                "completed_count": 80,
                "expired_count": 5,
                "departments": {
                    "건설부": 45,
                    "관리부": 30,
                    "안전부": 25
                }
            }
        }


class QRRegistrationFilter(BaseModel):
    """QR코드 등록 필터"""
    
    department: Optional[str] = Field(None, description="부서 필터")
    status: Optional[RegistrationStatus] = Field(None, description="상태 필터")
    created_by: Optional[str] = Field(None, description="생성자 필터")
    date_from: Optional[str] = Field(None, description="시작 날짜 (YYYY-MM-DD)")
    date_to: Optional[str] = Field(None, description="종료 날짜 (YYYY-MM-DD)")
    
    class Config:
        json_schema_extra = {
            "example": {
                "department": "건설부",
                "status": "pending",
                "created_by": "admin",
                "date_from": "2025-01-01",
                "date_to": "2025-01-31"
            }
        }


if __name__ == "__main__":
    # 검증 테스트
    print("✅ QR코드 등록 스키마 검증 시작")
    
    # 1. 근로자 등록 데이터 검증
    worker_data = WorkerRegistrationData(
        name="홍길동",
        employee_id="EMP001",
        phone="010-1234-5678",
        email="hong@example.com",
        employment_type="정규직",
        work_type="건설업",
        birth_date="1990-01-01",
        blood_type="A",
        is_special_exam_target=False
    )
    assert worker_data.name == "홍길동"
    assert worker_data.phone == "010-1234-5678"
    
    # 2. QR코드 등록 요청 검증
    request = QRRegistrationRequest(
        worker_data=worker_data,
        department="건설부",
        position="대리",
        expires_in_hours=24,
        notes="신규 입사자"
    )
    assert request.department == "건설부"
    assert request.expires_in_hours == 24
    
    # 3. 등록 완료 요청 검증
    complete_request = CompleteRegistrationRequest(
        token="abc123def456",
        additional_info={"notes": "등록 완료"}
    )
    assert complete_request.token == "abc123def456"
    
    # 4. 필터 검증
    filter_request = QRRegistrationFilter(
        department="건설부",
        status=RegistrationStatus.PENDING,
        date_from="2025-01-01",
        date_to="2025-01-31"
    )
    assert filter_request.department == "건설부"
    assert filter_request.status == RegistrationStatus.PENDING
    
    print("✅ 모든 검증 테스트 통과!")
    print("QR코드 등록 스키마가 정상적으로 작동합니다.")