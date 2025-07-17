"""
QR코드 기반 근로자 등록 시스템 모델

이 모듈은 QR코드를 통한 근로자 등록 및 관리 기능을 제공합니다.
- QR코드 생성 및 검증
- 임시 등록 토큰 관리
- 등록 진행 상태 추적

외부 패키지:
- qrcode: QR코드 생성 (https://pypi.org/project/qrcode/)
- python-jose: JWT 토큰 처리 (https://pypi.org/project/python-jose/)

예시 입력:
- worker_data: {"name": "홍길동", "employee_id": "EMP001", "department": "건설부"}
- expires_in: 3600 (1시간)

예시 출력:
- QR코드 이미지 (base64 인코딩)
- 등록 토큰 (JWT)
- 등록 상태 정보
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any
import json
import secrets
from sqlalchemy import Column, String, DateTime, Boolean, Text, Index, func, Integer, ForeignKey
from sqlalchemy.dialects.postgresql import UUID, JSON
from sqlalchemy.sql import func
import uuid

from src.config.database import Base


class RegistrationStatus(str, Enum):
    """등록 상태"""
    PENDING = "pending"      # 등록 대기
    COMPLETED = "completed"   # 등록 완료
    EXPIRED = "expired"       # 만료됨
    FAILED = "failed"         # 실패
    CANCELLED = "cancelled"   # 취소됨


class QRRegistrationToken(Base):
    """QR코드 등록 토큰"""
    
    __tablename__ = "qr_registration_tokens"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 토큰 정보
    token = Column(String(255), unique=True, nullable=False, index=True, comment="등록 토큰")
    qr_code_data = Column(Text, nullable=False, comment="QR코드 데이터 (base64)")
    
    # 등록 정보
    worker_data = Column(Text, nullable=False, comment="근로자 정보 (JSON)")
    department = Column(String(100), nullable=False, index=True, comment="부서")
    position = Column(String(100), comment="직급")
    
    # 상태 관리
    status = Column(String(20), default=RegistrationStatus.PENDING, index=True, comment="등록 상태")
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True, comment="만료 시간")
    
    # 등록 완료 정보
    worker_id = Column(Integer, ForeignKey('workers.id', ondelete='SET NULL'), comment="등록된 근로자 ID")
    completed_at = Column(DateTime(timezone=True), comment="등록 완료 시간")
    error_message = Column(Text, comment="오류 메시지")
    
    # 생성 정보
    created_by = Column(String(100), nullable=False, comment="생성자")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="수정 시간")
    
    def is_expired(self) -> bool:
        """토큰 만료 여부 확인"""
        return datetime.utcnow() > self.expires_at
    
    def get_worker_data(self) -> Dict[str, Any]:
        """근로자 데이터 파싱"""
        try:
            return json.loads(self.worker_data)
        except json.JSONDecodeError:
            return {}
    
    def set_worker_data(self, data: Dict[str, Any]) -> None:
        """근로자 데이터 설정"""
        self.worker_data = json.dumps(data, ensure_ascii=False)


class QRRegistrationLog(Base):
    """QR코드 등록 로그"""
    
    __tablename__ = "qr_registration_logs"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    
    # 관련 토큰
    token_id = Column(UUID(as_uuid=True), ForeignKey('qr_registration_tokens.id', ondelete='CASCADE'), nullable=False, index=True, comment="토큰 ID")
    
    # 로그 정보
    action = Column(String(50), nullable=False, index=True, comment="작업")
    status = Column(String(20), nullable=False, index=True, comment="상태")
    message = Column(Text, comment="메시지")
    
    # 메타데이터
    meta_data = Column(JSON, comment="메타데이터")
    
    # 사용자 정보
    user_agent = Column(Text, comment="사용자 에이전트")
    ip_address = Column(String(45), comment="사용자 IP")
    
    # 생성 정보
    created_by = Column(String(100), nullable=False, comment="생성자")
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="생성 시간")
    
    def get_metadata(self) -> Dict[str, Any]:
        """메타데이터 파싱"""
        if not self.meta_data:
            return {}
        return self.meta_data if isinstance(self.meta_data, dict) else {}
    
    def set_metadata(self, data: Dict[str, Any]) -> None:
        """메타데이터 설정"""
        self.meta_data = data


if __name__ == "__main__":
    # 검증 테스트
    print("✅ QR 등록 모델 검증 시작")
    
    # 1. 토큰 생성 테스트
    token = QRRegistrationToken(
        token=secrets.token_urlsafe(32),
        qr_code_data="test_qr_data",
        worker_data='{"name": "홍길동", "employee_id": "EMP001"}',
        department="건설부",
        expires_at=datetime.utcnow() + timedelta(hours=1),
        created_by="admin"
    )
    
    # 2. 데이터 파싱 테스트
    worker_data = token.get_worker_data()
    assert worker_data["name"] == "홍길동"
    assert worker_data["employee_id"] == "EMP001"
    
    # 3. 만료 확인 테스트
    assert not token.is_expired()
    
    # 4. 로그 생성 테스트
    log = QRRegistrationLog(
        token_id=token.id,
        action="created",
        status="success",
        message="QR코드 생성 완료",
        created_by="admin"
    )
    
    log.set_metadata({"qr_size": "200x200", "format": "PNG"})
    metadata = log.get_metadata()
    assert metadata["qr_size"] == "200x200"
    
    print("✅ 모든 검증 테스트 통과!")
    print("QR 등록 시스템 모델이 정상적으로 작동합니다.")