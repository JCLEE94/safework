"""
작업환경측정 통합 테스트
Integration tests for work environment monitoring system
"""

import pytest
from datetime import datetime, timedelta
from typing import Dict, List, Optional

import pytest_asyncio
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.work_environment import (
    WorkEnvironment, WorkEnvironmentWorkerExposure, MeasurementType, MeasurementResult
)
from src.models.worker import Worker
from tests.builders.worker_builder import WorkerBuilder
from tests.builders.work_environment_builder import WorkEnvironmentBuilder, WorkerExposureBuilder


class TestWorkEnvironmentMonitoring:
    """작업환경측정 시스템 통합 테스트"""

    @pytest_asyncio.fixture
    async def test_workers(self, db_session: AsyncSession) -> List[Worker]:
        """테스트용 근로자들 생성"""
        workers = []
        for i in range(3):
            worker = await WorkerBuilder().with_korean_data().with_name(f"근로자{i+1}").build(db_session)
            workers.append(worker)
        return workers

    @pytest_asyncio.fixture
    async def sample_work_environments(
        self, db_session: AsyncSession, test_workers: List[Worker]
    ) -> List[WorkEnvironment]:
        """테스트용 작업환경측정 기록들 생성"""
        environments = []

        # 소음 측정 - 부적합
        noise_env = (
            await WorkEnvironmentBuilder()
            .with_measurement_type(MeasurementType.NOISE)
            .with_location("생산라인 A구역")
            .with_measurement_values(95.5, "dB", 90.0, "dB")
            .with_result(MeasurementResult.FAIL)
            .with_improvement_measures("방음시설 보강 및 개인보호구 지급")
            .with_re_measurement_required()
            .build(db_session)
        )
        environments.append(noise_env)

        # 분진 측정 - 적합
        dust_env = (
            await WorkEnvironmentBuilder()
            .with_measurement_type(MeasurementType.DUST)
            .with_location("포장라인 B구역")
            .with_measurement_values(2.8, "mg/m³", 5.0, "mg/m³")
            .with_result(MeasurementResult.PASS)
            .build(db_session)
        )
        environments.append(dust_env)

        # 화학물질 측정 - 주의
        chemical_env = (
            await WorkEnvironmentBuilder()
            .with_measurement_type(MeasurementType.CHEMICAL)
            .with_location("화학처리실 C구역")
            .with_measurement_values(18.5, "ppm", 20.0, "ppm")
            .with_result(MeasurementResult.CAUTION)
            .with_improvement_measures("환기시설 개선 및 정기 모니터링 강화")
            .build(db_session)
        )
        environments.append(chemical_env)

        return environments

    async def test_create_work_environment_measurement(
        self, client: AsyncClient, authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 기록 생성 테스트"""
        measurement_data = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": "용접작업장 A동",
            "measurement_type": "소음",
            "measurement_agency": "환경측정센터",
            "measured_value": 88.5,
            "measurement_unit": "dB",
            "standard_value": 90.0,
            "standard_unit": "dB",
            "result": "적합",
            "improvement_measures": "현재 수준 유지",
            "re_measurement_required": "N",
            "report_number": "ENV-2024-001",
            "notes": "정기측정 완료"
        }

        response = await client.post(
            "/api/v1/work-environments/",
            json=measurement_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        created_env = response.json()

        # 생성된 측정 기록 검증
        assert created_env["location"] == "용접작업장 A동"
        assert created_env["measurement_type"] == "소음"
        assert created_env["measurement_agency"] == "환경측정센터"
        assert created_env["measured_value"] == 88.5
        assert created_env["measurement_unit"] == "dB"
        assert created_env["standard_value"] == 90.0
        assert created_env["result"] == "적합"
        assert created_env["report_number"] == "ENV-2024-001"
        assert created_env["notes"] == "정기측정 완료"

    async def test_work_environment_list_with_filters(
        self, 
        client: AsyncClient, 
        sample_work_environments: List[WorkEnvironment],
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 목록 조회 및 필터링 테스트"""
        # 전체 목록 조회
        response = await client.get(
            "/api/v1/work-environments/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 3
        assert len(data["items"]) >= 3

        # 측정항목별 필터링 (소음)
        response = await client.get(
            "/api/v1/work-environments/?measurement_type=소음",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["measurement_type"] == "소음"

        # 결과별 필터링 (부적합)
        response = await client.get(
            "/api/v1/work-environments/?result=부적합",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["result"] == "부적합"

        # 위치별 필터링
        response = await client.get(
            "/api/v1/work-environments/?location=생산라인",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert "생산라인" in item["location"]

        # 날짜 범위 필터링
        start_date = (datetime.now() - timedelta(days=30)).isoformat()
        end_date = datetime.now().isoformat()
        
        response = await client.get(
            f"/api/v1/work-environments/?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data["total"], int)

    async def test_work_environment_statistics(
        self, 
        client: AsyncClient, 
        sample_work_environments: List[WorkEnvironment],
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 통계 조회 테스트"""
        response = await client.get(
            "/api/v1/work-environments/statistics",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        stats = response.json()

        # 기본 통계 확인
        assert "total_measurements" in stats
        assert "pass_count" in stats
        assert "fail_count" in stats
        assert "pending_count" in stats
        assert "re_measurement_required" in stats
        assert "by_type" in stats
        assert "recent_failures" in stats

        # 통계 수치 검증
        assert isinstance(stats["total_measurements"], int)
        assert stats["total_measurements"] >= 3
        
        # 측정항목별 통계 확인
        by_type = stats["by_type"]
        assert "소음" in by_type
        assert "분진" in by_type
        assert "화학물질" in by_type

        # 부적합 건수 확인
        assert stats["fail_count"] >= 1
        assert stats["pass_count"] >= 1

        # 최근 부적합 사례 확인
        if stats["recent_failures"]:
            failure = stats["recent_failures"][0]
            assert "id" in failure
            assert "location" in failure
            assert "measurement_type" in failure
            assert "measurement_date" in failure

    async def test_compliance_status_monitoring(
        self, 
        client: AsyncClient, 
        sample_work_environments: List[WorkEnvironment],
        authenticated_headers: Dict[str, str]
    ):
        """법규 준수 현황 모니터링 테스트"""
        response = await client.get(
            "/api/v1/work-environments/compliance-status",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        compliance_data = response.json()

        assert "locations" in compliance_data
        assert "total_locations" in compliance_data
        assert isinstance(compliance_data["total_locations"], int)
        assert compliance_data["total_locations"] >= 3

        # 위치별 준수 현황 확인
        if compliance_data["locations"]:
            location_status = compliance_data["locations"][0]
            assert "location" in location_status
            assert "measurements" in location_status

            if location_status["measurements"]:
                measurement = location_status["measurements"][0]
                assert "type" in measurement
                assert "latest_date" in measurement
                assert "days_since" in measurement
                assert "is_overdue" in measurement
                assert "latest_result" in measurement

    async def test_work_environment_update_workflow(
        self, 
        client: AsyncClient, 
        sample_work_environments: List[WorkEnvironment],
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 수정 워크플로우 테스트"""
        env_id = sample_work_environments[0].id

        # 측정 결과 업데이트
        update_data = {
            "result": "부적합",
            "improvement_measures": "방음벽 설치 및 작업시간 조정",
            "re_measurement_required": "Y",
            "re_measurement_date": "2024-07-15T10:00:00",
            "notes": "개선조치 후 재측정 필요"
        }

        response = await client.put(
            f"/api/v1/work-environments/{env_id}",
            json=update_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        updated_env = response.json()

        # 업데이트된 정보 검증
        assert updated_env["result"] == "부적합"
        assert updated_env["improvement_measures"] == "방음벽 설치 및 작업시간 조정"
        assert updated_env["re_measurement_required"] == "Y"
        assert "2024-07-15" in updated_env["re_measurement_date"]
        assert updated_env["notes"] == "개선조치 후 재측정 필요"

    async def test_work_environment_with_worker_exposures(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        test_workers: List[Worker],
        authenticated_headers: Dict[str, str]
    ):
        """근로자 노출 정보가 포함된 작업환경측정 테스트"""
        # 작업환경측정 기록 생성
        measurement_data = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": "화학물질처리장",
            "measurement_type": "화학물질",
            "measurement_agency": "산업보건센터",
            "measured_value": 25.0,
            "measurement_unit": "ppm",
            "standard_value": 20.0,
            "standard_unit": "ppm",
            "result": "부적합",
            "improvement_measures": "환기설비 보강 및 개인보호구 강화"
        }

        response = await client.post(
            "/api/v1/work-environments/",
            json=measurement_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        work_env = response.json()
        env_id = work_env["id"]

        # 근로자 노출 정보 추가
        exposure_data = [
            {
                "work_environment_id": env_id,
                "worker_id": test_workers[0].id,
                "exposure_level": 22.5,
                "exposure_duration_hours": 8.0,
                "protection_equipment_used": "방독마스크, 보호복",
                "health_effect_risk": "호흡기 영향 가능성"
            },
            {
                "work_environment_id": env_id,
                "worker_id": test_workers[1].id,
                "exposure_level": 18.0,
                "exposure_duration_hours": 4.0,
                "protection_equipment_used": "방독마스크",
                "health_effect_risk": "경미한 위험"
            }
        ]

        response = await client.post(
            f"/api/v1/work-environments/{env_id}/exposures",
            json=exposure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["added_count"] == 2
        assert "노출 근로자가 추가되었습니다" in result["message"]

        # 노출 정보를 포함한 측정 기록 조회
        response = await client.get(
            f"/api/v1/work-environments/{env_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        detailed_env = response.json()
        
        assert len(detailed_env["worker_exposures"]) == 2
        
        # 첫 번째 노출 근로자 정보 검증
        exposure1 = detailed_env["worker_exposures"][0]
        assert exposure1["worker_id"] == test_workers[0].id
        assert exposure1["exposure_level"] == 22.5
        assert exposure1["exposure_duration_hours"] == 8.0
        assert exposure1["protection_equipment_used"] == "방독마스크, 보호복"
        assert exposure1["health_effect_risk"] == "호흡기 영향 가능성"

    async def test_work_environment_deletion_workflow(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 기록 삭제 워크플로우 테스트"""
        # 삭제용 측정 기록 생성
        env = (
            await WorkEnvironmentBuilder()
            .with_measurement_type(MeasurementType.TEMPERATURE)
            .with_location("고온작업장")
            .with_result(MeasurementResult.PENDING)
            .build(db_session)
        )

        # 측정 기록 삭제
        response = await client.delete(
            f"/api/v1/work-environments/{env.id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        assert response.json()["message"] == "작업환경측정 기록이 삭제되었습니다"

        # 삭제 확인
        response = await client.get(
            f"/api/v1/work-environments/{env.id}",
            headers=authenticated_headers
        )

        assert response.status_code == 404

    async def test_multiple_measurement_types_workflow(
        self, 
        client: AsyncClient, 
        authenticated_headers: Dict[str, str]
    ):
        """다양한 측정항목 워크플로우 테스트"""
        measurement_types = [
            ("소음", 88.5, "dB", 90.0, "적합"),
            ("분진", 4.2, "mg/m³", 5.0, "적합"),
            ("화학물질", 22.0, "ppm", 20.0, "부적합"),
            ("유기용제", 15.8, "ppm", 25.0, "적합"),
            ("진동", 3.5, "m/s²", 5.0, "적합"),
            ("조도", 180.0, "lux", 150.0, "적합"),
            ("고온", 32.5, "℃", 30.0, "주의")
        ]

        created_measurements = []

        for measurement_type, measured_val, unit, standard_val, result in measurement_types:
            measurement_data = {
                "measurement_date": "2024-01-15T10:00:00",
                "location": f"{measurement_type} 측정구역",
                "measurement_type": measurement_type,
                "measurement_agency": "종합환경측정센터",
                "measured_value": measured_val,
                "measurement_unit": unit,
                "standard_value": standard_val,
                "standard_unit": unit,
                "result": result,
                "improvement_measures": f"{measurement_type} 관리방안 수립" if result != "적합" else "현재 수준 유지"
            }

            response = await client.post(
                "/api/v1/work-environments/",
                json=measurement_data,
                headers=authenticated_headers
            )

            assert response.status_code == 200
            created_measurement = response.json()
            created_measurements.append(created_measurement)

            # 각 측정항목 검증
            assert created_measurement["measurement_type"] == measurement_type
            assert created_measurement["measured_value"] == measured_val
            assert created_measurement["result"] == result

        # 전체 통계에서 각 측정항목 확인
        response = await client.get(
            "/api/v1/work-environments/statistics",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        stats = response.json()
        
        # 모든 측정항목이 통계에 포함되어 있는지 확인
        for measurement_type, _, _, _, _ in measurement_types:
            assert measurement_type in stats["by_type"]
            assert stats["by_type"][measurement_type] >= 1

    async def test_work_environment_error_scenarios(
        self, 
        client: AsyncClient,
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 관련 오류 시나리오 테스트"""
        
        # 잘못된 측정항목으로 생성 시도
        invalid_measurement_data = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": "테스트구역",
            "measurement_type": "invalid_type",  # 잘못된 측정항목
            "measurement_agency": "테스트센터",
            "result": "적합"
        }

        response = await client.post(
            "/api/v1/work-environments/",
            json=invalid_measurement_data,
            headers=authenticated_headers
        )

        assert response.status_code == 422  # Validation error

        # 존재하지 않는 측정 기록 조회
        response = await client.get(
            "/api/v1/work-environments/99999",
            headers=authenticated_headers
        )

        assert response.status_code == 404
        assert "작업환경측정 기록을 찾을 수 없습니다" in response.json()["detail"]

        # 존재하지 않는 측정 기록 수정 시도
        response = await client.put(
            "/api/v1/work-environments/99999",
            json={"result": "적합"},
            headers=authenticated_headers
        )

        assert response.status_code == 404

        # 존재하지 않는 근로자로 노출 정보 추가 시도
        response = await client.post(
            "/api/v1/work-environments/1/exposures",
            json=[{
                "work_environment_id": 1,
                "worker_id": 99999,  # 존재하지 않는 근로자 ID
                "exposure_level": 10.0
            }],
            headers=authenticated_headers
        )

        # 404 또는 측정 기록이 존재하지 않는 경우에 대한 처리
        assert response.status_code in [404, 200]  # 측정기록이 없으면 404, 있으면 200 (하지만 근로자 추가는 스킵)

    async def test_work_environment_pagination(
        self, 
        client: AsyncClient, 
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 목록 페이지네이션 테스트"""
        # 추가 측정 기록 생성 (총 10개)
        for i in range(10):
            await WorkEnvironmentBuilder().with_location(f"테스트구역{i+1}").build(db_session)

        # 첫 번째 페이지 (5개씩)
        response = await client.get(
            "/api/v1/work-environments/?page=1&size=5",
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
            "/api/v1/work-environments/?page=2&size=5",
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

    async def test_work_environment_korean_text_handling(
        self, 
        client: AsyncClient,
        authenticated_headers: Dict[str, str]
    ):
        """한글 텍스트 처리 테스트"""
        korean_measurement_data = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": "제1공장 생산라인 가동구역",
            "measurement_type": "소음",
            "measurement_agency": "한국산업보건공단 부산지역본부",
            "measured_value": 92.3,
            "measurement_unit": "데시벨",
            "standard_value": 90.0,
            "standard_unit": "데시벨",
            "result": "부적합",
            "improvement_measures": """
            1. 소음원 차단을 위한 방음벽 설치
            2. 고소음 작업장 근로자 대상 청력보호구 지급
            3. 작업시간 단축 및 교대근무 도입 검토
            4. 정기적인 소음도 모니터링 실시
            """,
            "re_measurement_required": "Y",
            "re_measurement_date": "2024-04-15T10:00:00",
            "report_number": "소음측정-2024-부산-001",
            "notes": "법정 기준치 초과로 즉시 개선조치 필요. 근로자 건강보호를 위한 종합대책 수립 요구됨."
        }

        response = await client.post(
            "/api/v1/work-environments/",
            json=korean_measurement_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        korean_env = response.json()

        # 한글 텍스트 저장 및 조회 검증
        assert korean_env["location"] == "제1공장 생산라인 가동구역"
        assert korean_env["measurement_agency"] == "한국산업보건공단 부산지역본부"
        assert korean_env["measurement_unit"] == "데시벨"
        assert "방음벽 설치" in korean_env["improvement_measures"]
        assert "청력보호구" in korean_env["improvement_measures"]
        assert korean_env["report_number"] == "소음측정-2024-부산-001"
        assert "법정 기준치 초과" in korean_env["notes"]
        assert "종합대책 수립" in korean_env["notes"]


class TestWorkEnvironmentComplexWorkflows:
    """복합 워크플로우 테스트"""

    async def test_work_environment_compliance_lifecycle(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """작업환경측정 법규 준수 전체 생명주기 테스트"""
        location = "화학공정 A라인"
        
        # 1. 초기 측정 실시 (부적합)
        initial_measurement = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": location,
            "measurement_type": "화학물질",
            "measurement_agency": "환경측정센터",
            "measured_value": 35.0,
            "measurement_unit": "ppm",
            "standard_value": 25.0,
            "standard_unit": "ppm",
            "result": "부적합",
            "improvement_measures": "국소배기장치 설치 및 작업방법 개선",
            "re_measurement_required": "Y",
            "re_measurement_date": "2024-04-15T10:00:00",
            "report_number": "CHEM-2024-001"
        }

        response = await client.post(
            "/api/v1/work-environments/", json=initial_measurement, headers=authenticated_headers
        )
        assert response.status_code == 200
        initial_env = response.json()

        # 2. 개선조치 후 재측정 실시 (적합)
        re_measurement = {
            "measurement_date": "2024-04-20T10:00:00",
            "location": location,
            "measurement_type": "화학물질",
            "measurement_agency": "환경측정센터",
            "measured_value": 18.5,
            "measurement_unit": "ppm",
            "standard_value": 25.0,
            "standard_unit": "ppm",
            "result": "적합",
            "improvement_measures": "국소배기장치 설치 완료로 개선됨",
            "re_measurement_required": "N",
            "report_number": "CHEM-2024-001-RE"
        }

        response = await client.post(
            "/api/v1/work-environments/", json=re_measurement, headers=authenticated_headers
        )
        assert response.status_code == 200
        re_env = response.json()

        # 3. 정기 측정 실시 (6개월 후)
        regular_measurement = {
            "measurement_date": "2024-10-15T10:00:00",
            "location": location,
            "measurement_type": "화학물질",
            "measurement_agency": "환경측정센터",
            "measured_value": 20.2,
            "measurement_unit": "ppm",
            "standard_value": 25.0,
            "standard_unit": "ppm",
            "result": "적합",
            "improvement_measures": "현재 수준 유지",
            "re_measurement_required": "N",
            "report_number": "CHEM-2024-002"
        }

        response = await client.post(
            "/api/v1/work-environments/", json=regular_measurement, headers=authenticated_headers
        )
        assert response.status_code == 200
        regular_env = response.json()

        # 4. 해당 위치의 전체 측정 이력 확인
        response = await client.get(
            f"/api/v1/work-environments/?location={location}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        history = response.json()
        assert history["total"] == 3

        # 5. 법규 준수 현황 확인
        response = await client.get(
            "/api/v1/work-environments/compliance-status",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        compliance = response.json()

        # 해당 위치의 준수 현황 찾기
        location_status = None
        for loc_data in compliance["locations"]:
            if loc_data["location"] == location:
                location_status = loc_data
                break

        assert location_status is not None
        assert len(location_status["measurements"]) >= 1

        # 최신 측정 결과가 적합인지 확인
        chemical_measurement = None
        for measurement in location_status["measurements"]:
            if measurement["type"] == "화학물질":
                chemical_measurement = measurement
                break

        assert chemical_measurement is not None
        assert chemical_measurement["latest_result"] == "적합"

    async def test_multiple_location_comprehensive_monitoring(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """다중 위치 종합 모니터링 테스트"""
        locations_and_types = [
            ("생산라인 A동", "소음", 88.0, 90.0, "적합"),
            ("생산라인 A동", "분진", 6.2, 5.0, "부적합"),
            ("화학처리실 B동", "화학물질", 22.0, 25.0, "적합"),
            ("화학처리실 B동", "유기용제", 28.0, 20.0, "부적합"),
            ("용접작업장 C동", "소음", 95.0, 90.0, "부적합"),
            ("용접작업장 C동", "진동", 4.2, 5.0, "적합"),
            ("포장라인 D동", "분진", 3.8, 5.0, "적합"),
            ("포장라인 D동", "조도", 180.0, 150.0, "적합")
        ]

        created_measurements = []
        for location, meas_type, measured, standard, result in locations_and_types:
            measurement_data = {
                "measurement_date": "2024-01-15T10:00:00",
                "location": location,
                "measurement_type": meas_type,
                "measurement_agency": "종합환경측정센터",
                "measured_value": measured,
                "measurement_unit": "unit",
                "standard_value": standard,
                "standard_unit": "unit",
                "result": result
            }

            response = await client.post(
                "/api/v1/work-environments/", json=measurement_data, headers=authenticated_headers
            )
            assert response.status_code == 200
            created_measurements.append(response.json())

        # 전체 통계 분석
        response = await client.get(
            "/api/v1/work-environments/statistics", headers=authenticated_headers
        )
        assert response.status_code == 200
        stats = response.json()

        # 부적합 건수 확인 (3건 이상)
        assert stats["fail_count"] >= 3
        assert stats["pass_count"] >= 5

        # 위치별 준수현황 확인
        response = await client.get(
            "/api/v1/work-environments/compliance-status", headers=authenticated_headers
        )
        assert response.status_code == 200
        compliance = response.json()

        # 4개 위치 모두 포함되어 있는지 확인
        locations_in_compliance = {loc["location"] for loc in compliance["locations"]}
        expected_locations = {"생산라인 A동", "화학처리실 B동", "용접작업장 C동", "포장라인 D동"}
        assert expected_locations.issubset(locations_in_compliance)

        # 각 위치별로 해당하는 측정항목들이 모두 포함되어 있는지 확인
        for location_data in compliance["locations"]:
            location_name = location_data["location"]
            measurement_types = {m["type"] for m in location_data["measurements"]}
            
            if location_name == "생산라인 A동":
                assert "소음" in measurement_types
                assert "분진" in measurement_types
            elif location_name == "화학처리실 B동":
                assert "화학물질" in measurement_types
                assert "유기용제" in measurement_types

    async def test_work_environment_bulk_worker_exposure_tracking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """대량 근로자 노출 추적 관리 테스트"""
        # 여러 근로자 생성
        workers = []
        for i in range(10):
            worker = await WorkerBuilder().with_name(f"근로자{i+1}").build(db_session)
            workers.append(worker)

        # 고위험 화학물질 측정 기록 생성
        measurement_data = {
            "measurement_date": "2024-01-15T10:00:00",
            "location": "고위험 화학물질 취급구역",
            "measurement_type": "화학물질",
            "measurement_agency": "특수환경측정센터",
            "measured_value": 45.0,
            "measurement_unit": "ppm",
            "standard_value": 25.0,
            "standard_unit": "ppm",
            "result": "부적합",
            "improvement_measures": "즉시 작업중단 및 환기시설 보강"
        }

        response = await client.post(
            "/api/v1/work-environments/", json=measurement_data, headers=authenticated_headers
        )
        assert response.status_code == 200
        work_env = response.json()
        env_id = work_env["id"]

        # 다양한 노출 수준의 근로자들 추가
        exposure_data = []
        for i, worker in enumerate(workers):
            exposure_level = 30.0 + (i * 2)  # 30~48 ppm 범위
            risk_level = "높음" if exposure_level > 40 else "보통" if exposure_level > 35 else "낮음"
            protection_equipment = "전면마스크, 보호복, 보호장갑" if exposure_level > 40 else "반면마스크, 보호장갑"
            
            exposure_data.append({
                "work_environment_id": env_id,
                "worker_id": worker.id,
                "exposure_level": exposure_level,
                "exposure_duration_hours": 8.0 - (i * 0.5),  # 4~8시간 범위
                "protection_equipment_used": protection_equipment,
                "health_effect_risk": risk_level
            })

        # 일괄 노출 정보 등록
        response = await client.post(
            f"/api/v1/work-environments/{env_id}/exposures",
            json=exposure_data,
            headers=authenticated_headers
        )

        assert response.status_code == 200
        result = response.json()
        assert result["added_count"] == 10

        # 노출 정보를 포함한 상세 조회
        response = await client.get(
            f"/api/v1/work-environments/{env_id}",
            headers=authenticated_headers
        )

        assert response.status_code == 200
        detailed_env = response.json()
        assert len(detailed_env["worker_exposures"]) == 10

        # 고위험 노출자 확인
        high_risk_exposures = [
            exp for exp in detailed_env["worker_exposures"] 
            if exp["exposure_level"] > 40
        ]
        assert len(high_risk_exposures) >= 4  # 노출수준 40 초과 근로자들

        # 모든 고위험 노출자가 적절한 보호구를 착용했는지 확인
        for exposure in high_risk_exposures:
            assert "전면마스크" in exposure["protection_equipment_used"]
            assert "보호복" in exposure["protection_equipment_used"]
            assert exposure["health_effect_risk"] == "높음"