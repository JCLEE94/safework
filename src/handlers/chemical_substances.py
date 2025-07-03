from typing import Optional, List
from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from sqlalchemy import select, func, and_, or_, Integer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
import os
import shutil

from src.config.database import get_db
from src.config.settings import get_settings
from src.models import ChemicalSubstance, ChemicalUsageRecord, Worker
from src.schemas.chemical_substance import (
    ChemicalSubstanceCreate, ChemicalSubstanceUpdate, ChemicalSubstanceResponse,
    ChemicalSubstanceListResponse, ChemicalWithUsageResponse,
    ChemicalUsageCreate, ChemicalStatistics
)

router = APIRouter(prefix="/api/v1/chemical-substances", tags=["chemical-substances"])


@router.post("/", response_model=ChemicalSubstanceResponse)
async def create_chemical_substance(
    chemical_data: ChemicalSubstanceCreate,
    db: AsyncSession = Depends(get_db)
):
    """화학물질 등록"""
    # Check for duplicate CAS number
    if chemical_data.cas_number:
        existing = await db.scalar(
            select(ChemicalSubstance)
            .where(ChemicalSubstance.cas_number == chemical_data.cas_number)
        )
        if existing:
            raise HTTPException(status_code=400, detail="이미 등록된 CAS 번호입니다")
    
    chemical = ChemicalSubstance(**chemical_data.model_dump())
    chemical.created_by = "system"  # TODO: Should come from auth
    db.add(chemical)
    await db.commit()
    await db.refresh(chemical)
    
    return chemical


@router.get("/", response_model=ChemicalSubstanceListResponse)
async def list_chemical_substances(
    page: int = Query(1, ge=1),
    size: int = Query(10, ge=1, le=100),
    search: Optional[str] = None,
    hazard_class: Optional[str] = None,
    status: Optional[str] = None,
    special_management: Optional[bool] = None,
    db: AsyncSession = Depends(get_db)
):
    """화학물질 목록 조회"""
    query = select(ChemicalSubstance)
    
    # Apply filters
    conditions = []
    if search:
        conditions.append(
            or_(
                ChemicalSubstance.korean_name.contains(search),
                ChemicalSubstance.english_name.contains(search),
                ChemicalSubstance.cas_number.contains(search)
            )
        )
    if hazard_class:
        conditions.append(ChemicalSubstance.hazard_class == hazard_class)
    if status:
        conditions.append(ChemicalSubstance.status == status)
    if special_management is not None:
        conditions.append(ChemicalSubstance.special_management_material == ('Y' if special_management else 'N'))
    
    if conditions:
        query = query.where(and_(*conditions))
    
    # Get total count
    count_query = select(func.count()).select_from(ChemicalSubstance)
    if conditions:
        count_query = count_query.where(and_(*conditions))
    total = await db.scalar(count_query)
    
    # Apply pagination
    query = query.offset((page - 1) * size).limit(size)
    query = query.order_by(ChemicalSubstance.korean_name)
    
    result = await db.execute(query)
    items = result.scalars().all()
    
    return ChemicalSubstanceListResponse(
        items=items,
        total=total,
        page=page,
        pages=(total + size - 1) // size,
        size=size
    )


@router.get("/statistics", response_model=ChemicalStatistics)
async def get_chemical_statistics(db: AsyncSession = Depends(get_db)):
    """화학물질 통계 조회"""
    # Total chemicals
    total = await db.scalar(select(func.count(ChemicalSubstance.id)))
    
    # By status
    status_stats = await db.execute(
        select(
            ChemicalSubstance.status,
            func.count(ChemicalSubstance.id).label("count")
        )
        .group_by(ChemicalSubstance.status)
    )
    status_counts = {row[0].value: row[1] for row in status_stats}
    
    # Special chemicals
    special_counts = await db.execute(
        select(
            func.sum(func.cast(ChemicalSubstance.special_management_material == 'Y', Integer)).label("special"),
            func.sum(func.cast(ChemicalSubstance.carcinogen == 'Y', Integer)).label("carcinogen"),
        )
    )
    special_row = special_counts.one()
    
    # By hazard class
    hazard_stats = await db.execute(
        select(
            ChemicalSubstance.hazard_class,
            func.count(ChemicalSubstance.id).label("count")
        )
        .group_by(ChemicalSubstance.hazard_class)
    )
    
    # Low stock items
    low_stock_query = await db.execute(
        select(ChemicalSubstance)
        .where(
            and_(
                ChemicalSubstance.current_quantity < ChemicalSubstance.minimum_quantity,
                ChemicalSubstance.status == 'IN_USE'
            )
        )
        .limit(get_settings().max_recent_items)
    )
    low_stock_items = []
    for item in low_stock_query.scalars():
        low_stock_items.append({
            "id": item.id,
            "korean_name": item.korean_name,
            "current_quantity": item.current_quantity,
            "minimum_quantity": item.minimum_quantity,
            "unit": item.quantity_unit
        })
    
    # Expired MSDS
    settings = get_settings()
    one_year_ago = datetime.utcnow().date() - timedelta(days=settings.health_exam_interval_days)
    expired_msds_query = await db.execute(
        select(ChemicalSubstance)
        .where(
            or_(
                ChemicalSubstance.msds_revision_date < one_year_ago,
                ChemicalSubstance.msds_file_path.is_(None)
            )
        )
        .limit(settings.max_recent_items)
    )
    expired_msds = []
    for item in expired_msds_query.scalars():
        expired_msds.append({
            "id": item.id,
            "korean_name": item.korean_name,
            "msds_revision_date": item.msds_revision_date.isoformat() if item.msds_revision_date else None,
            "has_msds": bool(item.msds_file_path)
        })
    
    return ChemicalStatistics(
        total_chemicals=total,
        in_use_count=status_counts.get("사용중", 0),
        expired_count=status_counts.get("유효기간만료", 0),
        special_management_count=special_row.special or 0,
        carcinogen_count=special_row.carcinogen or 0,
        low_stock_items=low_stock_items,
        expired_msds=expired_msds,
        by_hazard_class={row[0].value: row[1] for row in hazard_stats}
    )


@router.get("/inventory-check")
async def check_inventory_status(db: AsyncSession = Depends(get_db)):
    """재고 점검 현황"""
    # Items below minimum stock
    below_minimum = await db.execute(
        select(ChemicalSubstance)
        .where(
            and_(
                ChemicalSubstance.current_quantity < ChemicalSubstance.minimum_quantity,
                ChemicalSubstance.status == 'IN_USE'
            )
        )
    )
    
    # Items above maximum stock
    above_maximum = await db.execute(
        select(ChemicalSubstance)
        .where(
            and_(
                ChemicalSubstance.current_quantity > ChemicalSubstance.maximum_quantity,
                ChemicalSubstance.status == 'IN_USE'
            )
        )
    )
    
    # Expired items
    expired = await db.execute(
        select(ChemicalSubstance)
        .where(ChemicalSubstance.status == 'EXPIRED')
    )
    
    return {
        "below_minimum": [
            {
                "id": item.id,
                "name": item.korean_name,
                "current": item.current_quantity,
                "minimum": item.minimum_quantity,
                "shortage": item.minimum_quantity - item.current_quantity
            }
            for item in below_minimum.scalars()
        ],
        "above_maximum": [
            {
                "id": item.id,
                "name": item.korean_name,
                "current": item.current_quantity,
                "maximum": item.maximum_quantity,
                "excess": item.current_quantity - item.maximum_quantity
            }
            for item in above_maximum.scalars()
        ],
        "expired": [
            {
                "id": item.id,
                "name": item.korean_name,
                "quantity": item.current_quantity
            }
            for item in expired.scalars()
        ]
    }


@router.get("/{chemical_id}", response_model=ChemicalWithUsageResponse)
async def get_chemical_substance(chemical_id: int, db: AsyncSession = Depends(get_db)):
    """화학물질 상세 조회"""
    result = await db.execute(
        select(ChemicalSubstance)
        .options(selectinload(ChemicalSubstance.usage_records))
        .where(ChemicalSubstance.id == chemical_id)
    )
    chemical = result.scalar_one_or_none()
    
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")
    
    return chemical


@router.put("/{chemical_id}", response_model=ChemicalSubstanceResponse)
async def update_chemical_substance(
    chemical_id: int,
    chemical_update: ChemicalSubstanceUpdate,
    db: AsyncSession = Depends(get_db)
):
    """화학물질 정보 수정"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")
    
    # Update fields
    update_data = chemical_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(chemical, field, value)
    
    chemical.updated_at = datetime.utcnow()
    chemical.updated_by = "system"  # Should come from auth
    await db.commit()
    await db.refresh(chemical)
    
    return chemical


@router.delete("/{chemical_id}")
async def delete_chemical_substance(chemical_id: int, db: AsyncSession = Depends(get_db)):
    """화학물질 삭제"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")
    
    # Check if there are usage records
    usage_count = await db.scalar(
        select(func.count(ChemicalUsageRecord.id))
        .where(ChemicalUsageRecord.chemical_id == chemical_id)
    )
    
    if usage_count > 0:
        # Mark as disposed instead of deleting
        chemical.status = "DISPOSED"
        await db.commit()
        return {"message": "사용 기록이 있어 폐기 상태로 변경되었습니다"}
    
    await db.delete(chemical)
    await db.commit()
    
    return {"message": "화학물질이 삭제되었습니다"}


@router.post("/{chemical_id}/usage", response_model=dict)
async def record_chemical_usage(
    chemical_id: int,
    usage_data: ChemicalUsageCreate,
    db: AsyncSession = Depends(get_db)
):
    """화학물질 사용 기록"""
    # Check if chemical exists
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")
    
    # Check if worker exists
    worker = await db.get(Worker, usage_data.worker_id)
    if not worker:
        raise HTTPException(status_code=404, detail="근로자를 찾을 수 없습니다")
    
    # Create usage record
    usage = ChemicalUsageRecord(
        chemical_id=chemical_id,
        **usage_data.model_dump()
    )
    usage.created_by = "system"  # Should come from auth
    db.add(usage)
    
    # Update chemical quantity
    if chemical.current_quantity and usage_data.quantity_used:
        chemical.current_quantity -= usage_data.quantity_used
        if chemical.current_quantity < 0:
            chemical.current_quantity = 0
    
    await db.commit()
    
    return {
        "message": "사용 기록이 저장되었습니다",
        "remaining_quantity": chemical.current_quantity
    }


@router.post("/{chemical_id}/msds", response_model=dict)
async def upload_msds(
    chemical_id: int,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db)
):
    """MSDS 파일 업로드"""
    chemical = await db.get(ChemicalSubstance, chemical_id)
    if not chemical:
        raise HTTPException(status_code=404, detail="화학물질을 찾을 수 없습니다")
    
    # Validate file type
    if not file.filename.lower().endswith(('.pdf', '.doc', '.docx')):
        raise HTTPException(status_code=400, detail="PDF, DOC, DOCX 파일만 허용됩니다")
    
    # Create upload directory
    settings = get_settings()
    upload_dir = os.path.join(settings.upload_dir, settings.msds_upload_subdir)
    os.makedirs(upload_dir, exist_ok=True)
    
    # Save file
    timestamp = datetime.utcnow().strftime("%Y%m%d%H%M%S")
    filename = f"{chemical_id}_{timestamp}_{file.filename}"
    file_path = os.path.join(upload_dir, filename)
    
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
    
    # Update chemical record
    chemical.msds_file_path = file_path
    chemical.msds_revision_date = datetime.utcnow().date()
    await db.commit()
    
    return {
        "message": "MSDS 파일이 업로드되었습니다",
        "file_path": file_path
    }