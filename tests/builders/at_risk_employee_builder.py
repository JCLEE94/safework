# 요관리대상자 테스트 빌더
"""
요관리대상자 관리 시스템 테스트 데이터 빌더
At-Risk Employee Management Test Data Builder
"""

from datetime import datetime, date, timedelta
from typing import Optional, Dict, List, Any
import random

from tests.builders.base_builder import BaseBuilder
from src.models import at_risk_employee as models
from src.schemas import at_risk_employee as schemas


class AtRiskEmployeeBuilder(BaseBuilder):
    """요관리대상자 테스트 데이터 빌더"""
    
    def __init__(self):
        super().__init__()
        self.reset()
    
    def reset(self):
        """빌더 초기화"""
        self._data = {
            "worker_id": 1,
            "risk_categories": [schemas.RiskCategory.OCCUPATIONAL_DISEASE],
            "primary_risk_category": schemas.RiskCategory.OCCUPATIONAL_DISEASE,
            "management_level": schemas.ManagementLevel.INTENSIVE,
            "detection_source": "건강진단",
            "detection_date": date.today(),
            "severity_score": 7.5,
            "work_fitness_status": "조건부 적합",
            "management_goals": "청력 보존 및 추가 악화 방지",
            "target_improvement_date": date.today() + timedelta(days=180),
            "registered_by": "보건관리자"
        }
        return self
    
    def with_worker_id(self, worker_id: int):
        """근로자 ID 설정"""
        self._data["worker_id"] = worker_id
        return self
    
    def with_occupational_disease_suspect(self):
        """직업병 의심자 설정"""
        self._data.update({
            "risk_categories": [
                schemas.RiskCategory.OCCUPATIONAL_DISEASE,
                schemas.RiskCategory.HEARING_LOSS
            ],
            "primary_risk_category": schemas.RiskCategory.OCCUPATIONAL_DISEASE,
            "management_level": schemas.ManagementLevel.MEDICAL_CARE,
            "detection_source": "특수건강진단",
            "risk_factors": {
                "occupational": ["소음 노출 (90dB 이상)", "진동 공구 사용"],
                "personal": ["연령 50세 이상", "흡연"],
                "work_conditions": ["야간작업", "10년 이상 근무"]
            },
            "severity_score": 8.5,
            "work_fitness_status": "조건부 적합",
            "work_restrictions": ["고소음 작업 제한", "진동 공구 사용 제한"],
            "management_goals": "청력 손실 진행 방지 및 직업병 예방"
        })
        return self
    
    def with_cardiovascular_risk(self):
        """심혈관계 위험자 설정"""
        self._data.update({
            "risk_categories": [
                schemas.RiskCategory.CARDIOVASCULAR,
                schemas.RiskCategory.GENERAL_DISEASE
            ],
            "primary_risk_category": schemas.RiskCategory.CARDIOVASCULAR,
            "management_level": schemas.ManagementLevel.INTENSIVE,
            "detection_source": "일반건강진단",
            "risk_factors": {
                "occupational": ["교대근무", "고열 작업", "중량물 취급"],
                "personal": ["고혈압", "당뇨", "비만 (BMI 30 이상)"],
                "work_conditions": ["야간작업", "스트레스 고위험"]
            },
            "severity_score": 7.0,
            "work_fitness_status": "적합",
            "work_restrictions": ["고소 작업 제한", "단독 작업 제한"],
            "management_goals": "심혈관계 위험요인 관리 및 급성 사건 예방"
        })
        return self
    
    def with_musculoskeletal_disorder(self):
        """근골격계 질환자 설정"""
        self._data.update({
            "risk_categories": [
                schemas.RiskCategory.MUSCULOSKELETAL,
                schemas.RiskCategory.ERGONOMIC_RISK
            ],
            "primary_risk_category": schemas.RiskCategory.MUSCULOSKELETAL,
            "management_level": schemas.ManagementLevel.INTENSIVE,
            "detection_source": "근골격계부담작업 유해요인조사",
            "risk_factors": {
                "occupational": ["반복 작업", "부적절한 자세", "중량물 취급"],
                "personal": ["요통 병력", "근력 약화"],
                "work_conditions": ["장시간 서서 작업", "진동 노출"]
            },
            "severity_score": 6.5,
            "work_fitness_status": "조건부 적합",
            "work_restrictions": ["25kg 이상 중량물 취급 제한", "반복 작업 시간 제한"],
            "management_goals": "근골격계 증상 완화 및 작업 방법 개선"
        })
        return self
    
    def with_mental_health_concern(self):
        """정신건강 관리 대상자 설정"""
        self._data.update({
            "risk_categories": [
                schemas.RiskCategory.MENTAL_HEALTH,
                schemas.RiskCategory.HIGH_STRESS
            ],
            "primary_risk_category": schemas.RiskCategory.MENTAL_HEALTH,
            "management_level": schemas.ManagementLevel.INTENSIVE,
            "detection_source": "직무스트레스 평가",
            "risk_factors": {
                "occupational": ["고객 응대", "감정노동", "업무 과부하"],
                "personal": ["우울증 진단", "불면증"],
                "work_conditions": ["야간작업", "불규칙한 근무"]
            },
            "severity_score": 7.5,
            "work_fitness_status": "적합",
            "work_restrictions": ["야간 근무 최소화"],
            "management_goals": "스트레스 관리 및 정신건강 증진"
        })
        return self
    
    def with_chemical_exposure(self):
        """화학물질 노출자 설정"""
        self._data.update({
            "risk_categories": [
                schemas.RiskCategory.CHEMICAL_EXPOSURE,
                schemas.RiskCategory.RESPIRATORY
            ],
            "primary_risk_category": schemas.RiskCategory.CHEMICAL_EXPOSURE,
            "management_level": schemas.ManagementLevel.MEDICAL_CARE,
            "detection_source": "작업환경측정",
            "risk_factors": {
                "occupational": ["벤젠 노출", "톨루엔 노출", "분진 노출"],
                "personal": ["알레르기 체질", "천식 병력"],
                "work_conditions": ["밀폐 공간 작업", "보호구 착용 불량"]
            },
            "severity_score": 8.0,
            "work_fitness_status": "조건부 적합",
            "work_restrictions": ["화학물질 직접 취급 제한", "밀폐공간 작업 제한"],
            "management_goals": "화학물질 노출 최소화 및 건강 모니터링"
        })
        return self
    
    def with_observation_level(self):
        """관찰 수준 설정"""
        self._data["management_level"] = schemas.ManagementLevel.OBSERVATION
        self._data["severity_score"] = random.uniform(3.0, 5.0)
        return self
    
    def with_work_restriction_level(self):
        """작업 제한 수준 설정"""
        self._data["management_level"] = schemas.ManagementLevel.WORK_RESTRICTION
        self._data["severity_score"] = random.uniform(8.0, 10.0)
        self._data["work_restrictions"] = [
            "고위험 작업 금지",
            "단독 작업 금지",
            "야간 작업 금지"
        ]
        return self
    
    def with_resolved_status(self):
        """해결된 상태 설정"""
        self._data["is_active"] = False
        self._data["resolution_date"] = date.today()
        self._data["resolution_reason"] = "건강 상태 개선으로 정상 복귀"
        return self
    
    def build_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 반환"""
        return self._data.copy()
    
    def build_create_schema(self) -> schemas.AtRiskEmployeeCreate:
        """생성 스키마 반환"""
        data = self._data.copy()
        # risk_factors를 RiskFactors 객체로 변환
        if "risk_factors" in data and isinstance(data["risk_factors"], dict):
            data["risk_factors"] = schemas.RiskFactors(**data["risk_factors"])
        return schemas.AtRiskEmployeeCreate(**data)
    
    def build_model(self) -> models.AtRiskEmployee:
        """모델 인스턴스 반환"""
        data = self._data.copy()
        # risk_factors가 딕셔너리면 그대로 사용 (JSON 필드)
        if "risk_factors" in data and hasattr(data["risk_factors"], "model_dump"):
            data["risk_factors"] = data["risk_factors"].model_dump()
        return models.AtRiskEmployee(**data)


class RiskManagementPlanBuilder(BaseBuilder):
    """위험 관리 계획 빌더"""
    
    def __init__(self):
        super().__init__()
        self.reset()
    
    def reset(self):
        """빌더 초기화"""
        self._data = {
            "at_risk_employee_id": 1,
            "plan_name": "청력 보존 프로그램",
            "plan_period_start": date.today(),
            "plan_period_end": date.today() + timedelta(days=180),
            "primary_goal": "소음성 난청 진행 방지 및 청력 보존",
            "specific_objectives": [
                "3개월 내 청력 역치 안정화",
                "보호구 착용률 100% 달성",
                "소음 노출 시간 50% 감소"
            ],
            "planned_interventions": [
                {
                    "type": "보건상담",
                    "frequency": "월 1회",
                    "duration": "6개월",
                    "provider": "보건관리자"
                },
                {
                    "type": "청력검사",
                    "frequency": "3개월마다",
                    "duration": "1년",
                    "provider": "의료기관"
                }
            ],
            "monitoring_schedule": {
                "health_check": "3개월마다",
                "consultation": "매월",
                "work_environment": "분기별"
            },
            "success_criteria": [
                "청력 역치 5dB 이내 유지",
                "자각 증상 개선",
                "보호구 착용 준수"
            ],
            "created_by": "보건관리자"
        }
        return self
    
    def with_cardiovascular_plan(self):
        """심혈관계 관리 계획"""
        self._data.update({
            "plan_name": "심혈관계 질환 예방 프로그램",
            "primary_goal": "심혈관계 위험요인 관리 및 급성 사건 예방",
            "specific_objectives": [
                "혈압 정상 범위 유지",
                "체중 5% 감량",
                "금연 달성"
            ],
            "planned_interventions": [
                {
                    "type": "보건상담",
                    "frequency": "2주마다",
                    "duration": "3개월",
                    "provider": "보건관리자"
                },
                {
                    "type": "생활습관지도",
                    "frequency": "주 1회",
                    "duration": "6개월",
                    "provider": "운동처방사"
                }
            ]
        })
        return self
    
    def build_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 반환"""
        return self._data.copy()
    
    def build_model(self) -> models.RiskManagementPlan:
        """모델 인스턴스 반환"""
        return models.RiskManagementPlan(**self._data)


class RiskInterventionBuilder(BaseBuilder):
    """위험 개입 기록 빌더"""
    
    def __init__(self):
        super().__init__()
        self.reset()
    
    def reset(self):
        """빌더 초기화"""
        self._data = {
            "at_risk_employee_id": 1,
            "plan_id": 1,
            "intervention_date": date.today(),
            "intervention_type": schemas.InterventionType.HEALTH_CONSULTATION,
            "provider": "보건관리자",
            "duration_minutes": 30,
            "intervention_details": {
                "topics_covered": ["청력 보호 중요성", "올바른 보호구 착용법"],
                "materials_provided": ["청력보호 가이드", "귀마개 샘플"],
                "demonstration": True
            },
            "worker_response": "적극적",
            "compliance_level": "양호",
            "barriers_identified": ["작업 중 불편함 호소"],
            "follow_up_required": True,
            "follow_up_plan": "2주 후 보호구 착용 상태 확인",
            "created_by": "보건관리자"
        }
        return self
    
    def with_medical_referral(self):
        """의료기관 의뢰"""
        self._data.update({
            "intervention_type": schemas.InterventionType.MEDICAL_REFERRAL,
            "provider": "산업보건의",
            "intervention_details": {
                "referral_reason": "청력 정밀검사 필요",
                "hospital": "서울대학교병원",
                "department": "이비인후과",
                "appointment_date": (date.today() + timedelta(days=7)).isoformat()
            },
            "referral_info": {
                "urgency": "일반",
                "symptoms": ["이명", "난청"],
                "previous_treatment": "없음"
            }
        })
        return self
    
    def build_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 반환"""
        return self._data.copy()
    
    def build_model(self) -> models.RiskIntervention:
        """모델 인스턴스 반환"""
        return models.RiskIntervention(**self._data)


class RiskMonitoringBuilder(BaseBuilder):
    """위험 모니터링 기록 빌더"""
    
    def __init__(self):
        super().__init__()
        self.reset()
    
    def reset(self):
        """빌더 초기화"""
        self._data = {
            "at_risk_employee_id": 1,
            "monitoring_date": date.today(),
            "monitoring_type": "정기 모니터링",
            "health_indicators": {
                "blood_pressure": "130/85",
                "hearing_threshold": {"right": "25dB", "left": "30dB"},
                "symptoms": ["경미한 이명"]
            },
            "work_status": {
                "current_work": "일반 작업",
                "restrictions_followed": True,
                "ppe_compliance": "양호"
            },
            "progress_assessment": "개선 중",
            "risk_level_change": "유지",
            "recommendations": [
                "현재 관리 계획 지속",
                "보호구 착용 철저"
            ],
            "next_monitoring_date": date.today() + timedelta(days=30),
            "monitored_by": "보건관리자"
        }
        return self
    
    def with_improvement(self):
        """개선된 모니터링 결과"""
        self._data.update({
            "health_indicators": {
                "blood_pressure": "120/80",
                "hearing_threshold": {"right": "20dB", "left": "25dB"},
                "symptoms": []
            },
            "progress_assessment": "현저한 개선",
            "risk_level_change": "감소",
            "recommendations": ["관리 수준 하향 조정 고려"]
        })
        return self
    
    def build_dict(self) -> Dict[str, Any]:
        """딕셔너리 형태로 반환"""
        return self._data.copy()
    
    def build_model(self) -> models.RiskMonitoring:
        """모델 인스턴스 반환"""
        return models.RiskMonitoring(**self._data)