from datetime import date, datetime

import pytest
from httpx import AsyncClient

from src.models import AccidentReport


async def test_create_accident_report(client: AsyncClient, test_worker):
    """산업재해 신고 테스트"""
    report_data = {
        "accident_datetime": datetime.now().isoformat(),
        "report_datetime": datetime.now().isoformat(),
        "accident_location": "A동 3층 용접작업장",
        "worker_id": test_worker.id,
        "accident_type": "FALL",
        "injury_type": "BRUISE",
        "severity": "MINOR",
        "accident_description": "사다리에서 떨어짐",
        "immediate_cause": "안전장비 미착용",
        "injured_body_part": "왼쪽 팔",
        "treatment_type": "응급처치",
        "hospital_name": "서울의료원",
    }

    response = await client.post("/api/v1/accident-reports/", json=report_data)
    assert response.status_code == 200

    data = response.json()
    assert data["worker_id"] == test_worker.id
    assert data["accident_type"] == "FALL"
    assert data["severity"] == "MINOR"


async def test_get_accident_report(client: AsyncClient, test_accident_report):
    """산업재해 신고서 조회 테스트"""
    response = await client.get(f"/api/v1/accident-reports/{test_accident_report.id}")
    assert response.status_code == 200

    data = response.json()
    assert data["id"] == test_accident_report.id
    assert data["worker_id"] == test_accident_report.worker_id


async def test_update_accident_report(client: AsyncClient, test_accident_report):
    """산업재해 신고서 수정 테스트"""
    update_data = {
        "investigation_status": "INVESTIGATING",
        "investigator_name": "김조사관",
        "immediate_actions": "응급처치 완료",
        "work_days_lost": 3,
    }

    response = await client.put(
        f"/api/v1/accident-reports/{test_accident_report.id}", json=update_data
    )
    assert response.status_code == 200

    data = response.json()
    assert data["investigation_status"] == "INVESTIGATING"
    assert data["work_days_lost"] == 3


async def test_list_accident_reports(client: AsyncClient, test_accident_report):
    """산업재해 신고 목록 조회 테스트"""
    response = await client.get("/api/v1/accident-reports/")
    assert response.status_code == 200

    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


async def test_get_accident_statistics(client: AsyncClient):
    """산업재해 통계 조회 테스트"""
    response = await client.get("/api/v1/accident-reports/statistics")
    assert response.status_code == 200

    data = response.json()
    assert "total_accidents" in data
    assert "by_type" in data
    assert "by_severity" in data
    assert "recent_accidents" in data


async def test_get_safety_metrics(client: AsyncClient):
    """안전 성과 지표 조회 테스트"""
    response = await client.get("/api/v1/accident-reports/safety-metrics")
    assert response.status_code == 200

    data = response.json()
    assert "year" in data
    assert "total_accidents" in data
    assert "frequency_rate" in data
    assert "severity_rate" in data


async def test_get_authority_reporting_required(client: AsyncClient):
    """관계당국 신고 대상 사고 조회 테스트"""
    response = await client.get("/api/v1/accident-reports/authority-reporting-required")
    assert response.status_code == 200

    data = response.json()
    assert "total_unreported" in data
    assert "accidents" in data


async def test_filter_accidents_by_severity(client: AsyncClient, test_accident_report):
    """사고 심각도별 필터링 테스트"""
    response = await client.get(
        f"/api/v1/accident-reports/?severity={test_accident_report.severity.value}"
    )
    assert response.status_code == 200

    data = response.json()
    assert all(
        item["severity"] == test_accident_report.severity.value
        for item in data["items"]
    )
