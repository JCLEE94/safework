"""
시스템 설정 관리 API 핸들러
System Settings Management API Handlers
"""

from fastapi import APIRouter, HTTPException, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List, Optional, Dict, Any
from datetime import datetime
import json

from ..config.database import get_db
from ..models.settings import SystemSettings, UserSettings, SettingsHistory
from ..schemas.settings import (
    SystemSettingsCreate, SystemSettingsUpdate, SystemSettingsResponse,
    UserSettingsCreate, UserSettingsUpdate, UserSettingsResponse,
    SettingsHistoryResponse, AllSettingsResponse, AllSettingsUpdate
)

router = APIRouter(prefix="/api/v1/settings", tags=["settings"])


# ===== 시스템 설정 API =====

@router.get("/system", response_model=SystemSettingsResponse)
async def get_system_settings(
    db: AsyncSession = Depends(get_db)
):
    """시스템 설정 조회"""
    try:
        result = await db.execute(select(SystemSettings).order_by(SystemSettings.id.desc()).limit(1))
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 기본 설정 생성
            default_settings = SystemSettings(
                company_name="건설업 보건관리 시스템",
                auto_backup_enabled=True,
                backup_frequency="daily",
                notification_enabled=True,
                email_notifications=True,
                sms_notifications=False,
                report_language="korean",
                data_retention_period=36,
                audit_log_enabled=True,
                password_policy_enabled=True,
                session_timeout=120,
                api_access_enabled=False,
                maintenance_mode=False,
                updated_by="system"
            )
            
            db.add(default_settings)
            await db.commit()
            await db.refresh(default_settings)
            settings = default_settings

        return SystemSettingsResponse.model_validate(settings)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 설정 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/system", response_model=SystemSettingsResponse)
async def update_system_settings(
    settings_data: SystemSettingsUpdate,
    user_id: str = "system",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """시스템 설정 수정"""
    try:
        # 현재 설정 조회
        result = await db.execute(select(SystemSettings).order_by(SystemSettings.id.desc()).limit(1))
        current_settings = result.scalar_one_or_none()
        
        if not current_settings:
            # 설정이 없으면 새로 생성
            if isinstance(settings_data, SystemSettingsUpdate):
                # SystemSettingsUpdate를 SystemSettingsCreate로 변환
                create_data = SystemSettingsCreate(
                    company_name=settings_data.company_name or "건설업 보건관리 시스템",
                    company_address=settings_data.company_address,
                    company_phone=settings_data.company_phone,
                    company_registration_number=settings_data.company_registration_number,
                    business_type=settings_data.business_type,
                    total_employees=settings_data.total_employees or 0,
                    safety_manager=settings_data.safety_manager,
                    health_manager=settings_data.health_manager,
                    representative_name=settings_data.representative_name,
                    auto_backup_enabled=settings_data.auto_backup_enabled if settings_data.auto_backup_enabled is not None else True,
                    backup_frequency=settings_data.backup_frequency or "daily",
                    notification_enabled=settings_data.notification_enabled if settings_data.notification_enabled is not None else True,
                    email_notifications=settings_data.email_notifications if settings_data.email_notifications is not None else True,
                    sms_notifications=settings_data.sms_notifications if settings_data.sms_notifications is not None else False,
                    report_language=settings_data.report_language or "korean",
                    data_retention_period=settings_data.data_retention_period or 36,
                    audit_log_enabled=settings_data.audit_log_enabled if settings_data.audit_log_enabled is not None else True,
                    password_policy_enabled=settings_data.password_policy_enabled if settings_data.password_policy_enabled is not None else True,
                    session_timeout=settings_data.session_timeout or 120,
                    api_access_enabled=settings_data.api_access_enabled if settings_data.api_access_enabled is not None else False,
                    maintenance_mode=settings_data.maintenance_mode if settings_data.maintenance_mode is not None else False
                )
                
                new_settings = SystemSettings(**create_data.model_dump(), updated_by=user_id)
            else:
                new_settings = SystemSettings(**settings_data.model_dump(), updated_by=user_id)
            
            db.add(new_settings)
            await db.commit()
            await db.refresh(new_settings)
            
            return SystemSettingsResponse.model_validate(new_settings)

        # 설정 변경 이력 기록
        update_data = settings_data.model_dump(exclude_unset=True)
        for key, new_value in update_data.items():
            if hasattr(current_settings, key):
                old_value = getattr(current_settings, key)
                if old_value != new_value:
                    # 변경 이력 생성
                    history = SettingsHistory(
                        setting_type="system",
                        setting_key=key,
                        old_value=str(old_value) if old_value is not None else None,
                        new_value=str(new_value) if new_value is not None else None,
                        changed_by=user_id
                    )
                    db.add(history)

        # 설정 업데이트
        for field, value in update_data.items():
            if hasattr(current_settings, field):
                setattr(current_settings, field, value)
        
        current_settings.updated_by = user_id
        
        await db.commit()
        await db.refresh(current_settings)

        return SystemSettingsResponse.model_validate(current_settings)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"시스템 설정 수정 중 오류가 발생했습니다: {str(e)}")


# ===== 사용자 설정 API =====

@router.get("/user", response_model=UserSettingsResponse)
async def get_user_settings(
    user_id: str = "default_user",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """사용자 설정 조회"""
    try:
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        settings = result.scalar_one_or_none()
        
        if not settings:
            # 기본 사용자 설정 생성
            default_settings = UserSettings(
                user_id=user_id,
                user_name="관리자",
                user_email="admin@company.com",
                user_role="시스템 관리자",
                department="안전관리팀",
                notification_preferences={
                    "accidents": True,
                    "health_exams": True,
                    "education_reminders": True,
                    "report_deadlines": True,
                    "system_updates": False
                },
                dashboard_layout="default",
                theme="light",
                language="korean",
                timezone="Asia/Seoul"
            )
            
            db.add(default_settings)
            await db.commit()
            await db.refresh(default_settings)
            settings = default_settings

        return UserSettingsResponse.model_validate(settings)

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용자 설정 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/user", response_model=UserSettingsResponse)
async def update_user_settings(
    settings_data: UserSettingsUpdate,
    user_id: str = "default_user",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """사용자 설정 수정"""
    try:
        # 현재 설정 조회
        result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        current_settings = result.scalar_one_or_none()
        
        if not current_settings:
            # 설정이 없으면 새로 생성
            create_data = UserSettingsCreate(
                user_id=user_id,
                user_name=settings_data.user_name or "관리자",
                user_email=settings_data.user_email,
                user_phone=settings_data.user_phone,
                user_role=settings_data.user_role,
                department=settings_data.department,
                notification_preferences=settings_data.notification_preferences or {
                    "accidents": True,
                    "health_exams": True,
                    "education_reminders": True,
                    "report_deadlines": True,
                    "system_updates": False
                },
                dashboard_layout=settings_data.dashboard_layout or "default",
                theme=settings_data.theme or "light",
                language=settings_data.language or "korean",
                timezone=settings_data.timezone or "Asia/Seoul"
            )
            
            new_settings = UserSettings(**create_data.model_dump())
            db.add(new_settings)
            await db.commit()
            await db.refresh(new_settings)
            
            return UserSettingsResponse.model_validate(new_settings)

        # 설정 변경 이력 기록
        update_data = settings_data.model_dump(exclude_unset=True)
        for key, new_value in update_data.items():
            if hasattr(current_settings, key):
                old_value = getattr(current_settings, key)
                if old_value != new_value:
                    # JSON 필드는 특별 처리
                    if key == 'notification_preferences':
                        old_str = json.dumps(old_value, ensure_ascii=False) if old_value else None
                        new_str = json.dumps(new_value, ensure_ascii=False) if new_value else None
                    else:
                        old_str = str(old_value) if old_value is not None else None
                        new_str = str(new_value) if new_value is not None else None
                    
                    # 변경 이력 생성
                    history = SettingsHistory(
                        setting_type="user",
                        setting_key=f"{user_id}.{key}",
                        old_value=old_str,
                        new_value=new_str,
                        changed_by=user_id
                    )
                    db.add(history)

        # 설정 업데이트
        for field, value in update_data.items():
            if hasattr(current_settings, field):
                setattr(current_settings, field, value)
        
        await db.commit()
        await db.refresh(current_settings)

        return UserSettingsResponse.model_validate(current_settings)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"사용자 설정 수정 중 오류가 발생했습니다: {str(e)}")


# ===== 통합 설정 API =====

@router.get("/", response_model=AllSettingsResponse)
async def get_all_settings(
    user_id: str = "default_user",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """전체 설정 조회"""
    try:
        # 시스템 설정 조회
        system_result = await db.execute(
            select(SystemSettings).order_by(SystemSettings.id.desc()).limit(1)
        )
        system_settings = system_result.scalar_one_or_none()
        
        # 사용자 설정 조회
        user_result = await db.execute(
            select(UserSettings).where(UserSettings.user_id == user_id)
        )
        user_settings = user_result.scalar_one_or_none()

        return AllSettingsResponse(
            system=SystemSettingsResponse.model_validate(system_settings) if system_settings else None,
            user=UserSettingsResponse.model_validate(user_settings) if user_settings else None
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/", response_model=AllSettingsResponse)
async def update_all_settings(
    settings_data: AllSettingsUpdate,
    user_id: str = "default_user",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """전체 설정 수정 (프론트엔드 호환)"""
    try:
        updated_system = None
        updated_user = None

        # 시스템 설정 수정
        if settings_data.system:
            system_result = await db.execute(
                select(SystemSettings).order_by(SystemSettings.id.desc()).limit(1)
            )
            current_system = system_result.scalar_one_or_none()
            
            if current_system:
                # 기존 설정 업데이트
                update_data = settings_data.system.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(current_system, field):
                        setattr(current_system, field, value)
                current_system.updated_by = user_id
                
                await db.commit()
                await db.refresh(current_system)
                updated_system = SystemSettingsResponse.model_validate(current_system)
            else:
                # 새 설정 생성
                create_data = settings_data.system.model_dump(exclude_unset=True)
                create_data['updated_by'] = user_id
                new_system = SystemSettings(**create_data)
                db.add(new_system)
                
                await db.commit()
                await db.refresh(new_system)
                updated_system = SystemSettingsResponse.model_validate(new_system)

        # 사용자 설정 수정
        if settings_data.user:
            user_result = await db.execute(
                select(UserSettings).where(UserSettings.user_id == user_id)
            )
            current_user = user_result.scalar_one_or_none()
            
            if current_user:
                # 기존 설정 업데이트
                update_data = settings_data.user.model_dump(exclude_unset=True)
                for field, value in update_data.items():
                    if hasattr(current_user, field):
                        setattr(current_user, field, value)
                
                await db.commit()
                await db.refresh(current_user)
                updated_user = UserSettingsResponse.model_validate(current_user)
            else:
                # 새 설정 생성
                create_data = settings_data.user.model_dump(exclude_unset=True)
                create_data['user_id'] = user_id
                new_user = UserSettings(**create_data)
                db.add(new_user)
                
                await db.commit()
                await db.refresh(new_user)
                updated_user = UserSettingsResponse.model_validate(new_user)

        return AllSettingsResponse(
            system=updated_system,
            user=updated_user
        )

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"설정 수정 중 오류가 발생했습니다: {str(e)}")


# ===== 설정 변경 이력 API =====

@router.get("/history", response_model=List[SettingsHistoryResponse])
async def get_settings_history(
    setting_type: Optional[str] = Query(None, description="설정 타입 (system/user)"),
    limit: int = Query(50, ge=1, le=500, description="조회 개수"),
    db: AsyncSession = Depends(get_db)
):
    """설정 변경 이력 조회"""
    try:
        query = select(SettingsHistory).order_by(SettingsHistory.created_at.desc())
        
        if setting_type:
            query = query.where(SettingsHistory.setting_type == setting_type)
        
        query = query.limit(limit)
        
        result = await db.execute(query)
        history_list = result.scalars().all()

        return [SettingsHistoryResponse.model_validate(history) for history in history_list]

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"설정 변경 이력 조회 중 오류가 발생했습니다: {str(e)}")


# ===== 시스템 상태 확인 API =====

@router.get("/status")
async def get_system_status(
    db: AsyncSession = Depends(get_db)
):
    """시스템 상태 확인"""
    try:
        # 시스템 설정에서 유지보수 모드 확인
        result = await db.execute(
            select(SystemSettings.maintenance_mode, SystemSettings.company_name)
            .order_by(SystemSettings.id.desc())
            .limit(1)
        )
        settings = result.first()
        
        if settings:
            maintenance_mode, company_name = settings
        else:
            maintenance_mode, company_name = False, "건설업 보건관리 시스템"

        return {
            "status": "maintenance" if maintenance_mode else "operational",
            "maintenance_mode": maintenance_mode,
            "company_name": company_name,
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"시스템 상태 확인 중 오류가 발생했습니다: {str(e)}")