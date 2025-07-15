from datetime import datetime

import pytest
from httpx import AsyncClient

from src.models import WorkEnvironment


async def test_create_work_environment(client: AsyncClient):
    """작업환경측정 기록 생성 테스트"""
    env_data = {
        "measurement_date": datetime.now().isoformat(),
        "location": "A동 3층 용접작업장",
        "measurement_type": "NOISE",
        "measurement_agency": "한국산업안전보건공단",
        "measured_value": 85.5,
        "measurement_unit": "dB",
        "standard_value": 90.0,
        "standard_unit": "dB",
        "result": "PASS",
        "report_number": "ENV-2024-001",
    }

    response = await client.post("/api/v1/work-environments/", json=env_data)
    assert response.status_code == 200

    data = response.json()
    assert data["location"] == "A동 3층 용접작업장"
    assert data["measurement_type"] == "NOISE"
    assert data["measured_value"] == 85.5
    assert data["result"] == "PASS"


async def test_get_work_environment(client: AsyncClient, test_work_environment):
    """작업환경측정 기록 조회 테스트"""
    response = await client.get(f"/api/v1/work-environments/{test_work_environment.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_work_environment.id
    assert data["location"] == test_work_environment.location


async def test_update_work_environment(client: AsyncClient, test_work_environment):
    """작업환경측정 기록 수정 테스트"""
    update_data = {
        "result": "FAIL",
        "improvement_measures": "환기시설 보강 필요",
        "re_measurement_required": "Y",
    }

    response = await client.put(
        f"/api/v1/work-environments/{test_work_environment.id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["result"] == "FAIL"
    assert data["improvement_measures"] == "환기시설 보강 필요"


async def test_list_work_environments(client: AsyncClient, test_work_environment):
    """작업환경측정 기록 목록 조회 테스트"""
    response = await client.get("/api/v1/work-environments/")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


async def test_add_worker_exposures(
    client: AsyncClient, test_work_environment, test_worker
):
    """노출 근로자 추가 테스트"""
    exposure_data = [
        {
            "worker_id": test_worker.id,
            "exposure_level": 82.5,
            "exposure_duration_hours": 8.0,
            "protection_equipment_used": "귀마개, 헬멧",
            "health_effect_risk": "경미",
        }
    ]

    response = await client.post(
        f"/api/v1/work-environments/{test_work_environment.id}/exposures",
        json=exposure_data,
    )
    assert response.status_code == 200

    data = response.json()
    assert data["added_count"] == 1


async def test_get_environment_statistics(client: AsyncClient):
    """작업환경측정 통계 조회 테스트"""
    response = await client.get("/api/v1/work-environments/statistics")
    assert response.status_code == 200

    data = response.json()
    assert "total_measurements" in data
    assert "pass_count" in data
    assert "fail_count" in data
    assert "by_type" in data


async def test_get_compliance_status(client: AsyncClient):
    """법규 준수 현황 조회 테스트"""
    response = await client.get("/api/v1/work-environments/compliance-status")
    assert response.status_code == 200

    data = response.json()
    assert "locations" in data
    assert "total_locations" in data
