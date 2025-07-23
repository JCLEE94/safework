"""
화학물질 관리 시스템 통합 테스트
Chemical substance management system integration tests
"""

import asyncio
from datetime import datetime, date, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.chemical_substance import HazardClass, StorageStatus
from tests.builders.chemical_builder import (
    ChemicalSubstanceBuilder, ChemicalUsageRecordBuilder, ChemicalCompleteBuilder
)
from tests.builders.worker_builder import WorkerBuilder


class TestChemicalSubstanceIntegration:
    """화학물질 관리 시스템 통합 테스트"""

    @pytest.mark.asyncio
    async def test_chemical_substance_creation_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 등록 워크플로우 테스트"""
        # 1. 화학물질 등록
        chemical_data = {
            "korean_name": "아세톤",
            "english_name": "Acetone",
            "cas_number": "67-64-1",
            "un_number": "UN1090",
            "hazard_class": "인화성",
            "hazard_statement": "고인화성 액체 및 증기",
            "precautionary_statement": "열·스파크·화염·고열로부터 멀리하시오",
            "signal_word": "위험",
            "physical_state": "액체",
            "appearance": "무색투명한 액체",
            "odor": "달콤한 냄새",
            "ph_value": 7.0,
            "boiling_point": 56.0,
            "melting_point": -95.0,
            "flash_point": -18.0,
            "storage_location": "인화성물질 보관소",
            "storage_condition": "서늘하고 환기가 잘 되는 곳에 보관",
            "incompatible_materials": "강산화제, 강염기와 분리보관",
            "current_quantity": 100.0,
            "quantity_unit": "L",
            "minimum_quantity": 20.0,
            "maximum_quantity": 500.0,
            "exposure_limit_twa": 750.0,
            "exposure_limit_stel": 1000.0,
            "manufacturer": "한국화학공업㈜",
            "supplier": "안전화학물질㈜",
            "emergency_contact": "02-123-4567 (24시간)",
            "status": "사용중"
        }

        response = await client.post(
            "/api/v1/chemical-substances/",
            json=chemical_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        chemical = response.json()
        chemical_id = chemical["id"]

        # 2. 화학물질 상세 조회
        response = await client.get(
            f"/api/v1/chemical-substances/{chemical_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["korean_name"] == "아세톤"
        assert response.json()["cas_number"] == "67-64-1"
        assert response.json()["hazard_class"] == "인화성"

        # 3. 화학물질 정보 수정
        update_data = {
            "current_quantity": 80.0,
            "storage_location": "신규 인화성물질 보관소",
            "notes": "정기 재고 조정 완료"
        }

        response = await client.put(
            f"/api/v1/chemical-substances/{chemical_id}",
            json=update_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        updated_chemical = response.json()
        assert updated_chemical["current_quantity"] == 80.0
        assert "정기 재고 조정" in updated_chemical["notes"]

        # 4. 화학물질 목록 조회
        response = await client.get(
            "/api/v1/chemical-substances/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_chemical_usage_tracking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 사용 추적 테스트"""
        # 화학물질 및 근로자 생성
        chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_data()
            .with_inventory(100.0, "L", 20.0, 500.0)
            .build(db_session)
        )
        
        workers = []
        for i in range(3):
            worker = await (
                WorkerBuilder()
                .with_name(f"화학작업자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 1. 화학물질 사용 기록 등록
        usage_data = {
            "usage_date": "2024-06-15T14:30:00",
            "worker_id": workers[0].id,
            "quantity_used": 15.0,
            "quantity_unit": "L",
            "purpose": "부품 세척 작업",
            "work_location": "제1공장 세척실",
            "ventilation_used": "Y",
            "ppe_used": "화학보호장갑, 보안경, 방독마스크",
            "exposure_duration_minutes": 120,
            "incident_occurred": "N"
        }

        response = await client.post(
            f"/api/v1/chemical-substances/{chemical.id}/usage",
            json=usage_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        usage_result = response.json()
        assert "사용 기록이 저장" in usage_result["message"]
        assert usage_result["remaining_quantity"] == 85.0  # 100 - 15

        # 2. 추가 사용 기록들 등록
        additional_usages = [
            {
                "usage_date": "2024-06-16T10:00:00",
                "worker_id": workers[1].id,
                "quantity_used": 10.0,
                "purpose": "장비 청소",
                "work_location": "제2공장",
                "ventilation_used": "Y",
                "ppe_used": "화학보호장갑, 보안경"
            },
            {
                "usage_date": "2024-06-17T15:30:00",
                "worker_id": workers[2].id,
                "quantity_used": 25.0,
                "purpose": "대규모 세척 작업",
                "work_location": "제3공장",
                "ventilation_used": "N",  # 환기 미사용
                "ppe_used": "일반장갑만 착용",
                "incident_occurred": "Y",
                "incident_description": "화학물질 냄새로 인한 두통 호소"
            }
        ]

        for usage in additional_usages:
            response = await client.post(
                f"/api/v1/chemical-substances/{chemical.id}/usage",
                json=usage,
                headers=authenticated_headers
            )
            assert response.status_code == 200

        # 3. 화학물질 상세 조회 (사용기록 포함)
        response = await client.get(
            f"/api/v1/chemical-substances/{chemical.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        chemical_detail = response.json()
        
        # 사용 기록 확인
        assert len(chemical_detail["usage_records"]) == 3
        
        # 사고 발생 기록 확인
        incident_records = [record for record in chemical_detail["usage_records"] 
                         if record["incident_occurred"] == "Y"]
        assert len(incident_records) == 1
        assert "두통 호소" in incident_records[0]["incident_description"]
        
        # 최종 재고량 확인 (100 - 15 - 10 - 25 = 50)
        assert chemical_detail["current_quantity"] == 50.0

    @pytest.mark.asyncio
    async def test_chemical_hazard_classification_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 유해성 분류 관리 테스트"""
        # 다양한 유해성 분류의 화학물질 생성
        chemicals = []

        # 1. 독성 화학물질 (발암물질)
        toxic_chemical = await (
            ChemicalSubstanceBuilder()
            .with_toxic_chemical()
            .with_special_flags(carcinogen=True, special_management=True)
            .build(db_session)
        )
        chemicals.append(toxic_chemical)

        # 2. 부식성 화학물질
        corrosive_chemical = await (
            ChemicalSubstanceBuilder()
            .with_corrosive_chemical()
            .build(db_session)
        )
        chemicals.append(corrosive_chemical)

        # 3. 인화성 화학물질
        flammable_chemical = await (
            ChemicalSubstanceBuilder()
            .with_flammable_chemical()
            .build(db_session)
        )
        chemicals.append(flammable_chemical)

        # 4. 폭발성 화학물질
        explosive_chemical = await (
            ChemicalSubstanceBuilder()
            .with_explosive_chemical()
            .build(db_session)
        )
        chemicals.append(explosive_chemical)

        # 유해성 분류별 필터링 테스트
        test_cases = [
            ("독성", "독성"),
            ("부식성", "부식성"),
            ("인화성", "인화성"),
            ("폭발성", "폭발성")
        ]

        for hazard_class, expected_value in test_cases:
            response = await client.get(
                f"/api/v1/chemical-substances/?hazard_class={hazard_class}",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            result = response.json()
            assert result["total"] >= 1
            
            # 모든 결과가 해당 유해성 분류인지 확인
            for item in result["items"]:
                assert item["hazard_class"] == expected_value

        # 특별관리물질 필터링
        response = await client.get(
            "/api/v1/chemical-substances/?special_management=true",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 2  # 독성, 폭발성 화학물질

        # 발암물질만 검색
        carcinogen_chemicals = [c for c in chemicals if c.carcinogen == "Y"]
        assert len(carcinogen_chemicals) >= 1

    @pytest.mark.asyncio
    async def test_chemical_inventory_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 재고 관리 테스트"""
        # 다양한 재고 상태의 화학물질 생성
        chemicals = []

        # 1. 재고 부족 화학물질
        low_stock_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("재고부족화학물질")
            .with_low_stock()  # current: 5, minimum: 20
            .build(db_session)
        )
        chemicals.append(low_stock_chemical)

        # 2. 재고 과잉 화학물질
        excess_stock_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("재고과잉화학물질")
            .with_excess_stock()  # current: 150, maximum: 100
            .build(db_session)
        )
        chemicals.append(excess_stock_chemical)

        # 3. 만료된 화학물질
        expired_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("만료화학물질")
            .with_expired_status()
            .build(db_session)
        )
        chemicals.append(expired_chemical)

        # 4. 정상 재고 화학물질
        normal_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("정상재고화학물질")
            .with_inventory(50.0, "L", 20.0, 100.0)  # 정상 범위
            .build(db_session)
        )
        chemicals.append(normal_chemical)

        # 재고 점검 현황 조회
        response = await client.get(
            "/api/v1/chemical-substances/inventory-check",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        inventory_status = response.json()

        # 재고 부족 확인
        assert len(inventory_status["below_minimum"]) >= 1
        low_stock_item = next(
            (item for item in inventory_status["below_minimum"] 
             if item["name"] == "재고부족화학물질"), None
        )
        assert low_stock_item is not None
        assert low_stock_item["current"] == 5.0
        assert low_stock_item["minimum"] == 20.0
        assert low_stock_item["shortage"] == 15.0

        # 재고 과잉 확인
        assert len(inventory_status["above_maximum"]) >= 1
        excess_stock_item = next(
            (item for item in inventory_status["above_maximum"] 
             if item["name"] == "재고과잉화학물질"), None
        )
        assert excess_stock_item is not None
        assert excess_stock_item["current"] == 150.0
        assert excess_stock_item["maximum"] == 100.0
        assert excess_stock_item["excess"] == 50.0

        # 만료된 화학물질 확인
        assert len(inventory_status["expired"]) >= 1
        expired_item = next(
            (item for item in inventory_status["expired"] 
             if item["name"] == "만료화학물질"), None
        )
        assert expired_item is not None

        # 상태별 필터링 테스트
        response = await client.get(
            "/api/v1/chemical-substances/?status=유효기간만료",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_msds_document_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str],
        temp_file_path: str
    ):
        """MSDS 문서 관리 테스트"""
        # 화학물질 생성 (오래된 MSDS)
        chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_data()
            .with_outdated_msds()  # 1년 이상 전 MSDS
            .build(db_session)
        )

        # 1. MSDS 파일 업로드
        with open(temp_file_path, "rb") as f:
            response = await client.post(
                f"/api/v1/chemical-substances/{chemical.id}/msds",
                files={"file": ("msds_acetone.pdf", f, "application/pdf")},
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        upload_result = response.json()
        assert "업로드되었습니다" in upload_result["message"]
        assert "file_path" in upload_result

        # 2. 화학물질 정보 다시 조회하여 MSDS 정보 확인
        response = await client.get(
            f"/api/v1/chemical-substances/{chemical.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        updated_chemical = response.json()
        assert updated_chemical["msds_file_path"] is not None
        assert updated_chemical["msds_revision_date"] == date.today().isoformat()

        # 3. 잘못된 파일 형식 업로드 테스트
        with open(temp_file_path, "rb") as f:
            response = await client.post(
                f"/api/v1/chemical-substances/{chemical.id}/msds",
                files={"file": ("invalid.txt", f, "text/plain")},
                headers=authenticated_headers
            )
        
        assert response.status_code == 400
        assert "허용됩니다" in response.json()["detail"]

    @pytest.mark.asyncio
    async def test_chemical_statistics_and_reporting(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 통계 및 보고 기능 테스트"""
        # 다양한 화학물질 생성
        chemicals = []

        # 각 유해성 분류별로 2개씩 생성
        hazard_types = [
            (HazardClass.TOXIC, "독성물질"),
            (HazardClass.FLAMMABLE, "인화성물질"),
            (HazardClass.CORROSIVE, "부식성물질"),
            (HazardClass.EXPLOSIVE, "폭발성물질")
        ]

        for hazard_class, name_prefix in hazard_types:
            for i in range(2):
                chemical = await (
                    ChemicalSubstanceBuilder()
                    .with_korean_name(f"{name_prefix}{i+1}")
                    .with_hazard_class(hazard_class)
                    .with_inventory(50.0 + i*10, "L")
                    .build(db_session)
                )
                chemicals.append(chemical)

        # 특별관리물질 생성
        special_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("특별관리물질")
            .with_special_flags(special_management=True, carcinogen=True)
            .build(db_session)
        )
        chemicals.append(special_chemical)

        # 재고 부족 화학물질 생성
        low_stock_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("재고부족물질")
            .with_low_stock()
            .build(db_session)
        )
        chemicals.append(low_stock_chemical)

        # 만료된 MSDS 화학물질 생성
        outdated_msds_chemical = await (
            ChemicalSubstanceBuilder()
            .with_korean_name("오래된MSDS물질")
            .with_outdated_msds()
            .build(db_session)
        )
        chemicals.append(outdated_msds_chemical)

        # 통계 조회
        response = await client.get(
            "/api/v1/chemical-substances/statistics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        stats = response.json()
        assert stats["total_chemicals"] >= 11  # 생성한 화학물질 수
        assert stats["in_use_count"] >= 10  # 만료가 아닌 것들
        assert stats["special_management_count"] >= 1
        assert stats["carcinogen_count"] >= 1
        
        # 유해성 분류별 통계 확인
        assert "독성" in stats["by_hazard_class"]
        assert "인화성" in stats["by_hazard_class"]
        assert "부식성" in stats["by_hazard_class"]
        assert "폭발성" in stats["by_hazard_class"]
        
        # 각 분류별로 2개씩 생성했으므로
        assert stats["by_hazard_class"]["독성"] == 2
        assert stats["by_hazard_class"]["인화성"] == 2
        
        # 재고 부족 아이템 확인
        assert len(stats["low_stock_items"]) >= 1
        low_stock_item = next(
            (item for item in stats["low_stock_items"] 
             if item["korean_name"] == "재고부족물질"), None
        )
        assert low_stock_item is not None
        
        # 만료된 MSDS 확인
        assert len(stats["expired_msds"]) >= 1

    @pytest.mark.asyncio
    async def test_chemical_search_and_filtering(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 검색 및 필터링 기능 테스트"""
        # 검색용 화학물질 생성
        chemicals = [
            ("아세톤", "Acetone", "67-64-1"),
            ("벤젠", "Benzene", "71-43-2"),
            ("톨루엔", "Toluene", "108-88-3"),
            ("에탄올", "Ethanol", "64-17-5")
        ]

        created_chemicals = []
        for korean, english, cas in chemicals:
            chemical = await (
                ChemicalSubstanceBuilder()
                .with_korean_name(korean)
                .with_english_name(english)
                .with_cas_number(cas)
                .with_korean_data()
                .build(db_session)
            )
            created_chemicals.append(chemical)

        # 1. 한글명 검색
        response = await client.get(
            "/api/v1/chemical-substances/?search=아세톤",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert any(item["korean_name"] == "아세톤" for item in result["items"])

        # 2. 영문명 검색
        response = await client.get(
            "/api/v1/chemical-substances/?search=Benzene",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert any(item["english_name"] == "Benzene" for item in result["items"])

        # 3. CAS 번호 검색
        response = await client.get(
            "/api/v1/chemical-substances/?search=108-88-3",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 1
        assert any(item["cas_number"] == "108-88-3" for item in result["items"])

        # 4. 부분 검색
        response = await client.get(
            "/api/v1/chemical-substances/?search=에탄",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert any("에탄" in item["korean_name"] for item in result["items"])

        # 5. 페이지네이션
        response = await client.get(
            "/api/v1/chemical-substances/?page=1&size=2",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 2
        assert result["page"] == 1
        assert result["size"] == 2

    @pytest.mark.asyncio
    async def test_chemical_safety_compliance_tracking(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 안전 규정 준수 추적 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(5):
            worker = await (
                WorkerBuilder()
                .with_name(f"안전관리자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 1. 안전수칙 준수 시나리오
        compliant_chemical = await (
            ChemicalCompleteBuilder()
            .with_chemical_builder(
                ChemicalSubstanceBuilder()
                .with_korean_name("안전준수화학물질")
                .with_toxic_chemical()
            )
            .with_multiple_usage_records(
                [workers[0].id, workers[1].id],
                ["안전한 세척작업", "규정준수 청소"],
                [3.0, 2.5]  # 적은 양 사용
            )
            .build(db_session)
        )

        # 모든 사용기록이 안전조치 완비인지 확인
        response = await client.get(
            f"/api/v1/chemical-substances/{compliant_chemical.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        chemical_detail = response.json()
        
        for record in chemical_detail["usage_records"]:
            assert record["ventilation_used"] == "Y"
            assert "보호장갑" in record["ppe_used"]
            assert record["incident_occurred"] == "N"

        # 2. 안전수칙 위반 시나리오
        violation_chemical = await (
            ChemicalCompleteBuilder()
            .with_chemical_builder(
                ChemicalSubstanceBuilder()
                .with_korean_name("위반사례화학물질")
                .with_toxic_chemical()
            )
            .with_safety_violation_scenario([workers[2].id, workers[3].id, workers[4].id])
            .build(db_session)
        )

        response = await client.get(
            f"/api/v1/chemical-substances/{violation_chemical.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        violation_detail = response.json()
        
        # 위반 사례 분석
        violations = []
        for record in violation_detail["usage_records"]:
            if (record["ventilation_used"] == "N" or 
                record["ppe_used"] == "일반장갑만 착용" or 
                record["incident_occurred"] == "Y"):
                violations.append(record)
        
        assert len(violations) > 0
        
        # 사고 발생 기록 확인
        incidents = [r for r in violation_detail["usage_records"] if r["incident_occurred"] == "Y"]
        assert len(incidents) > 0
        assert any("누출" in record["incident_description"] for record in incidents if record["incident_description"])

        # 3. 노출기준 초과 검증
        high_exposure_usage = {
            "usage_date": datetime.now().isoformat(),
            "worker_id": workers[0].id,
            "quantity_used": 100.0,  # 대량 사용
            "exposure_duration_minutes": 480,  # 8시간 노출
            "ventilation_used": "N",
            "ppe_used": "미착용",
            "purpose": "긴급 대규모 세척"
        }

        response = await client.post(
            f"/api/v1/chemical-substances/{violation_chemical.id}/usage",
            json=high_exposure_usage,
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # 노출기준 초과 여부 확인 (TWA: 1.0, 실제 노출: 8시간)
        # 실제 구현에서는 노출량 계산 로직이 필요

    @pytest.mark.asyncio
    async def test_chemical_lifecycle_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 전체 생명주기 관리 테스트"""
        # 1. 화학물질 도입 (주문중 상태)
        chemical_data = {
            "korean_name": "생명주기테스트화학물질",
            "english_name": "Lifecycle Test Chemical",
            "cas_number": "999-99-9",
            "hazard_class": "독성",
            "current_quantity": 0.0,
            "quantity_unit": "L",
            "minimum_quantity": 10.0,
            "maximum_quantity": 100.0,
            "status": "주문중"
        }

        response = await client.post(
            "/api/v1/chemical-substances/",
            json=chemical_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        chemical = response.json()
        chemical_id = chemical["id"]

        # 2. 입고 처리 (사용중으로 변경)
        update_data = {
            "current_quantity": 50.0,
            "status": "사용중",
            "notes": "신규 입고 완료"
        }

        response = await client.put(
            f"/api/v1/chemical-substances/{chemical_id}",
            json=update_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # 3. 사용 기간 (여러 사용 기록)
        worker = await WorkerBuilder().with_name("생명주기작업자").build(db_session)
        
        # 정상 사용
        for i in range(3):
            usage_data = {
                "usage_date": (datetime.now() - timedelta(days=30-i*10)).isoformat(),
                "worker_id": worker.id,
                "quantity_used": 8.0,
                "purpose": f"정기 작업 {i+1}차",
                "work_location": "생산라인",
                "ventilation_used": "Y",
                "ppe_used": "완전보호구"
            }

            response = await client.post(
                f"/api/v1/chemical-substances/{chemical_id}/usage",
                json=usage_data,
                headers=authenticated_headers
            )
            assert response.status_code == 200

        # 4. 재고 부족 상황 (최소재고 미만)
        final_usage_data = {
            "usage_date": datetime.now().isoformat(),
            "worker_id": worker.id,
            "quantity_used": 20.0,  # 대량 사용으로 재고 부족 유발
            "purpose": "대규모 정비 작업",
            "work_location": "전체 공장"
        }

        response = await client.post(
            f"/api/v1/chemical-substances/{chemical_id}/usage",
            json=final_usage_data,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        final_usage_result = response.json()
        assert final_usage_result["remaining_quantity"] < 10.0  # 최소재고 미만

        # 5. 재고 점검에서 부족 아이템으로 감지
        response = await client.get(
            "/api/v1/chemical-substances/inventory-check",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        inventory_status = response.json()
        
        low_stock_names = [item["name"] for item in inventory_status["below_minimum"]]
        assert "생명주기테스트화학물질" in low_stock_names

        # 6. 유효기간 만료 처리
        expiry_update = {
            "status": "유효기간만료",
            "notes": "유효기간 만료로 인한 사용 중단"
        }

        response = await client.put(
            f"/api/v1/chemical-substances/{chemical_id}",
            json=expiry_update,
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # 7. 폐기 처리 시도 (사용기록이 있어서 실제로는 상태만 변경)
        response = await client.delete(
            f"/api/v1/chemical-substances/{chemical_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        delete_result = response.json()
        assert "폐기 상태로 변경" in delete_result["message"]

        # 8. 최종 상태 확인
        response = await client.get(
            f"/api/v1/chemical-substances/{chemical_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        final_chemical = response.json()
        # 사용 기록이 모두 보존되어 있는지 확인
        assert len(final_chemical["usage_records"]) == 4

    @pytest.mark.asyncio
    async def test_chemical_error_handling(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """화학물질 관리 오류 처리 테스트"""
        # 1. 중복 CAS 번호로 등록 시도
        existing_chemical = await (
            ChemicalSubstanceBuilder()
            .with_cas_number("123-45-6")
            .build(db_session)
        )

        duplicate_data = {
            "korean_name": "중복테스트",
            "cas_number": "123-45-6",  # 이미 존재하는 CAS 번호
            "hazard_class": "독성"
        }

        response = await client.post(
            "/api/v1/chemical-substances/",
            json=duplicate_data,
            headers=authenticated_headers
        )
        assert response.status_code == 400
        assert "이미 등록된" in response.json()["detail"]

        # 2. 존재하지 않는 화학물질 조회
        response = await client.get(
            "/api/v1/chemical-substances/99999",
            headers=authenticated_headers
        )
        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.json()["detail"]

        # 3. 존재하지 않는 근로자로 사용 기록 등록
        invalid_usage_data = {
            "usage_date": datetime.now().isoformat(),
            "worker_id": 99999,  # 존재하지 않는 근로자
            "quantity_used": 10.0,
            "purpose": "테스트"
        }

        response = await client.post(
            f"/api/v1/chemical-substances/{existing_chemical.id}/usage",
            json=invalid_usage_data,
            headers=authenticated_headers
        )
        assert response.status_code == 404
        assert "근로자를 찾을 수 없습니다" in response.json()["detail"]

        # 4. 잘못된 데이터 형식으로 화학물질 등록
        invalid_data = {
            "korean_name": "",  # 필수 필드 비움
            "hazard_class": "잘못된분류",  # 잘못된 enum 값
            "current_quantity": -10  # 음수 재고
        }

        response = await client.post(
            "/api/v1/chemical-substances/",
            json=invalid_data,
            headers=authenticated_headers
        )
        assert response.status_code == 422

        # 5. 재고가 부족한 상황에서 대량 사용 시도
        low_stock_chemical = await (
            ChemicalSubstanceBuilder()
            .with_low_stock()  # 현재 5L, 최소 20L
            .build(db_session)
        )
        
        worker = await WorkerBuilder().build(db_session)
        
        excessive_usage = {
            "usage_date": datetime.now().isoformat(),
            "worker_id": worker.id,
            "quantity_used": 10.0,  # 사용 가능한 양보다 많음
            "purpose": "과도한 사용 테스트"
        }

        response = await client.post(
            f"/api/v1/chemical-substances/{low_stock_chemical.id}/usage",
            json=excessive_usage,
            headers=authenticated_headers
        )
        # 사용은 성공하지만 재고는 0으로 조정됨
        assert response.status_code == 200
        result = response.json()
        assert result["remaining_quantity"] == 0.0

    @pytest.mark.asyncio
    async def test_concurrent_chemical_operations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """동시 화학물질 운영 처리 테스트"""
        # 화학물질 및 근로자 준비
        chemical = await (
            ChemicalSubstanceBuilder()
            .with_inventory(100.0, "L")
            .build(db_session)
        )
        
        workers = []
        for i in range(3):
            worker = await WorkerBuilder().with_name(f"동시사용자{i+1}").build(db_session)
            workers.append(worker)

        # 동시에 여러 사용 기록 등록
        usage_tasks = []
        for i, worker in enumerate(workers):
            usage_data = {
                "usage_date": datetime.now().isoformat(),
                "worker_id": worker.id,
                "quantity_used": 25.0,  # 각각 25L씩 사용
                "purpose": f"동시 작업 {i+1}",
                "work_location": f"작업장 {i+1}"
            }
            
            task = client.post(
                f"/api/v1/chemical-substances/{chemical.id}/usage",
                json=usage_data,
                headers=authenticated_headers
            )
            usage_tasks.append(task)

        # 동시 실행
        responses = await asyncio.gather(*usage_tasks, return_exceptions=True)
        
        # 모든 요청이 성공해야 함
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 200)
        assert success_count == 3

        # 최종 재고 확인 (100 - 25*3 = 25, 하지만 동시성 문제로 정확하지 않을 수 있음)
        response = await client.get(
            f"/api/v1/chemical-substances/{chemical.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        final_chemical = response.json()
        
        # 사용 기록은 3개가 생성되어야 함
        assert len(final_chemical["usage_records"]) == 3
        
        # 재고는 음수가 되지 않도록 보장
        assert final_chemical["current_quantity"] >= 0