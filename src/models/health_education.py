import enum
from datetime import datetime
from typing import Optional

from sqlalchemy import Column, DateTime
from sqlalchemy import Enum as SQLEnum
from sqlalchemy import Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from src.config.database import Base


class EducationType(enum.Enum):
    NEW_EMPLOYEE = "신규채용교육"
    REGULAR_QUARTERLY = "정기교육_분기"
    SPECIAL_HAZARD = "특별안전보건교육"
    MANAGER_TRAINING = "관리감독자교육"
    CHANGE_WORK = "작업내용변경교육"
    SPECIAL_SUBSTANCE = "특별관리물질교육"
    MSDS = "MSDS교육"
    EMERGENCY_RESPONSE = "응급처치교육"
    OTHER = "기타교육"


class EducationMethod(enum.Enum):
    CLASSROOM = "집체교육"
    ONLINE = "온라인교육"
    FIELD = "현장교육"
    SELF_STUDY = "자체교육"
    EXTERNAL = "외부교육"
    MIXED = "혼합교육"


class EducationStatus(enum.Enum):
    SCHEDULED = "예정"
    IN_PROGRESS = "진행중"
    COMPLETED = "완료"
    ABSENT = "불참"
    CANCELLED = "취소"


class HealthEducation(Base):
    __tablename__ = "health_educations"

    id = Column(Integer, primary_key=True, index=True)
    education_date = Column(DateTime, nullable=False)
    education_type = Column(SQLEnum(EducationType), nullable=False)
    education_title = Column(String(300), nullable=False)
    education_content = Column(Text)

    # Education details
    education_method = Column(SQLEnum(EducationMethod), nullable=False)
    education_hours = Column(Float, nullable=False)
    instructor_name = Column(String(100))
    instructor_qualification = Column(String(200))
    education_location = Column(String(200))

    # Requirements
    required_by_law = Column(String(1), default="Y")
    legal_requirement_hours = Column(Float)

    # Materials
    education_material_path = Column(String(500))
    attendance_sheet_path = Column(String(500))

    # Common fields
    notes = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    updated_by = Column(String(100))


class HealthEducationAttendance(Base):
    __tablename__ = "health_education_attendances"

    id = Column(Integer, primary_key=True, index=True)
    education_id = Column(
        Integer, ForeignKey("health_educations.id", ondelete="CASCADE")
    )
    worker_id = Column(Integer, ForeignKey("workers.id", ondelete="CASCADE"))

    status = Column(SQLEnum(EducationStatus), nullable=False)
    attendance_hours = Column(Float)
    test_score = Column(Float)
    certificate_number = Column(String(100))
    certificate_issue_date = Column(DateTime)

    # Feedback
    satisfaction_score = Column(Integer)  # 1-5
    feedback_comments = Column(Text)

    created_at = Column(DateTime, default=datetime.utcnow)
    created_by = Column(String(100))

    # Relationships
    education = relationship("HealthEducation", backref="attendances")
    worker = relationship("Worker", backref="education_records")
