"""
QR코드 생성 및 관리 서비스

이 모듈은 근로자 등록을 위한 QR코드 생성 및 관리 기능을 제공합니다.
- QR코드 생성 (qrcode 라이브러리 사용)
- 등록 토큰 생성 및 검증
- 등록 상태 관리

외부 패키지:
- qrcode: QR코드 생성 (https://pypi.org/project/qrcode/)
- pillow: 이미지 처리 (https://pypi.org/project/Pillow/)
- python-jose: JWT 토큰 처리 (https://pypi.org/project/python-jose/)

예시 입력:
- worker_data: {"name": "홍길동", "employee_id": "EMP001", "department": "건설부"}
- expires_in: 3600 (1시간)

예시 출력:
- QR코드 이미지 (base64 인코딩)
- 등록 토큰 정보
- 등록 URL
"""

import base64
import io
import json
import secrets
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
import uuid

import qrcode
from PIL import Image
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, or_

from src.config.settings import get_settings
from src.models.qr_registration import QRRegistrationToken, QRRegistrationLog, RegistrationStatus
from src.utils.logger import logger

settings = get_settings()


class QRCodeService:
    """QR코드 생성 및 관리 서비스"""
    
    def __init__(self):
        self.base_url = settings.base_url or "https://safework.jclee.me"
        self.token_expiry_hours = 24  # 24시간 유효
        
    async def generate_qr_registration_token(
        self,
        worker_data: Dict[str, Any],
        department: str,
        position: Optional[str] = None,
        expires_in_hours: int = 24,
        created_by: str = "system",
        db: AsyncSession = None
    ) -> Dict[str, Any]:
        """
        QR코드 등록 토큰 생성
        
        Args:
            worker_data: 근로자 기본 정보
            department: 부서
            position: 직급
            expires_in_hours: 유효시간 (시간)
            created_by: 생성자
            db: 데이터베이스 세션
            
        Returns:
            Dict containing token, qr_code, and registration_url
        """
        try:
            # 토큰 생성
            token = secrets.token_urlsafe(32)
            expires_at = datetime.utcnow() + timedelta(hours=expires_in_hours)
            
            # 등록 URL 생성
            registration_url = f"{self.base_url}/worker-registration?token={token}"
            
            # QR코드 생성
            qr_code_data = self._generate_qr_code(registration_url)
            
            # 데이터베이스에 토큰 저장
            if db:
                db_token = QRRegistrationToken(
                    token=token,
                    qr_code_data=qr_code_data,
                    worker_data=json.dumps(worker_data, ensure_ascii=False),
                    department=department,
                    position=position,
                    expires_at=expires_at,
                    created_by=created_by
                )
                
                db.add(db_token)
                await db.commit()
                await db.refresh(db_token)
                
                # 로그 기록
                await self._log_action(
                    db_token.id, "created", "success", 
                    f"QR코드 등록 토큰 생성 완료 - 부서: {department}",
                    created_by, db
                )
                
                logger.info(f"QR 등록 토큰 생성 완료: {token[:10]}... (부서: {department})")
                
                return {
                    "token_id": str(db_token.id),
                    "token": token,
                    "qr_code": qr_code_data,
                    "registration_url": registration_url,
                    "expires_at": expires_at.isoformat(),
                    "department": department,
                    "worker_data": worker_data
                }
            else:
                # 데이터베이스 없이 임시 생성
                return {
                    "token": token,
                    "qr_code": qr_code_data,
                    "registration_url": registration_url,
                    "expires_at": expires_at.isoformat(),
                    "department": department,
                    "worker_data": worker_data
                }
                
        except Exception as e:
            logger.error(f"QR코드 생성 중 오류 발생: {str(e)}")
            raise
    
    def _generate_qr_code(self, data: str, size: int = 300) -> str:
        """
        QR코드 이미지 생성
        
        Args:
            data: QR코드에 포함될 데이터
            size: 이미지 크기 (픽셀)
            
        Returns:
            Base64 인코딩된 QR코드 이미지
        """
        try:
            # QR코드 생성
            qr = qrcode.QRCode(
                version=1,
                error_correction=qrcode.constants.ERROR_CORRECT_M,
                box_size=10,
                border=4,
            )
            qr.add_data(data)
            qr.make(fit=True)
            
            # 이미지 생성
            img = qr.make_image(fill_color="black", back_color="white")
            
            # 이미지 리사이즈
            img = img.resize((size, size), Image.Resampling.LANCZOS)
            
            # Base64 인코딩
            buffer = io.BytesIO()
            img.save(buffer, format='PNG')
            img_str = base64.b64encode(buffer.getvalue()).decode()
            
            return f"data:image/png;base64,{img_str}"
            
        except Exception as e:
            logger.error(f"QR코드 이미지 생성 중 오류: {str(e)}")
            raise
    
    async def validate_registration_token(
        self, 
        token: str, 
        db: AsyncSession
    ) -> Optional[QRRegistrationToken]:
        """
        등록 토큰 검증
        
        Args:
            token: 검증할 토큰
            db: 데이터베이스 세션
            
        Returns:
            유효한 토큰 객체 또는 None
        """
        try:
            # 토큰 조회
            stmt = select(QRRegistrationToken).where(
                and_(
                    QRRegistrationToken.token == token,
                    QRRegistrationToken.status == RegistrationStatus.PENDING,
                    QRRegistrationToken.expires_at > datetime.utcnow()
                )
            )
            result = await db.execute(stmt)
            db_token = result.scalar_one_or_none()
            
            if db_token:
                # 로그 기록
                await self._log_action(
                    db_token.id, "validated", "success",
                    "토큰 검증 성공", "system", db
                )
                logger.info(f"토큰 검증 성공: {token[:10]}...")
                return db_token
            else:
                logger.warning(f"유효하지 않은 토큰: {token[:10]}...")
                return None
                
        except Exception as e:
            logger.error(f"토큰 검증 중 오류: {str(e)}")
            return None
    
    async def complete_registration(
        self,
        token: str,
        worker_id: int,
        registered_by: str,
        db: AsyncSession
    ) -> bool:
        """
        등록 완료 처리
        
        Args:
            token: 등록 토큰
            worker_id: 등록된 근로자 ID
            registered_by: 등록 처리자
            db: 데이터베이스 세션
            
        Returns:
            성공 여부
        """
        try:
            # 토큰 조회
            stmt = select(QRRegistrationToken).where(QRRegistrationToken.token == token)
            result = await db.execute(stmt)
            db_token = result.scalar_one_or_none()
            
            if not db_token:
                return False
            
            # 상태 업데이트
            db_token.status = RegistrationStatus.COMPLETED
            db_token.worker_id = worker_id
            db_token.completed_at = datetime.utcnow()
            
            await db.commit()
            
            # 로그 기록
            await self._log_action(
                db_token.id, "completed", "success",
                f"등록 완료 - 근로자 ID: {worker_id}",
                registered_by, db
            )
            
            logger.info(f"등록 완료: 토큰 {token[:10]}... -> 근로자 ID {worker_id}")
            return True
            
        except Exception as e:
            logger.error(f"등록 완료 처리 중 오류: {str(e)}")
            return False
    
    async def get_registration_status(
        self,
        token: str,
        db: AsyncSession
    ) -> Optional[Dict[str, Any]]:
        """
        등록 상태 조회
        
        Args:
            token: 조회할 토큰
            db: 데이터베이스 세션
            
        Returns:
            등록 상태 정보
        """
        try:
            # 토큰 조회
            stmt = select(QRRegistrationToken).where(QRRegistrationToken.token == token)
            result = await db.execute(stmt)
            db_token = result.scalar_one_or_none()
            
            if not db_token:
                return None
            
            return {
                "token_id": str(db_token.id),
                "status": db_token.status,
                "department": db_token.department,
                "position": db_token.position,
                "expires_at": db_token.expires_at.isoformat(),
                "is_expired": db_token.is_expired(),
                "worker_data": db_token.get_worker_data(),
                "worker_id": db_token.worker_id,
                "completed_at": db_token.completed_at.isoformat() if db_token.completed_at else None,
                "created_at": db_token.created_at.isoformat()
            }
            
        except Exception as e:
            logger.error(f"등록 상태 조회 중 오류: {str(e)}")
            return None
    
    async def list_pending_registrations(
        self,
        department: Optional[str] = None,
        limit: int = 50,
        db: AsyncSession = None
    ) -> List[Dict[str, Any]]:
        """
        대기 중인 등록 목록 조회
        
        Args:
            department: 부서 필터
            limit: 최대 결과 수
            db: 데이터베이스 세션
            
        Returns:
            대기 중인 등록 목록
        """
        try:
            conditions = [
                QRRegistrationToken.status == RegistrationStatus.PENDING,
                QRRegistrationToken.expires_at > datetime.utcnow()
            ]
            
            if department:
                conditions.append(QRRegistrationToken.department == department)
            
            stmt = select(QRRegistrationToken).where(
                and_(*conditions)
            ).order_by(QRRegistrationToken.created_at.desc()).limit(limit)
            
            result = await db.execute(stmt)
            tokens = result.scalars().all()
            
            return [
                {
                    "token_id": str(token.id),
                    "token": token.token,
                    "department": token.department,
                    "position": token.position,
                    "worker_data": token.get_worker_data(),
                    "expires_at": token.expires_at.isoformat(),
                    "created_by": token.created_by,
                    "created_at": token.created_at.isoformat()
                }
                for token in tokens
            ]
            
        except Exception as e:
            logger.error(f"대기 등록 목록 조회 중 오류: {str(e)}")
            return []
    
    async def _log_action(
        self,
        token_id: uuid.UUID,
        action: str,
        status: str,
        message: str,
        user_id: str,
        db: AsyncSession,
        additional_data: Optional[Dict[str, Any]] = None
    ):
        """로그 기록"""
        try:
            log = QRRegistrationLog(
                token_id=token_id,
                action=action,
                status=status,
                message=message,
                user_id=user_id
            )
            
            if additional_data:
                log.set_additional_data(additional_data)
            
            db.add(log)
            await db.commit()
            
        except Exception as e:
            logger.error(f"로그 기록 중 오류: {str(e)}")


# 싱글톤 인스턴스
qr_service = QRCodeService()


def get_qr_service() -> QRCodeService:
    """QR코드 서비스 의존성 주입"""
    return qr_service


if __name__ == "__main__":
    # 검증 테스트
    print("✅ QR코드 서비스 검증 시작")
    
    # 1. 서비스 초기화
    service = QRCodeService()
    
    # 2. QR코드 생성 테스트
    test_data = "https://safework.jclee.me/register?token=test123"
    qr_code = service._generate_qr_code(test_data)
    assert qr_code.startswith("data:image/png;base64,")
    print("✅ QR코드 생성 테스트 통과")
    
    # 3. 등록 토큰 생성 테스트 (DB 없이)
    import asyncio
    
    async def test_token_generation():
        worker_data = {
            "name": "홍길동",
            "employee_id": "EMP001",
            "phone": "010-1234-5678",
            "department": "건설부"
        }
        
        result = await service.generate_qr_registration_token(
            worker_data=worker_data,
            department="건설부",
            position="대리",
            expires_in_hours=24,
            created_by="admin"
        )
        
        assert "token" in result
        assert "qr_code" in result
        assert "registration_url" in result
        assert result["department"] == "건설부"
        print("✅ 등록 토큰 생성 테스트 통과")
        
        return result
    
    # 테스트 실행
    token_result = asyncio.run(test_token_generation())
    
    print("✅ 모든 검증 테스트 통과!")
    print("QR코드 서비스가 정상적으로 작동합니다.")
    print(f"생성된 토큰: {token_result['token'][:20]}...")
    print(f"등록 URL: {token_result['registration_url']}")