"""
법정서식 관리 API 핸들러
Legal Forms Management API Handlers
"""

from fastapi import APIRouter, HTTPException, Depends, Query, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from sqlalchemy.orm import selectinload
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID

from ..config.database import get_db
from ..models.legal_forms import (
    LegalForm, LegalFormAttachment, LegalFormApproval, UnifiedDocument,
    LegalFormStatus, LegalFormPriority, LegalFormCategory
)
from ..schemas.legal_forms import (
    LegalFormCreate, LegalFormUpdate, LegalFormResponse, LegalFormListResponse,
    LegalFormStatistics, DepartmentStatistics, LegalFormFilter,
    PaginatedLegalFormResponse, UnifiedDocumentCreate, UnifiedDocumentUpdate,
    UnifiedDocumentResponse, PaginatedDocumentResponse, DocumentCategoryStats
)

router = APIRouter(prefix="/api/v1/legal-forms", tags=["legal-forms"])

# 통합 문서 라우터
unified_router = APIRouter(prefix="/api/v1/unified-documents", tags=["unified-documents"])


# ===== 법정서식 API =====

@router.get("/statistics", response_model=LegalFormStatistics)
async def get_legal_form_statistics(
    db: AsyncSession = Depends(get_db)
):
    """법정서식 통계 조회"""
    try:
        # 총 서식 수
        total_result = await db.execute(select(func.count(LegalForm.id)))
        total_forms = total_result.scalar() or 0

        # 상태별 통계
        status_result = await db.execute(
            select(LegalForm.status, func.count(LegalForm.id))
            .group_by(LegalForm.status)
        )
        by_status = {row[0].value: row[1] for row in status_result.fetchall()}

        # 분류별 통계
        category_result = await db.execute(
            select(LegalForm.category, func.count(LegalForm.id))
            .group_by(LegalForm.category)
        )
        by_category = {row[0].value: row[1] for row in category_result.fetchall()}

        # 우선순위별 통계
        priority_result = await db.execute(
            select(LegalForm.priority, func.count(LegalForm.id))
            .group_by(LegalForm.priority)
        )
        by_priority = {row[0].value: row[1] for row in priority_result.fetchall()}

        # 마감 임박 서식 (7일 이내)
        upcoming_deadline = datetime.now() + timedelta(days=7)
        upcoming_result = await db.execute(
            select(func.count(LegalForm.id))
            .where(
                and_(
                    LegalForm.submission_deadline.isnot(None),
                    LegalForm.submission_deadline <= upcoming_deadline,
                    LegalForm.submission_deadline > datetime.now(),
                    LegalForm.status.in_([LegalFormStatus.DRAFT, LegalFormStatus.IN_PROGRESS])
                )
            )
        )
        upcoming_deadlines = upcoming_result.scalar() or 0

        # 마감 초과 서식
        overdue_result = await db.execute(
            select(func.count(LegalForm.id))
            .where(
                and_(
                    LegalForm.submission_deadline.isnot(None),
                    LegalForm.submission_deadline < datetime.now(),
                    LegalForm.status.in_([LegalFormStatus.DRAFT, LegalFormStatus.IN_PROGRESS])
                )
            )
        )
        overdue_forms = overdue_result.scalar() or 0

        # 완료율 계산
        completed_count = by_status.get('completed', 0) + by_status.get('approved', 0)
        completion_rate = (completed_count / total_forms * 100) if total_forms > 0 else 0

        # 이번 달 제출 수
        month_start = datetime.now().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        monthly_result = await db.execute(
            select(func.count(LegalForm.id))
            .where(
                and_(
                    LegalForm.submitted_at >= month_start,
                    LegalForm.status.in_([LegalFormStatus.SUBMITTED, LegalFormStatus.APPROVED])
                )
            )
        )
        monthly_submissions = monthly_result.scalar() or 0

        return LegalFormStatistics(
            total_forms=total_forms,
            by_status=by_status,
            by_category=by_category,
            by_priority=by_priority,
            upcoming_deadlines=upcoming_deadlines,
            overdue_forms=overdue_forms,
            completion_rate=completion_rate,
            monthly_submissions=monthly_submissions
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/department-stats", response_model=List[DepartmentStatistics])
async def get_department_statistics(
    db: AsyncSession = Depends(get_db)
):
    """부서별 법정서식 통계 조회"""
    try:
        # 부서별 통계 계산
        dept_result = await db.execute(
            select(
                LegalForm.department,
                func.count(LegalForm.id).label('total'),
                func.count(
                    func.case(
                        (LegalForm.status == LegalFormStatus.IN_PROGRESS, 1)
                    )
                ).label('pending'),
                func.count(
                    func.case(
                        (
                            and_(
                                LegalForm.submission_deadline < datetime.now(),
                                LegalForm.status.in_([LegalFormStatus.DRAFT, LegalFormStatus.IN_PROGRESS])
                            ), 1
                        )
                    )
                ).label('overdue'),
                func.count(
                    func.case(
                        (LegalForm.status.in_([LegalFormStatus.COMPLETED, LegalFormStatus.APPROVED]), 1)
                    )
                ).label('completed')
            )
            .where(LegalForm.department.isnot(None))
            .group_by(LegalForm.department)
        )

        department_stats = []
        for row in dept_result.fetchall():
            dept, total, pending, overdue, completed = row
            completion_rate = (completed / total * 100) if total > 0 else 0
            
            department_stats.append(DepartmentStatistics(
                department=dept,
                total_forms=total,
                pending_forms=pending,
                overdue_forms=overdue,
                completion_rate=completion_rate
            ))

        return department_stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"부서별 통계 조회 중 오류가 발생했습니다: {str(e)}")


@router.get("/", response_model=PaginatedLegalFormResponse)
async def get_legal_forms(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    category: Optional[LegalFormCategory] = Query(None, description="서식 분류"),
    status: Optional[LegalFormStatus] = Query(None, description="서식 상태"),
    priority: Optional[LegalFormPriority] = Query(None, description="우선순위"),
    department: Optional[str] = Query(None, description="담당 부서"),
    search: Optional[str] = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db)
):
    """법정서식 목록 조회 (페이지네이션)"""
    try:
        # 기본 쿼리
        query = select(LegalForm)
        count_query = select(func.count(LegalForm.id))

        # 필터 조건 적용
        conditions = []
        
        if category:
            conditions.append(LegalForm.category == category)
        if status:
            conditions.append(LegalForm.status == status)
        if priority:
            conditions.append(LegalForm.priority == priority)
        if department:
            conditions.append(LegalForm.department == department)
        if search:
            search_condition = or_(
                LegalForm.form_name.ilike(f"%{search}%"),
                LegalForm.form_name_korean.ilike(f"%{search}%"),
                LegalForm.form_code.ilike(f"%{search}%"),
                LegalForm.description.ilike(f"%{search}%")
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
        query = query.offset(offset).limit(size).order_by(LegalForm.created_at.desc())

        # 데이터 조회
        result = await db.execute(query)
        forms = result.scalars().all()

        # 응답 데이터 변환
        items = [LegalFormListResponse.model_validate(form) for form in forms]
        pages = (total + size - 1) // size

        return PaginatedLegalFormResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"법정서식 목록 조회 중 오류가 발생했습니다: {str(e)}")


@router.post("/", response_model=LegalFormResponse)
async def create_legal_form(
    form_data: LegalFormCreate,
    db: AsyncSession = Depends(get_db)
):
    """법정서식 생성"""
    try:
        # 서식 코드 중복 확인
        existing_result = await db.execute(
            select(LegalForm).where(LegalForm.form_code == form_data.form_code)
        )
        if existing_result.scalar_one_or_none():
            raise HTTPException(status_code=400, detail="이미 존재하는 서식 코드입니다")

        # 새 법정서식 생성
        new_form = LegalForm(
            form_code=form_data.form_code,
            form_name=form_data.form_name,
            form_name_korean=form_data.form_name_korean,
            category=form_data.category,
            department=form_data.department,
            description=form_data.description,
            required_fields=[field.model_dump() for field in form_data.required_fields],
            submission_deadline=form_data.submission_deadline,
            regulatory_basis=form_data.regulatory_basis,
            template_path=form_data.template_path,
            priority=form_data.priority,
            assignee=form_data.assignee
        )

        db.add(new_form)
        await db.commit()
        await db.refresh(new_form)

        # 관계 데이터와 함께 조회
        result = await db.execute(
            select(LegalForm)
            .options(selectinload(LegalForm.attachments), selectinload(LegalForm.approval_history))
            .where(LegalForm.id == new_form.id)
        )
        created_form = result.scalar_one()

        return LegalFormResponse.model_validate(created_form)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"법정서식 생성 중 오류가 발생했습니다: {str(e)}")


@router.get("/{form_id}", response_model=LegalFormResponse)
async def get_legal_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """법정서식 상세 조회"""
    try:
        result = await db.execute(
            select(LegalForm)
            .options(selectinload(LegalForm.attachments), selectinload(LegalForm.approval_history))
            .where(LegalForm.id == form_id)
        )
        form = result.scalar_one_or_none()
        
        if not form:
            raise HTTPException(status_code=404, detail="법정서식을 찾을 수 없습니다")

        return LegalFormResponse.model_validate(form)

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"법정서식 조회 중 오류가 발생했습니다: {str(e)}")


@router.put("/{form_id}", response_model=LegalFormResponse)
async def update_legal_form(
    form_id: UUID,
    form_data: LegalFormUpdate,
    db: AsyncSession = Depends(get_db)
):
    """법정서식 수정"""
    try:
        result = await db.execute(select(LegalForm).where(LegalForm.id == form_id))
        form = result.scalar_one_or_none()
        
        if not form:
            raise HTTPException(status_code=404, detail="법정서식을 찾을 수 없습니다")

        # 업데이트할 필드만 적용
        update_data = form_data.model_dump(exclude_unset=True)
        
        # required_fields는 특별 처리
        if 'required_fields' in update_data and update_data['required_fields']:
            update_data['required_fields'] = [field.model_dump() for field in form_data.required_fields]

        for field, value in update_data.items():
            setattr(form, field, value)

        # 버전 증가
        form.version += 1

        await db.commit()
        await db.refresh(form)

        # 관계 데이터와 함께 조회
        updated_result = await db.execute(
            select(LegalForm)
            .options(selectinload(LegalForm.attachments), selectinload(LegalForm.approval_history))
            .where(LegalForm.id == form_id)
        )
        updated_form = updated_result.scalar_one()

        return LegalFormResponse.model_validate(updated_form)

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"법정서식 수정 중 오류가 발생했습니다: {str(e)}")


@router.delete("/{form_id}")
async def delete_legal_form(
    form_id: UUID,
    db: AsyncSession = Depends(get_db)
):
    """법정서식 삭제"""
    try:
        result = await db.execute(select(LegalForm).where(LegalForm.id == form_id))
        form = result.scalar_one_or_none()
        
        if not form:
            raise HTTPException(status_code=404, detail="법정서식을 찾을 수 없습니다")

        await db.delete(form)
        await db.commit()

        return {"message": "법정서식이 성공적으로 삭제되었습니다"}

    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"법정서식 삭제 중 오류가 발생했습니다: {str(e)}")


# ===== 통합 문서 API =====

@unified_router.get("/", response_model=PaginatedDocumentResponse)
async def get_unified_documents(
    page: int = Query(1, ge=1, description="페이지 번호"),
    size: int = Query(20, ge=1, le=100, description="페이지 크기"),
    category: Optional[str] = Query(None, description="문서 카테고리"),
    doc_type: Optional[str] = Query(None, description="문서 타입"),
    search: Optional[str] = Query(None, description="검색어"),
    db: AsyncSession = Depends(get_db)
):
    """통합 문서 목록 조회"""
    try:
        # 기본 쿼리
        query = select(UnifiedDocument)
        count_query = select(func.count(UnifiedDocument.id))

        # 필터 조건 적용
        conditions = []
        
        if category:
            conditions.append(UnifiedDocument.category == category)
        if doc_type:
            conditions.append(UnifiedDocument.type == doc_type)
        if search:
            search_condition = or_(
                UnifiedDocument.title.ilike(f"%{search}%"),
                UnifiedDocument.description.ilike(f"%{search}%")
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
        query = query.offset(offset).limit(size).order_by(UnifiedDocument.created_at.desc())

        # 데이터 조회
        result = await db.execute(query)
        documents = result.scalars().all()

        # 응답 데이터 변환
        items = [UnifiedDocumentResponse.model_validate(doc) for doc in documents]
        pages = (total + size - 1) // size

        return PaginatedDocumentResponse(
            items=items,
            total=total,
            page=page,
            size=size,
            pages=pages
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"통합 문서 목록 조회 중 오류가 발생했습니다: {str(e)}")


@unified_router.post("/", response_model=UnifiedDocumentResponse)
async def create_unified_document(
    document_data: UnifiedDocumentCreate,
    db: AsyncSession = Depends(get_db)
):
    """통합 문서 생성"""
    try:
        new_document = UnifiedDocument(
            title=document_data.title,
            type=document_data.type,
            category=document_data.category,
            file_path="",  # 실제 파일 업로드 시 설정
            file_size=0,   # 실제 파일 업로드 시 설정
            mime_type="application/octet-stream",  # 실제 파일 업로드 시 설정
            description=document_data.description,
            tags=document_data.tags,
            created_by=current_user_id,  # 실제 사용자 정보로 대체
            is_template=document_data.is_template,
            access_level=document_data.access_level,
            metadata=document_data.metadata
        )

        db.add(new_document)
        await db.commit()
        await db.refresh(new_document)

        return UnifiedDocumentResponse.model_validate(new_document)

    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"통합 문서 생성 중 오류가 발생했습니다: {str(e)}")


@unified_router.get("/categories/stats", response_model=List[DocumentCategoryStats])
async def get_category_statistics(
    db: AsyncSession = Depends(get_db)
):
    """문서 카테고리별 통계 조회"""
    try:
        result = await db.execute(
            select(
                UnifiedDocument.category,
                func.count(UnifiedDocument.id).label('total'),
                func.count(
                    func.case((UnifiedDocument.is_template == True, 1))
                ).label('templates')
            )
            .group_by(UnifiedDocument.category)
        )

        stats = []
        for row in result.fetchall():
            category, total, templates = row
            stats.append(DocumentCategoryStats(
                category_id=category,
                category_name=category,
                count=total,
                templates=templates
            ))

        return stats

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"카테고리 통계 조회 중 오류가 발생했습니다: {str(e)}")