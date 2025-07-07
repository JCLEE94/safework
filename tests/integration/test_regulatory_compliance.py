"""
법적 규정 준수 통합 테스트
Regulatory Compliance Integration Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json

from src.app import create_app


class TestRegulatoryCompliance:
    """한국 산업안전보건법 및 관련 법규 준수 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_company_data(self):
        """샘플 사업장 데이터"""
        return {
            "company_name": "안전건설(주)",
            "business_registration": "123-45-67890",
            "industry_code": "41220",  # 건물건설업
            "industry_type": "construction",
            "employee_count": 150,
            "annual_revenue": 50000000000,  # 500억원
            "risk_level": "high",
            "kosha_ms_certified": True,
            "kosha_certification_date": "2024-01-15",
            "safety_management_grade": "A",
            "address": "서울특별시 강남구 테헤란로 123",
            "representative": "김대표",
            "established_date": "2010-03-15"
        }
    
    async def test_safety_health_management_system_requirements(self, test_client, sample_company_data):
        """안전보건관리체제 구축 요구사항 테스트"""
        
        # 1. 사업장 등록 및 법적 요구사항 자동 판단
        response = test_client.post("/api/v1/regulatory/company/register", json=sample_company_data)
        assert response.status_code == 201
        
        company_id = response.json()["id"]
        requirements = response.json()["legal_requirements"]
        
        # 50인 이상 사업장 요구사항 확인
        assert "safety_health_manager" in requirements
        assert "safety_committee" in requirements
        assert "risk_assessment" in requirements
        
        # 2. 안전보건관리책임자 선임
        safety_manager_data = {
            "company_id": company_id,
            "manager_type": "safety_health_chief",
            "name": "김안전",
            "qualification": "산업안전기사",
            "qualification_number": "12-345678",
            "appointment_date": datetime.now().isoformat(),
            "experience_years": 10,
            "education": [
                {
                    "course": "안전보건관리책임자 교육",
                    "institution": "한국산업안전보건공단",
                    "completion_date": "2024-01-10",
                    "certificate_number": "KOSHA-2024-001234"
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/appointments/safety-manager", json=safety_manager_data)
        assert response.status_code == 201
        
        # 3. 관리감독자 지정
        supervisors_data = {
            "company_id": company_id,
            "supervisors": [
                {
                    "name": "이감독",
                    "department": "건설현장1팀",
                    "position": "현장소장",
                    "appointment_date": datetime.now().isoformat(),
                    "safety_education_completed": True,
                    "education_date": "2024-01-20"
                },
                {
                    "name": "박감독",
                    "department": "건설현장2팀",
                    "position": "공사과장",
                    "appointment_date": datetime.now().isoformat(),
                    "safety_education_completed": True,
                    "education_date": "2024-01-20"
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/appointments/supervisors", json=supervisors_data)
        assert response.status_code == 201
        
        # 4. 산업안전보건위원회 구성
        safety_committee_data = {
            "company_id": company_id,
            "establishment_date": datetime.now().isoformat(),
            "members": [
                {"name": "김대표", "role": "위원장", "representing": "사업주"},
                {"name": "김안전", "role": "간사", "representing": "안전관리자"},
                {"name": "이노무", "role": "위원", "representing": "근로자대표"},
                {"name": "박생산", "role": "위원", "representing": "부서장"},
                {"name": "최근로", "role": "위원", "representing": "근로자"},
                {"name": "정명예", "role": "위원", "representing": "명예산업안전감독관"}
            ],
            "meeting_schedule": "quarterly",
            "next_meeting_date": (datetime.now() + timedelta(days=30)).isoformat()
        }
        
        response = test_client.post("/api/v1/regulatory/safety-committee", json=safety_committee_data)
        assert response.status_code == 201
        
        # 5. 법적 요구사항 준수 확인
        response = test_client.get(f"/api/v1/regulatory/compliance/check?company_id={company_id}")
        assert response.status_code == 200
        
        compliance_status = response.json()
        assert compliance_status["safety_health_chief"]["compliant"] == True
        assert compliance_status["supervisors"]["compliant"] == True
        assert compliance_status["safety_committee"]["compliant"] == True
        
        return company_id
    
    async def test_mandatory_safety_education_compliance(self, test_client, sample_company_data):
        """법정 안전보건교육 준수 테스트"""
        
        # 1. 사업장 등록
        response = test_client.post("/api/v1/regulatory/company/register", json=sample_company_data)
        company_id = response.json()["id"]
        
        # 2. 교육 대상자 자동 식별
        response = test_client.get(f"/api/v1/regulatory/education/required-targets?company_id={company_id}")
        assert response.status_code == 200
        
        education_targets = response.json()
        
        # 법정 교육 종류별 대상자 확인
        assert "new_employee_education" in education_targets
        assert "regular_education" in education_targets
        assert "supervisor_education" in education_targets
        assert "special_education" in education_targets
        
        # 3. 신규 채용자 교육 이수 등록
        new_employee_education = {
            "education_type": "new_employee",
            "participants": [
                {
                    "worker_id": 1,
                    "name": "신입사원1",
                    "hire_date": datetime.now().isoformat(),
                    "education_date": datetime.now().isoformat(),
                    "education_hours": 8,
                    "education_content": [
                        "산업안전보건법령 및 산업재해보상보험 제도",
                        "작업장 안전수칙",
                        "보호구 착용방법",
                        "위험성평가 및 위험예지훈련"
                    ],
                    "instructor": "김안전교육강사",
                    "test_score": 85,
                    "certificate_issued": True
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/education/record", json=new_employee_education)
        assert response.status_code == 201
        
        # 4. 정기 안전보건교육 계획 수립
        regular_education_plan = {
            "company_id": company_id,
            "year": 2024,
            "education_plans": [
                {
                    "month": 1,
                    "target_group": "사무직",
                    "required_hours": 3,
                    "topics": ["VDT 증후군 예방", "사무실 안전"]
                },
                {
                    "month": 1,
                    "target_group": "현장직",
                    "required_hours": 6,
                    "topics": ["추락재해 예방", "중량물 취급", "개인보호구"]
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/education/annual-plan", json=regular_education_plan)
        assert response.status_code == 201
        
        # 5. 교육 실시 현황 보고서
        response = test_client.get(f"/api/v1/regulatory/education/compliance-report?company_id={company_id}&year=2024")
        assert response.status_code == 200
        
        education_report = response.json()
        assert "completion_rate" in education_report
        assert "by_education_type" in education_report
        assert "non_compliant_workers" in education_report
        
        # 법적 최소 교육시간 준수 확인
        assert education_report["compliance_status"]["meets_legal_requirements"] == True
    
    async def test_health_examination_legal_requirements(self, test_client):
        """건강진단 법적 요구사항 테스트"""
        
        # 1. 일반건강진단 대상자 확인
        general_exam_requirements = {
            "worker_categories": [
                {
                    "category": "사무직",
                    "exam_cycle_months": 24,
                    "last_exam_date": "2023-01-15"
                },
                {
                    "category": "현장직",
                    "exam_cycle_months": 12,
                    "last_exam_date": "2023-07-20"
                }
            ],
            "current_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/regulatory/health-exam/check-requirements", json=general_exam_requirements)
        assert response.status_code == 200
        
        exam_requirements = response.json()
        assert len(exam_requirements["overdue_workers"]) >= 0
        assert len(exam_requirements["upcoming_workers"]) >= 0
        
        # 2. 특수건강진단 대상 유해인자 및 주기
        special_exam_data = {
            "hazardous_factors": [
                {
                    "factor": "소음",
                    "exposure_level": "85dB 이상",
                    "workers_exposed": 25,
                    "exam_cycle_months": 12,
                    "special_requirements": ["청력검사"]
                },
                {
                    "factor": "분진",
                    "type": "광물성분진",
                    "workers_exposed": 15,
                    "exam_cycle_months": 12,
                    "special_requirements": ["흉부X선", "폐기능검사"]
                },
                {
                    "factor": "화학물질",
                    "substances": ["톨루엔", "크실렌"],
                    "workers_exposed": 10,
                    "exam_cycle_months": 6,
                    "special_requirements": ["요중대사물검사", "간기능검사"]
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/health-exam/special-requirements", json=special_exam_data)
        assert response.status_code == 200
        
        special_requirements = response.json()
        assert special_requirements["total_special_exam_workers"] == 50
        assert len(special_requirements["exam_schedule"]) > 0
        
        # 3. 배치전 건강진단 대상자
        pre_placement_data = {
            "new_workers": [
                {
                    "worker_id": 101,
                    "name": "신규근로자1",
                    "assigned_work": "용접작업",
                    "hazardous_factors": ["용접흄", "소음"],
                    "hire_date": datetime.now().isoformat()
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/health-exam/pre-placement", json=pre_placement_data)
        assert response.status_code == 201
        
        # 4. 건강진단 실시 결과 보고
        exam_results_report = {
            "exam_period": {
                "start": "2024-01-01",
                "end": "2024-06-30"
            },
            "exam_statistics": {
                "general_exam": {
                    "target_workers": 150,
                    "completed": 148,
                    "results": {
                        "A": 120,
                        "B": 20,
                        "C": 6,
                        "D": 2
                    }
                },
                "special_exam": {
                    "target_workers": 50,
                    "completed": 50,
                    "results": {
                        "A": 40,
                        "C1": 8,
                        "D1": 2
                    }
                }
            }
        }
        
        response = test_client.post("/api/v1/regulatory/health-exam/submit-report", json=exam_results_report)
        assert response.status_code == 201
        
        # 5. 유소견자 사후관리 의무 이행
        follow_up_management = {
            "d_grade_workers": [
                {
                    "worker_id": 201,
                    "exam_date": "2024-03-15",
                    "diagnosis": "고혈압",
                    "work_restriction": "야간작업 제한",
                    "medical_treatment": True,
                    "follow_up_exam_date": "2024-06-15"
                }
            ],
            "c_grade_workers": [
                {
                    "worker_id": 202,
                    "exam_date": "2024-03-20",
                    "diagnosis": "요통",
                    "health_counseling_date": "2024-04-01",
                    "work_improvement": "중량물 취급 제한"
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/health-exam/follow-up-management", json=follow_up_management)
        assert response.status_code == 201
    
    async def test_workplace_monitoring_requirements(self, test_client):
        """작업환경측정 법적 요구사항 테스트"""
        
        # 1. 측정 대상 유해인자 확인
        measurement_requirements = {
            "workplace_hazards": [
                {
                    "location": "도장작업장",
                    "hazardous_factors": ["톨루엔", "크실렌", "MEK"],
                    "workers_exposed": 8,
                    "daily_exposure_hours": 6
                },
                {
                    "location": "용접작업장",
                    "hazardous_factors": ["용접흄", "망간", "소음"],
                    "workers_exposed": 12,
                    "daily_exposure_hours": 8
                },
                {
                    "location": "목공작업장",
                    "hazardous_factors": ["목재분진", "소음"],
                    "workers_exposed": 6,
                    "daily_exposure_hours": 8
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/monitoring/requirements", json=measurement_requirements)
        assert response.status_code == 200
        
        monitoring_requirements = response.json()
        assert monitoring_requirements["measurement_required"] == True
        assert monitoring_requirements["measurement_cycle_months"] == 6
        assert len(monitoring_requirements["measurement_items"]) > 0
        
        # 2. 작업환경측정 계획 신고
        measurement_plan = {
            "company_id": 1,
            "measurement_agency": "한국산업보건환경연구소",
            "agency_registration": "측정기관-2024-001",
            "planned_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "measurement_items": [
                {
                    "workplace": "도장작업장",
                    "substances": ["톨루엔", "크실렌"],
                    "sampling_method": "개인시료채취",
                    "number_of_samples": 5
                }
            ],
            "estimated_cost": 3000000
        }
        
        response = test_client.post("/api/v1/regulatory/monitoring/submit-plan", json=measurement_plan)
        assert response.status_code == 201
        
        plan_id = response.json()["plan_id"]
        
        # 3. 측정 결과 보고
        measurement_results = {
            "plan_id": plan_id,
            "measurement_date": datetime.now().isoformat(),
            "results": [
                {
                    "workplace": "도장작업장",
                    "substance": "톨루엔",
                    "measurement_value": 15.5,
                    "unit": "ppm",
                    "exposure_limit": 20,
                    "evaluation": "노출기준 미만"
                },
                {
                    "workplace": "용접작업장",
                    "substance": "망간",
                    "measurement_value": 0.25,
                    "unit": "mg/m³",
                    "exposure_limit": 0.2,
                    "evaluation": "노출기준 초과"
                }
            ],
            "improvement_required": True
        }
        
        response = test_client.post("/api/v1/regulatory/monitoring/submit-results", json=measurement_results)
        assert response.status_code == 201
        
        # 4. 노출기준 초과 시 개선 조치
        improvement_plan = {
            "result_id": response.json()["result_id"],
            "exceeded_items": [
                {
                    "workplace": "용접작업장",
                    "substance": "망간",
                    "improvement_measures": [
                        "국소배기장치 성능 개선",
                        "작업시간 단축",
                        "호흡보호구 지급"
                    ],
                    "implementation_deadline": (datetime.now() + timedelta(days=60)).isoformat(),
                    "estimated_cost": 5000000
                }
            ],
            "re_measurement_date": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        response = test_client.post("/api/v1/regulatory/monitoring/improvement-plan", json=improvement_plan)
        assert response.status_code == 201
        
        # 5. 측정 결과 근로자 공지
        notification_data = {
            "result_id": response.json()["result_id"],
            "notification_methods": [
                "게시판 공고",
                "부서별 교육",
                "개별 통지"
            ],
            "notification_date": datetime.now().isoformat(),
            "worker_feedback_received": True
        }
        
        response = test_client.post("/api/v1/regulatory/monitoring/worker-notification", json=notification_data)
        assert response.status_code == 201
    
    async def test_msds_management_compliance(self, test_client):
        """물질안전보건자료(MSDS) 관리 준수 테스트"""
        
        # 1. MSDS 대상 화학물질 목록
        chemical_inventory = {
            "chemicals": [
                {
                    "name": "톨루엔",
                    "cas_no": "108-88-3",
                    "manufacturer": "한국화학(주)",
                    "usage": "도료 희석제",
                    "monthly_usage_kg": 500,
                    "msds_required": True,
                    "classification": "인화성액체 구분2"
                },
                {
                    "name": "아세톤",
                    "cas_no": "67-64-1",
                    "manufacturer": "대한솔벤트",
                    "usage": "세척제",
                    "monthly_usage_kg": 200,
                    "msds_required": True,
                    "classification": "인화성액체 구분2"
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/msds/inventory", json=chemical_inventory)
        assert response.status_code == 201
        
        # 2. MSDS 비치 및 게시 확인
        msds_compliance_check = {
            "workplace_locations": [
                {
                    "location": "화학물질 보관소",
                    "msds_binder_available": True,
                    "msds_posted": True,
                    "language": "korean",
                    "last_update": "2024-01-15"
                },
                {
                    "location": "도장작업장",
                    "msds_binder_available": True,
                    "msds_posted": True,
                    "emergency_info_posted": True
                }
            ],
            "digital_msds_system": True,
            "worker_access_guaranteed": True
        }
        
        response = test_client.post("/api/v1/regulatory/msds/compliance-check", json=msds_compliance_check)
        assert response.status_code == 200
        
        compliance_result = response.json()
        assert compliance_result["compliant"] == True
        
        # 3. MSDS 교육 실시 기록
        msds_education = {
            "education_date": datetime.now().isoformat(),
            "participants": [
                {"worker_id": 301, "name": "작업자1", "department": "도장팀"},
                {"worker_id": 302, "name": "작업자2", "department": "도장팀"}
            ],
            "education_content": [
                "MSDS 읽는 방법",
                "위험성 정보 이해",
                "비상시 대응 방법",
                "개인보호구 선택"
            ],
            "education_hours": 2,
            "test_conducted": True,
            "average_score": 85
        }
        
        response = test_client.post("/api/v1/regulatory/msds/education-record", json=msds_education)
        assert response.status_code == 201
        
        # 4. 화학물질 위험성평가
        risk_assessment = {
            "assessment_date": datetime.now().isoformat(),
            "chemicals_assessed": [
                {
                    "chemical": "톨루엔",
                    "exposure_scenario": "도장작업",
                    "exposure_route": ["흡입", "피부"],
                    "risk_level": "중간",
                    "control_measures": [
                        "국소배기장치 설치",
                        "호흡보호구 착용",
                        "작업시간 제한"
                    ]
                }
            ],
            "overall_risk": "acceptable_with_controls"
        }
        
        response = test_client.post("/api/v1/regulatory/msds/risk-assessment", json=risk_assessment)
        assert response.status_code == 201
        
        # 5. 연간 화학물질 사용량 보고
        annual_chemical_report = {
            "year": 2024,
            "reporting_company": "안전건설(주)",
            "chemicals": [
                {
                    "name": "톨루엔",
                    "cas_no": "108-88-3",
                    "annual_usage_kg": 6000,
                    "emission_kg": 300,
                    "disposal_kg": 100
                }
            ],
            "submitted_to": "환경부",
            "submission_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/regulatory/msds/annual-report", json=annual_chemical_report)
        assert response.status_code == 201
    
    async def test_accident_reporting_requirements(self, test_client):
        """산업재해 발생 보고 의무 테스트"""
        
        # 1. 중대재해 발생 신고 (즉시)
        serious_accident = {
            "accident_type": "serious",
            "occurred_at": datetime.now().isoformat(),
            "location": "3층 철골 작업장",
            "accident_details": {
                "type": "추락",
                "height_meters": 8,
                "victim": {
                    "name": "김근로",
                    "age": 45,
                    "position": "철골공",
                    "employment_type": "regular"
                },
                "injury_severity": "사망",
                "cause": "안전대 미착용"
            },
            "emergency_measures": [
                "119 신고",
                "작업 중지",
                "현장 보존"
            ],
            "reported_within_hours": 0.5
        }
        
        response = test_client.post("/api/v1/regulatory/accident/report-serious", json=serious_accident)
        assert response.status_code == 201
        
        report_id = response.json()["report_id"]
        assert response.json()["reported_to"] == ["고용노동부", "안전보건공단"]
        
        # 2. 일반 산업재해 발생 보고 (1개월 이내)
        regular_accident = {
            "accident_type": "regular",
            "occurred_at": (datetime.now() - timedelta(days=10)).isoformat(),
            "reported_at": datetime.now().isoformat(),
            "victim_info": {
                "name": "이근로",
                "employee_id": "EMP123",
                "department": "건설현장2팀"
            },
            "accident_info": {
                "type": "협착",
                "body_part": "손가락",
                "lost_days": 5,
                "medical_treatment": "병원 치료",
                "treatment_cost": 500000
            },
            "investigation_result": {
                "direct_cause": "작업 절차 미준수",
                "indirect_cause": "안전교육 부족",
                "preventive_measures": [
                    "작업 절차 재교육",
                    "안전장치 보강"
                ]
            }
        }
        
        response = test_client.post("/api/v1/regulatory/accident/report-regular", json=regular_accident)
        assert response.status_code == 201
        
        # 3. 산업재해 조사표 작성
        investigation_form = {
            "report_id": report_id,
            "investigation_date": datetime.now().isoformat(),
            "investigators": [
                {"name": "김안전", "role": "안전관리자"},
                {"name": "이보건", "role": "보건관리자"}
            ],
            "accident_analysis": {
                "timeline": [
                    {"time": "09:00", "event": "작업 시작"},
                    {"time": "10:30", "event": "안전대 미착용 상태로 철골 위 이동"},
                    {"time": "10:45", "event": "발을 헛디뎌 추락"}
                ],
                "contributing_factors": [
                    "안전대 미착용",
                    "안전난간 미설치",
                    "작업 전 안전점검 미실시"
                ],
                "similar_accidents": 2,
                "risk_assessment_conducted": False
            },
            "corrective_actions": [
                {
                    "action": "전 작업자 안전대 착용 의무화",
                    "responsible": "현장소장",
                    "deadline": (datetime.now() + timedelta(days=1)).isoformat()
                },
                {
                    "action": "추락방지 안전난간 설치",
                    "responsible": "안전관리자",
                    "deadline": (datetime.now() + timedelta(days=7)).isoformat()
                }
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/accident/investigation-form", json=investigation_form)
        assert response.status_code == 201
        
        # 4. 재해율 산정 및 보고
        accident_statistics = {
            "year": 2024,
            "quarter": 2,
            "statistics": {
                "total_workers": 150,
                "total_working_hours": 72000,
                "accidents": {
                    "fatal": 1,
                    "lost_time": 5,
                    "no_lost_time": 10,
                    "near_miss": 25
                },
                "lost_days": 180,
                "accident_rate": 3.33,  # 재해율
                "frequency_rate": 6.94,  # 도수율
                "severity_rate": 2.50  # 강도율
            }
        }
        
        response = test_client.post("/api/v1/regulatory/accident/quarterly-statistics", json=accident_statistics)
        assert response.status_code == 201
        
        # 5. 중대재해 감축 로드맵 이행
        reduction_roadmap = {
            "target_year": 2024,
            "baseline_year": 2023,
            "targets": {
                "fatal_reduction": 50,  # 50% 감축
                "serious_injury_reduction": 30  # 30% 감축
            },
            "implementation_status": [
                {
                    "measure": "고위험 작업 사전허가제",
                    "status": "implemented",
                    "effectiveness": "high"
                },
                {
                    "measure": "안전보건 전담조직 신설",
                    "status": "in_progress",
                    "completion_rate": 80
                }
            ],
            "investment": {
                "safety_equipment": 100000000,
                "safety_education": 50000000,
                "system_improvement": 80000000
            }
        }
        
        response = test_client.post("/api/v1/regulatory/accident/reduction-roadmap", json=reduction_roadmap)
        assert response.status_code == 201
    
    async def test_regulatory_audit_and_inspection(self, test_client):
        """법적 감독 및 검사 대응 테스트"""
        
        # 1. 정기 감독 준비 체크리스트
        inspection_preparation = {
            "inspection_type": "정기감독",
            "scheduled_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "checklist": {
                "documentation": [
                    {"item": "안전보건관리규정", "status": "ready", "location": "안전관리실"},
                    {"item": "안전보건교육일지", "status": "ready", "location": "교육실"},
                    {"item": "건강진단결과", "status": "ready", "location": "보건실"},
                    {"item": "작업환경측정결과", "status": "updating", "completion_date": "2024-07-25"}
                ],
                "physical_conditions": [
                    {"area": "작업장 정리정돈", "status": "in_progress"},
                    {"area": "안전보호구 비치", "status": "completed"},
                    {"area": "비상구 확보", "status": "completed"}
                ],
                "personnel": [
                    {"role": "안전보건관리책임자", "name": "김대표", "available": True},
                    {"role": "안전관리자", "name": "김안전", "available": True},
                    {"role": "보건관리자", "name": "이보건", "available": True}
                ]
            }
        }
        
        response = test_client.post("/api/v1/regulatory/inspection/prepare", json=inspection_preparation)
        assert response.status_code == 201
        
        preparation_id = response.json()["preparation_id"]
        
        # 2. 자체 점검 실시
        self_inspection = {
            "inspection_date": datetime.now().isoformat(),
            "inspectors": ["안전팀", "보건팀"],
            "areas_inspected": [
                {
                    "area": "건설현장1",
                    "findings": [
                        {
                            "issue": "일부 근로자 안전모 미착용",
                            "severity": "minor",
                            "corrective_action": "즉시 시정",
                            "photo_evidence": "evidence_001.jpg"
                        }
                    ],
                    "score": 85
                },
                {
                    "area": "화학물질보관소",
                    "findings": [],
                    "score": 100
                }
            ],
            "overall_compliance_rate": 92.5
        }
        
        response = test_client.post("/api/v1/regulatory/inspection/self-inspection", json=self_inspection)
        assert response.status_code == 201
        
        # 3. 감독 결과 및 시정 조치
        inspection_result = {
            "inspection_id": "MOEL-2024-12345",
            "inspection_date": datetime.now().isoformat(),
            "inspector": "고용노동부 서울지방청",
            "violations": [
                {
                    "violation_code": "OSH-001",
                    "description": "안전난간 높이 미달",
                    "legal_basis": "산업안전보건기준에관한규칙 제13조",
                    "location": "3층 작업장",
                    "penalty": {
                        "type": "시정명령",
                        "deadline": (datetime.now() + timedelta(days=14)).isoformat()
                    }
                },
                {
                    "violation_code": "OSH-002",
                    "description": "특수건강진단 미실시 근로자 2명",
                    "legal_basis": "산업안전보건법 제130조",
                    "penalty": {
                        "type": "과태료",
                        "amount": 1000000
                    }
                }
            ],
            "total_fine": 1000000
        }
        
        response = test_client.post("/api/v1/regulatory/inspection/result", json=inspection_result)
        assert response.status_code == 201
        
        # 4. 시정 조치 이행 보고
        corrective_actions = {
            "inspection_id": "MOEL-2024-12345",
            "actions": [
                {
                    "violation_code": "OSH-001",
                    "action_taken": "안전난간 높이 1.2m로 재설치",
                    "completion_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "cost": 3000000,
                    "evidence": ["photo_after_001.jpg", "invoice_001.pdf"]
                },
                {
                    "violation_code": "OSH-002",
                    "action_taken": "미실시 근로자 2명 특수건강진단 완료",
                    "completion_date": (datetime.now() + timedelta(days=5)).isoformat(),
                    "evidence": ["health_exam_results.pdf"]
                }
            ],
            "report_submitted_date": (datetime.now() + timedelta(days=10)).isoformat()
        }
        
        response = test_client.post("/api/v1/regulatory/inspection/corrective-report", json=corrective_actions)
        assert response.status_code == 201
        
        # 5. 연간 법규 준수 평가
        annual_compliance_review = {
            "year": 2024,
            "company_id": 1,
            "compliance_areas": [
                {
                    "area": "안전보건관리체제",
                    "requirements": 15,
                    "compliant": 15,
                    "compliance_rate": 100
                },
                {
                    "area": "안전보건교육",
                    "requirements": 12,
                    "compliant": 11,
                    "compliance_rate": 91.7,
                    "non_compliance": ["관리감독자 정기교육 일부 미달"]
                },
                {
                    "area": "건강관리",
                    "requirements": 10,
                    "compliant": 10,
                    "compliance_rate": 100
                },
                {
                    "area": "작업환경관리",
                    "requirements": 8,
                    "compliant": 8,
                    "compliance_rate": 100
                }
            ],
            "overall_compliance_rate": 97.9,
            "improvement_plans": [
                "관리감독자 교육 이수율 100% 달성",
                "자율안전관리 시스템 구축"
            ]
        }
        
        response = test_client.post("/api/v1/regulatory/compliance/annual-review", json=annual_compliance_review)
        assert response.status_code == 201


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 법적 규정 준수 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 법적 규정 준수 통합 테스트 실패")
        sys.exit(1)