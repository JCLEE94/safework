import pytest
from httpx import AsyncClient
from datetime import datetime, date
from src.models import ChemicalSubstance


@pytest.mark.asyncio
async def test_create_chemical_substance(async_client: AsyncClient):
    """화학물질 등록 테스트"""
    chemical_data = {
        "korean_name": "메탄올",
        "english_name": "Methanol",
        "cas_number": "67-56-1",
        "hazard_class": "TOXIC",
        "hazard_statement": "삼키면 유독함",
        "signal_word": "위험",
        "physical_state": "액체",
        "storage_location": "화학물질 보관실 A-1",
        "current_quantity": 50.0,
        "quantity_unit": "L",
        "minimum_quantity": 10.0,
        "maximum_quantity": 100.0,
        "manufacturer": "한국화학",
        "msds_revision_date": "2024-01-01"
    }
    
    response = await async_client.post("/api/v1/chemical-substances/", json=chemical_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["korean_name"] == "메탄올"
    assert data["cas_number"] == "67-56-1"
    assert data["hazard_class"] == "TOXIC"


@pytest.mark.asyncio
async def test_get_chemical_substance(async_client: AsyncClient, test_chemical_substance):
    """화학물질 상세 조회 테스트"""
    response = await async_client.get(f"/api/v1/chemical-substances/{test_chemical_substance.id}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["id"] == test_chemical_substance.id
    assert data["korean_name"] == test_chemical_substance.korean_name


@pytest.mark.asyncio
async def test_update_chemical_substance(async_client: AsyncClient, test_chemical_substance):
    """화학물질 정보 수정 테스트"""
    update_data = {
        "current_quantity": 25.0,
        "storage_location": "화학물질 보관실 B-2",
        "notes": "재고 감소로 인한 위치 변경"
    }
    
    response = await async_client.put(f"/api/v1/chemical-substances/{test_chemical_substance.id}", json=update_data)
    assert response.status_code == 200
    
    data = response.json()
    assert data["current_quantity"] == 25.0
    assert data["storage_location"] == "화학물질 보관실 B-2"


@pytest.mark.asyncio
async def test_list_chemical_substances(async_client: AsyncClient, test_chemical_substance):
    """화학물질 목록 조회 테스트"""
    response = await async_client.get("/api/v1/chemical-substances/")
    assert response.status_code == 200
    
    data = response.json()
    assert "items" in data
    assert "total" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_record_chemical_usage(async_client: AsyncClient, test_chemical_substance, test_worker):
    """화학물질 사용 기록 테스트"""
    usage_data = {
        "usage_date": datetime.now().isoformat(),
        "worker_id": test_worker.id,
        "quantity_used": 5.0,
        "quantity_unit": "L",
        "purpose": "용접 작업",
        "work_location": "A동 3층",
        "ventilation_used": "Y",
        "ppe_used": "방독면, 장갑"
    }
    
    response = await async_client.post(f"/api/v1/chemical-substances/{test_chemical_substance.id}/usage", json=usage_data)
    assert response.status_code == 200
    
    data = response.json()
    assert "message" in data
    assert "remaining_quantity" in data


@pytest.mark.asyncio
async def test_get_chemical_statistics(async_client: AsyncClient):
    """화학물질 통계 조회 테스트"""
    response = await async_client.get("/api/v1/chemical-substances/statistics")
    assert response.status_code == 200
    
    data = response.json()
    assert "total_chemicals" in data
    assert "in_use_count" in data
    assert "by_hazard_class" in data
    assert "low_stock_items" in data


@pytest.mark.asyncio
async def test_check_inventory_status(async_client: AsyncClient):
    """재고 점검 현황 테스트"""
    response = await async_client.get("/api/v1/chemical-substances/inventory-check")
    assert response.status_code == 200
    
    data = response.json()
    assert "below_minimum" in data
    assert "above_maximum" in data
    assert "expired" in data


@pytest.mark.asyncio
async def test_search_chemicals(async_client: AsyncClient, test_chemical_substance):
    """화학물질 검색 테스트"""
    response = await async_client.get(f"/api/v1/chemical-substances/?search={test_chemical_substance.korean_name}")
    assert response.status_code == 200
    
    data = response.json()
    assert data["total"] >= 1
    assert any(item["korean_name"] == test_chemical_substance.korean_name for item in data["items"])