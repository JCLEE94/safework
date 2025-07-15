from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field

from src.models.chemical_substance import HazardClass, StorageStatus


class ChemicalSubstanceBase(BaseModel):
    korean_name: str = Field(..., description="한글명")
    english_name: Optional[str] = Field(None, description="영문명")
    cas_number: Optional[str] = Field(None, description="CAS번호")
    un_number: Optional[str] = Field(None, description="UN번호")

    hazard_class: HazardClass = Field(..., description="유해성분류")
    hazard_statement: Optional[str] = Field(None, description="유해문구")
    precautionary_statement: Optional[str] = Field(None, description="예방조치문구")
    signal_word: Optional[str] = Field(None, description="신호어")

    physical_state: Optional[str] = Field(None, description="물리적상태")
    appearance: Optional[str] = Field(None, description="외관")
    odor: Optional[str] = Field(None, description="냄새")
    ph_value: Optional[float] = Field(None, description="pH")
    boiling_point: Optional[float] = Field(None, description="끓는점")
    melting_point: Optional[float] = Field(None, description="녹는점")
    flash_point: Optional[float] = Field(None, description="인화점")

    storage_location: Optional[str] = Field(None, description="보관장소")
    storage_condition: Optional[str] = Field(None, description="보관조건")
    incompatible_materials: Optional[str] = Field(None, description="피해야할물질")

    current_quantity: Optional[float] = Field(None, description="현재재고량")
    quantity_unit: Optional[str] = Field(None, description="단위")
    minimum_quantity: Optional[float] = Field(None, description="최소재고량")
    maximum_quantity: Optional[float] = Field(None, description="최대재고량")

    exposure_limit_twa: Optional[float] = Field(
        None, description="시간가중평균노출기준"
    )
    exposure_limit_stel: Optional[float] = Field(None, description="단시간노출기준")
    exposure_limit_ceiling: Optional[float] = Field(None, description="최고노출기준")

    msds_file_path: Optional[str] = Field(None, description="MSDS파일")
    msds_revision_date: Optional[date] = Field(None, description="MSDS개정일")
    manufacturer: Optional[str] = Field(None, description="제조사")
    supplier: Optional[str] = Field(None, description="공급사")
    emergency_contact: Optional[str] = Field(None, description="비상연락처")

    special_management_material: Optional[str] = Field("N", description="특별관리물질")
    carcinogen: Optional[str] = Field("N", description="발암물질")
    mutagen: Optional[str] = Field("N", description="변이원성물질")
    reproductive_toxin: Optional[str] = Field("N", description="생식독성물질")

    status: Optional[StorageStatus] = Field(StorageStatus.IN_USE, description="상태")
    notes: Optional[str] = Field(None, description="비고")


class ChemicalSubstanceCreate(ChemicalSubstanceBase):
    pass


class ChemicalSubstanceUpdate(BaseModel):
    storage_location: Optional[str] = None
    current_quantity: Optional[float] = None
    status: Optional[StorageStatus] = None
    msds_file_path: Optional[str] = None
    msds_revision_date: Optional[date] = None
    notes: Optional[str] = None


class ChemicalSubstanceResponse(ChemicalSubstanceBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ChemicalUsageBase(BaseModel):
    usage_date: datetime = Field(..., description="사용일시")
    worker_id: int = Field(..., description="사용자ID")
    quantity_used: float = Field(..., description="사용량")
    quantity_unit: Optional[str] = Field(None, description="단위")
    purpose: Optional[str] = Field(None, description="사용목적")
    work_location: Optional[str] = Field(None, description="작업장소")

    ventilation_used: Optional[str] = Field("N", description="환기장치사용")
    ppe_used: Optional[str] = Field(None, description="보호구착용")
    exposure_duration_minutes: Optional[int] = Field(None, description="노출시간(분)")

    incident_occurred: Optional[str] = Field("N", description="사고발생")
    incident_description: Optional[str] = Field(None, description="사고내용")


class ChemicalUsageCreate(ChemicalUsageBase):
    chemical_id: int


class ChemicalUsageResponse(ChemicalUsageBase):
    id: int
    chemical_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChemicalWithUsageResponse(ChemicalSubstanceResponse):
    usage_records: List[ChemicalUsageResponse] = []


class ChemicalSubstanceListResponse(BaseModel):
    items: List[ChemicalSubstanceResponse]
    total: int
    page: int
    pages: int
    size: int


class ChemicalStatistics(BaseModel):
    total_chemicals: int
    in_use_count: int
    expired_count: int
    special_management_count: int
    carcinogen_count: int
    low_stock_items: List[dict]
    expired_msds: List[dict]
    by_hazard_class: dict
