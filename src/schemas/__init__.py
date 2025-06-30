"""
스키마 패키지
"""

from .worker import (
    WorkerCreate, WorkerUpdate, WorkerResponse, WorkerListResponse,
    HealthConsultationCreate, HealthConsultationResponse
)
from .health_exam import (
    HealthExamCreate, HealthExamUpdate, HealthExamResponse, HealthExamListResponse,
    VitalSignsCreate, VitalSignsResponse,
    LabResultCreate, LabResultResponse
)
from .work_environment import (
    WorkEnvironmentCreate, WorkEnvironmentUpdate, WorkEnvironmentResponse, WorkEnvironmentListResponse,
    WorkerExposureCreate, WorkerExposureResponse, WorkEnvironmentWithExposuresResponse,
    WorkEnvironmentStatistics
)
from .health_education import (
    HealthEducationCreate, HealthEducationUpdate, HealthEducationResponse, HealthEducationListResponse,
    AttendanceCreate, AttendanceUpdate, AttendanceResponse, EducationWithAttendanceResponse,
    EducationStatistics
)
from .chemical_substance import (
    ChemicalSubstanceCreate, ChemicalSubstanceUpdate, ChemicalSubstanceResponse, ChemicalSubstanceListResponse,
    ChemicalUsageCreate, ChemicalUsageResponse, ChemicalWithUsageResponse,
    ChemicalStatistics
)
from .accident_report import (
    AccidentReportCreate, AccidentReportUpdate, AccidentReportResponse, AccidentReportListResponse,
    AccidentStatistics
)

__all__ = [
    # Worker
    "WorkerCreate", "WorkerUpdate", "WorkerResponse", "WorkerListResponse",
    "HealthConsultationCreate", "HealthConsultationResponse",
    # Health Exam
    "HealthExamCreate", "HealthExamUpdate", "HealthExamResponse", "HealthExamListResponse",
    "VitalSignsCreate", "VitalSignsResponse",
    "LabResultCreate", "LabResultResponse",
    # Work Environment
    "WorkEnvironmentCreate", "WorkEnvironmentUpdate", "WorkEnvironmentResponse", "WorkEnvironmentListResponse",
    "WorkerExposureCreate", "WorkerExposureResponse", "WorkEnvironmentWithExposuresResponse",
    "WorkEnvironmentStatistics",
    # Health Education
    "HealthEducationCreate", "HealthEducationUpdate", "HealthEducationResponse", "HealthEducationListResponse",
    "AttendanceCreate", "AttendanceUpdate", "AttendanceResponse", "EducationWithAttendanceResponse",
    "EducationStatistics",
    # Chemical Substance
    "ChemicalSubstanceCreate", "ChemicalSubstanceUpdate", "ChemicalSubstanceResponse", "ChemicalSubstanceListResponse",
    "ChemicalUsageCreate", "ChemicalUsageResponse", "ChemicalWithUsageResponse",
    "ChemicalStatistics",
    # Accident Report
    "AccidentReportCreate", "AccidentReportUpdate", "AccidentReportResponse", "AccidentReportListResponse",
    "AccidentStatistics"
]