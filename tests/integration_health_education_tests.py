"""
건강교육 시스템 통합 테스트
Health education system integration tests
"""

import asyncio
from datetime import datetime, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health_education import (
    EducationType, EducationMethod, EducationStatus
)
from tests.builders.health_education_builder import (
    HealthEducationBuilder, AttendanceBuilder, EducationCompleteBuilder
)
from tests.builders.worker_builder import WorkerBuilder


class TestHealthEducationIntegration:
    """건강교육 시스템 통합 테스트"""

    @pytest.mark.asyncio
    async def test_health_education_creation_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """보건교육 생성 워크플로우 테스트"""
        # 1. 교육 생성
        education_data = {
            "education_date": "2024-06-15T09:00:00",
            "education_type": "신규채용교육",
            "education_title": "신규근로자 안전보건교육",
            "education_content": "산업안전보건법 기초, 개인보호구 사용법",
            "education_method": "집체교육",
            "education_hours": 8.0,
            "instructor_name": "김안전",
            "instructor_qualification": "산업안전기사",
            "education_location": "본사 교육실",
            "required_by_law": "Y",
            "legal_requirement_hours": 8.0
        }

        response = await client.post(
            "/api/v1/health-educations/",
            json=education_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        education = response.json()
        education_id = education["id"]

        # 2. 교육 상세 조회
        response = await client.get(
            f"/api/v1/health-educations/{education_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["education_title"] == education_data["education_title"]
        assert response.json()["total_attendees"] == 0
        assert response.json()["completed_count"] == 0

        # 3. 교육 수정
        update_data = {
            "education_content": "산업안전보건법, 개인보호구 사용법, 응급처치",
            "notes": "실습 위주 교육으로 진행"
        }

        response = await client.put(
            f"/api/v1/health-educations/{education_id}",
            json=update_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "실습 위주" in response.json()["notes"]

        # 4. 교육 목록 조회
        response = await client.get(
            "/api/v1/health-educations/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_education_attendance_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 참석자 관리 테스트"""
        # 교육 및 근로자 생성
        education = await HealthEducationBuilder().with_korean_data().build(db_session)
        
        workers = []
        for i in range(3):
            worker = await (
                WorkerBuilder()
                .with_name(f"근로자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 1. 참석자 등록
        attendance_data = [
            {
                "education_id": education.id,
                "worker_id": workers[0].id,
                "status": "완료",
                "attendance_hours": 8.0,
                "test_score": 90.0
            },
            {
                "education_id": education.id,
                "worker_id": workers[1].id,
                "status": "진행중",
                "attendance_hours": 4.0
            },
            {
                "education_id": education.id,
                "worker_id": workers[2].id,
                "status": "불참"
            }
        ]

        response = await client.post(
            f"/api/v1/health-educations/{education.id}/attendance",
            json=attendance_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert "3명의 참석자" in response.json()["message"]

        # 2. 교육 상세 조회 (참석자 포함)
        response = await client.get(
            f"/api/v1/health-educations/{education.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        education_detail = response.json()
        assert education_detail["total_attendees"] == 3
        assert education_detail["completed_count"] == 1
        assert len(education_detail["attendances"]) == 3

        # 3. 참석 정보 수정
        attendance_id = education_detail["attendances"][1]["id"]  # 진행중 -> 완료
        update_data = {
            "status": "완료",
            "attendance_hours": 8.0,
            "test_score": 85.0,
            "certificate_number": "CERT-2024-001",
            "satisfaction_score": 4,
            "feedback_comments": "유익한 교육이었습니다"
        }

        response = await client.put(
            f"/api/v1/health-educations/attendance/{attendance_id}",
            json=update_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # 4. 수정 후 확인
        response = await client.get(
            f"/api/v1/health-educations/{education.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["completed_count"] == 2

    @pytest.mark.asyncio
    async def test_worker_education_history_tracking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """근로자 교육 이력 추적 테스트"""
        # 근로자 생성
        worker = await (
            WorkerBuilder()
            .with_name("김근로자")
            .with_korean_data()
            .build(db_session)
        )

        # 다양한 유형의 교육 이력 생성
        educations = []
        
        # 1. 신규채용교육 (완료)
        education1 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_new_employee_training()
                .with_past_session(90)
            )
            .with_multiple_attendees([worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )
        educations.append(education1)

        # 2. 정기교육 (완료)
        education2 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_quarterly_training()
                .with_past_session(30)
            )
            .with_multiple_attendees([worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )
        educations.append(education2)

        # 3. 특별안전보건교육 (불참)
        education3 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_special_hazard_training()
                .with_past_session(15)
            )
            .with_multiple_attendees([worker.id], [EducationStatus.ABSENT])
            .build(db_session)
        )
        educations.append(education3)

        # 근로자 교육 이력 조회
        response = await client.get(
            f"/api/v1/health-educations/worker/{worker.id}/history",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        history_data = response.json()
        assert history_data["worker_name"] == "김근로자"
        assert history_data["total_hours_completed"] == 14.0  # 8 + 6 (불참 제외)
        assert len(history_data["education_history"]) == 3
        
        # 교육 유형별 확인
        education_types = [item["type"] for item in history_data["education_history"]]
        assert "신규채용교육" in education_types
        assert "정기교육_분기" in education_types
        assert "특별안전보건교육" in education_types
        
        # 준수 상태 확인 (신규직원 기준)
        assert history_data["compliance_status"] == "준수"  # 14시간 >= 8시간

    @pytest.mark.asyncio
    async def test_education_statistics_and_reporting(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 통계 및 보고 기능 테스트"""
        # 테스트 데이터 생성
        workers = []
        for i in range(5):
            worker = await (
                WorkerBuilder()
                .with_name(f"근로자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 다양한 교육 생성
        educations = []

        # 1. 완료된 신규교육
        education1 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_new_employee_training()
                .with_past_session(30)
            )
            .with_multiple_attendees(
                [w.id for w in workers[:3]], 
                [EducationStatus.COMPLETED] * 3
            )
            .build(db_session)
        )
        educations.append(education1)

        # 2. 진행중인 정기교육
        education2 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_quarterly_training()
                .with_online_method()
                .with_past_session(7)
            )
            .with_multiple_attendees(
                [w.id for w in workers[:4]], 
                [EducationStatus.IN_PROGRESS] * 4
            )
            .build(db_session)
        )
        educations.append(education2)

        # 3. 예정된 특별교육
        education3 = await (
            HealthEducationBuilder()
            .with_special_hazard_training()
            .with_field_training()
            .with_upcoming_session(15)
            .build(db_session)
        )
        educations.append(education3)

        # 4. MSDS 교육 (혼합 결과)
        education4 = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_msds_training()
                .with_past_session(45)
            )
            .with_multiple_attendees(
                [w.id for w in workers], 
                [EducationStatus.COMPLETED, EducationStatus.COMPLETED, 
                 EducationStatus.ABSENT, EducationStatus.COMPLETED, 
                 EducationStatus.ABSENT]
            )
            .build(db_session)
        )
        educations.append(education4)

        # 통계 조회
        response = await client.get(
            "/api/v1/health-educations/statistics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        stats = response.json()
        assert stats["total_sessions"] >= 4
        assert stats["total_hours"] >= 24.0  # 8 + 6 + 4 + 2 + 기타
        assert stats["total_attendees"] >= 14  # 3 + 4 + 0 + 5 + 기타
        
        # 유형별 통계 확인
        assert "신규채용교육" in stats["by_type"]
        assert "정기교육_분기" in stats["by_type"]
        assert "특별안전보건교육" in stats["by_type"]
        assert "MSDS교육" in stats["by_type"]
        
        # 방법별 통계 확인
        assert "집체교육" in stats["by_method"]
        assert "온라인교육" in stats["by_method"]
        assert "현장교육" in stats["by_method"]
        
        # 완료율 확인 (MSDS: 3완료/5전체, 신규: 3완료/3전체 등)
        assert 0 <= stats["completion_rate"] <= 100
        
        # 예정된 교육 확인
        assert len(stats["upcoming_sessions"]) >= 1
        upcoming_titles = [session["title"] for session in stats["upcoming_sessions"]]
        assert any("특별안전보건교육" in title for title in upcoming_titles)

    @pytest.mark.asyncio
    async def test_education_filtering_and_search(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 필터링 및 검색 기능 테스트"""
        # 다양한 교육 데이터 생성
        educations = []
        
        # 신규교육 (집체)
        education1 = await (
            HealthEducationBuilder()
            .with_new_employee_training()
            .with_education_date(datetime(2024, 3, 15, 9, 0))
            .with_korean_data()
            .build(db_session)
        )
        educations.append(education1)

        # 정기교육 (온라인)
        education2 = await (
            HealthEducationBuilder()
            .with_quarterly_training()
            .with_online_method()
            .with_education_date(datetime(2024, 4, 10, 14, 0))
            .build(db_session)
        )
        educations.append(education2)

        # 관리자교육 (외부)
        education3 = await (
            HealthEducationBuilder()
            .with_manager_training()
            .with_education_method(EducationMethod.EXTERNAL)
            .with_education_date(datetime(2024, 5, 20, 10, 0))
            .build(db_session)
        )
        educations.append(education3)

        # 1. 교육 유형별 필터링
        response = await client.get(
            "/api/v1/health-educations/?education_type=신규채용교육",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert all(item["education_type"] == "신규채용교육" for item in result["items"])

        # 2. 교육 방법별 필터링
        response = await client.get(
            "/api/v1/health-educations/?education_method=온라인교육",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert all(item["education_method"] == "온라인교육" for item in result["items"])

        # 3. 날짜 범위 필터링
        start_date = "2024-04-01T00:00:00"
        end_date = "2024-04-30T23:59:59"
        response = await client.get(
            f"/api/v1/health-educations/?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        # 4월 교육만 조회되어야 함
        for item in result["items"]:
            education_date = datetime.fromisoformat(item["education_date"].replace('Z', '+00:00'))
            assert datetime(2024, 4, 1) <= education_date <= datetime(2024, 4, 30, 23, 59, 59)

        # 4. 복합 필터링
        response = await client.get(
            "/api/v1/health-educations/?education_type=관리감독자교육&education_method=외부교육",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        for item in result["items"]:
            assert item["education_type"] == "관리감독자교육"
            assert item["education_method"] == "외부교육"

        # 5. 페이지네이션 테스트
        response = await client.get(
            "/api/v1/health-educations/?page=1&size=2",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 2
        assert result["page"] == 1
        assert result["size"] == 2

    @pytest.mark.asyncio
    async def test_education_compliance_tracking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 법규 준수 추적 테스트"""
        # 근로자들 생성 (입사일 다름)
        new_worker = await (
            WorkerBuilder()
            .with_name("신입사원")
            .with_hire_date(datetime(2024, 5, 1))  # 올해 입사
            .with_korean_data()
            .build(db_session)
        )

        experienced_worker = await (
            WorkerBuilder()
            .with_name("기존직원")
            .with_hire_date(datetime(2022, 3, 15))  # 기존 직원
            .with_korean_data()
            .build(db_session)
        )

        # 1. 신규직원 교육 (8시간 필요 - 준수)
        new_employee_education = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_new_employee_training()
                .with_past_session(30)
            )
            .with_multiple_attendees([new_worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )

        # 2. 기존직원 교육 (12시간 필요 - 6시간만 이수)
        quarterly_education = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_quarterly_training()  # 6시간
                .with_past_session(45)
            )
            .with_multiple_attendees([experienced_worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )

        # 신규직원 이력 조회 - 준수 상태여야 함
        response = await client.get(
            f"/api/v1/health-educations/worker/{new_worker.id}/history",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        new_worker_history = response.json()
        assert new_worker_history["total_hours_completed"] == 8.0
        assert new_worker_history["required_hours_this_year"] == 8  # 신규직원
        assert new_worker_history["compliance_status"] == "준수"

        # 기존직원 이력 조회 - 미달 상태여야 함
        response = await client.get(
            f"/api/v1/health-educations/worker/{experienced_worker.id}/history",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        experienced_worker_history = response.json()
        assert experienced_worker_history["total_hours_completed"] == 6.0
        assert experienced_worker_history["required_hours_this_year"] == 12  # 기존직원
        assert experienced_worker_history["compliance_status"] == "미달"

        # 3. 기존직원 추가 교육 이수
        additional_education = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_special_hazard_training()  # 4시간
                .with_past_session(20)
            )
            .with_multiple_attendees([experienced_worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )

        msds_education = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_msds_training()  # 2시간
                .with_past_session(10)
            )
            .with_multiple_attendees([experienced_worker.id], [EducationStatus.COMPLETED])
            .build(db_session)
        )

        # 재조회 - 이제 준수 상태여야 함 (6 + 4 + 2 = 12시간)
        response = await client.get(
            f"/api/v1/health-educations/worker/{experienced_worker.id}/history",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        updated_history = response.json()
        assert updated_history["total_hours_completed"] == 12.0
        assert updated_history["compliance_status"] == "준수"

    @pytest.mark.asyncio
    async def test_education_material_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str],
        temp_file_path: str
    ):
        """교육 자료 관리 테스트"""
        # 교육 생성
        education = await (
            HealthEducationBuilder()
            .with_korean_data()
            .build(db_session)
        )

        # 교육 자료 업로드
        with open(temp_file_path, "rb") as f:
            response = await client.post(
                f"/api/v1/health-educations/{education.id}/materials",
                files={"file": ("test_material.pdf", f, "application/pdf")},
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        upload_result = response.json()
        assert "업로드되었습니다" in upload_result["message"]
        assert "file_path" in upload_result

        # 교육 정보 다시 조회하여 자료 경로 확인
        response = await client.get(
            f"/api/v1/health-educations/{education.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        updated_education = response.json()
        assert updated_education["education_material_path"] is not None

    @pytest.mark.asyncio
    async def test_education_performance_analytics(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 성과 분석 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(10):
            worker = await (
                WorkerBuilder()
                .with_name(f"분석대상자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 다양한 성과를 보이는 교육 생성
        education = await (
            EducationCompleteBuilder()
            .with_education_builder(
                HealthEducationBuilder()
                .with_korean_data()
                .with_new_employee_training()
            )
            .with_mixed_performance_scenario([w.id for w in workers])
            .build(db_session)
        )

        # 교육 상세 조회로 성과 분석
        response = await client.get(
            f"/api/v1/health-educations/{education.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        education_detail = response.json()
        attendances = education_detail["attendances"]
        
        # 성과 분석
        test_scores = [att["test_score"] for att in attendances if att["test_score"] is not None]
        satisfaction_scores = [att["satisfaction_score"] for att in attendances if att["satisfaction_score"] is not None]
        
        # 점수 분포 확인
        assert len(test_scores) > 0
        assert min(test_scores) >= 60  # 최소 점수
        assert max(test_scores) <= 100  # 최대 점수
        
        # 만족도 분포 확인
        assert len(satisfaction_scores) > 0
        assert all(1 <= score <= 5 for score in satisfaction_scores)
        
        # 완료율 계산
        completed_count = len([att for att in attendances if att["status"] == "완료"])
        completion_rate = (completed_count / len(attendances)) * 100
        assert 0 <= completion_rate <= 100

    @pytest.mark.asyncio
    async def test_education_error_handling(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """교육 관리 오류 처리 테스트"""
        # 1. 존재하지 않는 교육 조회
        response = await client.get(
            "/api/v1/health-educations/99999",
            headers=authenticated_headers
        )
        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.json()["detail"]

        # 2. 잘못된 데이터로 교육 생성
        invalid_data = {
            "education_date": "invalid-date",
            "education_type": "잘못된유형",
            "education_title": "",  # 필수 필드 비움
            "education_method": "잘못된방법",
            "education_hours": -1  # 음수 시간
        }

        response = await client.post(
            "/api/v1/health-educations/",
            json=invalid_data,
            headers=authenticated_headers
        )
        assert response.status_code == 422

        # 3. 존재하지 않는 근로자로 참석 등록
        education = await HealthEducationBuilder().build(db_session)
        
        invalid_attendance = [{
            "education_id": education.id,
            "worker_id": 99999,  # 존재하지 않는 근로자
            "status": "완료"
        }]

        response = await client.post(
            f"/api/v1/health-educations/{education.id}/attendance",
            json=invalid_attendance,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        # 존재하지 않는 근로자는 자동으로 스킵됨
        assert response.json()["added_count"] == 0

        # 4. 존재하지 않는 참석 정보 수정
        response = await client.put(
            "/api/v1/health-educations/attendance/99999",
            json={"status": "완료"},
            headers=authenticated_headers
        )
        assert response.status_code == 404

        # 5. 존재하지 않는 근로자의 교육 이력 조회
        response = await client.get(
            "/api/v1/health-educations/worker/99999/history",
            headers=authenticated_headers
        )
        assert response.status_code == 404

    @pytest.mark.asyncio
    async def test_concurrent_education_operations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """동시 교육 운영 처리 테스트"""
        # 교육 및 근로자 준비
        education = await HealthEducationBuilder().build(db_session)
        
        workers = []
        for i in range(5):
            worker = await WorkerBuilder().with_name(f"동시참석자{i+1}").build(db_session)
            workers.append(worker)

        # 동시에 여러 참석자 등록 요청
        attendance_data = [
            {
                "education_id": education.id,
                "worker_id": worker.id,
                "status": "완료",
                "attendance_hours": 8.0,
                "test_score": 80.0 + i * 2  # 점수 차등
            }
            for i, worker in enumerate(workers)
        ]

        # 동시 요청 시뮬레이션
        tasks = []
        for i in range(3):  # 동일한 요청을 3번 동시에
            task = client.post(
                f"/api/v1/health-educations/{education.id}/attendance",
                json=attendance_data,
                headers=authenticated_headers
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 첫 번째 요청은 성공, 나머지는 중복으로 인해 0명 추가
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert success_count > 0

        # 실제 등록된 참석자 수 확인
        response = await client.get(
            f"/api/v1/health-educations/{education.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        # 중복 등록 방지로 실제로는 5명만 등록됨
        assert response.json()["total_attendees"] == 5