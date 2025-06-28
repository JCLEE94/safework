"""
법령 준수 모니터링 시스템
Compliance Monitoring System
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from enum import Enum

from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ..config.database import get_db
from ..services.cache import CacheService
from ..utils.notifications import send_compliance_alert

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/compliance", tags=["compliance"])


class ComplianceCategory(str, Enum):
    HEALTH_EXAM = "health_exam"
    EDUCATION = "education"
    ENVIRONMENT = "environment"
    CHEMICAL = "chemical"
    SAFETY = "safety"
    MANAGEMENT = "management"


class ComplianceStatus(str, Enum):
    COMPLIANT = "compliant"
    WARNING = "warning"
    VIOLATION = "violation"
    PENDING = "pending"


class PenaltyLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class CheckFrequency(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    ANNUALLY = "annually"


class ComplianceRule(BaseModel):
    id: str
    title: str
    description: str
    category: ComplianceCategory
    effective_date: datetime
    check_frequency: CheckFrequency
    auto_check: bool = True
    penalty_level: PenaltyLevel
    legal_basis: str
    responsible_role: str
    grace_period_days: int = 30


class ComplianceCheckResult(BaseModel):
    rule_id: str
    status: ComplianceStatus
    last_check: datetime
    next_check: datetime
    current_value: Optional[Any] = None
    required_value: Optional[Any] = None
    action_required: Optional[str] = None
    responsible_person: Optional[str] = None
    deadline: Optional[datetime] = None
    notes: Optional[str] = None


class ComplianceAlert(BaseModel):
    rule_id: str
    status: ComplianceStatus
    message: str
    severity: PenaltyLevel
    created_at: datetime
    acknowledged: bool = False
    action_taken: Optional[str] = None


# 2024년 법령 변경사항 반영된 규칙들
COMPLIANCE_RULES = [
    ComplianceRule(
        id="safety_manager_appointment_2024",
        title="보건관리자 선임 의무 (강화)",
        description="상시근로자 300명 이상 건설현장 보건관리자 의무 선임 (2024년 개정)",
        category=ComplianceCategory.MANAGEMENT,
        effective_date=datetime(2024, 1, 1),
        check_frequency=CheckFrequency.MONTHLY,
        penalty_level=PenaltyLevel.HIGH,
        legal_basis="산업안전보건법 제18조, 시행령 제21조",
        responsible_role="현장소장"
    ),
    ComplianceRule(
        id="special_health_exam_asbestos_2024",
        title="석면 취급업무 특수건강진단 주기 단축",
        description="석면 취급업무 특수건강진단 주기: 6개월 → 4개월 (2024년 개정)",
        category=ComplianceCategory.HEALTH_EXAM,
        effective_date=datetime(2024, 3, 1),
        check_frequency=CheckFrequency.MONTHLY,
        penalty_level=PenaltyLevel.CRITICAL,
        legal_basis="산업안전보건법 제130조, 시행규칙 제200조",
        responsible_role="보건관리자"
    ),
    ComplianceRule(
        id="basic_safety_education_extension_2024",
        title="건설업 기초안전보건교육 시간 확대",
        description="기초안전보건교육 시간: 4시간 → 6시간 (2024년 개정)",
        category=ComplianceCategory.EDUCATION,
        effective_date=datetime(2024, 7, 1),
        check_frequency=CheckFrequency.WEEKLY,
        penalty_level=PenaltyLevel.MEDIUM,
        legal_basis="산업안전보건법 제31조, 시행규칙 제26조",
        responsible_role="안전관리자"
    ),
    ComplianceRule(
        id="noise_measurement_frequency_2024",
        title="소음측정 주기 단축",
        description="85dB 초과 작업장 소음측정: 6개월 → 3개월 (2024년 개정)",
        category=ComplianceCategory.ENVIRONMENT,
        effective_date=datetime(2024, 5, 1),
        check_frequency=CheckFrequency.MONTHLY,
        penalty_level=PenaltyLevel.HIGH,
        legal_basis="산업안전보건법 제125조, 시행규칙 제190조",
        responsible_role="환경관리자"
    ),
    ComplianceRule(
        id="msds_digital_management_2024",
        title="MSDS 디지털 관리 의무화",
        description="모든 화학제품 MSDS 디지털 보관 및 2년 주기 업데이트 (2024년 개정)",
        category=ComplianceCategory.CHEMICAL,
        effective_date=datetime(2024, 9, 1),
        check_frequency=CheckFrequency.QUARTERLY,
        penalty_level=PenaltyLevel.HIGH,
        legal_basis="화학물질관리법 제19조, 시행규칙 제12조",
        responsible_role="화학물질관리자"
    ),
    ComplianceRule(
        id="executive_safety_inspection_2024",
        title="경영책임자 안전보건 점검 의무",
        description="월 1회 이상 안전보건 점검 및 기록 보관 (중대재해처벌법 강화)",
        category=ComplianceCategory.MANAGEMENT,
        effective_date=datetime(2024, 1, 1),
        check_frequency=CheckFrequency.WEEKLY,
        penalty_level=PenaltyLevel.CRITICAL,
        legal_basis="중대재해처벌법 제4조, 시행령 제4조",
        responsible_role="경영책임자"
    )
]


class ComplianceMonitoringService:
    """법령 준수 모니터링 서비스"""
    
    def __init__(self, db: Session):
        self.db = db
        self.cache_service = CacheService()
    
    async def check_all_compliance(self) -> List[ComplianceCheckResult]:
        """모든 법령 준수 사항 점검"""
        results = []
        
        for rule in COMPLIANCE_RULES:
            try:
                result = await self.check_single_compliance(rule)
                results.append(result)
                
                # 위반 또는 경고 상태인 경우 알림 발송
                if result.status in [ComplianceStatus.VIOLATION, ComplianceStatus.WARNING]:
                    await self.create_compliance_alert(rule, result)
                    
            except Exception as e:
                logger.error(f"Failed to check compliance for rule {rule.id}: {e}")
                
        return results
    
    async def check_single_compliance(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """개별 법령 준수 사항 점검"""
        
        # 캐시에서 이전 점검 결과 확인
        cache_key = f"compliance_check:{rule.id}"
        cached_result = await self.cache_service.get(cache_key)
        
        current_time = datetime.utcnow()
        
        # 점검 주기에 따른 다음 점검일 계산
        if cached_result:
            last_check = datetime.fromisoformat(cached_result.get('last_check', ''))
            next_check = self.calculate_next_check(last_check, rule.check_frequency)
            
            # 아직 점검 시기가 아니면 이전 결과 반환
            if current_time < next_check:
                return ComplianceCheckResult(**cached_result)
        
        # 실제 점검 수행
        check_result = await self.perform_compliance_check(rule)
        
        # 결과 캐시 저장
        result_dict = check_result.dict()
        result_dict['last_check'] = current_time.isoformat()
        result_dict['next_check'] = self.calculate_next_check(current_time, rule.check_frequency).isoformat()
        
        await self.cache_service.set(cache_key, result_dict, expire=86400 * 7)  # 7일 캐시
        
        return check_result
    
    async def perform_compliance_check(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """실제 법령 준수 점검 수행"""
        
        current_time = datetime.utcnow()
        
        # 규칙별 점검 로직
        if rule.id == "safety_manager_appointment_2024":
            return await self.check_safety_manager_appointment(rule)
        elif rule.id == "special_health_exam_asbestos_2024":
            return await self.check_special_health_exam(rule)
        elif rule.id == "basic_safety_education_extension_2024":
            return await self.check_safety_education(rule)
        elif rule.id == "noise_measurement_frequency_2024":
            return await self.check_noise_measurement(rule)
        elif rule.id == "msds_digital_management_2024":
            return await self.check_msds_management(rule)
        elif rule.id == "executive_safety_inspection_2024":
            return await self.check_executive_inspection(rule)
        else:
            # 기본 점검 (통과)
            return ComplianceCheckResult(
                rule_id=rule.id,
                status=ComplianceStatus.COMPLIANT,
                last_check=current_time,
                next_check=self.calculate_next_check(current_time, rule.check_frequency)
            )
    
    async def check_safety_manager_appointment(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """보건관리자 선임 점검"""
        
        # 근로자 수 조회
        worker_count = await self.get_current_worker_count()
        
        if worker_count >= 300:
            # 보건관리자 선임 여부 확인
            has_safety_manager = await self.check_safety_manager_exists()
            
            if has_safety_manager:
                status = ComplianceStatus.COMPLIANT
                action_required = None
            else:
                status = ComplianceStatus.VIOLATION
                action_required = "보건관리자 즉시 선임 필요"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=worker_count,
            required_value=300,
            action_required=action_required
        )
    
    async def check_special_health_exam(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """특수건강진단 점검"""
        
        # 석면 취급 근로자 조회
        asbestos_workers = await self.get_asbestos_workers()
        
        overdue_count = 0
        upcoming_due_count = 0
        
        for worker in asbestos_workers:
            last_exam_date = worker.get('last_special_exam_date')
            if last_exam_date:
                days_since_exam = (datetime.utcnow() - last_exam_date).days
                
                if days_since_exam > 120:  # 4개월 초과
                    overdue_count += 1
                elif days_since_exam > 90:  # 3개월 초과 (1개월 여유)
                    upcoming_due_count += 1
        
        if overdue_count > 0:
            status = ComplianceStatus.VIOLATION
            action_required = f"{overdue_count}명 특수건강진단 즉시 실시 필요"
        elif upcoming_due_count > 0:
            status = ComplianceStatus.WARNING
            action_required = f"{upcoming_due_count}명 특수건강진단 1개월 내 실시 예정"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=f"연체: {overdue_count}명, 예정: {upcoming_due_count}명",
            action_required=action_required
        )
    
    async def check_safety_education(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """안전교육 점검"""
        
        # 신규 근로자 교육 이수 현황 확인
        recent_workers = await self.get_recent_workers(days=30)
        incomplete_education = []
        
        for worker in recent_workers:
            education_hours = worker.get('safety_education_hours', 0)
            if education_hours < 6:  # 신규 기준 6시간
                incomplete_education.append(worker)
        
        if len(incomplete_education) > 0:
            status = ComplianceStatus.VIOLATION
            action_required = f"{len(incomplete_education)}명 기초안전보건교육 6시간 이수 필요"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=f"미이수: {len(incomplete_education)}명",
            action_required=action_required
        )
    
    async def check_noise_measurement(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """소음측정 점검"""
        
        # 85dB 초과 작업장 소음측정 현황 확인
        high_noise_areas = await self.get_high_noise_areas()
        overdue_measurements = []
        
        for area in high_noise_areas:
            last_measurement_date = area.get('last_noise_measurement_date')
            if last_measurement_date:
                days_since_measurement = (datetime.utcnow() - last_measurement_date).days
                if days_since_measurement > 90:  # 3개월 초과
                    overdue_measurements.append(area)
        
        if len(overdue_measurements) > 0:
            status = ComplianceStatus.VIOLATION
            action_required = f"{len(overdue_measurements)}개 구역 소음측정 즉시 실시 필요"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=f"연체 측정: {len(overdue_measurements)}개 구역",
            action_required=action_required
        )
    
    async def check_msds_management(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """MSDS 관리 점검"""
        
        # 화학물질 MSDS 현황 확인
        chemicals = await self.get_all_chemicals()
        missing_msds = []
        outdated_msds = []
        
        for chemical in chemicals:
            msds_date = chemical.get('msds_last_updated')
            if not msds_date:
                missing_msds.append(chemical)
            else:
                days_since_update = (datetime.utcnow() - msds_date).days
                if days_since_update > 730:  # 2년 초과
                    outdated_msds.append(chemical)
        
        if len(missing_msds) > 0 or len(outdated_msds) > 0:
            status = ComplianceStatus.VIOLATION
            action_required = f"MSDS 누락: {len(missing_msds)}개, 업데이트 필요: {len(outdated_msds)}개"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=f"총 화학물질: {len(chemicals)}개",
            action_required=action_required
        )
    
    async def check_executive_inspection(self, rule: ComplianceRule) -> ComplianceCheckResult:
        """경영책임자 점검 의무 확인"""
        
        # 최근 한 달간 경영책임자 점검 기록 확인
        recent_inspections = await self.get_executive_inspections(days=30)
        
        if len(recent_inspections) == 0:
            status = ComplianceStatus.VIOLATION
            action_required = "경영책임자 월간 안전보건 점검 즉시 실시 필요"
        elif len(recent_inspections) < 1:
            status = ComplianceStatus.WARNING
            action_required = "경영책임자 안전보건 점검 빈도 증가 필요"
        else:
            status = ComplianceStatus.COMPLIANT
            action_required = None
        
        return ComplianceCheckResult(
            rule_id=rule.id,
            status=status,
            last_check=datetime.utcnow(),
            next_check=self.calculate_next_check(datetime.utcnow(), rule.check_frequency),
            current_value=f"최근 30일간 점검: {len(recent_inspections)}회",
            required_value="최소 1회",
            action_required=action_required
        )
    
    def calculate_next_check(self, last_check: datetime, frequency: CheckFrequency) -> datetime:
        """다음 점검일 계산"""
        
        if frequency == CheckFrequency.DAILY:
            return last_check + timedelta(days=1)
        elif frequency == CheckFrequency.WEEKLY:
            return last_check + timedelta(days=7)
        elif frequency == CheckFrequency.MONTHLY:
            return last_check + timedelta(days=30)
        elif frequency == CheckFrequency.QUARTERLY:
            return last_check + timedelta(days=90)
        elif frequency == CheckFrequency.ANNUALLY:
            return last_check + timedelta(days=365)
        else:
            return last_check + timedelta(days=30)  # 기본값
    
    async def create_compliance_alert(self, rule: ComplianceRule, result: ComplianceCheckResult):
        """법령 준수 알림 생성"""
        
        alert = ComplianceAlert(
            rule_id=rule.id,
            status=result.status,
            message=f"{rule.title}: {result.action_required or '점검 필요'}",
            severity=rule.penalty_level,
            created_at=datetime.utcnow()
        )
        
        # 알림 발송
        try:
            await send_compliance_alert(alert, rule)
        except Exception as e:
            logger.error(f"Failed to send compliance alert: {e}")
    
    # 데이터 조회 메서드들 (실제 DB 연동)
    async def get_current_worker_count(self) -> int:
        """현재 근로자 수 조회"""
        # 실제 구현에서는 DB에서 조회
        return 350  # 모의 데이터
    
    async def check_safety_manager_exists(self) -> bool:
        """보건관리자 선임 여부 확인"""
        # 실제 구현에서는 DB에서 조회
        return True  # 모의 데이터
    
    async def get_asbestos_workers(self) -> List[Dict]:
        """석면 취급 근로자 목록"""
        # 실제 구현에서는 DB에서 조회
        return [
            {'id': 1, 'name': '홍길동', 'last_special_exam_date': datetime.utcnow() - timedelta(days=100)},
            {'id': 2, 'name': '김철수', 'last_special_exam_date': datetime.utcnow() - timedelta(days=130)}
        ]
    
    async def get_recent_workers(self, days: int) -> List[Dict]:
        """신규 근로자 목록"""
        return [
            {'id': 1, 'name': '이영희', 'safety_education_hours': 4},
            {'id': 2, 'name': '박민수', 'safety_education_hours': 6}
        ]
    
    async def get_high_noise_areas(self) -> List[Dict]:
        """고소음 작업 구역"""
        return [
            {'id': 1, 'name': '용접구역', 'last_noise_measurement_date': datetime.utcnow() - timedelta(days=95)},
            {'id': 2, 'name': '절단구역', 'last_noise_measurement_date': datetime.utcnow() - timedelta(days=80)}
        ]
    
    async def get_all_chemicals(self) -> List[Dict]:
        """화학물질 목록"""
        return [
            {'id': 1, 'name': '톨루엔', 'msds_last_updated': datetime.utcnow() - timedelta(days=700)},
            {'id': 2, 'name': '벤젠', 'msds_last_updated': None}
        ]
    
    async def get_executive_inspections(self, days: int) -> List[Dict]:
        """경영책임자 점검 기록"""
        return [
            {'id': 1, 'date': datetime.utcnow() - timedelta(days=15), 'inspector': '대표이사'}
        ]


# API 엔드포인트들
@router.get("/check-all")
async def check_all_compliance(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    """모든 법령 준수 사항 점검"""
    
    try:
        service = ComplianceMonitoringService(db)
        results = await service.check_all_compliance()
        
        # 통계 계산
        total_rules = len(results)
        compliant_count = len([r for r in results if r.status == ComplianceStatus.COMPLIANT])
        warning_count = len([r for r in results if r.status == ComplianceStatus.WARNING])
        violation_count = len([r for r in results if r.status == ComplianceStatus.VIOLATION])
        
        return {
            "results": results,
            "summary": {
                "total_rules": total_rules,
                "compliant": compliant_count,
                "warnings": warning_count,
                "violations": violation_count,
                "compliance_rate": round((compliant_count / total_rules) * 100, 1) if total_rules > 0 else 0
            },
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to check compliance: {e}")
        raise HTTPException(status_code=500, detail="법령 준수 점검 중 오류가 발생했습니다")


@router.get("/rules")
async def get_compliance_rules():
    """법령 준수 규칙 목록 조회"""
    
    return {
        "rules": [rule.dict() for rule in COMPLIANCE_RULES],
        "categories": [category.value for category in ComplianceCategory],
        "total_rules": len(COMPLIANCE_RULES)
    }


@router.get("/dashboard")
async def get_compliance_dashboard(db: Session = Depends(get_db)):
    """법령 준수 대시보드 데이터"""
    
    try:
        service = ComplianceMonitoringService(db)
        results = await service.check_all_compliance()
        
        # 카테고리별 분석
        category_analysis = {}
        for category in ComplianceCategory:
            category_results = [r for r in results if any(rule.category == category for rule in COMPLIANCE_RULES if rule.id == r.rule_id)]
            category_analysis[category.value] = {
                "total": len(category_results),
                "compliant": len([r for r in category_results if r.status == ComplianceStatus.COMPLIANT]),
                "violations": len([r for r in category_results if r.status == ComplianceStatus.VIOLATION])
            }
        
        # 우선순위 높은 위반사항
        high_priority_violations = [
            r for r in results 
            if r.status == ComplianceStatus.VIOLATION 
            and any(rule.penalty_level in [PenaltyLevel.HIGH, PenaltyLevel.CRITICAL] 
                   for rule in COMPLIANCE_RULES if rule.id == r.rule_id)
        ]
        
        return {
            "overall_compliance_rate": round(
                len([r for r in results if r.status == ComplianceStatus.COMPLIANT]) / len(results) * 100, 1
            ) if results else 0,
            "category_analysis": category_analysis,
            "high_priority_violations": high_priority_violations[:5],  # 상위 5개
            "upcoming_deadlines": [
                r for r in results 
                if r.deadline and r.deadline <= datetime.utcnow() + timedelta(days=30)
            ],
            "last_updated": datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Failed to get compliance dashboard: {e}")
        raise HTTPException(status_code=500, detail="대시보드 데이터 조회 중 오류가 발생했습니다")