"""
건강진단 전체 워크플로우 통합 테스트
Health Examination Workflow Integration Tests
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestHealthExaminationWorkflow:
    """건강진단 예약부터 결과 관리까지 전체 워크플로우 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_worker_data(self):
        """샘플 근로자 데이터"""
        return {
            "name": "이건강",
            "gender": "female",
            "birth_date": "1990-08-20",
            "employee_id": "EMP002",
            "department": "안전관리팀",
            "position": "안전관리자",
            "hire_date": "2020-03-01",
            "phone": "010-2222-3333",
            "emergency_contact": "010-4444-5555",
            "work_type": "office_work",
            "employment_type": "regular"
        }
    
    @pytest.fixture
    def sample_exam_schedule_data(self):
        """샘플 건강진단 일정 데이터"""
        return {
            "exam_type": "general",
            "scheduled_date": (datetime.now() + timedelta(days=14)).isoformat(),
            "medical_institution": "서울아산병원",
            "exam_items": [
                "일반검진",
                "흉부X선",
                "혈액검사",
                "소변검사",
                "청력검사",
                "시력검사"
            ],
            "fasting_required": True,
            "special_instructions": "전날 저녁 9시 이후 금식",
            "estimated_duration_minutes": 120
        }
    
    async def test_comprehensive_health_exam_scheduling_workflow(self, test_client, sample_worker_data, sample_exam_schedule_data):
        """종합 건강진단 예약 전체 워크플로우 테스트"""
        
        # 1. 근로자 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        # 2. 건강진단 예약
        exam_data = sample_exam_schedule_data.copy()
        exam_data["worker_id"] = worker_id
        
        response = test_client.post("/api/v1/health-exams/", json=exam_data)
        assert response.status_code == 201
        
        exam_id = response.json()["id"]
        created_exam = response.json()
        
        # 예약 데이터 검증
        assert created_exam["worker_id"] == worker_id
        assert created_exam["exam_type"] == "general"
        assert created_exam["status"] == "scheduled"
        
        # 3. 건강진단 일정 조회
        response = test_client.get(f"/api/v1/health-exams/{exam_id}")
        assert response.status_code == 200
        
        exam_detail = response.json()
        assert exam_detail["medical_institution"] == "서울아산병원"
        assert exam_detail["fasting_required"] == True
        
        # 4. 근로자별 건강진단 일정 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}/health-exams")
        assert response.status_code == 200
        
        worker_exams = response.json()
        assert len(worker_exams) >= 1
        assert worker_exams[0]["id"] == exam_id
        
        # 5. 건강진단 알림 설정
        notification_data = {
            "send_sms": True,
            "send_email": True,
            "reminder_days_before": [7, 3, 1],
            "additional_recipients": ["hr@company.com"]
        }
        
        response = test_client.post(f"/api/v1/health-exams/{exam_id}/notifications", json=notification_data)
        assert response.status_code == 201
        
        return exam_id, worker_id
    
    async def test_health_exam_result_input_and_analysis(self, test_client, sample_worker_data):
        """건강진단 결과 입력 및 분석 테스트"""
        
        # 1. 사전 준비: 근로자 및 건강진단 예약
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        exam_data = {
            "worker_id": worker_id,
            "exam_type": "general",
            "scheduled_date": datetime.now().isoformat(),
            "medical_institution": "건강검진센터"
        }
        
        response = test_client.post("/api/v1/health-exams/", json=exam_data)
        exam_id = response.json()["id"]
        
        # 2. 건강진단 결과 입력
        exam_results = {
            "exam_date": datetime.now().isoformat(),
            "overall_result": "정상",
            "detailed_results": {
                "신장": "165cm",
                "체중": "60kg",
                "BMI": "22.0",
                "혈압": "120/80",
                "혈당": "90mg/dL",
                "총콜레스테롤": "180mg/dL",
                "HDL콜레스테롤": "50mg/dL",
                "LDL콜레스테롤": "110mg/dL",
                "중성지방": "100mg/dL",
                "AST": "25U/L",
                "ALT": "20U/L",
                "감마지티피": "15U/L",
                "크레아티닌": "0.8mg/dL",
                "헤모글로빈": "13.5g/dL",
                "백혈구": "6000/μL",
                "혈소판": "250000/μL"
            },
            "abnormal_findings": [],
            "doctor_opinion": "전반적으로 건강 상태 양호",
            "follow_up_required": False,
            "next_exam_recommended_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "health_grade": "A",
            "work_suitability": "적합"
        }
        
        response = test_client.put(f"/api/v1/health-exams/{exam_id}/results", json=exam_results)
        assert response.status_code == 200
        
        # 3. 결과 데이터 검증
        response = test_client.get(f"/api/v1/health-exams/{exam_id}")
        updated_exam = response.json()
        
        assert updated_exam["status"] == "completed"
        assert updated_exam["overall_result"] == "정상"
        assert updated_exam["health_grade"] == "A"
        
        # 4. 건강 트렌드 분석
        response = test_client.get(f"/api/v1/workers/{worker_id}/health-trends")
        assert response.status_code == 200
        
        health_trends = response.json()
        assert "bmi_trend" in health_trends
        assert "blood_pressure_trend" in health_trends
        assert "cholesterol_trend" in health_trends
        
        # 5. 이상 소견 알림 테스트 (정상 결과이므로 알림 없음)
        response = test_client.get(f"/api/v1/health-exams/{exam_id}/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) == 0  # 정상 결과이므로 알림 없음
    
    async def test_abnormal_health_exam_result_management(self, test_client, sample_worker_data):
        """이상 소견 건강진단 결과 관리 테스트"""
        
        # 1. 근로자 및 건강진단 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        exam_data = {
            "worker_id": worker_id,
            "exam_type": "general",
            "scheduled_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/health-exams/", json=exam_data)
        exam_id = response.json()["id"]
        
        # 2. 이상 소견이 있는 건강진단 결과 입력
        abnormal_results = {
            "exam_date": datetime.now().isoformat(),
            "overall_result": "요관찰자",
            "detailed_results": {
                "혈압": "150/95",  # 고혈압 1단계
                "혈당": "130mg/dL",  # 공복혈당장애 의심
                "총콜레스테롤": "250mg/dL",  # 높음
                "간기능": "정상"
            },
            "abnormal_findings": [
                {
                    "category": "심혈관계",
                    "finding": "고혈압 1단계",
                    "severity": "moderate",
                    "recommendation": "생활습관 개선 및 3개월 후 재검"
                },
                {
                    "category": "내분비계",
                    "finding": "공복혈당장애 의심",
                    "severity": "mild",
                    "recommendation": "당뇨병 정밀검사 필요"
                }
            ],
            "doctor_opinion": "고혈압 및 당뇨병 전단계로 추정, 생활습관 개선 및 정기 추적 관찰 필요",
            "follow_up_required": True,
            "work_restrictions": [
                "야간근무 제한",
                "과도한 신체적 노동 주의"
            ],
            "health_grade": "C1",
            "work_suitability": "조건부 적합"
        }
        
        response = test_client.put(f"/api/v1/health-exams/{exam_id}/results", json=abnormal_results)
        assert response.status_code == 200
        
        # 3. 근로자 건강 상태 업데이트 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}")
        worker = response.json()
        assert worker["health_status"] == "observation"
        
        # 4. 유소견자 관리대장 자동 등록 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}/abnormal-findings")
        assert response.status_code == 200
        
        findings = response.json()
        assert len(findings) >= 1
        assert findings[0]["health_exam_id"] == exam_id
        
        # 5. 자동 후속 관리 계획 생성
        follow_up_plan = {
            "management_category": "C1",
            "follow_up_exam_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "recommended_actions": [
                "규칙적인 운동 (주 3회 이상)",
                "저염식 식이요법",
                "금연 및 절주",
                "스트레스 관리"
            ],
            "work_environment_modifications": [
                "야간근무 배제",
                "무거운 물건 들기 제한"
            ],
            "medical_follow_up": [
                "심장내과 상담",
                "내분비내과 정밀검사"
            ]
        }
        
        response = test_client.post(f"/api/v1/abnormal-findings/{findings[0]['id']}/follow-up-plan", json=follow_up_plan)
        assert response.status_code == 201
        
        # 6. 관리자 알림 확인
        response = test_client.get(f"/api/v1/health-exams/{exam_id}/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) > 0
        assert any(alert["type"] == "abnormal_finding" for alert in alerts)
    
    async def test_special_health_exam_for_hazardous_workers(self, test_client):
        """유해물질 취급 근로자 특수건강진단 테스트"""
        
        # 1. 유해물질 취급 근로자 등록
        hazardous_worker_data = {
            "name": "박화학자",
            "gender": "male",
            "birth_date": "1985-12-10",
            "department": "화학공정팀",
            "position": "화학기술자",
            "work_type": "chemical_handling",
            "hazardous_substances": ["톨루엔", "크실렌", "메틸에틸케톤"],
            "exposure_start_date": "2020-01-01",
            "employment_type": "regular"
        }
        
        response = test_client.post("/api/v1/workers/", json=hazardous_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        # 2. 특수건강진단 예약
        special_exam_data = {
            "worker_id": worker_id,
            "exam_type": "special",
            "scheduled_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "medical_institution": "직업환경의학전문병원",
            "hazardous_substances": ["톨루엔", "크실렌"],
            "exposure_period_months": 48,
            "exam_items": [
                "문진",
                "임상검사",
                "흉부X선",
                "폐기능검사",
                "신경행동검사",
                "혈액검사",
                "소변검사"
            ],
            "biological_monitoring": [
                "요중 마뇨산",
                "요중 메틸마뇨산"
            ]
        }
        
        response = test_client.post("/api/v1/health-exams/", json=special_exam_data)
        assert response.status_code == 201
        special_exam_id = response.json()["id"]
        
        # 3. 특수건강진단 결과 입력
        special_results = {
            "exam_date": datetime.now().isoformat(),
            "overall_result": "정상",
            "detailed_results": {
                "폐기능검사": "정상",
                "신경행동검사": "정상",
                "간기능검사": "정상",
                "신기능검사": "정상"
            },
            "biological_monitoring_results": {
                "요중_마뇨산": "0.8g/g_creatinine (정상: <2.5)",
                "요중_메틸마뇨산": "0.3g/g_creatinine (정상: <1.5)"
            },
            "exposure_assessment": {
                "current_exposure_level": "허용기준 이하",
                "personal_protective_equipment": "적절히 사용",
                "work_environment_assessment": "양호"
            },
            "doctor_opinion": "현재 유해물질 노출로 인한 건강 영향 없음",
            "follow_up_required": False,
            "next_special_exam_date": (datetime.now() + timedelta(days=365)).isoformat(),
            "health_grade": "정상",
            "work_suitability": "적합"
        }
        
        response = test_client.put(f"/api/v1/health-exams/{special_exam_id}/results", json=special_results)
        assert response.status_code == 200
        
        # 4. 특수건강진단 결과 보고서 생성
        response = test_client.post(f"/api/v1/health-exams/{special_exam_id}/special-report")
        assert response.status_code == 200
        
        # 5. 근로자 노출 이력 업데이트 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}/exposure-history")
        assert response.status_code == 200
        
        exposure_history = response.json()
        assert len(exposure_history) > 0
        assert "톨루엔" in [exp["substance"] for exp in exposure_history]
    
    async def test_health_exam_batch_scheduling(self, test_client):
        """건강진단 일괄 예약 테스트"""
        
        # 1. 여러 근로자 등록
        workers = []
        for i in range(10):
            worker_data = {
                "name": f"근로자{i+1:02d}",
                "gender": "male" if i % 2 == 0 else "female",
                "birth_date": f"198{5+i%5}-0{1+i%9}-{10+i%20}",
                "department": "생산팀" if i < 5 else "관리팀",
                "position": "작업자",
                "employment_type": "regular"
            }
            
            response = test_client.post("/api/v1/workers/", json=worker_data)
            assert response.status_code == 201
            workers.append(response.json())
        
        # 2. 일괄 건강진단 예약
        batch_schedule_data = {
            "worker_ids": [worker["id"] for worker in workers[:5]],  # 첫 5명
            "exam_type": "general",
            "scheduled_date_start": (datetime.now() + timedelta(days=7)).isoformat(),
            "scheduled_date_end": (datetime.now() + timedelta(days=14)).isoformat(),
            "medical_institution": "종합검진센터",
            "time_slots": [
                {"time": "09:00", "capacity": 2},
                {"time": "10:00", "capacity": 2},
                {"time": "11:00", "capacity": 1}
            ],
            "exam_items": ["일반검진", "흉부X선", "혈액검사"],
            "auto_assign_time_slots": True
        }
        
        response = test_client.post("/api/v1/health-exams/batch-schedule", json=batch_schedule_data)
        assert response.status_code == 201
        
        batch_result = response.json()
        assert len(batch_result["scheduled_exams"]) == 5
        assert batch_result["failed_schedules"] == 0
        
        # 3. 예약 결과 확인
        for scheduled_exam in batch_result["scheduled_exams"]:
            exam_id = scheduled_exam["exam_id"]
            
            response = test_client.get(f"/api/v1/health-exams/{exam_id}")
            assert response.status_code == 200
            
            exam = response.json()
            assert exam["status"] == "scheduled"
            assert exam["medical_institution"] == "종합검진센터"
        
        # 4. 일괄 알림 발송
        notification_data = {
            "exam_ids": [exam["exam_id"] for exam in batch_result["scheduled_exams"]],
            "notification_type": "sms_and_email",
            "message_template": "건강진단이 예약되었습니다. 일시: {{scheduled_date}}, 장소: {{medical_institution}}"
        }
        
        response = test_client.post("/api/v1/health-exams/batch-notify", json=notification_data)
        assert response.status_code == 200
        
        notification_result = response.json()
        assert notification_result["sent_count"] == 5
    
    async def test_health_exam_statistical_analysis(self, test_client):
        """건강진단 통계 분석 테스트"""
        
        # 1. 다양한 건강진단 결과 데이터 생성 (시뮬레이션)
        test_scenarios = [
            {"health_grade": "A", "overall_result": "정상", "count": 5},
            {"health_grade": "B", "overall_result": "경계", "count": 3},
            {"health_grade": "C1", "overall_result": "요관찰자", "count": 2},
            {"health_grade": "C2", "overall_result": "유소견자", "count": 1}
        ]
        
        created_exams = []
        for scenario in test_scenarios:
            for i in range(scenario["count"]):
                # 근로자 생성
                worker_data = {
                    "name": f"{scenario['health_grade']}등급근로자{i+1}",
                    "employment_type": "regular"
                }
                
                response = test_client.post("/api/v1/workers/", json=worker_data)
                worker_id = response.json()["id"]
                
                # 건강진단 생성
                exam_data = {
                    "worker_id": worker_id,
                    "exam_type": "general",
                    "exam_date": (datetime.now() - timedelta(days=i*30)).isoformat(),
                    "overall_result": scenario["overall_result"],
                    "health_grade": scenario["health_grade"],
                    "status": "completed"
                }
                
                response = test_client.post("/api/v1/health-exams/", json=exam_data)
                created_exams.append(response.json())
        
        # 2. 건강진단 통계 조회
        response = test_client.get("/api/v1/health-exams/statistics")
        assert response.status_code == 200
        
        statistics = response.json()
        assert "total_exams" in statistics
        assert "by_health_grade" in statistics
        assert "abnormal_findings_rate" in statistics
        
        # 3. 월별 트렌드 분석
        response = test_client.get("/api/v1/health-exams/trends?period=monthly&months=6")
        assert response.status_code == 200
        
        trends = response.json()
        assert "monthly_data" in trends
        assert "health_grade_trends" in trends
        
        # 4. 부서별 건강 상태 분석
        response = test_client.get("/api/v1/health-exams/analysis/by-department")
        assert response.status_code == 200
        
        dept_analysis = response.json()
        assert isinstance(dept_analysis, list)
        
        # 5. 이상 소견 패턴 분석
        response = test_client.get("/api/v1/health-exams/analysis/abnormal-patterns")
        assert response.status_code == 200
        
        pattern_analysis = response.json()
        assert "common_findings" in pattern_analysis
        assert "risk_factors" in pattern_analysis
    
    async def test_health_exam_compliance_monitoring(self, test_client):
        """건강진단 법적 준수 모니터링 테스트"""
        
        # 1. 건강진단 기한 만료 임박 근로자 확인
        response = test_client.get("/api/v1/health-exams/compliance/overdue?days_ahead=30")
        assert response.status_code == 200
        
        overdue_list = response.json()
        
        # 2. 부서별 건강진단 수검률 확인
        response = test_client.get("/api/v1/health-exams/compliance/completion-rate")
        assert response.status_code == 200
        
        completion_rates = response.json()
        assert "overall_rate" in completion_rates
        assert "by_department" in completion_rates
        
        # 3. 특수건강진단 대상자 관리 현황
        response = test_client.get("/api/v1/health-exams/compliance/special-exam-targets")
        assert response.status_code == 200
        
        special_targets = response.json()
        assert "total_targets" in special_targets
        assert "by_substance" in special_targets
        
        # 4. 법정 보고서 생성
        report_data = {
            "report_type": "quarterly_health_exam",
            "quarter": 2,
            "year": 2024,
            "include_statistics": True,
            "include_abnormal_findings": True
        }
        
        response = test_client.post("/api/v1/health-exams/compliance/report", json=report_data)
        assert response.status_code == 200
        
        compliance_report = response.json()
        assert "exam_statistics" in compliance_report
        assert "compliance_status" in compliance_report
        assert "recommendations" in compliance_report


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 건강진단 워크플로우 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 건강진단 워크플로우 통합 테스트 실패")
        sys.exit(1)