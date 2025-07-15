"""
보건교육 시스템 통합 테스트
Health Education System Integration Tests
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestHealthEducationSystem:
    """보건교육 계획 수립부터 효과 평가까지 전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_education_program_data(self):
        """샘플 교육 프로그램 데이터"""
        return {
            "program_name": "화학물질 안전취급 교육",
            "education_type": "mandatory",
            "target_audience": "chemical_handlers",
            "duration_hours": 4,
            "frequency": "quarterly",
            "learning_objectives": [
                "화학물질의 위험성 이해",
                "MSDS 읽는 방법 습득",
                "개인보호구 올바른 착용법",
                "응급처치 방법 숙지"
            ],
            "curriculum": [
                {
                    "module": "화학물질 기초 지식",
                    "duration_minutes": 60,
                    "content_type": "lecture",
                    "topics": ["화학물질 분류", "위험성 평가", "노출 경로"]
                },
                {
                    "module": "MSDS 활용법",
                    "duration_minutes": 60,
                    "content_type": "interactive",
                    "topics": ["MSDS 구성", "정보 해석", "실습"]
                },
                {
                    "module": "개인보호구 실습",
                    "duration_minutes": 90,
                    "content_type": "hands_on",
                    "topics": ["보호구 종류", "착용 실습", "관리 방법"]
                },
                {
                    "module": "응급상황 대응",
                    "duration_minutes": 30,
                    "content_type": "simulation",
                    "topics": ["응급처치", "대피 절차", "신고 체계"]
                }
            ],
            "instructor_requirements": [
                "산업보건 전문가",
                "화학물질 취급 경험 5년 이상"
            ],
            "materials_needed": [
                "MSDS 샘플",
                "각종 개인보호구",
                "화학물질 모형",
                "응급처치 키트"
            ],
            "evaluation_methods": [
                "필기시험",
                "실기평가",
                "현장적용평가"
            ],
            "pass_criteria": {
                "written_exam": 80,
                "practical_exam": 85,
                "overall_score": 80
            }
        }
    
    @pytest.fixture
    def sample_worker_data(self):
        """샘플 근로자 데이터"""
        return {
            "name": "정화학",
            "department": "화학처리팀",
            "position": "화학기술자",
            "work_type": "chemical_handling",
            "hire_date": "2020-01-01",
            "education_level": "university",
            "experience_years": 4
        }
    
    async def test_education_program_creation_and_scheduling(self, test_client, sample_education_program_data):
        """교육 프로그램 생성 및 일정 수립 테스트"""
        
        # 1. 교육 프로그램 등록
        response = test_client.post("/api/v1/health-educations/programs/", json=sample_education_program_data)
        assert response.status_code == 201
        
        program_data = response.json()
        program_id = program_data["id"]
        
        # 등록된 데이터 검증
        assert program_data["program_name"] == sample_education_program_data["program_name"]
        assert program_data["duration_hours"] == 4
        assert len(program_data["curriculum"]) == 4
        
        # 2. 교육 일정 생성
        education_schedule_data = {
            "program_id": program_id,
            "scheduled_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "duration_hours": 4,
            "location": "교육센터 A강의실",
            "instructor": "김화학박사",
            "max_participants": 20,
            "registration_deadline": (datetime.now() + timedelta(days=7)).isoformat(),
            "materials_provided": True,
            "refreshments_provided": True,
            "parking_available": True
        }
        
        response = test_client.post("/api/v1/health-educations/schedules/", json=education_schedule_data)
        assert response.status_code == 201
        
        schedule_id = response.json()["id"]
        
        # 3. 교육 일정 상세 조회
        response = test_client.get(f"/api/v1/health-educations/schedules/{schedule_id}")
        assert response.status_code == 200
        
        schedule_detail = response.json()
        assert schedule_detail["program_id"] == program_id
        assert schedule_detail["instructor"] == "김화학박사"
        assert schedule_detail["status"] == "scheduled"
        
        # 4. 프로그램별 교육 일정 조회
        response = test_client.get(f"/api/v1/health-educations/programs/{program_id}/schedules")
        assert response.status_code == 200
        
        program_schedules = response.json()
        assert len(program_schedules) >= 1
        assert program_schedules[0]["id"] == schedule_id
        
        return program_id, schedule_id
    
    async def test_worker_education_enrollment_and_attendance(self, test_client, sample_worker_data, sample_education_program_data):
        """근로자 교육 신청 및 참석 관리 테스트"""
        
        # 1. 사전 준비: 근로자 및 교육 프로그램 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        response = test_client.post("/api/v1/health-educations/programs/", json=sample_education_program_data)
        program_id = response.json()["id"]
        
        schedule_data = {
            "program_id": program_id,
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "max_participants": 20
        }
        
        response = test_client.post("/api/v1/health-educations/schedules/", json=schedule_data)
        schedule_id = response.json()["id"]
        
        # 2. 근로자 교육 신청
        enrollment_data = {
            "worker_id": worker_id,
            "schedule_id": schedule_id,
            "enrollment_reason": "법정 의무교육",
            "special_requirements": "없음",
            "manager_approval": True,
            "enrollment_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/health-educations/enrollments/", json=enrollment_data)
        assert response.status_code == 201
        
        enrollment_id = response.json()["id"]
        
        # 3. 교육 참석 확인
        attendance_data = {
            "enrollment_id": enrollment_id,
            "attendance_status": "present",
            "check_in_time": datetime.now().isoformat(),
            "participation_score": 90,  # 참여도 점수
            "notes": "적극적으로 질문하고 참여함"
        }
        
        response = test_client.post("/api/v1/health-educations/attendance/", json=attendance_data)
        assert response.status_code == 201
        
        attendance_id = response.json()["id"]
        
        # 4. 교육 이수 평가
        evaluation_data = {
            "enrollment_id": enrollment_id,
            "written_exam_score": 85,
            "practical_exam_score": 90,
            "overall_score": 87,
            "pass_status": "passed",
            "evaluator": "김화학박사",
            "evaluation_date": datetime.now().isoformat(),
            "strengths": ["이론 이해도 높음", "실습 숙련도 우수"],
            "areas_for_improvement": ["응급처치 절차 추가 숙지 필요"],
            "certificate_issued": True
        }
        
        response = test_client.put(f"/api/v1/health-educations/enrollments/{enrollment_id}/evaluation", json=evaluation_data)
        assert response.status_code == 200
        
        # 5. 근로자 교육 이력 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}/education-history")
        assert response.status_code == 200
        
        education_history = response.json()
        assert len(education_history) >= 1
        assert education_history[0]["program_name"] == sample_education_program_data["program_name"]
        assert education_history[0]["pass_status"] == "passed"
        
        return enrollment_id
    
    async def test_mandatory_education_compliance_tracking(self, test_client):
        """법정 의무교육 준수 추적 테스트"""
        
        # 1. 의무교육 프로그램 정의
        mandatory_programs = [
            {
                "program_name": "신규근로자 안전보건교육",
                "education_type": "mandatory",
                "target_audience": "new_employees",
                "required_within_days": 7,
                "duration_hours": 8,
                "frequency": "once",
                "legal_basis": "산업안전보건법 제31조"
            },
            {
                "program_name": "관리감독자 안전보건교육",
                "education_type": "mandatory",
                "target_audience": "supervisors",
                "required_within_days": 365,
                "duration_hours": 16,
                "frequency": "annual",
                "legal_basis": "산업안전보건법 제32조"
            },
            {
                "program_name": "특수건강진단 대상자 교육",
                "education_type": "mandatory",
                "target_audience": "hazardous_workers",
                "required_within_days": 90,
                "duration_hours": 2,
                "frequency": "quarterly",
                "legal_basis": "산업안전보건법 제130조"
            }
        ]
        
        created_programs = []
        for program_data in mandatory_programs:
            response = test_client.post("/api/v1/health-educations/programs/", json=program_data)
            assert response.status_code == 201
            created_programs.append(response.json())
        
        # 2. 의무교육 대상자 자동 식별
        response = test_client.get("/api/v1/health-educations/compliance/mandatory-targets")
        assert response.status_code == 200
        
        mandatory_targets = response.json()
        assert "new_employees" in mandatory_targets
        assert "supervisors" in mandatory_targets
        assert "hazardous_workers" in mandatory_targets
        
        # 3. 교육 미수료자 현황
        response = test_client.get("/api/v1/health-educations/compliance/overdue")
        assert response.status_code == 200
        
        overdue_list = response.json()
        
        # 4. 자동 알림 설정
        reminder_config = {
            "reminder_intervals": [30, 14, 7, 1],  # 교육 기한 전 알림 (일)
            "overdue_alerts": [1, 7, 30],  # 교육 기한 후 알림 (일)
            "escalation_rules": [
                {
                    "days_overdue": 7,
                    "escalate_to": ["department_manager"],
                    "action": "email_notification"
                },
                {
                    "days_overdue": 30,
                    "escalate_to": ["safety_manager", "hr_manager"],
                    "action": "formal_warning"
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/compliance/reminder-config", json=reminder_config)
        assert response.status_code == 201
        
        # 5. 부서별 의무교육 이수율 조회
        response = test_client.get("/api/v1/health-educations/compliance/completion-rates")
        assert response.status_code == 200
        
        completion_rates = response.json()
        assert "overall_rate" in completion_rates
        assert "by_department" in completion_rates
        assert "by_program" in completion_rates
    
    async def test_education_effectiveness_evaluation(self, test_client):
        """교육 효과성 평가 테스트"""
        
        # 1. 교육 전후 평가 설정
        pre_post_evaluation_data = {
            "program_id": 1,  # 기존 프로그램 ID 사용
            "evaluation_type": "pre_post_assessment",
            "pre_assessment": {
                "knowledge_test": {
                    "questions": [
                        {
                            "question": "화학물질 안전보건자료(MSDS)에서 가장 중요한 정보는?",
                            "options": ["제조사", "위험성 정보", "가격", "색상"],
                            "correct_answer": 1
                        },
                        {
                            "question": "개인보호구 착용 순서로 올바른 것은?",
                            "options": ["호흡기→안면보호→장갑", "장갑→호흡기→안면보호", "안면보호→호흡기→장갑", "순서 무관"],
                            "correct_answer": 0
                        }
                    ]
                },
                "attitude_survey": {
                    "questions": [
                        "안전보건 규정 준수의 중요성을 얼마나 인식하고 있습니까?",
                        "개인보호구 착용에 대한 귀하의 태도는?"
                    ]
                }
            },
            "post_assessment": {
                "immediate_evaluation": "교육 직후 평가",
                "follow_up_periods": [30, 90, 180]  # 교육 후 추적 평가 (일)
            }
        }
        
        response = test_client.post("/api/v1/health-educations/evaluations/setup", json=pre_post_evaluation_data)
        assert response.status_code == 201
        
        evaluation_setup_id = response.json()["id"]
        
        # 2. 교육 전 평가 실시
        pre_assessment_results = {
            "evaluation_setup_id": evaluation_setup_id,
            "participant_results": [
                {
                    "worker_id": 1,
                    "knowledge_score": 65,
                    "attitude_scores": [3, 2],  # 1-5 척도
                    "assessment_date": datetime.now().isoformat()
                },
                {
                    "worker_id": 2,
                    "knowledge_score": 70,
                    "attitude_scores": [4, 3],
                    "assessment_date": datetime.now().isoformat()
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/evaluations/pre-assessment", json=pre_assessment_results)
        assert response.status_code == 201
        
        # 3. 교육 후 즉시 평가
        post_assessment_results = {
            "evaluation_setup_id": evaluation_setup_id,
            "assessment_type": "immediate",
            "participant_results": [
                {
                    "worker_id": 1,
                    "knowledge_score": 90,
                    "attitude_scores": [5, 4],
                    "satisfaction_score": 4.5,
                    "assessment_date": datetime.now().isoformat()
                },
                {
                    "worker_id": 2,
                    "knowledge_score": 95,
                    "attitude_scores": [5, 5],
                    "satisfaction_score": 4.8,
                    "assessment_date": datetime.now().isoformat()
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/evaluations/post-assessment", json=post_assessment_results)
        assert response.status_code == 201
        
        # 4. 현장 적용도 평가 (30일 후)
        field_application_data = {
            "evaluation_setup_id": evaluation_setup_id,
            "assessment_type": "field_application",
            "evaluation_period": 30,
            "observations": [
                {
                    "worker_id": 1,
                    "observed_behaviors": [
                        "개인보호구 올바른 착용",
                        "MSDS 확인 후 작업",
                        "안전절차 준수"
                    ],
                    "improvement_areas": ["응급상황 대응 속도"],
                    "overall_application_score": 85,
                    "observer": "현장안전관리자"
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/evaluations/field-assessment", json=field_application_data)
        assert response.status_code == 201
        
        # 5. 교육 효과성 종합 분석
        response = test_client.get(f"/api/v1/health-educations/evaluations/{evaluation_setup_id}/effectiveness-analysis")
        assert response.status_code == 200
        
        effectiveness_analysis = response.json()
        assert "knowledge_improvement" in effectiveness_analysis
        assert "attitude_change" in effectiveness_analysis
        assert "behavior_change" in effectiveness_analysis
        assert "roi_analysis" in effectiveness_analysis
    
    async def test_customized_education_content_management(self, test_client):
        """맞춤형 교육 콘텐츠 관리 테스트"""
        
        # 1. 부서별 맞춤 교육 콘텐츠 생성
        customized_content_data = {
            "base_program_id": 1,
            "customizations": [
                {
                    "target_department": "화학처리팀",
                    "specific_hazards": ["톨루엔", "크실렌", "메틸에틸케톤"],
                    "additional_modules": [
                        {
                            "module_name": "톨루엔 특별 안전교육",
                            "duration_minutes": 30,
                            "content": "톨루엔 특성, 노출 위험성, 특별 보호조치"
                        }
                    ],
                    "case_studies": [
                        "A사 톨루엔 노출 사고 사례",
                        "B사 화학물질 안전관리 우수 사례"
                    ]
                },
                {
                    "target_department": "용접팀",
                    "specific_hazards": ["용접흄", "자외선", "고온"],
                    "additional_modules": [
                        {
                            "module_name": "용접작업 특별 안전교육",
                            "duration_minutes": 45,
                            "content": "용접흄 위험성, 환기 중요성, 보호구 선택"
                        }
                    ]
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/content/customize", json=customized_content_data)
        assert response.status_code == 201
        
        customization_id = response.json()["id"]
        
        # 2. 멀티미디어 교육 자료 업로드
        multimedia_content = {
            "customization_id": customization_id,
            "content_items": [
                {
                    "type": "video",
                    "title": "화학물질 안전취급 실습 영상",
                    "file_path": "/education/videos/chemical_safety_practice.mp4",
                    "duration_minutes": 15,
                    "accessibility_features": ["subtitles", "sign_language"]
                },
                {
                    "type": "interactive_simulation",
                    "title": "화학물질 누출 대응 시뮬레이션",
                    "file_path": "/education/simulations/spill_response.html",
                    "interaction_time_minutes": 20
                },
                {
                    "type": "vr_training",
                    "title": "가상현실 화학공정 안전교육",
                    "file_path": "/education/vr/chemical_process_safety.vr",
                    "required_equipment": ["VR 헤드셋", "컨트롤러"]
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/content/multimedia", json=multimedia_content)
        assert response.status_code == 201
        
        # 3. 개인별 학습 경로 추천
        learning_path_data = {
            "worker_id": 1,
            "current_competency_level": "intermediate",
            "learning_preferences": ["visual", "hands_on"],
            "available_time_hours": 8,
            "priority_areas": ["chemical_safety", "emergency_response"],
            "career_goals": ["safety_specialist"]
        }
        
        response = test_client.post("/api/v1/health-educations/learning-path/generate", json=learning_path_data)
        assert response.status_code == 200
        
        learning_path = response.json()
        assert "recommended_courses" in learning_path
        assert "estimated_completion_time" in learning_path
        assert "skill_progression" in learning_path
        
        # 4. 적응형 학습 시스템
        adaptive_learning_config = {
            "enable_difficulty_adjustment": True,
            "performance_thresholds": {
                "increase_difficulty": 90,
                "decrease_difficulty": 60
            },
            "content_recommendation_engine": True,
            "real_time_feedback": True
        }
        
        response = test_client.post("/api/v1/health-educations/adaptive-learning/config", json=adaptive_learning_config)
        assert response.status_code == 201
    
    async def test_education_resource_management(self, test_client):
        """교육 자원 관리 테스트"""
        
        # 1. 강사 자원 관리
        instructor_data = {
            "name": "박안전박사",
            "qualifications": [
                "산업보건학 박사",
                "산업안전기사",
                "화학물질관리 전문가"
            ],
            "specializations": ["화학안전", "작업환경측정", "위험성평가"],
            "teaching_experience_years": 12,
            "available_days": ["월", "화", "수", "목"],
            "max_hours_per_week": 20,
            "hourly_rate": 150000,
            "evaluation_score": 4.8,
            "certifications": [
                {
                    "name": "안전보건교육기관 강사 자격",
                    "issued_by": "고용노동부",
                    "valid_until": "2025-12-31"
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/instructors/", json=instructor_data)
        assert response.status_code == 201
        
        instructor_id = response.json()["id"]
        
        # 2. 교육 시설 및 장비 관리
        facility_data = {
            "name": "교육센터 A강의실",
            "capacity": 30,
            "location": "본관 2층",
            "equipment": [
                "프로젝터",
                "스크린",
                "마이크 시스템",
                "컴퓨터",
                "VR 헤드셋 10대",
                "실습용 보호구 세트"
            ],
            "accessibility_features": [
                "휠체어 접근 가능",
                "청각장애인용 보조기기"
            ],
            "booking_rules": {
                "advance_booking_days": 7,
                "max_booking_hours": 8,
                "cleaning_time_minutes": 30
            }
        }
        
        response = test_client.post("/api/v1/health-educations/facilities/", json=facility_data)
        assert response.status_code == 201
        
        facility_id = response.json()["id"]
        
        # 3. 교육 자료 라이브러리 관리
        educational_materials = {
            "categories": [
                {
                    "category": "화학물질 안전",
                    "materials": [
                        {
                            "title": "화학물질 분류 및 표시 가이드",
                            "type": "handbook",
                            "language": "korean",
                            "last_updated": datetime.now().isoformat(),
                            "version": "2024.1"
                        },
                        {
                            "title": "MSDS 읽기 실습서",
                            "type": "workbook",
                            "language": "korean",
                            "interactive_elements": True
                        }
                    ]
                },
                {
                    "category": "개인보호구",
                    "materials": [
                        {
                            "title": "PPE 선택 및 착용 가이드",
                            "type": "video_series",
                            "duration_minutes": 45,
                            "languages": ["korean", "english"]
                        }
                    ]
                }
            ]
        }
        
        response = test_client.post("/api/v1/health-educations/materials/library", json=educational_materials)
        assert response.status_code == 201
        
        # 4. 자원 활용률 분석
        response = test_client.get("/api/v1/health-educations/resources/utilization-analysis")
        assert response.status_code == 200
        
        utilization_analysis = response.json()
        assert "instructor_utilization" in utilization_analysis
        assert "facility_utilization" in utilization_analysis
        assert "material_usage" in utilization_analysis
        
        # 5. 교육 비용 관리
        cost_analysis_data = {
            "analysis_period": "2024-Q2",
            "cost_categories": [
                "instructor_fees",
                "facility_rental",
                "materials",
                "equipment",
                "refreshments"
            ],
            "include_opportunity_cost": True
        }
        
        response = test_client.post("/api/v1/health-educations/cost-analysis", json=cost_analysis_data)
        assert response.status_code == 200
        
        cost_analysis = response.json()
        assert "total_cost" in cost_analysis
        assert "cost_per_participant" in cost_analysis
        assert "cost_effectiveness_ratio" in cost_analysis


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 보건교육 시스템 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 보건교육 시스템 통합 테스트 실패")
        sys.exit(1)