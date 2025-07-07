"""
특별관리물질 관리 API 핸들러
Special Materials Management API Handlers
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json

from ..config.database import get_db
from ..models.special_materials import (
    SpecialMaterial, SpecialMaterialUsage, ExposureAssessment, SpecialMaterialMonitoring,
    ControlMeasure, SpecialMaterialType, ExposureLevel, MonitoringStatus
)
from ..utils.auth_deps import get_current_user_id
from ..schemas.special_materials import (
    SpecialMaterialCreate, SpecialMaterialUpdate, SpecialMaterialResponse,
    SpecialMaterialUsageCreate, SpecialMaterialUsageResponse,
    ExposureAssessmentCreate, ExposureAssessmentResponse,
    SpecialMaterialMonitoringCreate, SpecialMaterialMonitoringResponse,
    ControlMeasureCreate, ControlMeasureResponse,
    SpecialMaterialStatistics, DepartmentSpecialMaterialStats,
    SpecialMaterialFilter, PaginatedSpecialMaterialResponse, PaginatedUsageResponse, PaginatedMonitoringResponse
)

router = APIRouter(prefix="/api/v1/special-materials", tags=["special-materials"])


# ===== 특별관리물질 마스터 API =====

@router.get("/", response_model=PaginatedSpecialMaterialResponse)
async def get_special_materials(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    material_type: Optional[SpecialMaterialType] = Query(None, description="물질 유형"),
    is_prohibited: Optional[bool] = Query(None, description="사용금지 여부"),
    requires_permit: Optional[bool] = Query(None, description="허가 필요 여부"),
    search: Optional[str] = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db)
):
    """특별관리물질 목록 조회"""
    try:
        # 기본 쿼리
        query = select(SpecialMaterial)
        count_query = select(func.count(SpecialMaterial.id))

        # 필터 조건 적용
        conditions = []
        
        if material_type:
            conditions.append(SpecialMaterial.material_type == material_type)
        if is_prohibited is not None:
            conditions.append(SpecialMaterial.is_prohibited == is_prohibited)
        if requires_permit is not None:
            conditions.append(SpecialMaterial.requires_permit == requires_permit)
        if search:
            search_condition = or_(
                SpecialMaterial.material_name.ilike(f"%{search}%"),
                SpecialMaterial.material_name_korean.ilike(f"%{search}%"),
                SpecialMaterial.material_code.ilike(f"%{search}%"),
                SpecialMaterial.cas_number.ilike(f"%{search}%")
            )
            conditions.append(search_condition)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 총 개수 조회
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션 적용
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(SpecialMaterial.created_at.desc())

        # 데이터 조회
        result = await db.execute(query)
        materials = result.scalars().all()

        # 응답 데이터 변환
        items = [SpecialMaterialResponse.model_validate(material) for material in materials]
        pages = (total + size - 1) // size

        return PaginatedSpecialMaterialResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"특별관리물질 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/", response_model=SpecialMaterialResponse)
async def create_special_material(
    material_data: SpecialMaterialCreate,
    current_user_id: str = Depends(get_current_user_id),  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """특별관리물질 등록"""
    try:
        # 중복 코드 확인
        existing_result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.material_code == material_data.material_code)
        )
        existing_material = existing_result.scalar_one_or_none()
        
        if existing_material:
            raise HTTPException(status_code=400, detail="이미 존재하는 물질 코드입니다")

        # 새 물질 생성
        new_material = SpecialMaterial(
            **material_data.model_dump(),
            created_by=user_id
        )

        db.add(new_material)
        await db.commit()
        await db.refresh(new_material)

        return SpecialMaterialResponse.model_validate(new_material)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"특별관리물질 등록 중 오류가 발생했습니다: {str(e)}")


@router.get("/{material_id}", response_model=SpecialMaterialResponse)
async def get_special_material(
    material_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """특별관리물질 상세 조회"""
    try:
        result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == material_id)
        )
        material = result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        return SpecialMaterialResponse.model_validate(material)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"특별관리물질 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/{material_id}", response_model=SpecialMaterialResponse)
async def update_special_material(
    material_id: UUID,
    material_data: SpecialMaterialUpdate,
    current_user_id: str = Depends(get_current_user_id),  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """특별관리물질 수정"""
    try:
        result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == material_id)
        )
        material = result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        # 데이터 업데이트
        update_data = material_data.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(material, field, value)

        await db.commit()
        await db.refresh(material)

        return SpecialMaterialResponse.model_validate(material)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"특별관리물질 수정 중 오류가 발생했습니다: {str(e)}")


# ===== 사용 기록 API =====

@router.get("/usage", response_model=PaginatedUsageResponse)
async def get_usage_records(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    material_id: Optional[UUID] = Query(None, description="물질 ID"),
    worker_id: Optional[UUID] = Query(None, description="작업자 ID"),
    location: Optional[str] = Query(None, description="사용 장소"),
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    db: AsyncSession = Depends(get_db)
):
    """사용 기록 목록 조회"""
    try:
        # 기본 쿼리 (물질 정보 조인)
        query = select(
            SpecialMaterialUsage,
            SpecialMaterial.material_name_korean.label("material_name")
        ).join(SpecialMaterial)
        
        count_query = select(func.count(SpecialMaterialUsage.id))

        # 필터 조건 적용
        conditions = []
        
        if material_id:
            conditions.append(SpecialMaterialUsage.material_id == material_id)
        if worker_id:
            conditions.append(SpecialMaterialUsage.worker_id == worker_id)
        if location:
            conditions.append(SpecialMaterialUsage.usage_location.ilike(f"%{location}%"))
        if start_date:
            conditions.append(SpecialMaterialUsage.usage_date >= start_date)
        if end_date:
            conditions.append(SpecialMaterialUsage.usage_date <= end_date)

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 총 개수 조회
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션 적용
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(SpecialMaterialUsage.usage_date.desc())

        # 데이터 조회
        result = await db.execute(query)
        rows = result.all()

        # 응답 데이터 변환
        items = []
        for row in rows:
            usage = row[0]
            material_name = row[1]
            
            usage_dict = SpecialMaterialUsageResponse.model_validate(usage).model_dump()
            usage_dict['material_name'] = material_name
            
            items.append(SpecialMaterialUsageResponse(**usage_dict))

        pages = (total + size - 1) // size

        return PaginatedUsageResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"사용 기록 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/usage", response_model=SpecialMaterialUsageResponse)
async def create_usage_record(
    usage_data: SpecialMaterialUsageCreate,
    current_user_id: str = Depends(get_current_user_id),  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """사용 기록 등록"""
    try:
        # 물질 존재 확인
        material_result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == usage_data.material_id)
        )
        material = material_result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        # 새 사용 기록 생성
        new_usage = SpecialMaterialUsage(
            **usage_data.model_dump(),
            recorded_by=user_id
        )

        db.add(new_usage)
        await db.commit()
        await db.refresh(new_usage)

        return SpecialMaterialUsageResponse.model_validate(new_usage)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"사용 기록 등록 중 오류가 발생했습니다: {str(e)}")


# ===== 노출 평가 API =====

@router.get("/exposure-assessments", response_model=List[ExposureAssessmentResponse])
async def get_exposure_assessments(
    material_id: Optional[UUID] = Query(None, description="물질 ID"),
    exposure_level: Optional[ExposureLevel] = Query(None, description="노출 수준"),
    start_date: Optional[datetime] = Query(None, description="시작일"),
    end_date: Optional[datetime] = Query(None, description="종료일"),
    db: AsyncSession = Depends(get_db)
):
    """노출 평가 목록 조회"""
    try:
        # 기본 쿼리
        query = select(
            ExposureAssessment,
            SpecialMaterial.material_name_korean.label("material_name")
        ).join(SpecialMaterial)

        # 필터 조건 적용
        conditions = []
        
        if material_id:
            conditions.append(ExposureAssessment.material_id == material_id)
        if exposure_level:
            conditions.append(ExposureAssessment.exposure_level == exposure_level)
        if start_date:
            conditions.append(ExposureAssessment.assessment_date >= start_date)
        if end_date:
            conditions.append(ExposureAssessment.assessment_date <= end_date)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(ExposureAssessment.assessment_date.desc())

        # 데이터 조회
        result = await db.execute(query)
        rows = result.all()

        # 응답 데이터 변환
        assessments = []
        for row in rows:
            assessment = row[0]
            material_name = row[1]
            
            assessment_dict = ExposureAssessmentResponse.model_validate(assessment).model_dump()
            assessment_dict['material_name'] = material_name
            
            assessments.append(ExposureAssessmentResponse(**assessment_dict))

        return assessments

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"노출 평가 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/exposure-assessments", response_model=ExposureAssessmentResponse)
async def create_exposure_assessment(
    assessment_data: ExposureAssessmentCreate,
    db: AsyncSession = Depends(get_db)
):
    """노출 평가 등록"""
    try:
        # 물질 존재 확인
        material_result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == assessment_data.material_id)
        )
        material = material_result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        # 새 노출 평가 생성
        new_assessment = ExposureAssessment(**assessment_data.model_dump())

        db.add(new_assessment)
        await db.commit()
        await db.refresh(new_assessment)

        return ExposureAssessmentResponse.model_validate(new_assessment)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"노출 평가 등록 중 오류가 발생했습니다: {str(e)}")


# ===== 모니터링 API =====

@router.get("/monitoring", response_model=PaginatedMonitoringResponse)
async def get_monitoring_records(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    material_id: Optional[UUID] = Query(None, description="물질 ID"),
    status: Optional[MonitoringStatus] = Query(None, description="상태"),
    monitoring_type: Optional[str] = Query(None, description="모니터링 유형"),
    overdue_only: bool = Query(False, description="기한 초과만"),
    db: AsyncSession = Depends(get_db)
):
    """모니터링 기록 목록 조회"""
    try:
        # 기본 쿼리
        query = select(
            SpecialMaterialMonitoring,
            SpecialMaterial.material_name_korean.label("material_name")
        ).join(SpecialMaterial)
        
        count_query = select(func.count(SpecialMaterialMonitoring.id))

        # 필터 조건 적용
        conditions = []
        
        if material_id:
            conditions.append(SpecialMaterialMonitoring.material_id == material_id)
        if status:
            conditions.append(SpecialMaterialMonitoring.status == status)
        if monitoring_type:
            conditions.append(SpecialMaterialMonitoring.monitoring_type.ilike(f"%{monitoring_type}%"))
        if overdue_only:
            conditions.append(
                and_(
                    SpecialMaterialMonitoring.scheduled_date < datetime.now(),
                    SpecialMaterialMonitoring.status.in_([MonitoringStatus.PENDING, MonitoringStatus.IN_PROGRESS])
                )
            )

        if conditions:
            query = query.where(and_(*conditions))
            count_query = count_query.where(and_(*conditions))

        # 총 개수 조회
        total_result = await db.execute(count_query)
        total = total_result.scalar() or 0

        # 페이지네이션 적용
        offset = (page - 1) * size
        query = query.offset(offset).limit(size).order_by(SpecialMaterialMonitoring.scheduled_date.desc())

        # 데이터 조회
        result = await db.execute(query)
        rows = result.all()

        # 응답 데이터 변환
        items = []
        for row in rows:
            monitoring = row[0]
            material_name = row[1]
            
            monitoring_dict = SpecialMaterialMonitoringResponse.model_validate(monitoring).model_dump()
            monitoring_dict['material_name'] = material_name
            
            items.append(SpecialMaterialMonitoringResponse(**monitoring_dict))

        pages = (total + size - 1) // size

        return PaginatedMonitoringResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"모니터링 기록 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/monitoring", response_model=SpecialMaterialMonitoringResponse)
async def create_monitoring_record(
    monitoring_data: SpecialMaterialMonitoringCreate,
    current_user_id: str = Depends(get_current_user_id),  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """모니터링 기록 등록"""
    try:
        # 물질 존재 확인
        material_result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == monitoring_data.material_id)
        )
        material = material_result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        # 새 모니터링 기록 생성
        new_monitoring = SpecialMaterialMonitoring(
            **monitoring_data.model_dump(),
            created_by=user_id
        )

        db.add(new_monitoring)
        await db.commit()
        await db.refresh(new_monitoring)

        return SpecialMaterialMonitoringResponse.model_validate(new_monitoring)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"모니터링 기록 등록 중 오류가 발생했습니다: {str(e)}")


# ===== 통계 API =====

@router.get("/statistics", response_model=SpecialMaterialStatistics)
async def get_special_material_statistics(
    db: AsyncSession = Depends(get_db)
):
    """특별관리물질 통계 조회"""
    try:
        # 총 물질 수
        total_result = await db.execute(select(func.count(SpecialMaterial.id)))
        total_materials = total_result.scalar() or 0

        # 유형별 통계
        type_result = await db.execute(
            select(SpecialMaterial.material_type, func.count(SpecialMaterial.id))
            .group_by(SpecialMaterial.material_type)
        )
        by_type = {row[0].value: row[1] for row in type_result.fetchall()}

        # 사용금지 물질 수
        prohibited_result = await db.execute(
            select(func.count(SpecialMaterial.id))
            .where(SpecialMaterial.is_prohibited == True)
        )
        prohibited_materials = prohibited_result.scalar() or 0

        # 허가 필요 물질 수
        permit_result = await db.execute(
            select(func.count(SpecialMaterial.id))
            .where(SpecialMaterial.requires_permit == True)
        )
        permit_required_materials = permit_result.scalar() or 0

        # 총 사용 기록 수
        usage_result = await db.execute(select(func.count(SpecialMaterialUsage.id)))
        total_usage_records = usage_result.scalar() or 0

        # 총 노출 평가 수
        assessment_result = await db.execute(select(func.count(ExposureAssessment.id)))
        total_exposure_assessments = assessment_result.scalar() or 0

        # 고위험 노출 수
        high_risk_result = await db.execute(
            select(func.count(ExposureAssessment.id))
            .where(ExposureAssessment.exposure_level.in_([ExposureLevel.HIGH, ExposureLevel.CRITICAL]))
        )
        high_risk_exposures = high_risk_result.scalar() or 0

        # 기한 초과 모니터링 수
        overdue_result = await db.execute(
            select(func.count(SpecialMaterialMonitoring.id))
            .where(
                and_(
                    SpecialMaterialMonitoring.scheduled_date < datetime.now(),
                    SpecialMaterialMonitoring.status.in_([MonitoringStatus.PENDING, MonitoringStatus.IN_PROGRESS])
                )
            )
        )
        overdue_monitoring = overdue_result.scalar() or 0

        # 대기 중인 시정조치 수
        actions_result = await db.execute(
            select(func.count(SpecialMaterialMonitoring.id))
            .where(
                and_(
                    SpecialMaterialMonitoring.corrective_actions.isnot(None),
                    SpecialMaterialMonitoring.action_status != "completed"
                )
            )
        )
        pending_corrective_actions = actions_result.scalar() or 0

        return SpecialMaterialStatistics(
            total_materials=total_materials,
            by_type=by_type,
            prohibited_materials=prohibited_materials,
            permit_required_materials=permit_required_materials,
            total_usage_records=total_usage_records,
            total_exposure_assessments=total_exposure_assessments,
            high_risk_exposures=high_risk_exposures,
            overdue_monitoring=overdue_monitoring,
            pending_corrective_actions=pending_corrective_actions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"특별관리물질 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/department-stats", response_model=List[DepartmentSpecialMaterialStats])
async def get_department_statistics(
    db: AsyncSession = Depends(get_db)
):
    """부서별 특별관리물질 통계 조회"""
    try:
        # 부서별 통계 계산 (사용 기록 기준)
        dept_result = await db.execute(
            select(
                SpecialMaterialUsage.usage_location.label('department'),
                func.count(func.distinct(SpecialMaterialUsage.material_id)).label('materials_used'),
                func.count(SpecialMaterialUsage.id).label('usage_records')
            )
            .where(SpecialMaterialUsage.usage_location.isnot(None))
            .group_by(SpecialMaterialUsage.usage_location)
        )

        department_stats = []
        for row in dept_result.fetchall():
            dept, materials_used, usage_records = row
            
            # 고위험 노출 수 (부서별)
            high_risk_result = await db.execute(
                select(func.count(ExposureAssessment.id))
                .where(
                    and_(
                        ExposureAssessment.assessment_location.ilike(f"%{dept}%"),
                        ExposureAssessment.exposure_level.in_([ExposureLevel.HIGH, ExposureLevel.CRITICAL])
                    )
                )
            )
            high_risk_exposures = high_risk_result.scalar() or 0
            
            # 기한 초과 모니터링 수 (부서별)
            overdue_result = await db.execute(
                select(func.count(SpecialMaterialMonitoring.id))
                .where(
                    and_(
                        SpecialMaterialMonitoring.location.ilike(f"%{dept}%"),
                        SpecialMaterialMonitoring.scheduled_date < datetime.now(),
                        SpecialMaterialMonitoring.status.in_([MonitoringStatus.PENDING, MonitoringStatus.IN_PROGRESS])
                    )
                )
            )
            overdue_monitoring = overdue_result.scalar() or 0
            
            # 준수율 계산 (기준 초과가 아닌 모니터링 비율)
            compliance_result = await db.execute(
                select(
                    func.count(SpecialMaterialMonitoring.id).label('total'),
                    func.count(
                        func.case(
                            (SpecialMaterialMonitoring.compliance_status == True, 1)
                        )
                    ).label('compliant')
                )
                .where(SpecialMaterialMonitoring.location.ilike(f"%{dept}%"))
            )
            
            compliance_row = compliance_result.fetchone()
            total_monitoring = compliance_row[0] if compliance_row else 0
            compliant_monitoring = compliance_row[1] if compliance_row else 0
            compliance_rate = (compliant_monitoring / total_monitoring * 100) if total_monitoring > 0 else 100.0
            
            department_stats.append(DepartmentSpecialMaterialStats(
                department=dept,
                total_materials_used=materials_used,
                total_usage_records=usage_records,
                high_risk_exposures=high_risk_exposures,
                overdue_monitoring=overdue_monitoring,
                compliance_rate=float(compliance_rate)
            ))

        return department_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"부서별 특별관리물질 통계 조회 중 오류가 발생했습니다: {str(e)}")


# ===== 관리 조치 API =====

@router.get("/control-measures", response_model=List[ControlMeasureResponse])
async def get_control_measures(
    material_id: Optional[UUID] = Query(None, description="물질 ID"),
    is_active: Optional[bool] = Query(None, description="활성 상태"),
    db: AsyncSession = Depends(get_db)
):
    """관리 조치 목록 조회"""
    try:
        # 기본 쿼리
        query = select(
            ControlMeasure,
            SpecialMaterial.material_name_korean.label("material_name")
        ).join(SpecialMaterial)

        # 필터 조건 적용
        conditions = []
        
        if material_id:
            conditions.append(ControlMeasure.material_id == material_id)
        if is_active is not None:
            conditions.append(ControlMeasure.is_active == is_active)

        if conditions:
            query = query.where(and_(*conditions))

        query = query.order_by(ControlMeasure.implementation_date.desc())

        # 데이터 조회
        result = await db.execute(query)
        rows = result.all()

        # 응답 데이터 변환
        measures = []
        for row in rows:
            measure = row[0]
            material_name = row[1]
            
            measure_dict = ControlMeasureResponse.model_validate(measure).model_dump()
            measure_dict['material_name'] = material_name
            
            measures.append(ControlMeasureResponse(**measure_dict))

        return measures

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"관리 조치 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/control-measures", response_model=ControlMeasureResponse)
async def create_control_measure(
    measure_data: ControlMeasureCreate,
    current_user_id: str = Depends(get_current_user_id),  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """관리 조치 등록"""
    try:
        # 물질 존재 확인
        material_result = await db.execute(
            select(SpecialMaterial).where(SpecialMaterial.id == measure_data.material_id)
        )
        material = material_result.scalar_one_or_none()
        
        if not material:
            raise HTTPException(status_code=404, detail="특별관리물질을 찾을 수 없습니다")

        # 새 관리 조치 생성
        new_measure = ControlMeasure(
            **measure_data.model_dump(),
            created_by=user_id
        )

        db.add(new_measure)
        await db.commit()
        await db.refresh(new_measure)

        return ControlMeasureResponse.model_validate(new_measure)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"관리 조치 등록 중 오류가 발생했습니다: {str(e)}")