import pytest
from httpx import AsyncClient
from datetime import datetime, date
from src.models import HealthExam, VitalSigns, LabResult, Worker
from src.models.health import ExamType, ExamResult


@pytest.mark.asyncio
async def test_create_health_exam(async_client: AsyncClient, test_worker):
    """건강진단 기록 생성 테스트"""
    exam_data = {
        "worker_id": test_worker.id,
        "exam_date": datetime.now().isoformat(),
        "exam_type": "GENERAL",
        "exam_agency": "서울의료원",
        "doctor_name": "김의사",
        "vital_signs": {
            "blood_pressure_systolic": 120,
            "blood_pressure_diastolic": 80,
            "heart_rate": 72,
            "height": 175.0,
            "weight": 70.0
        },
        "lab_results": [
            {
                "test_name": "혈당",
                "test_value": "90",
                "test_unit": "mg/dL",
                "reference_range": "70-100",
                "result_status": "정상"
            }
        ]
    }
    
    response = await async_client.post("/api/v1/health-exams/", json=exam_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["worker_id"] == test_worker.id
    assert data["exam_agency"] == "서울의료원"
    assert data["vital_signs"]["blood_pressure_systolic"] == 120
    assert len(data["lab_results"]) == 1


@pytest.mark.asyncio
async def test_get_health_exam(async_client: AsyncClient, test_health_exam):
    """건강진단 기록 조회 테스트"""
    response = await async_client.get(f"/api/v1/health-exams/{test_health_exam.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == test_health_exam.id
    assert data["worker_id"] == test_health_exam.worker_id


@pytest.mark.asyncio
async def test_update_health_exam(async_client: AsyncClient, test_health_exam):
    """건강진단 기록 수정 테스트"""
    update_data = {
        "exam_result": "ABNORMAL",
        "overall_opinion": "정기 검진 필요",
        "work_fitness": "업무가능"
    }
    
    response = await async_client.put(f"/api/v1/health-exams/{test_health_exam.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["exam_result"] == "ABNORMAL"
    assert data["overall_opinion"] == "정기 검진 필요"


@pytest.mark.asyncio
async def test_list_health_exams(async_client: AsyncClient, test_health_exam):
    """건강진단 기록 목록 조회 테스트"""
    response = await async_client.get("/api/v1/health-exams/")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_worker_latest_exam(async_client: AsyncClient, test_health_exam):
    """근로자 최신 건강진단 조회 테스트"""
    response = await async_client.get(f"/api/v1/health-exams/worker/{test_health_exam.worker_id}/latest")
    assert response.status_code == 200
    
    data = response.json()
    assert data["worker_id"] == test_health_exam.worker_id


@pytest.mark.asyncio
async def test_get_exam_statistics(async_client: AsyncClient):
    """건강진단 통계 조회 테스트"""
    response = await async_client.get("/api/v1/health-exams/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert "by_type" in data
    assert "by_result" in data
    assert "total_this_year" in data


@pytest.mark.asyncio
async def test_get_exams_due_soon(async_client: AsyncClient):
    """건강진단 예정자 목록 조회 테스트"""
    response = await async_client.get("/api/v1/health-exams/due-soon?days=30")
    assert response.status_code == 200
    
    data = response.json()
    assert "total" in data
    assert "workers" in data