"""
건강교육 관련 테스트 데이터 빌더
Health education test data builders
"""

from datetime import datetime, timedelta
from typing import Optional

from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health_education import (
    HealthEducation, HealthEducationAttendance, EducationType, 
    EducationMethod, EducationStatus
)
from tests.builders.base_builder import BaseBuilder


class HealthEducationBuilder(BaseBuilder[HealthEducation]):
    """건강교육 기록 빌더"""

    def __init__(self):
        super().__init__()
        self._education_date: datetime = datetime.now()
        self._education_type: EducationType = EducationType.NEW_EMPLOYEE
        self._education_title: str = "신규근로자 안전보건교육"
        self._education_content: Optional[str] = "안전작업수칙 및 보건관리 지침"
        self._education_method: EducationMethod = EducationMethod.CLASSROOM
        self._education_hours: float = 8.0
        self._instructor_name: Optional[str] = "김안전"
        self._instructor_qualification: Optional[str] = "산업안전기사"
        self._education_location: Optional[str] = "본사 교육실"
        self._required_by_law: str = "Y"
        self._legal_requirement_hours: Optional[float] = 8.0
        self._education_material_path: Optional[str] = None
        self._attendance_sheet_path: Optional[str] = None
        self._notes: Optional[str] = None
        self._created_by: Optional[str] = "test_user"
        self._updated_by: Optional[str] = "test_user"

    def with_education_date(self, education_date: datetime) -> "HealthEducationBuilder":
        """교육일시 설정"""
        self._education_date = education_date
        return self

    def with_education_type(self, education_type: EducationType) -> "HealthEducationBuilder":
        """교육유형 설정"""
        self._education_type = education_type
        return self

    def with_education_title(self, title: str) -> "HealthEducationBuilder":
        """교육제목 설정"""
        self._education_title = title
        return self

    def with_education_content(self, content: str) -> "HealthEducationBuilder":
        """교육내용 설정"""
        self._education_content = content
        return self

    def with_education_method(self, method: EducationMethod) -> "HealthEducationBuilder":
        """교육방법 설정"""
        self._education_method = method
        return self

    def with_education_hours(self, hours: float) -> "HealthEducationBuilder":
        """교육시간 설정"""
        self._education_hours = hours
        return self

    def with_instructor(self, name: str, qualification: str = "산업안전기사") -> "HealthEducationBuilder":
        """강사 정보 설정"""
        self._instructor_name = name
        self._instructor_qualification = qualification
        return self

    def with_education_location(self, location: str) -> "HealthEducationBuilder":
        """교육장소 설정"""
        self._education_location = location
        return self

    def with_legal_requirements(self, required: bool = True, hours: float = 8.0) -> "HealthEducationBuilder":
        """법정교육 정보 설정"""
        self._required_by_law = "Y" if required else "N"
        self._legal_requirement_hours = hours if required else None
        return self

    def with_materials(
        self, 
        material_path: Optional[str] = None, 
        attendance_sheet_path: Optional[str] = None
    ) -> "HealthEducationBuilder":
        """교육자료 경로 설정"""
        self._education_material_path = material_path
        self._attendance_sheet_path = attendance_sheet_path
        return self

    def with_notes(self, notes: str) -> "HealthEducationBuilder":
        """비고 설정"""
        self._notes = notes
        return self

    def with_created_by(self, created_by: str) -> "HealthEducationBuilder":
        """생성자 설정"""
        self._created_by = created_by
        self._updated_by = created_by
        return self

    def with_korean_data(self) -> "HealthEducationBuilder":
        """한국어 테스트 데이터 설정"""
        self._education_title = "건설업 특별안전보건교육"
        self._education_content = "건설현장 위험요소 및 안전작업수칙, 개인보호구 착용법, 응급처치"
        self._instructor_name = "이안전"
        self._instructor_qualification = "건설안전기사, 산업위생관리기사"
        self._education_location = "현장 안전교육실"
        self._notes = "신규 및 작업변경 근로자 필수 이수"
        return self

    def with_new_employee_training(self) -> "HealthEducationBuilder":
        """신규근로자 교육 설정"""
        self._education_type = EducationType.NEW_EMPLOYEE
        self._education_title = "신규근로자 안전보건교육"
        self._education_content = "안전보건 기본지식, 작업장 위험요소, 개인보호구 사용법"
        self._education_hours = 8.0
        self._legal_requirement_hours = 8.0
        return self

    def with_quarterly_training(self) -> "HealthEducationBuilder":
        """분기별 정기교육 설정"""
        self._education_type = EducationType.REGULAR_QUARTERLY
        self._education_title = "정기안전보건교육 (1분기)"
        self._education_content = "계절별 안전수칙, 최신 안전법규, 사고사례 분석"
        self._education_hours = 6.0
        self._legal_requirement_hours = 6.0
        return self

    def with_special_hazard_training(self) -> "HealthEducationBuilder":
        """특별안전보건교육 설정"""
        self._education_type = EducationType.SPECIAL_HAZARD
        self._education_title = "고소작업 특별안전보건교육"
        self._education_content = "추락재해 예방, 안전장비 점검, 응급상황 대처법"
        self._education_hours = 4.0
        self._legal_requirement_hours = 4.0
        return self

    def with_manager_training(self) -> "HealthEducationBuilder":
        """관리감독자 교육 설정"""
        self._education_type = EducationType.MANAGER_TRAINING
        self._education_title = "관리감독자 안전보건교육"
        self._education_content = "관리감독자 역할과 책임, 위험성평가, 사고조사 방법"
        self._education_hours = 16.0
        self._legal_requirement_hours = 16.0
        return self

    def with_msds_training(self) -> "HealthEducationBuilder":
        """MSDS 교육 설정"""
        self._education_type = EducationType.MSDS
        self._education_title = "화학물질 안전보건자료 교육"
        self._education_content = "MSDS 이해 및 활용, 화학물질 취급 안전수칙"
        self._education_hours = 2.0
        self._legal_requirement_hours = 2.0
        return self

    def with_online_method(self) -> "HealthEducationBuilder":
        """온라인 교육 설정"""
        self._education_method = EducationMethod.ONLINE
        self._education_location = "온라인 교육플랫폼"
        self._education_material_path = "/uploads/education/online_materials.pdf"
        return self

    def with_field_training(self) -> "HealthEducationBuilder":
        """현장교육 설정"""
        self._education_method = EducationMethod.FIELD
        self._education_location = "건설현장 1공구"
        return self

    def with_upcoming_session(self, days_from_now: int = 7) -> "HealthEducationBuilder":
        """다가오는 교육 세션 설정"""
        self._education_date = datetime.now() + timedelta(days=days_from_now)
        return self

    def with_past_session(self, days_ago: int = 30) -> "HealthEducationBuilder":
        """과거 교육 세션 설정"""
        self._education_date = datetime.now() - timedelta(days=days_ago)
        return self

    async def build(self, db_session: AsyncSession) -> HealthEducation:
        """건강교육 기록 생성"""
        education = HealthEducation(
            education_date=self._education_date,
            education_type=self._education_type,
            education_title=self._education_title,
            education_content=self._education_content,
            education_method=self._education_method,
            education_hours=self._education_hours,
            instructor_name=self._instructor_name,
            instructor_qualification=self._instructor_qualification,
            education_location=self._education_location,
            required_by_law=self._required_by_law,
            legal_requirement_hours=self._legal_requirement_hours,
            education_material_path=self._education_material_path,
            attendance_sheet_path=self._attendance_sheet_path,
            notes=self._notes,
            created_by=self._created_by,
            updated_by=self._updated_by
        )

        db_session.add(education)
        await db_session.commit()
        await db_session.refresh(education)
        return education


class AttendanceBuilder(BaseBuilder[HealthEducationAttendance]):
    """교육 참석 정보 빌더"""

    def __init__(self):
        super().__init__()
        self._education_id: Optional[int] = None
        self._worker_id: Optional[int] = None
        self._status: EducationStatus = EducationStatus.COMPLETED
        self._attendance_hours: Optional[float] = 8.0
        self._test_score: Optional[float] = 85.0
        self._certificate_number: Optional[str] = None
        self._certificate_issue_date: Optional[datetime] = None
        self._satisfaction_score: Optional[int] = 4
        self._feedback_comments: Optional[str] = "교육이 유익했습니다"
        self._created_by: Optional[str] = "test_user"

    def with_education_id(self, education_id: int) -> "AttendanceBuilder":
        """교육 ID 설정"""
        self._education_id = education_id
        return self

    def with_worker_id(self, worker_id: int) -> "AttendanceBuilder":
        """근로자 ID 설정"""
        self._worker_id = worker_id
        return self

    def with_status(self, status: EducationStatus) -> "AttendanceBuilder":
        """참석 상태 설정"""
        self._status = status
        return self

    def with_attendance_hours(self, hours: float) -> "AttendanceBuilder":
        """참석 시간 설정"""
        self._attendance_hours = hours
        return self

    def with_test_score(self, score: float) -> "AttendanceBuilder":
        """테스트 점수 설정"""
        self._test_score = score
        return self

    def with_certificate(self, number: str, issue_date: datetime = None) -> "AttendanceBuilder":
        """수료증 정보 설정"""
        self._certificate_number = number
        self._certificate_issue_date = issue_date or datetime.now()
        return self

    def with_satisfaction(self, score: int, comments: str = None) -> "AttendanceBuilder":
        """만족도 평가 설정"""
        self._satisfaction_score = score
        if comments:
            self._feedback_comments = comments
        return self

    def with_created_by(self, created_by: str) -> "AttendanceBuilder":
        """생성자 설정"""
        self._created_by = created_by
        return self

    def with_completed_status(self) -> "AttendanceBuilder":
        """완료 상태로 설정"""
        self._status = EducationStatus.COMPLETED
        self._certificate_number = f"CERT-{datetime.now().strftime('%Y%m%d%H%M%S')}"
        self._certificate_issue_date = datetime.now()
        return self

    def with_absent_status(self) -> "AttendanceBuilder":
        """불참 상태로 설정"""
        self._status = EducationStatus.ABSENT
        self._attendance_hours = 0.0
        self._test_score = None
        self._certificate_number = None
        self._certificate_issue_date = None
        self._satisfaction_score = None
        self._feedback_comments = None
        return self

    def with_in_progress_status(self) -> "AttendanceBuilder":
        """진행중 상태로 설정"""
        self._status = EducationStatus.IN_PROGRESS
        self._certificate_number = None
        self._certificate_issue_date = None
        return self

    def with_excellent_performance(self) -> "AttendanceBuilder":
        """우수 성과로 설정"""
        self._test_score = 95.0
        self._satisfaction_score = 5
        self._feedback_comments = "매우 유익하고 실무에 도움이 되는 교육이었습니다"
        return self

    def with_poor_performance(self) -> "AttendanceBuilder":
        """저조한 성과로 설정"""
        self._test_score = 65.0
        self._satisfaction_score = 2
        self._feedback_comments = "이해하기 어려운 부분이 많았습니다"
        return self

    def with_korean_feedback(self) -> "AttendanceBuilder":
        """한국어 피드백 설정"""
        self._feedback_comments = "현장 실무에 도움되는 유익한 교육이었습니다. 감사합니다."
        return self

    async def build(self, db_session: AsyncSession) -> HealthEducationAttendance:
        """교육 참석 정보 생성"""
        if self._education_id is None:
            raise ValueError("education_id is required")
        if self._worker_id is None:
            raise ValueError("worker_id is required")

        attendance = HealthEducationAttendance(
            education_id=self._education_id,
            worker_id=self._worker_id,
            status=self._status,
            attendance_hours=self._attendance_hours,
            test_score=self._test_score,
            certificate_number=self._certificate_number,
            certificate_issue_date=self._certificate_issue_date,
            satisfaction_score=self._satisfaction_score,
            feedback_comments=self._feedback_comments,
            created_by=self._created_by
        )

        db_session.add(attendance)
        await db_session.commit()
        await db_session.refresh(attendance)
        return attendance


class EducationCompleteBuilder:
    """완전한 교육 기록 (교육+참석자) 생성 빌더"""

    def __init__(self):
        self._education_builder = HealthEducationBuilder()
        self._attendance_builders: list[AttendanceBuilder] = []

    def with_education_builder(self, builder: HealthEducationBuilder) -> "EducationCompleteBuilder":
        """교육 빌더 설정"""
        self._education_builder = builder
        return self

    def add_attendance(self, builder: AttendanceBuilder) -> "EducationCompleteBuilder":
        """참석자 빌더 추가"""
        self._attendance_builders.append(builder)
        return self

    def with_multiple_attendees(
        self, 
        worker_ids: list[int], 
        statuses: list[EducationStatus] = None
    ) -> "EducationCompleteBuilder":
        """다중 참석자 설정"""
        if statuses is None:
            statuses = [EducationStatus.COMPLETED] * len(worker_ids)
        
        for worker_id, status in zip(worker_ids, statuses):
            builder = (
                AttendanceBuilder()
                .with_worker_id(worker_id)
                .with_status(status)
            )
            
            if status == EducationStatus.COMPLETED:
                builder = builder.with_completed_status().with_korean_feedback()
            elif status == EducationStatus.ABSENT:
                builder = builder.with_absent_status()
            elif status == EducationStatus.IN_PROGRESS:
                builder = builder.with_in_progress_status()
            
            self._attendance_builders.append(builder)
        
        return self

    def with_mixed_performance_scenario(self, worker_ids: list[int]) -> "EducationCompleteBuilder":
        """다양한 성과 시나리오 설정"""
        performance_patterns = ["excellent", "good", "average", "poor"]
        
        for i, worker_id in enumerate(worker_ids):
            builder = AttendanceBuilder().with_worker_id(worker_id)
            
            pattern = performance_patterns[i % len(performance_patterns)]
            if pattern == "excellent":
                builder = builder.with_excellent_performance()
            elif pattern == "poor":
                builder = builder.with_poor_performance()
            else:
                # good or average - use default values
                builder = builder.with_completed_status()
            
            self._attendance_builders.append(builder)
        
        return self

    def with_compliance_scenario(self, worker_ids: list[int]) -> "EducationCompleteBuilder":
        """법규 준수 시나리오 설정"""
        # 모든 참석자가 완료 상태로 설정 (법규 준수)
        self._education_builder = self._education_builder.with_legal_requirements(True)
        
        for worker_id in worker_ids:
            builder = (
                AttendanceBuilder()
                .with_worker_id(worker_id)
                .with_completed_status()
                .with_korean_feedback()
                .with_satisfaction(4)
            )
            self._attendance_builders.append(builder)
        
        return self

    async def build(self, db_session: AsyncSession) -> HealthEducation:
        """완전한 교육 기록 생성"""
        # 1. 교육 기록 생성
        education = await self._education_builder.build(db_session)

        # 2. 참석자 정보들 생성
        for attendance_builder in self._attendance_builders:
            await attendance_builder.with_education_id(education.id).build(db_session)

        # 관계 로드를 위해 새로 고침
        await db_session.refresh(education)
        return education