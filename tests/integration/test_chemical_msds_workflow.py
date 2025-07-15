"""
화학물질 및 MSDS 관리 통합 테스트
Chemical Substance and MSDS Management Integration Tests
"""

import asyncio
import io
import json
from datetime import datetime, timedelta

import pytest
from fastapi import UploadFile
from fastapi.testclient import TestClient

from src.app import create_app


class TestChemicalSubstanceManagement:
    """화학물질 관리 전체 워크플로우 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_chemical_data(self):
        """샘플 화학물질 데이터"""
        return {
            "name": "톨루엔",
            "cas_number": "108-88-3",
            "manufacturer": "한국화학(주)",
            "supplier": "화학원료상사",
            "usage_purpose": "도료 희석제",
            "physical_state": "액체",
            "hazard_classification": [
                "인화성 액체 구분2",
                "피부 부식성/자극성 구분2",
                "생식독성 구분2"
            ],
            "storage_location": "화학물질 저장고 A동",
            "storage_conditions": "서늘하고 건조한 곳, 화기 엄금",
            "quantity_kg": 500.0,
            "purchase_date": "2024-01-15",
            "expiry_date": "2025-01-15",
            "special_management_required": True,
            "occupational_exposure_limit": "20 ppm (8시간 TWA)"
        }
    
    @pytest.fixture
    def sample_msds_content(self):
        """샘플 MSDS 내용"""
        return {
            "section_1": {
                "product_name": "톨루엔",
                "manufacturer": "한국화학(주)",
                "emergency_contact": "02-1234-5678"
            },
            "section_2": {
                "hazard_classification": "인화성 액체 구분2",
                "signal_word": "위험",
                "hazard_statements": ["H225: 고인화성 액체 및 증기"]
            },
            "section_8": {
                "exposure_limits": "20 ppm (8시간 TWA)",
                "protective_equipment": ["보안경", "화학물질용 장갑", "방독마스크"]
            },
            "section_11": {
                "acute_toxicity": "LD50 > 5000 mg/kg (경구, 쥐)",
                "chronic_effects": "장기간 노출 시 신경계 영향 가능"
            }
        }
    
    async def test_chemical_substance_registration_flow(self, test_client, sample_chemical_data):
        """화학물질 등록 전체 흐름 테스트"""
        
        # 1. 화학물질 등록
        response = test_client.post("/api/v1/chemical-substances/", json=sample_chemical_data)
        assert response.status_code == 201
        
        chemical_data = response.json()
        chemical_id = chemical_data["id"]
        
        # 등록된 데이터 검증
        assert chemical_data["name"] == sample_chemical_data["name"]
        assert chemical_data["cas_number"] == sample_chemical_data["cas_number"]
        assert chemical_data["special_management_required"] == True
        
        # 2. 등록된 화학물질 조회
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}")
        assert response.status_code == 200
        
        retrieved_chemical = response.json()
        assert retrieved_chemical["id"] == chemical_id
        assert retrieved_chemical["name"] == sample_chemical_data["name"]
        
        # 3. 화학물질 목록 조회
        response = test_client.get("/api/v1/chemical-substances/")
        assert response.status_code == 200
        
        chemicals_list = response.json()
        assert len(chemicals_list) >= 1
        assert any(chem["id"] == chemical_id for chem in chemicals_list)
        
        # 4. 화학물질 검색 테스트
        response = test_client.get(f"/api/v1/chemical-substances/?search=톨루엔")
        assert response.status_code == 200
        
        search_results = response.json()
        assert len(search_results) >= 1
        assert search_results[0]["name"] == "톨루엔"
        
        return chemical_id
    
    async def test_msds_file_upload_and_parsing(self, test_client, sample_chemical_data, sample_msds_content):
        """MSDS 파일 업로드 및 파싱 테스트"""
        
        # 1. 화학물질 등록
        response = test_client.post("/api/v1/chemical-substances/", json=sample_chemical_data)
        chemical_id = response.json()["id"]
        
        # 2. MSDS 파일 생성 (JSON 형태로 테스트)
        msds_content = json.dumps(sample_msds_content, ensure_ascii=False)
        msds_file = io.BytesIO(msds_content.encode('utf-8'))
        
        # 3. MSDS 파일 업로드
        files = {"msds_file": ("toluene_msds.json", msds_file, "application/json")}
        data = {"chemical_id": chemical_id, "version": "1.0", "language": "ko"}
        
        response = test_client.post("/api/v1/chemical-substances/msds/upload", files=files, data=data)
        assert response.status_code == 201
        
        msds_data = response.json()
        msds_id = msds_data["id"]
        
        # 4. MSDS 데이터 파싱 결과 검증
        assert msds_data["chemical_id"] == chemical_id
        assert msds_data["version"] == "1.0"
        
        # 5. MSDS 내용 조회
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/msds")
        assert response.status_code == 200
        
        msds_list = response.json()
        assert len(msds_list) >= 1
        assert msds_list[0]["id"] == msds_id
        
        # 6. MSDS 상세 정보 조회
        response = test_client.get(f"/api/v1/chemical-substances/msds/{msds_id}")
        assert response.status_code == 200
        
        msds_detail = response.json()
        assert msds_detail["chemical_id"] == chemical_id
        
        # 7. MSDS 만료일 확인 및 알림 테스트
        expiry_check_data = {
            "expiry_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "reminder_days_before": 7
        }
        
        response = test_client.put(f"/api/v1/chemical-substances/msds/{msds_id}/expiry", json=expiry_check_data)
        assert response.status_code == 200
        
        return msds_id
    
    async def test_special_management_substance_tracking(self, test_client, sample_chemical_data):
        """특별관리물질 추적 테스트"""
        
        # 1. 특별관리물질로 화학물질 등록
        special_chemical_data = sample_chemical_data.copy()
        special_chemical_data.update({
            "name": "벤젠",
            "cas_number": "71-43-2",
            "special_management_required": True,
            "carcinogen_category": "1A",
            "regulatory_status": "산업안전보건법 특별관리물질"
        })
        
        response = test_client.post("/api/v1/chemical-substances/", json=special_chemical_data)
        assert response.status_code == 201
        chemical_id = response.json()["id"]
        
        # 2. 특별관리물질 취급일지 생성
        handling_log_data = {
            "chemical_id": chemical_id,
            "work_date": datetime.now().isoformat(),
            "worker_name": "이작업자",
            "worker_id": "W001",
            "work_location": "화학처리실 B동",
            "work_description": "벤젠을 이용한 분석 작업",
            "handling_time_minutes": 120,
            "quantity_used_ml": 50.0,
            "protective_equipment_used": [
                "전면형 방독면",
                "화학물질용 장갑",
                "보안경",
                "화학물질용 보호복"
            ],
            "ventilation_status": "국소배기장치 정상 작동",
            "exposure_monitoring": {
                "measurement_taken": True,
                "exposure_level_ppm": 0.5,
                "measurement_method": "개인시료채취",
                "measurement_duration_minutes": 120
            },
            "safety_measures": [
                "작업 전 환기 실시",
                "개인보호구 착용 점검",
                "응급처치 용품 비치 확인"
            ],
            "supervisor": "김감독관"
        }
        
        response = test_client.post("/api/v1/special-materials/handling-log", json=handling_log_data)
        assert response.status_code == 201
        
        log_id = response.json()["id"]
        
        # 3. 취급일지 조회
        response = test_client.get(f"/api/v1/special-materials/handling-log/{log_id}")
        assert response.status_code == 200
        
        log_detail = response.json()
        assert log_detail["chemical_id"] == chemical_id
        assert log_detail["worker_name"] == "이작업자"
        
        # 4. 월별 취급 현황 조회
        response = test_client.get(f"/api/v1/special-materials/{chemical_id}/monthly-usage?year=2024&month=7")
        assert response.status_code == 200
        
        monthly_usage = response.json()
        assert "total_quantity_used" in monthly_usage
        assert "total_handling_time" in monthly_usage
        assert "worker_exposure_records" in monthly_usage
        
        # 5. 법정 보고서 생성
        report_data = {
            "report_period_start": "2024-07-01",
            "report_period_end": "2024-07-31",
            "include_worker_health_data": True,
            "include_exposure_measurements": True
        }
        
        response = test_client.post(f"/api/v1/special-materials/{chemical_id}/regulatory-report", json=report_data)
        assert response.status_code == 200
        
        report = response.json()
        assert "chemical_info" in report
        assert "usage_summary" in report
        assert "worker_exposure_data" in report
    
    async def test_chemical_usage_logging(self, test_client, sample_chemical_data):
        """화학물질 사용 기록 테스트"""
        
        # 1. 화학물질 등록
        response = test_client.post("/api/v1/chemical-substances/", json=sample_chemical_data)
        chemical_id = response.json()["id"]
        
        # 2. 사용 기록 생성
        usage_records = []
        for i in range(5):
            usage_data = {
                "chemical_id": chemical_id,
                "usage_date": (datetime.now() - timedelta(days=i)).isoformat(),
                "user_name": f"작업자{i+1}",
                "department": "도장작업팀",
                "purpose": "금속 표면 도장",
                "quantity_used": 10.0 + i * 2,
                "unit": "L",
                "work_location": f"작업장 {i+1}동",
                "safety_precautions": [
                    "환기 실시",
                    "보호구 착용",
                    "화기 근접 금지"
                ],
                "disposal_method": "유해폐기물 처리업체 위탁",
                "supervisor_approval": True
            }
            
            response = test_client.post("/api/v1/chemical-substances/usage", json=usage_data)
            assert response.status_code == 201
            usage_records.append(response.json()["id"])
        
        # 3. 사용 이력 조회
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/usage-history")
        assert response.status_code == 200
        
        usage_history = response.json()
        assert len(usage_history) == 5
        
        # 4. 사용량 통계 조회
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/usage-statistics?period=monthly")
        assert response.status_code == 200
        
        statistics = response.json()
        assert "total_usage" in statistics
        assert "average_daily_usage" in statistics
        assert "usage_trend" in statistics
        
        # 5. 재고 관리
        # 현재 재고량 확인
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/inventory")
        assert response.status_code == 200
        
        inventory = response.json()
        current_stock = inventory["current_quantity"]
        
        # 재고 조정
        adjustment_data = {
            "adjustment_type": "consumption",
            "quantity": 60.0,  # 총 사용량
            "reason": "월간 사용량 반영",
            "adjusted_by": "창고관리자"
        }
        
        response = test_client.post(f"/api/v1/chemical-substances/{chemical_id}/inventory/adjust", json=adjustment_data)
        assert response.status_code == 200
        
        # 재고 확인
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/inventory")
        updated_inventory = response.json()
        assert updated_inventory["current_quantity"] < current_stock
    
    async def test_hazard_classification_and_labeling(self, test_client, sample_chemical_data):
        """위험성 분류 및 라벨링 테스트"""
        
        # 1. 화학물질 등록
        response = test_client.post("/api/v1/chemical-substances/", json=sample_chemical_data)
        chemical_id = response.json()["id"]
        
        # 2. GHS 분류 정보 업데이트
        ghs_classification = {
            "physical_hazards": [
                {
                    "hazard_class": "인화성 액체",
                    "hazard_category": "구분2",
                    "signal_word": "위험",
                    "hazard_statement": "H225: 고인화성 액체 및 증기"
                }
            ],
            "health_hazards": [
                {
                    "hazard_class": "피부 부식성/자극성",
                    "hazard_category": "구분2",
                    "signal_word": "경고",
                    "hazard_statement": "H315: 피부에 자극을 일으킴"
                },
                {
                    "hazard_class": "생식독성",
                    "hazard_category": "구분2",
                    "signal_word": "경고",
                    "hazard_statement": "H361: 태아 또는 생식능력에 손상을 일으킬 것으로 의심됨"
                }
            ],
            "environmental_hazards": [],
            "precautionary_statements": [
                "P201: 사용 전 특별 지시사항을 확보하시오",
                "P210: 열·스파크·화염·고열로부터 멀리하시오",
                "P264: 취급 후에는 손을 철저히 씻으시오",
                "P280: 보호장갑/보호의/보안경/안면보호구를 착용하시오"
            ]
        }
        
        response = test_client.put(f"/api/v1/chemical-substances/{chemical_id}/ghs-classification", json=ghs_classification)
        assert response.status_code == 200
        
        # 3. 라벨 생성
        label_data = {
            "label_size": "A4",
            "language": "ko",
            "include_company_logo": True,
            "custom_warnings": [
                "임신 중인 여성은 취급 금지",
                "밀폐된 공간에서 사용 금지"
            ]
        }
        
        response = test_client.post(f"/api/v1/chemical-substances/{chemical_id}/generate-label", json=label_data)
        assert response.status_code == 200
        
        # PDF 라벨 파일이 생성되었는지 확인
        assert response.headers["content-type"] == "application/pdf"
        
        # 4. 안전보건자료 요약 생성
        response = test_client.post(f"/api/v1/chemical-substances/{chemical_id}/safety-summary")
        assert response.status_code == 200
        
        safety_summary = response.json()
        assert "hazard_overview" in safety_summary
        assert "first_aid_measures" in safety_summary
        assert "handling_precautions" in safety_summary
        assert "storage_requirements" in safety_summary
    
    async def test_chemical_inventory_management(self, test_client, sample_chemical_data):
        """화학물질 재고 관리 테스트"""
        
        # 1. 여러 화학물질 등록
        chemicals = []
        for i in range(3):
            chemical_data = sample_chemical_data.copy()
            chemical_data["name"] = f"화학물질{i+1}"
            chemical_data["cas_number"] = f"123-45-{i}"
            chemical_data["quantity_kg"] = 100.0 + i * 50
            
            response = test_client.post("/api/v1/chemical-substances/", json=chemical_data)
            assert response.status_code == 201
            chemicals.append(response.json())
        
        # 2. 전체 재고 현황 조회
        response = test_client.get("/api/v1/chemical-substances/inventory/overview")
        assert response.status_code == 200
        
        inventory_overview = response.json()
        assert "total_chemicals" in inventory_overview
        assert "low_stock_alerts" in inventory_overview
        assert "expired_chemicals" in inventory_overview
        
        # 3. 재고 부족 알림 설정
        for chemical in chemicals:
            alert_config = {
                "minimum_stock_kg": 50.0,
                "alert_recipients": ["warehouse@company.com"],
                "alert_frequency": "daily"
            }
            
            response = test_client.post(f"/api/v1/chemical-substances/{chemical['id']}/inventory/alert-config", json=alert_config)
            assert response.status_code == 201
        
        # 4. 재고 이동 기록
        transfer_data = {
            "from_location": "화학물질 저장고 A동",
            "to_location": "작업장 1동",
            "quantity_kg": 25.0,
            "transfer_date": datetime.now().isoformat(),
            "transferred_by": "창고담당자",
            "approved_by": "안전관리자",
            "purpose": "도장 작업용"
        }
        
        response = test_client.post(f"/api/v1/chemical-substances/{chemicals[0]['id']}/inventory/transfer", json=transfer_data)
        assert response.status_code == 201
        
        # 5. 만료 예정 화학물질 확인
        response = test_client.get("/api/v1/chemical-substances/inventory/expiring?days=30")
        assert response.status_code == 200
        
        expiring_chemicals = response.json()
        # 만료 예정 화학물질 목록 확인
        
        # 6. 재고 보고서 생성
        report_params = {
            "report_type": "monthly_inventory",
            "include_usage_analysis": True,
            "include_cost_analysis": True
        }
        
        response = test_client.post("/api/v1/chemical-substances/inventory/report", json=report_params)
        assert response.status_code == 200
        
        inventory_report = response.json()
        assert "inventory_summary" in inventory_report
        assert "usage_analysis" in inventory_report
        assert "recommendations" in inventory_report
    
    async def test_regulatory_compliance_monitoring(self, test_client, sample_chemical_data):
        """법적 규정 준수 모니터링 테스트"""
        
        # 1. 규제 대상 화학물질 등록
        regulated_chemical_data = sample_chemical_data.copy()
        regulated_chemical_data.update({
            "name": "폼알데하이드",
            "cas_number": "50-00-0",
            "regulatory_classifications": [
                "산업안전보건법 특별관리물질",
                "화학물질관리법 제한물질",
                "환경부 유독물질"
            ],
            "reporting_requirements": [
                "분기별 사용량 보고",
                "연간 안전성 평가",
                "작업환경측정 의무"
            ]
        })
        
        response = test_client.post("/api/v1/chemical-substances/", json=regulated_chemical_data)
        chemical_id = response.json()["id"]
        
        # 2. 규정 준수 체크리스트 생성
        compliance_checklist = {
            "chemical_id": chemical_id,
            "compliance_items": [
                {
                    "requirement": "MSDS 비치",
                    "status": "completed",
                    "due_date": "2024-01-15",
                    "completed_date": "2024-01-10",
                    "responsible_person": "안전관리자"
                },
                {
                    "requirement": "작업환경측정",
                    "status": "pending",
                    "due_date": "2024-07-31",
                    "responsible_person": "보건관리자"
                },
                {
                    "requirement": "특수건강진단",
                    "status": "in_progress",
                    "due_date": "2024-08-15",
                    "responsible_person": "보건관리자"
                }
            ]
        }
        
        response = test_client.post("/api/v1/chemical-substances/compliance/checklist", json=compliance_checklist)
        assert response.status_code == 201
        
        # 3. 규정 준수 현황 모니터링
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/compliance/status")
        assert response.status_code == 200
        
        compliance_status = response.json()
        assert "overall_compliance_rate" in compliance_status
        assert "pending_requirements" in compliance_status
        assert "overdue_items" in compliance_status
        
        # 4. 자동 알림 설정
        notification_config = {
            "compliance_due_alerts": True,
            "alert_days_before": [30, 14, 7, 1],
            "recipients": ["safety@company.com", "health@company.com"],
            "escalation_rules": [
                {
                    "days_overdue": 7,
                    "escalate_to": ["manager@company.com"]
                }
            ]
        }
        
        response = test_client.post(f"/api/v1/chemical-substances/{chemical_id}/compliance/notifications", json=notification_config)
        assert response.status_code == 201
        
        # 5. 규정 위반 리스크 평가
        response = test_client.get(f"/api/v1/chemical-substances/{chemical_id}/compliance/risk-assessment")
        assert response.status_code == 200
        
        risk_assessment = response.json()
        assert "risk_level" in risk_assessment
        assert "violation_risks" in risk_assessment
        assert "mitigation_recommendations" in risk_assessment


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 화학물질 MSDS 관리 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 화학물질 MSDS 관리 통합 테스트 실패")
        sys.exit(1)