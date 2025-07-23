"""
건강진단 워크플로우 통합 테스트
Integration tests for health examination workflow
"""

import json
import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health import HealthExam, VitalSigns, LabResult, ExamType, ExamResult, PostManagement
from src.models.worker import Worker
from tests.builders.health_builder import HealthExamBuilder, VitalSignsBuilder, LabResultBuilder
from tests.builders.worker_builder import WorkerBuilder


class TestHealthExaminationWorkflow:
    """건강진단 워크플로우 통합 테스트"""

    @pytest_asyncio.fixture
    async def test_worker(self, db_session: AsyncSession) -> Worker:
        """테스트용 근로자 생성"""
        worker = await WorkerBuilder().with_korean_data().build(db_session)
        return worker

    @pytest_asyncio.fixture
    async def sample_health_exams(
        self, db_session: AsyncSession, test_worker: Worker
    ) -> List[HealthExam]:
        """테스트용 건강진단 기록들 생성"""
        exams = []
        
        # 일반건강진단 (1년 전)
        general_exam = (
            await HealthExamBuilder()
            .with_worker_id(test_worker.id)
            .with_exam_type(ExamType.GENERAL)
            .with_exam_date(datetime.now().date() - timedelta(days=365))
            .with_exam_result(ExamResult.NORMAL_A)
            .with_exam_institution("서울건강검진센터")
            .with_exam_doctor("김의사")
            .build(db_session)
        )
        exams.append(general_exam)

        # 특수건강진단 (6개월 전)
        special_exam = (
            await HealthExamBuilder()
            .with_worker_id(test_worker.id)
            .with_exam_type(ExamType.SPECIAL)
            .with_exam_date(datetime.now().date() - timedelta(days=180))
            .with_exam_result(ExamResult.NORMAL_B)
            .with_harmful_factors(["소음", "분진"])
            .with_post_management(PostManagement.OBSERVATION)
            .build(db_session)
        )
        exams.append(special_exam)

        # 배치전건강진단 (최근)
        pre_exam = (
            await HealthExamBuilder()
            .with_worker_id(test_worker.id)
            .with_exam_type(ExamType.PRE_EMPLOYMENT)
            .with_exam_date(datetime.now().date() - timedelta(days=30))
            .with_exam_result(ExamResult.NORMAL)
            .build(db_session)
        )
        exams.append(pre_exam)

        return exams

    async def test_create_health_examination_complete_workflow(
        self, client: AsyncClient, test_worker: Worker, authenticated_headers: Dict[str, str]
    ):
        """완전한 건강진단 생성 워크플로우 테스트"""
        # 건강진단 기본 정보
        exam_data = {
            "worker_id": test_worker.id,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "general",
            "exam_result": "normal_a",
            "exam_agency": "서울종합건강검진센터",
            "doctor_name": "김건강",
            "overall_opinion": "건강상태 양호",
            "disease_diagnosis": "특이소견 없음",
            "work_fitness": "업무적합",
            "restrictions": "제한사항 없음",
            "followup_required": "N",
            "notes": "정기검진 완료",
            "vital_signs": {
                "height": 175.5,
                "weight": 70.2,
                "bmi": 22.8,
                "blood_pressure_systolic": 120,
                "blood_pressure_diastolic": 80,
                "heart_rate": 72,
                "vision_left": 1.0,
                "vision_right": 1.0,
                "waist_circumference": 85.0
            },
            "lab_results": [
                {
                    "test_name": "혈색소",
                    "test_value": "14.5",
                    "test_unit": "g/dL",
                    "reference_range": "12-16",
                    "result_status": "정상"
                },
                {
                    "test_name": "총콜레스테롤",
                    "test_value": "190",
                    "test_unit": "mg/dL",
                    "reference_range": "<200",
                    "result_status": "정상"
                },
                {
                    "test_name": "공복혈당",
                    "test_value": "95",
                    "test_unit": "mg/dL",
                    "reference_range": "70-100",
                    "result_status": "정상"
                }
            ]
        }

        # 건강진단 생성 요청
        response = await client.post(
            "/api/v1/health-exams/",
            json=exam_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        created_exam = response.json()

        # 생성된 검진 정보 검증
        assert created_exam["worker_id"] == test_worker.id
        assert created_exam["exam_type"] == "general"
        assert created_exam["exam_result"] == "normal_a"
        assert created_exam["exam_agency"] == "서울종합건강검진센터"
        assert created_exam["doctor_name"] == "김건강"
        assert created_exam["overall_opinion"] == "건강상태 양호"

        # 기초검사 결과 검증
        assert created_exam["vital_signs"] is not None
        vital_signs = created_exam["vital_signs"]
        assert vital_signs["height"] == 175.5
        assert vital_signs["weight"] == 70.2
        assert vital_signs["bmi"] == 22.8
        assert vital_signs["blood_pressure_systolic"] == 120

        # 임상검사 결과 검증
        assert len(created_exam["lab_results"]) == 3
        lab_results = created_exam["lab_results"]
        
        hemoglobin_result = next((r for r in lab_results if r["test_name"] == "혈색소"), None)
        assert hemoglobin_result is not None
        assert hemoglobin_result["test_value"] == "14.5"
        assert hemoglobin_result["result_status"] == "정상"

    async def test_health_exam_list_with_filters(
        self, 
        client: AsyncClient, 
        sample_health_exams: List[HealthExam],
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 목록 조회 및 필터링 테스트"""
        worker_id = sample_health_exams[0].worker_id

        # 전체 목록 조회
        response = await client.get(
            "/api/v1/health-exams/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

        # 근로자별 필터링
        response = await client.get(
            f"/api/v1/health-exams/?worker_id={worker_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 3
        for item in data["items"]:
            assert item["worker_id"] == worker_id

        # 검진 유형별 필터링
        response = await client.get(
            "/api/v1/health-exams/?exam_type=general",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["exam_type"] == "general"

        # 날짜 범위 필터링
        start_date = (datetime.now() - timedelta(days=200)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = await client.get(
            f"/api/v1/health-exams/?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 2  # 특수검진과 배치전검진

    async def test_health_exam_statistics(
        self, 
        client: AsyncClient, 
        sample_health_exams: List[HealthExam],
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 통계 조회 테스트"""
        response = await client.get(
            "/api/v1/health-exams/statistics",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        stats = response.json()

        # 검진 유형별 통계 확인
        assert "by_type" in stats
        type_stats = stats["by_type"]
        assert "general" in type_stats
        assert "special" in type_stats
        assert "pre_employment" in type_stats

        # 결과별 통계 확인
        assert "by_result" in stats
        result_stats = stats["by_result"]
        assert "normal" in result_stats or "normal_a" in result_stats

        # 연간 검진 수 확인
        assert "total_this_year" in stats
        assert isinstance(stats["total_this_year"], int)

        # 추적검사 필요 건수 확인
        assert "followup_required" in stats
        assert isinstance(stats["followup_required"], int)

    async def test_health_exam_due_soon_workflow(
        self, 
        client: AsyncClient, 
        sample_health_exams: List[HealthExam],
        authenticated_headers: Dict[str, str]
    ):
        """검진 예정자 조회 워크플로우 테스트"""
        # 30일 이내 검진 예정자 조회
        response = await client.get(
            "/api/v1/health-exams/due-soon?days=30",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        
        assert "total" in data
        assert "workers" in data
        assert isinstance(data["total"], int)
        assert isinstance(data["workers"], list)

        # 검진 예정자 정보 검증
        if data["workers"]:
            worker = data["workers"][0]
            assert "worker_id" in worker
            assert "worker_name" in worker
            assert "employee_number" in worker
            assert "latest_exam_date" in worker
            assert "next_exam_date" in worker
            assert "days_until_due" in worker

        # 더 긴 기간으로 조회 (1년 이내)
        response = await client.get(
            "/api/v1/health-exams/due-soon?days=365",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1  # 적어도 1명은 있어야 함 (1년 전 검진 기록)

    async def test_worker_latest_exam_retrieval(
        self, 
        client: AsyncClient, 
        sample_health_exams: List[HealthExam],
        authenticated_headers: Dict[str, str]
    ):
        """근로자 최신 건강진단 기록 조회 테스트"""
        worker_id = sample_health_exams[0].worker_id

        response = await client.get(
            f"/api/v1/health-exams/worker/{worker_id}/latest",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        latest_exam = response.json()

        # 최신 검진이 배치전검진이어야 함 (가장 최근 30일 전)
        assert latest_exam["exam_type"] == "pre_employment"
        assert latest_exam["worker_id"] == worker_id

        # 존재하지 않는 근로자 조회
        response = await client.get(
            "/api/v1/health-exams/worker/99999/latest",
            headers=authenticated_headers
        )

        assert response.status_code == 404

    async def test_health_exam_update_workflow(
        self, 
        client: AsyncClient, 
        sample_health_exams: List[HealthExam],
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 수정 워크플로우 테스트"""
        exam_id = sample_health_exams[0].id

        # 검진 결과 업데이트
        update_data = {
            "exam_result": "normal_b",
            "overall_opinion": "경미한 이상소견 있음",
            "work_fitness": "업무적합 (경과관찰 필요)",
            "followup_required": "Y",
            "followup_date": "2024-07-15T09:00:00",
            "notes": "콜레스테롤 수치 경계선, 3개월 후 재검 권장"
        }

        response = await client.put(
            f"/api/v1/health-exams/{exam_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        updated_exam = response.json()

        # 업데이트된 정보 검증
        assert updated_exam["exam_result"] == "normal_b"
        assert updated_exam["overall_opinion"] == "경미한 이상소견 있음"
        assert updated_exam["work_fitness"] == "업무적합 (경과관찰 필요)"
        assert updated_exam["followup_required"] == "Y"
        assert "2024-07-15" in updated_exam["followup_date"]

    async def test_health_exam_deletion_workflow(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_worker: Worker,
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 삭제 워크플로우 테스트"""
        # 삭제용 검진 기록 생성
        exam = (
            await HealthExamBuilder()
            .with_worker_id(test_worker.id)
            .with_exam_type(ExamType.TEMPORARY)
            .with_exam_date(datetime.now().date())
            .build(db_session)
        )

        # 검진 기록 삭제
        response = await client.delete(
            f"/api/v1/health-exams/{exam.id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "건강진단 기록이 삭제되었습니다"

        # 삭제 확인
        response = await client.get(
            f"/api/v1/health-exams/{exam.id}",
            headers=authenticated_headers
        )

        assert response.status_code == 404

    async def test_special_health_exam_with_harmful_factors(
        self, 
        client: AsyncClient, 
        test_worker: Worker,
        authenticated_headers: Dict[str, str]
    ):
        """유해인자가 포함된 특수건강진단 테스트"""
        exam_data = {
            "worker_id": test_worker.id,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "special",
            "exam_result": "occupational_c1",  # 직업성질환 의심
            "exam_agency": "산업보건연구원",
            "doctor_name": "박산업의학",
            "overall_opinion": "소음성 난청 의심소견",
            "disease_diagnosis": "소음성 난청 의심",
            "work_fitness": "작업제한 필요",
            "restrictions": "소음 90dB 이상 작업장 근무 제한",
            "followup_required": "Y",
            "followup_date": "2024-04-15T09:00:00",
            "notes": "3개월 후 청력 재검사 필요",
            "vital_signs": {
                "height": 170.0,
                "weight": 75.0,
                "hearing_left": "경도난청",
                "hearing_right": "정상"
            },
            "lab_results": [
                {
                    "test_name": "순음청력검사_좌측_4000Hz",
                    "test_value": "45",
                    "test_unit": "dB",
                    "reference_range": "<25",
                    "result_status": "이상"
                },
                {
                    "test_name": "순음청력검사_우측_4000Hz",
                    "test_value": "20",
                    "test_unit": "dB",
                    "reference_range": "<25",
                    "result_status": "정상"
                }
            ]
        }

        response = await client.post(
            "/api/v1/health-exams/",
            json=exam_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        special_exam = response.json()

        # 특수검진 특성 검증
        assert special_exam["exam_type"] == "special"
        assert special_exam["exam_result"] == "occupational_c1"
        assert "소음성 난청" in special_exam["disease_diagnosis"]
        assert special_exam["restrictions"] is not None
        assert special_exam["followup_required"] == "Y"

        # 청력 검사 결과 검증
        hearing_tests = [r for r in special_exam["lab_results"] if "청력검사" in r["test_name"]]
        assert len(hearing_tests) == 2
        
        left_hearing = next((r for r in hearing_tests if "좌측" in r["test_name"]), None)
        assert left_hearing["result_status"] == "이상"
        assert int(left_hearing["test_value"]) > 25

    async def test_health_exam_error_scenarios(
        self, 
        client: AsyncClient,
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 관련 오류 시나리오 테스트"""
        
        # 존재하지 않는 근로자로 검진 생성 시도
        invalid_exam_data = {
            "worker_id": 99999,  # 존재하지 않는 ID
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "general",
            "exam_agency": "테스트검진센터"
        }

        response = await client.post(
            "/api/v1/health-exams/",
            json=invalid_exam_data,
            headers=authenticated_headers
        )

        assert response.status_code == 404
        assert "근로자를 찾을 수 없습니다" in response.json()["detail"]

        # 존재하지 않는 검진 기록 조회
        response = await client.get(
            "/api/v1/health-exams/99999",
            headers=authenticated_headers
        )

        assert response.status_code == 404
        assert "건강진단 기록을 찾을 수 없습니다" in response.json()["detail"]

        # 잘못된 검진 유형으로 생성 시도
        invalid_type_data = {
            "worker_id": 1,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "invalid_type",  # 잘못된 검진 유형
            "exam_agency": "테스트검진센터"
        }

        response = await client.post(
            "/api/v1/health-exams/",
            json=invalid_type_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422  # Validation error

    async def test_health_exam_pagination(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_worker: Worker,
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 목록 페이지네이션 테스트"""
        # 추가 검진 기록 생성 (총 10개)
        for i in range(10):
            await HealthExamBuilder().with_worker_id(test_worker.id).build(db_session)

        # 첫 번째 페이지 (5개씩)
        response = await client.get(
            "/api/v1/health-exams/?page=1&size=5",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        page1_data = response.json()
        assert len(page1_data["items"]) == 5
        assert page1_data["page"] == 1
        assert page1_data["size"] == 5
        assert page1_data["total"] >= 10

        # 두 번째 페이지
        response = await client.get(
            "/api/v1/health-exams/?page=2&size=5",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        page2_data = response.json()
        assert len(page2_data["items"]) == 5
        assert page2_data["page"] == 2

        # 페이지별 데이터가 다른지 확인
        page1_ids = {item["id"] for item in page1_data["items"]}
        page2_ids = {item["id"] for item in page2_data["items"]}
        assert page1_ids.isdisjoint(page2_ids)  # 겹치지 않아야 함

    async def test_health_exam_korean_text_handling(
        self, 
        client: AsyncClient, 
        test_worker: Worker,
        authenticated_headers: Dict[str, str]
    ):
        """한글 텍스트 처리 테스트"""
        korean_exam_data = {
            "worker_id": test_worker.id,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "general",
            "exam_result": "normal_a",
            "exam_agency": "서울대학교병원 건강증진센터",
            "doctor_name": "김한글의사",
            "overall_opinion": "전반적인 건강상태가 양호하며, 특별한 이상소견은 관찰되지 않았습니다.",
            "disease_diagnosis": "특이 질환 없음. 정상 범위 내 소견.",
            "work_fitness": "현재 업무에 적합하며, 특별한 제한사항 없음",
            "restrictions": "고온 환경 작업 시 충분한 수분 섭취 권장",
            "notes": "정기적인 운동과 금연을 통한 건강관리 지속 필요. 다음 정기검진까지 건강한 생활습관 유지 바람.",
            "lab_results": [
                {
                    "test_name": "간기능검사 (AST/ALT)",
                    "test_value": "25/30",
                    "test_unit": "IU/L",
                    "reference_range": "AST<40, ALT<40",
                    "result_status": "정상",
                    "notes": "간기능 정상 범위 내"
                }
            ]
        }

        response = await client.post(
            "/api/v1/health-exams/",
            json=korean_exam_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        korean_exam = response.json()

        # 한글 텍스트 저장 및 조회 검증
        assert korean_exam["exam_agency"] == "서울대학교병원 건강증진센터"
        assert korean_exam["doctor_name"] == "김한글의사"
        assert "양호하며" in korean_exam["overall_opinion"]
        assert "특이 질환 없음" in korean_exam["disease_diagnosis"]
        assert "적합하며" in korean_exam["work_fitness"]
        assert "수분 섭취" in korean_exam["restrictions"]
        assert "생활습관" in korean_exam["notes"]

        # 한글 검사 결과 검증
        lab_result = korean_exam["lab_results"][0]
        assert lab_result["test_name"] == "간기능검사 (AST/ALT)"
        assert lab_result["result_status"] == "정상"
        assert "정상 범위" in lab_result["notes"]


class TestHealthExamComplexWorkflows:
    """복합 워크플로우 테스트"""

    async def test_health_exam_lifecycle_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 전체 생명주기 관리 테스트"""
        # 1. 근로자 생성
        worker = await WorkerBuilder().with_korean_data().build(db_session)

        # 2. 배치전 건강진단 실시
        pre_exam_data = {
            "worker_id": worker.id,
            "exam_date": "2023-01-15T09:00:00",
            "exam_type": "pre_employment",
            "exam_result": "normal",
            "exam_agency": "입사전검진센터",
            "overall_opinion": "입사 가능한 건강상태"
        }

        response = await client.post(
            "/api/v1/health-exams/", json=pre_exam_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        pre_exam = response.json()

        # 3. 정기 일반건강진단 실시 (1년 후)
        general_exam_data = {
            "worker_id": worker.id,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "general",
            "exam_result": "normal_b",
            "exam_agency": "정기검진센터",
            "overall_opinion": "경미한 이상소견",
            "followup_required": "Y",
            "followup_date": "2024-07-15T09:00:00"
        }

        response = await client.post(
            "/api/v1/health-exams/", json=general_exam_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        general_exam = response.json()

        # 4. 특수건강진단 실시 (유해인자 노출)
        special_exam_data = {
            "worker_id": worker.id,
            "exam_date": "2024-02-15T09:00:00",
            "exam_type": "special",
            "exam_result": "occupational_c1",
            "exam_agency": "산업보건센터",
            "overall_opinion": "직업성 질환 의심"
        }

        response = await client.post(
            "/api/v1/health-exams/", json=special_exam_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        special_exam = response.json()

        # 5. 근로자별 검진 이력 전체 조회
        response = await client.get(
            f"/api/v1/health-exams/?worker_id={worker.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        exam_history = response.json()
        assert exam_history["total"] == 3

        # 6. 검진 유형별 분류 확인
        exam_types = [exam["exam_type"] for exam in exam_history["items"]]
        assert "pre_employment" in exam_types
        assert "general" in exam_types
        assert "special" in exam_types

        # 7. 최신 검진 결과 조회
        response = await client.get(
            f"/api/v1/health-exams/worker/{worker.id}/latest",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        latest_exam = response.json()
        assert latest_exam["exam_type"] == "special"  # 가장 최근 검진

    async def test_health_exam_followup_tracking_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """건강진단 추적관리 워크플로우 테스트"""
        # 근로자 생성
        worker = await WorkerBuilder().build(db_session)

        # 추적관리가 필요한 검진 생성
        exam_data = {
            "worker_id": worker.id,
            "exam_date": "2024-01-15T09:00:00",
            "exam_type": "general",
            "exam_result": "general_d1",  # 일반질환 의심
            "exam_agency": "종합병원",
            "overall_opinion": "고혈압 의심소견",
            "work_fitness": "업무제한 필요",
            "restrictions": "중량물 취급 제한",
            "followup_required": "Y",
            "followup_date": "2024-04-15T09:00:00",
            "notes": "3개월 후 혈압 재측정 필요"
        }

        # 검진 생성
        response = await client.post(
            "/api/v1/health-exams/", json=exam_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        initial_exam = response.json()

        # 추적검사 실시 (3개월 후)
        followup_exam_data = {
            "worker_id": worker.id,
            "exam_date": "2024-04-20T09:00:00",
            "exam_type": "temporary",
            "exam_result": "normal_b",
            "exam_agency": "추적검사센터",
            "overall_opinion": "혈압 정상화됨",
            "work_fitness": "업무적합",
            "restrictions": "제한사항 해제",
            "followup_required": "N",
            "notes": "생활습관 개선으로 혈압 정상화"
        }

        response = await client.post(
            "/api/v1/health-exams/", json=followup_exam_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        followup_exam = response.json()

        # 추적관리 완료 확인
        assert followup_exam["exam_result"] == "normal_b"
        assert followup_exam["followup_required"] == "N"
        assert "정상화" in followup_exam["overall_opinion"]

        # 전체 이력에서 추적관리 과정 확인
        response = await client.get(
            f"/api/v1/health-exams/?worker_id={worker.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        history = response.json()
        assert history["total"] == 2

        # 시간 순서대로 정렬되어 있는지 확인
        exams = sorted(history["items"], key=lambda x: x["exam_date"])
        assert exams[0]["followup_required"] == "Y"  # 초기검진
        assert exams[1]["followup_required"] == "N"  # 추적검진

    async def test_bulk_health_exam_operations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """대량 건강진단 처리 테스트"""
        # 다수의 근로자 생성
        workers = []
        for i in range(5):
            worker = await WorkerBuilder().with_name(f"근로자{i+1}").build(db_session)
            workers.append(worker)

        # 각 근로자별로 검진 기록 생성
        created_exams = []
        for worker in workers:
            exam_data = {
                "worker_id": worker.id,
                "exam_date": "2024-01-15T09:00:00",
                "exam_type": "general",
                "exam_result": "normal_a",
                "exam_agency": "단체검진센터"
            }

            response = await client.post(
                "/api/v1/health-exams/", json=exam_data, headers=authenticated_headers
            )
            assert response.status_code == 200
            created_exams.append(response.json())

        # 전체 검진 통계 확인
        response = await client.get(
            "/api/v1/health-exams/statistics", headers=authenticated_headers
        )
        assert response.status_code == 200
        stats = response.json()

        # 생성된 검진이 통계에 반영되었는지 확인
        assert stats["by_type"]["general"] >= 5
        assert stats["by_result"]["normal_a"] >= 5

        # 페이지네이션을 통한 대량 데이터 조회
        response = await client.get(
            "/api/v1/health-exams/?page=1&size=10", headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 5
        assert len(data["items"]) >= 5