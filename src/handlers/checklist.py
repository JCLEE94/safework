"""
체크리스트 관리 API 핸들러
Checklist Management API Handlers
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
from ..models.checklist import (
    ChecklistTemplate, ChecklistTemplateItem, ChecklistInstance, ChecklistInstanceItem,
    ChecklistAttachment, ChecklistSchedule, ChecklistType, ChecklistStatus, ChecklistPriority
)
from ..schemas.checklist import (
    ChecklistTemplateCreate, ChecklistTemplateUpdate, ChecklistTemplateResponse,
    ChecklistInstanceCreate, ChecklistInstanceUpdate, ChecklistInstanceResponse,
    ChecklistInstanceListResponse, ChecklistStatistics, DepartmentChecklistStats,
    ChecklistFilter, PaginatedChecklistTemplateResponse, PaginatedChecklistInstanceResponse,
    ChecklistScheduleCreate, ChecklistScheduleResponse, ChecklistInstanceItemCheck
)

router = APIRouter(prefix="/api/v1/checklists", tags=["checklists"])


# ===== 체크리스트 템플릿 API =====

@router.get("/templates", response_model=PaginatedChecklistTemplateResponse)
async def get_checklist_templates(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    type: Optional[ChecklistType] = Query(None, description="체크리스트 유형"),
    is_active: Optional[bool] = Query(None, description="활성 상태"),
    search: Optional[str] = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 템플릿 목록 조회"""
    try:
        # 기본 쿼리
        query = select(ChecklistTemplate).options(selectinload(ChecklistTemplate.items))
        count_query = select(func.count(ChecklistTemplate.id))

        # 필터 조건 적용
        conditions = []
        
        if type:
            conditions.append(ChecklistTemplate.type == type)
        if is_active is not None:
            conditions.append(ChecklistTemplate.is_active == is_active)
        if search:
            search_condition = or_(
                ChecklistTemplate.name.ilike(f"%{search}%"),
                ChecklistTemplate.name_korean.ilike(f"%{search}%"),
                ChecklistTemplate.description.ilike(f"%{search}%")
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
        query = query.offset(offset).limit(size).order_by(ChecklistTemplate.created_at.desc())

        # 데이터 조회
        result = await db.execute(query)
        templates = result.scalars().all()

        # 응답 데이터 변환
        items = [ChecklistTemplateResponse.model_validate(template) for template in templates]
        pages = (total + size - 1) // size

        return PaginatedChecklistTemplateResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크리스트 템플릿 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/templates", response_model=ChecklistTemplateResponse)
async def create_checklist_template(
    template_data: ChecklistTemplateCreate,
    user_id: str = "system",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 템플릿 생성"""
    try:
        # 새 템플릿 생성
        new_template = ChecklistTemplate(
            name=template_data.name,
            name_korean=template_data.name_korean,
            type=template_data.type,
            description=template_data.description,
            is_active=template_data.is_active,
            is_mandatory=template_data.is_mandatory,
            frequency_days=template_data.frequency_days,
            legal_basis=template_data.legal_basis,
            created_by=user_id
        )

        db.add(new_template)
        await db.flush()  # ID 생성을 위해 flush

        # 템플릿 항목들 생성
        for item_data in template_data.items:
            new_item = ChecklistTemplateItem(
                template_id=new_template.id,
                **item_data.model_dump()
            )
            db.add(new_item)

        await db.commit()
        await db.refresh(new_template)

        # 관계 데이터와 함께 조회
        result = await db.execute(
            select(ChecklistTemplate)
            .options(selectinload(ChecklistTemplate.items))
            .where(ChecklistTemplate.id == new_template.id)
        )
        created_template = result.scalar_one()

        return ChecklistTemplateResponse.model_validate(created_template)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"체크리스트 템플릿 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/templates/{template_id}", response_model=ChecklistTemplateResponse)
async def get_checklist_template(
    template_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 템플릿 상세 조회"""
    try:
        result = await db.execute(
            select(ChecklistTemplate)
            .options(selectinload(ChecklistTemplate.items))
            .where(ChecklistTemplate.id == template_id)
        )
        template = result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="체크리스트 템플릿을 찾을 수 없습니다")

        return ChecklistTemplateResponse.model_validate(template)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크리스트 템플릿 조회 중 오류가 발생했습니다: {str(e)}")


# ===== 체크리스트 인스턴스 API =====

@router.get("/instances", response_model=PaginatedChecklistInstanceResponse)
async def get_checklist_instances(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    status: Optional[ChecklistStatus] = Query(None, description="상태"),
    priority: Optional[ChecklistPriority] = Query(None, description="우선순위"),
    assignee: Optional[str] = Query(None, description="담당자"),
    department: Optional[str] = Query(None, description="부서"),
    search: Optional[str] = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 인스턴스 목록 조회"""
    try:
        # 기본 쿼리 (템플릿 정보 조인)
        query = select(
            ChecklistInstance,
            ChecklistTemplate.name.label("template_name"),
            ChecklistTemplate.type.label("template_type")
        ).join(ChecklistTemplate)
        
        count_query = select(func.count(ChecklistInstance.id))

        # 필터 조건 적용
        conditions = []
        
        if status:
            conditions.append(ChecklistInstance.status == status)
        if priority:
            conditions.append(ChecklistInstance.priority == priority)
        if assignee:
            conditions.append(ChecklistInstance.assignee.ilike(f"%{assignee}%"))
        if department:
            conditions.append(ChecklistInstance.department.ilike(f"%{department}%"))
        if search:
            search_condition = or_(
                ChecklistInstance.title.ilike(f"%{search}%"),
                ChecklistInstance.notes.ilike(f"%{search}%")
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
        query = query.offset(offset).limit(size).order_by(ChecklistInstance.created_at.desc())

        # 데이터 조회
        result = await db.execute(query)
        rows = result.all()

        # 응답 데이터 변환
        items = []
        for row in rows:
            instance = row[0]
            template_name = row[1]
            template_type = row[2]
            
            instance_dict = ChecklistInstanceListResponse.model_validate(instance).model_dump()
            instance_dict['template_name'] = template_name
            instance_dict['template_type'] = template_type
            
            items.append(ChecklistInstanceListResponse(**instance_dict))

        pages = (total + size - 1) // size

        return PaginatedChecklistInstanceResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크리스트 인스턴스 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/instances", response_model=ChecklistInstanceResponse)
async def create_checklist_instance(
    instance_data: ChecklistInstanceCreate,
    user_id: str = "system",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 인스턴스 생성"""
    try:
        # 템플릿 존재 확인
        template_result = await db.execute(
            select(ChecklistTemplate)
            .options(selectinload(ChecklistTemplate.items))
            .where(ChecklistTemplate.id == instance_data.template_id)
        )
        template = template_result.scalar_one_or_none()
        
        if not template:
            raise HTTPException(status_code=404, detail="체크리스트 템플릿을 찾을 수 없습니다")

        # 새 인스턴스 생성
        new_instance = ChecklistInstance(
            template_id=instance_data.template_id,
            title=instance_data.title,
            assignee=instance_data.assignee,
            department=instance_data.department,
            scheduled_date=instance_data.scheduled_date,
            due_date=instance_data.due_date,
            priority=instance_data.priority,
            notes=instance_data.notes,
            location=instance_data.location,
            created_by=user_id
        )

        db.add(new_instance)
        await db.flush()  # ID 생성을 위해 flush

        # 템플릿 항목들을 기반으로 인스턴스 항목들 생성
        max_total_score = 0
        for template_item in template.items:
            instance_item = ChecklistInstanceItem(
                instance_id=new_instance.id,
                template_item_id=template_item.id,
                is_checked=False
            )
            db.add(instance_item)
            max_total_score += template_item.max_score

        # 최대 총점 설정
        new_instance.max_total_score = max_total_score

        await db.commit()
        await db.refresh(new_instance)

        # 관계 데이터와 함께 조회
        result = await db.execute(
            select(ChecklistInstance)
            .options(selectinload(ChecklistInstance.items))
            .where(ChecklistInstance.id == new_instance.id)
        )
        created_instance = result.scalar_one()

        return ChecklistInstanceResponse.model_validate(created_instance)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"체크리스트 인스턴스 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/instances/{instance_id}", response_model=ChecklistInstanceResponse)
async def get_checklist_instance(
    instance_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 인스턴스 상세 조회"""
    try:
        result = await db.execute(
            select(ChecklistInstance)
            .options(
                selectinload(ChecklistInstance.items),
                selectinload(ChecklistInstance.template)
            )
            .where(ChecklistInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise HTTPException(status_code=404, detail="체크리스트 인스턴스를 찾을 수 없습니다")

        return ChecklistInstanceResponse.model_validate(instance)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크리스트 인스턴스 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/instances/{instance_id}", response_model=ChecklistInstanceResponse)
async def update_checklist_instance(
    instance_id: UUID,
    instance_data: ChecklistInstanceUpdate,
    user_id: str = "system",  # 실제로는 JWT에서 추출
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 인스턴스 수정 (점검 결과 포함)"""
    try:
        result = await db.execute(
            select(ChecklistInstance)
            .options(selectinload(ChecklistInstance.items))
            .where(ChecklistInstance.id == instance_id)
        )
        instance = result.scalar_one_or_none()
        
        if not instance:
            raise HTTPException(status_code=404, detail="체크리스트 인스턴스를 찾을 수 없습니다")

        # 기본 정보 업데이트
        update_data = instance_data.model_dump(exclude_unset=True, exclude={'items'})
        for field, value in update_data.items():
            setattr(instance, field, value)

        # 점검 항목 업데이트
        if instance_data.items:
            total_score = 0
            checked_count = 0
            
            for item_check in instance_data.items:
                # 해당 인스턴스 항목 찾기
                instance_item = None
                for item in instance.items:
                    if item.template_item_id == item_check.template_item_id:
                        instance_item = item
                        break
                
                if instance_item:
                    # 점검 결과 업데이트
                    instance_item.is_checked = item_check.is_checked
                    instance_item.is_compliant = item_check.is_compliant
                    instance_item.score = item_check.score
                    instance_item.findings = item_check.findings
                    instance_item.corrective_action = item_check.corrective_action
                    instance_item.corrective_due_date = item_check.corrective_due_date
                    
                    if item_check.is_checked:
                        instance_item.checked_at = datetime.now()
                        instance_item.checked_by = user_id
                        checked_count += 1
                        
                        if item_check.score is not None:
                            total_score += item_check.score

            # 총점 및 완료율 계산
            instance.total_score = total_score
            
            if len(instance.items) > 0:
                instance.completion_rate = int((checked_count / len(instance.items)) * 100)
                
                # 모든 항목이 완료되면 상태를 완료로 변경
                if checked_count == len(instance.items):
                    instance.status = ChecklistStatus.COMPLETED
                    instance.completed_at = datetime.now()
                elif checked_count > 0:
                    instance.status = ChecklistStatus.IN_PROGRESS
                    if not instance.started_at:
                        instance.started_at = datetime.now()

        await db.commit()
        await db.refresh(instance)

        # 관계 데이터와 함께 다시 조회
        updated_result = await db.execute(
            select(ChecklistInstance)
            .options(selectinload(ChecklistInstance.items))
            .where(ChecklistInstance.id == instance_id)
        )
        updated_instance = updated_result.scalar_one()

        return ChecklistInstanceResponse.model_validate(updated_instance)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"체크리스트 인스턴스 수정 중 오류가 발생했습니다: {str(e)}")


# ===== 체크리스트 통계 API =====

@router.get("/statistics", response_model=ChecklistStatistics)
async def get_checklist_statistics(
    db: AsyncSession = Depends(get_db)
):
    """체크리스트 통계 조회"""
    try:
        # 총 인스턴스 수
        total_result = await db.execute(select(func.count(ChecklistInstance.id)))
        total_instances = total_result.scalar() or 0

        # 상태별 통계
        status_result = await db.execute(
            select(ChecklistInstance.status, func.count(ChecklistInstance.id))
            .group_by(ChecklistInstance.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.fetchall()}

        # 유형별 통계 (템플릿 조인)
        type_result = await db.execute(
            select(ChecklistTemplate.type, func.count(ChecklistInstance.id))
            .join(ChecklistInstance)
            .group_by(ChecklistTemplate.type)
        )
        by_type = {row[0].value: row[1] for row in type_result.fetchall()}

        # 우선순위별 통계
        priority_result = await db.execute(
            select(ChecklistInstance.priority, func.count(ChecklistInstance.id))
            .group_by(ChecklistInstance.priority)
        )
        by_priority = {row[0].value: row[1] for row in priority_result.fetchall()}

        # 기한 초과 수
        overdue_result = await db.execute(
            select(func.count(ChecklistInstance.id))
            .where(
                and_(
                    ChecklistInstance.due_date < datetime.now(),
                    ChecklistInstance.status.in_([ChecklistStatus.PENDING, ChecklistStatus.IN_PROGRESS])
                )
            )
        )
        overdue_count = overdue_result.scalar() or 0

        # 마감 임박 수 (3일 이내)
        due_soon_date = datetime.now() + timedelta(days=3)
        due_soon_result = await db.execute(
            select(func.count(ChecklistInstance.id))
            .where(
                and_(
                    ChecklistInstance.due_date.isnot(None),
                    ChecklistInstance.due_date <= due_soon_date,
                    ChecklistInstance.due_date > datetime.now(),
                    ChecklistInstance.status.in_([ChecklistStatus.PENDING, ChecklistStatus.IN_PROGRESS])
                )
            )
        )
        due_soon_count = due_soon_result.scalar() or 0

        # 평균 완료율
        completion_result = await db.execute(
            select(func.avg(ChecklistInstance.completion_rate))
            .where(ChecklistInstance.completion_rate.isnot(None))
        )
        completion_rate = completion_result.scalar() or 0.0

        # 이번 달 완료 수
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        this_month_result = await db.execute(
            select(func.count(ChecklistInstance.id))
            .where(
                and_(
                    ChecklistInstance.completed_at >= month_start,
                    ChecklistInstance.status == ChecklistStatus.COMPLETED
                )
            )
        )
        this_month_completed = this_month_result.scalar() or 0

        return ChecklistStatistics(
            total_instances=total_instances,
            by_status=by_status,
            by_type=by_type,
            by_priority=by_priority,
            overdue_count=overdue_count,
            due_soon_count=due_soon_count,
            completion_rate=float(completion_rate),
            this_month_completed=this_month_completed
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"체크리스트 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/department-stats", response_model=List[DepartmentChecklistStats])
async def get_department_checklist_statistics(
    db: AsyncSession = Depends(get_db)
):
    """부서별 체크리스트 통계 조회"""
    try:
        # 부서별 통계 계산
        dept_result = await db.execute(
            select(
                ChecklistInstance.department,
                func.count(ChecklistInstance.id).label('total'),
                func.count(
                    func.case(
                        (ChecklistInstance.status == ChecklistStatus.PENDING, 1)
                    )
                ).label('pending'),
                func.count(
                    func.case(
                        (
                            and_(
                                ChecklistInstance.due_date < datetime.now(),
                                ChecklistInstance.status.in_([ChecklistStatus.PENDING, ChecklistStatus.IN_PROGRESS])
                            ), 1
                        )
                    )
                ).label('overdue'),
                func.avg(ChecklistInstance.completion_rate).label('avg_completion')
            )
            .where(ChecklistInstance.department.isnot(None))
            .group_by(ChecklistInstance.department)
        )

        department_stats = []
        for row in dept_result.fetchall():
            dept, total, pending, overdue, avg_completion = row
            completion_rate = avg_completion if avg_completion is not None else 0.0
            
            department_stats.append(DepartmentChecklistStats(
                department=dept,
                total_instances=total,
                pending_instances=pending,
                overdue_instances=overdue,
                completion_rate=float(completion_rate)
            ))

        return department_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"부서별 체크리스트 통계 조회 중 오류가 발생했습니다: {str(e)}")