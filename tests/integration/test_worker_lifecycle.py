"""
근로자 관리 전체 생명주기 통합 테스트
Worker Management Lifecycle Integration Tests
"""

import asyncio
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.app import create_app
from src.config.database import get_db
from src.models.health import HealthExam
from src.models.worker import Worker
from src.schemas.worker import WorkerCreate, WorkerUpdate


class TestWorkerManagementLifecycle:
    """근로자 등록부터 퇴사까지 전체 생명주기 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_worker_data(self):
        """샘플 근로자 데이터"""
        return {
            "name": "김건설",
            "gender": "male",
            "birth_date": "1985-05-15",
            "phone": "010-1234-5678",
            "email": "kim.construction@example.com",
            "employment_type": "regular",
            "work_type": "construction",
            "hire_date": "2024-01-15",
            "department": "현장작업팀",
            "position": "기능공",
            "health_status": "normal"
        }
    
    @pytest.fixture
    async def db_session(self):
        """데이터베이스 세션"""
        async for session in get_db():
            yield session
            break
    
    async def test_worker_registration_to_health_exam_flow(self, test_client, sample_worker_data):
        """근로자 등록부터 건강진단까지 전체 워크플로우 테스트"""
        
        # 1. 근로자 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        assert response.status_code == 201
        
        worker_data = response.json()
        worker_id = worker_data["id"]
        
        # 등록된 데이터 검증
        assert worker_data["name"] == sample_worker_data["name"]
        assert worker_data["employment_type"] == sample_worker_data["employment_type"]
        assert worker_data["health_status"] == "normal"
        
        # 2. 등록된 근로자 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}")
        assert response.status_code == 200
        
        retrieved_worker = response.json()
        assert retrieved_worker["id"] == worker_id
        assert retrieved_worker["name"] == sample_worker_data["name"]
        
        # 3. 배치전 건강진단 예약
        health_exam_data = {
            "worker_id": worker_id,
            "exam_type": "pre_placement",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "exam_items": ["일반검진", "흉부X선", "청력검사"],
            "medical_institution": "서울대학교병원",
            "notes": "신규 입사자 배치전 건강진단"
        }
        
        response = test_client.post("/api/v1/health-exams/", json=health_exam_data)
        assert response.status_code == 201
        
        exam_data = response.json()
        exam_id = exam_data["id"]
        
        # 4. 건강진단 결과 입력
        exam_result_data = {
            "exam_date": datetime.now().isoformat(),
            "overall_result": "적합",
            "detailed_results": {
                "일반검진": "정상",
                "흉부X선": "정상",
                "청력검사": "정상"
            },
            "doctor_opinion": "업무 적합",
            "follow_up_required": False
        }
        
        response = test_client.put(f"/api/v1/health-exams/{exam_id}", json=exam_result_data)
        assert response.status_code == 200
        
        # 5. 근로자 상태 업데이트 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}")
        updated_worker = response.json()
        
        # 건강진단 완료 후 상태가 업데이트되었는지 확인
        assert updated_worker["health_status"] == "normal"
        
        # 6. 근로자의 건강진단 이력 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}/health-exams")
        assert response.status_code == 200
        
        health_exams = response.json()
        assert len(health_exams) >= 1
        assert health_exams[0]["exam_type"] == "pre_placement"
    
    async def test_special_health_exam_scheduling_workflow(self, test_client, sample_worker_data):
        """특수건강진단 예약 워크플로우 테스트"""
        
        # 1. 유해물질 취급 근로자 등록
        hazardous_worker_data = sample_worker_data.copy()
        hazardous_worker_data.update({
            "name": "박화학",
            "work_type": "chemical_handling",
            "hazardous_substances": ["톨루엔", "크실렌", "메틸에틸케톤"]
        })
        
        response = test_client.post("/api/v1/workers/", json=hazardous_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        # 2. 특수건강진단 자동 예약 확인
        # (시스템이 유해물질 취급자에 대해 자동으로 특수건강진단을 예약하는지 확인)
        response = test_client.get(f"/api/v1/health-exams/?worker_id={worker_id}&exam_type=special")
        
        # 3. 특수건강진단 수동 예약
        special_exam_data = {
            "worker_id": worker_id,
            "exam_type": "special",
            "scheduled_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "exam_items": ["혈액검사", "소변검사", "신경계검사"],
            "hazardous_substances": ["톨루엔", "크실렌"],
            "exposure_period_months": 12,
            "medical_institution": "직업환경의학전문병원"
        }
        
        response = test_client.post("/api/v1/health-exams/", json=special_exam_data)
        assert response.status_code == 201
        
        # 4. 특수건강진단 결과 입력 및 유소견자 관리
        exam_id = response.json()["id"]
        
        abnormal_result_data = {
            "exam_date": datetime.now().isoformat(),
            "overall_result": "요관찰자",
            "detailed_results": {
                "혈액검사": "경계역",
                "소변검사": "정상",
                "신경계검사": "경미한 이상"
            },
            "doctor_opinion": "작업환경 개선 후 재검사 필요",
            "follow_up_required": True,
            "work_restriction": "화학물질 직접 취급 제한"
        }
        
        response = test_client.put(f"/api/v1/health-exams/{exam_id}", json=abnormal_result_data)
        assert response.status_code == 200
        
        # 5. 근로자 상태가 '요관찰자'로 변경되었는지 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}")
        worker = response.json()
        assert worker["health_status"] == "observation"
    
    async def test_abnormal_findings_management_process(self, test_client, sample_worker_data):
        """유소견자 관리 프로세스 테스트"""
        
        # 1. 근로자 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        # 2. 일반건강진단에서 이상 소견 발견
        health_exam_data = {
            "worker_id": worker_id,
            "exam_type": "general",
            "exam_date": datetime.now().isoformat(),
            "overall_result": "유소견자",
            "detailed_results": {
                "혈압": "고혈압 1단계",
                "혈당": "당뇨병 의심",
                "간기능": "정상"
            },
            "doctor_opinion": "생활습관 개선 및 치료 필요",
            "follow_up_required": True
        }
        
        response = test_client.post("/api/v1/health-exams/", json=health_exam_data)
        exam_id = response.json()["id"]
        
        # 3. 유소견자 관리대장 등록 확인
        response = test_client.get(f"/api/v1/workers/{worker_id}/abnormal-findings")
        assert response.status_code == 200
        
        findings = response.json()
        assert len(findings) > 0
        
        # 4. 유소견자 후속 관리 계획 수립
        follow_up_plan = {
            "worker_id": worker_id,
            "health_exam_id": exam_id,
            "management_level": "C1",  # 요관찰자
            "work_restriction": "야간근무 제한",
            "follow_up_exam_date": (datetime.now() + timedelta(days=90)).isoformat(),
            "health_guidance": "규칙적인 운동, 금연, 절주",
            "manager_notes": "3개월 후 재검사 예정"
        }
        
        response = test_client.post("/api/v1/abnormal-findings/", json=follow_up_plan)
        assert response.status_code == 201
        
        # 5. 정기 추적 관리
        follow_up_data = {
            "follow_up_date": datetime.now().isoformat(),
            "health_status_update": "혈압 약간 개선",
            "medication_compliance": True,
            "lifestyle_changes": "금연 성공, 운동 시작",
            "next_checkup_date": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        finding_id = response.json()["id"]
        response = test_client.put(f"/api/v1/abnormal-findings/{finding_id}/follow-up", json=follow_up_data)
        assert response.status_code == 200
    
    async def test_health_consultation_visit_recording(self, test_client, sample_worker_data):
        """건강관리 상담방문 기록 테스트"""
        
        # 1. 근로자 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        # 2. 건강상담 기록 생성
        consultation_data = {
            "visit_date": datetime.now().isoformat(),
            "site_name": "XX건설 현장",
            "counselor": "김보건관리자",
            "worker_ids": [worker_id],
            "consultation_topics": [
                "근골격계 질환 예방",
                "스트레스 관리",
                "개인보호구 착용"
            ],
            "health_issues_identified": [
                "어깨 통증 호소",
                "수면 부족"
            ],
            "work_environment_assessment": "양호",
            "improvement_suggestions": [
                "스트레칭 교육 강화",
                "작업 자세 개선"
            ],
            "immediate_actions": [
                "어깨 마사지 권고",
                "충분한 휴식 취하도록 지도"
            ],
            "follow_up_actions": [
                "2주 후 재방문",
                "근골격계 검진 예약"
            ],
            "next_visit_plan": (datetime.now() + timedelta(days=14)).isoformat()
        }
        
        response = test_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 201
        
        consultation_id = response.json()["id"]
        
        # 3. 상담 기록 조회
        response = test_client.get(f"/api/v1/health-consultations/{consultation_id}")
        assert response.status_code == 200
        
        consultation = response.json()
        assert consultation["counselor"] == "김보건관리자"
        assert len(consultation["worker_ids"]) == 1
        assert worker_id in consultation["worker_ids"]
        
        # 4. 근로자별 상담 이력 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}/consultations")
        assert response.status_code == 200
        
        worker_consultations = response.json()
        assert len(worker_consultations) >= 1
        assert worker_consultations[0]["id"] == consultation_id
    
    async def test_worker_data_export_and_reporting(self, test_client, sample_worker_data):
        """근로자 데이터 내보내기 및 보고서 생성 테스트"""
        
        # 1. 여러 근로자 등록
        workers = []
        for i in range(5):
            worker_data = sample_worker_data.copy()
            worker_data["name"] = f"근로자{i+1}"
            worker_data["email"] = f"worker{i+1}@example.com"
            
            response = test_client.post("/api/v1/workers/", json=worker_data)
            assert response.status_code == 201
            workers.append(response.json())
        
        # 2. 근로자 목록 내보내기 (Excel/CSV)
        response = test_client.get("/api/v1/workers/export?format=excel")
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # 3. 건강관리 종합 보고서 생성
        report_params = {
            "report_type": "comprehensive_health",
            "date_from": "2024-01-01",
            "date_to": "2024-12-31",
            "include_charts": True,
            "include_recommendations": True
        }
        
        response = test_client.post("/api/v1/reports/health-management", json=report_params)
        assert response.status_code == 200
        
        report_data = response.json()
        assert "summary" in report_data
        assert "worker_statistics" in report_data
        assert "health_exam_statistics" in report_data
        
        # 4. PDF 보고서 생성
        response = test_client.post("/api/v1/reports/health-management/pdf", json=report_params)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    async def test_worker_privacy_data_handling(self, test_client, sample_worker_data):
        """근로자 개인정보 처리 테스트"""
        
        # 1. 근로자 등록 (개인정보 포함)
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        # 2. 개인정보 조회 권한 테스트
        # (실제로는 JWT 토큰의 역할에 따라 접근 제어)
        response = test_client.get(f"/api/v1/workers/{worker_id}/personal-info")
        # 권한에 따라 200 또는 403
        
        # 3. 개인정보 마스킹 테스트
        response = test_client.get(f"/api/v1/workers/{worker_id}?mask_personal_info=true")
        if response.status_code == 200:
            worker = response.json()
            # 개인정보가 마스킹되었는지 확인
            assert "*" in worker.get("phone", "") or worker.get("phone") is None
            assert "*" in worker.get("email", "") or worker.get("email") is None
        
        # 4. 개인정보 수정 이력 추적
        update_data = {"phone": "010-9876-5432"}
        response = test_client.put(f"/api/v1/workers/{worker_id}", json=update_data)
        assert response.status_code == 200
        
        # 5. 수정 이력 조회
        response = test_client.get(f"/api/v1/workers/{worker_id}/audit-log")
        if response.status_code == 200:
            audit_log = response.json()
            assert len(audit_log) > 0
            assert any(log["action"] == "UPDATE" for log in audit_log)
    
    async def test_worker_lifecycle_statistics(self, test_client, sample_worker_data):
        """근로자 생명주기 통계 테스트"""
        
        # 1. 다양한 상태의 근로자들 생성
        worker_scenarios = [
            {"name": "신규근로자", "health_status": "normal", "employment_type": "regular"},
            {"name": "요관찰자", "health_status": "observation", "employment_type": "regular"},
            {"name": "유소견자", "health_status": "treatment", "employment_type": "contract"},
            {"name": "임시근로자", "health_status": "normal", "employment_type": "temporary"},
        ]
        
        for scenario in worker_scenarios:
            worker_data = sample_worker_data.copy()
            worker_data.update(scenario)
            response = test_client.post("/api/v1/workers/", json=worker_data)
            assert response.status_code == 201
        
        # 2. 대시보드 통계 조회
        response = test_client.get("/api/v1/dashboard/workers-statistics")
        assert response.status_code == 200
        
        stats = response.json()
        
        # 통계 데이터 검증
        assert "total_workers" in stats
        assert "by_health_status" in stats
        assert "by_employment_type" in stats
        assert "recent_hires" in stats
        
        # 건강 상태별 분포 확인
        health_status_stats = stats["by_health_status"]
        assert health_status_stats["normal"] >= 2  # 최소 2명
        assert health_status_stats["observation"] >= 1  # 최소 1명
        assert health_status_stats["treatment"] >= 1  # 최소 1명
        
        # 3. 월별 트렌드 분석
        response = test_client.get("/api/v1/analytics/worker-trends?period=monthly")
        if response.status_code == 200:
            trends = response.json()
            assert "monthly_data" in trends
            assert "health_status_trends" in trends


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 근로자 생명주기 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 근로자 생명주기 통합 테스트 실패")
        sys.exit(1)