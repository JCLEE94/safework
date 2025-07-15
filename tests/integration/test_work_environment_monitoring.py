"""
작업환경 측정 및 모니터링 통합 테스트
Work Environment Monitoring Integration Tests
"""

import asyncio
import json
import random
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestWorkEnvironmentMonitoring:
    """작업환경 측정부터 개선 조치까지 전체 프로세스 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_workplace_data(self):
        """샘플 작업장 데이터"""
        return {
            "workplace_name": "A동 화학처리실",
            "department": "화학공정팀",
            "work_process": "화학물질 혼합 및 처리",
            "location": "본관 3층",
            "area_square_meters": 120.5,
            "worker_count": 8,
            "shift_type": "3교대",
            "ventilation_type": "국소배기장치",
            "hazard_categories": [
                "화학물질",
                "소음",
                "분진"
            ],
            "responsible_manager": "김공정장",
            "safety_equipment": [
                "국소배기장치",
                "개인보호구 보관함",
                "응급세안시설",
                "화재감지기"
            ]
        }
    
    @pytest.fixture
    def sample_measurement_plan_data(self):
        """샘플 측정 계획 데이터"""
        return {
            "measurement_type": "regular",
            "planned_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "measurement_items": [
                {
                    "substance": "톨루엔",
                    "measurement_method": "개인시료채취",
                    "sampling_duration_minutes": 480,
                    "exposure_limit_ppm": 20
                },
                {
                    "substance": "소음",
                    "measurement_method": "작업환경소음측정",
                    "sampling_duration_minutes": 480,
                    "exposure_limit_db": 85
                },
                {
                    "substance": "분진",
                    "measurement_method": "총분진포집",
                    "sampling_duration_minutes": 480,
                    "exposure_limit_mg": 5.0
                }
            ],
            "measurement_agency": "한국산업안전보건공단",
            "measurement_personnel": "측정전문가",
            "weather_conditions": "맑음, 온도 22℃, 습도 55%"
        }
    
    async def test_work_environment_measurement_planning_workflow(self, test_client, sample_workplace_data, sample_measurement_plan_data):
        """작업환경 측정 계획 수립 워크플로우 테스트"""
        
        # 1. 작업장 등록
        response = test_client.post("/api/v1/work-environments/workplaces/", json=sample_workplace_data)
        assert response.status_code == 201
        
        workplace_data = response.json()
        workplace_id = workplace_data["id"]
        
        # 등록된 데이터 검증
        assert workplace_data["workplace_name"] == sample_workplace_data["workplace_name"]
        assert workplace_data["department"] == sample_workplace_data["department"]
        assert len(workplace_data["hazard_categories"]) == 3
        
        # 2. 작업환경 측정 계획 수립
        plan_data = sample_measurement_plan_data.copy()
        plan_data["workplace_id"] = workplace_id
        
        response = test_client.post("/api/v1/work-environments/measurement-plans/", json=plan_data)
        assert response.status_code == 201
        
        plan_id = response.json()["id"]
        
        # 3. 측정 계획 상세 조회
        response = test_client.get(f"/api/v1/work-environments/measurement-plans/{plan_id}")
        assert response.status_code == 200
        
        plan_detail = response.json()
        assert plan_detail["workplace_id"] == workplace_id
        assert plan_detail["measurement_type"] == "regular"
        assert len(plan_detail["measurement_items"]) == 3
        
        # 4. 작업장별 측정 계획 조회
        response = test_client.get(f"/api/v1/work-environments/workplaces/{workplace_id}/measurement-plans")
        assert response.status_code == 200
        
        workplace_plans = response.json()
        assert len(workplace_plans) >= 1
        assert workplace_plans[0]["id"] == plan_id
        
        return workplace_id, plan_id
    
    async def test_measurement_execution_and_result_recording(self, test_client, sample_workplace_data):
        """측정 실시 및 결과 기록 테스트"""
        
        # 1. 사전 준비: 작업장 및 측정 계획 등록
        response = test_client.post("/api/v1/work-environments/workplaces/", json=sample_workplace_data)
        workplace_id = response.json()["id"]
        
        plan_data = {
            "workplace_id": workplace_id,
            "measurement_type": "regular",
            "planned_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/work-environments/measurement-plans/", json=plan_data)
        plan_id = response.json()["id"]
        
        # 2. 측정 결과 입력
        measurement_results = {
            "plan_id": plan_id,
            "measurement_date": datetime.now().isoformat(),
            "weather_conditions": {
                "temperature_celsius": 23.5,
                "humidity_percent": 58,
                "atmospheric_pressure_hpa": 1013,
                "wind_speed_ms": 2.1
            },
            "measurement_results": [
                {
                    "substance": "톨루엔",
                    "measurement_method": "개인시료채취",
                    "sampling_points": [
                        {
                            "location": "혼합기 옆",
                            "worker_name": "이작업자",
                            "measured_value": 15.2,
                            "unit": "ppm",
                            "sampling_time_minutes": 480,
                            "exposure_limit": 20.0,
                            "exceeds_limit": False
                        },
                        {
                            "location": "저장탱크 주변",
                            "worker_name": "박작업자",
                            "measured_value": 18.7,
                            "unit": "ppm",
                            "sampling_time_minutes": 480,
                            "exposure_limit": 20.0,
                            "exceeds_limit": False
                        }
                    ],
                    "average_concentration": 16.95,
                    "max_concentration": 18.7,
                    "assessment": "노출기준 이하"
                },
                {
                    "substance": "소음",
                    "measurement_method": "작업환경소음측정",
                    "sampling_points": [
                        {
                            "location": "압축기 근처",
                            "measured_value": 88.5,
                            "unit": "dB(A)",
                            "exposure_limit": 85.0,
                            "exceeds_limit": True
                        }
                    ],
                    "average_concentration": 88.5,
                    "assessment": "노출기준 초과"
                }
            ],
            "measurement_agency": "한국산업안전보건공단",
            "measurement_personnel": "김측정사",
            "equipment_used": [
                "개인시료채취기 (SKC-224)",
                "소음측정기 (B&K Type 2250)",
                "분진측정기 (TSI 8534)"
            ],
            "quality_control": {
                "blank_samples": 2,
                "duplicate_samples": 1,
                "calibration_status": "정상"
            }
        }
        
        response = test_client.post("/api/v1/work-environments/measurement-results/", json=measurement_results)
        assert response.status_code == 201
        
        result_id = response.json()["id"]
        
        # 3. 측정 결과 검증
        response = test_client.get(f"/api/v1/work-environments/measurement-results/{result_id}")
        assert response.status_code == 200
        
        result_detail = response.json()
        assert result_detail["plan_id"] == plan_id
        assert len(result_detail["measurement_results"]) == 2
        
        # 소음이 노출기준을 초과했는지 확인
        noise_result = next(r for r in result_detail["measurement_results"] if r["substance"] == "소음")
        assert noise_result["assessment"] == "노출기준 초과"
        
        # 4. 노출기준 초과 자동 알림 확인
        response = test_client.get(f"/api/v1/work-environments/measurement-results/{result_id}/alerts")
        assert response.status_code == 200
        
        alerts = response.json()
        assert len(alerts) > 0
        assert any(alert["type"] == "exposure_limit_exceeded" for alert in alerts)
        
        return result_id
    
    async def test_exposure_limit_exceeded_response_workflow(self, test_client, sample_workplace_data):
        """노출기준 초과 시 대응 워크플로우 테스트"""
        
        # 1. 노출기준 초과 측정 결과 생성
        response = test_client.post("/api/v1/work-environments/workplaces/", json=sample_workplace_data)
        workplace_id = response.json()["id"]
        
        # 심각한 노출기준 초과 시나리오
        severe_exposure_results = {
            "workplace_id": workplace_id,
            "measurement_date": datetime.now().isoformat(),
            "measurement_results": [
                {
                    "substance": "벤젠",
                    "measurement_method": "개인시료채취",
                    "sampling_points": [
                        {
                            "location": "반응기 주변",
                            "worker_name": "최작업자",
                            "measured_value": 2.5,  # 노출기준 1ppm 대비 2.5배 초과
                            "unit": "ppm",
                            "exposure_limit": 1.0,
                            "exceeds_limit": True
                        }
                    ],
                    "average_concentration": 2.5,
                    "assessment": "노출기준 심각한 초과"
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/measurement-results/", json=severe_exposure_results)
        result_id = response.json()["id"]
        
        # 2. 즉시 조치 계획 수립
        immediate_action_plan = {
            "result_id": result_id,
            "priority_level": "urgent",
            "immediate_actions": [
                {
                    "action": "작업 즉시 중단",
                    "responsible_person": "현장관리자",
                    "target_date": datetime.now().isoformat(),
                    "status": "completed"
                },
                {
                    "action": "근로자 대피 및 의료 검진",
                    "responsible_person": "보건관리자",
                    "target_date": datetime.now().isoformat(),
                    "status": "in_progress"
                }
            ],
            "short_term_actions": [
                {
                    "action": "환기설비 점검 및 개선",
                    "responsible_person": "시설관리팀",
                    "target_date": (datetime.now() + timedelta(days=3)).isoformat(),
                    "estimated_cost": 2000000
                },
                {
                    "action": "개인보호구 지급 및 교육",
                    "responsible_person": "안전관리자",
                    "target_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "estimated_cost": 500000
                }
            ],
            "long_term_actions": [
                {
                    "action": "공정 개선 검토",
                    "responsible_person": "기술팀장",
                    "target_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "estimated_cost": 10000000
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/improvement-plans/", json=immediate_action_plan)
        assert response.status_code == 201
        
        improvement_plan_id = response.json()["id"]
        
        # 3. 관련 근로자 특수건강진단 예약
        affected_workers_data = {
            "workplace_id": workplace_id,
            "exposure_substance": "벤젠",
            "health_exam_type": "emergency_special",
            "scheduled_date": (datetime.now() + timedelta(days=7)).isoformat(),
            "exam_items": [
                "혈액검사",
                "골수기능검사",
                "간기능검사"
            ]
        }
        
        response = test_client.post("/api/v1/health-exams/emergency-schedule", json=affected_workers_data)
        assert response.status_code == 201
        
        # 4. 당국 신고 자동 처리
        regulatory_report_data = {
            "incident_type": "exposure_limit_exceeded",
            "measurement_result_id": result_id,
            "severity_level": "high",
            "affected_worker_count": 1,
            "substance": "벤젠",
            "exposure_level": 2.5,
            "immediate_actions_taken": "작업 중단, 근로자 대피"
        }
        
        response = test_client.post("/api/v1/regulatory/exposure-incident-report", json=regulatory_report_data)
        assert response.status_code == 201
        
        # 5. 개선 조치 진행 상황 추적
        response = test_client.get(f"/api/v1/work-environments/improvement-plans/{improvement_plan_id}")
        assert response.status_code == 200
        
        plan_status = response.json()
        assert plan_status["priority_level"] == "urgent"
        assert len(plan_status["immediate_actions"]) >= 2
    
    async def test_continuous_environmental_monitoring(self, test_client, sample_workplace_data):
        """연속 환경 모니터링 테스트"""
        
        # 1. 작업장에 연속 모니터링 센서 설치
        response = test_client.post("/api/v1/work-environments/workplaces/", json=sample_workplace_data)
        workplace_id = response.json()["id"]
        
        sensor_installation_data = {
            "workplace_id": workplace_id,
            "sensors": [
                {
                    "sensor_type": "air_quality",
                    "parameters": ["CO2", "VOCs", "PM2.5"],
                    "location": "작업구역 중앙",
                    "installation_date": datetime.now().isoformat(),
                    "calibration_date": datetime.now().isoformat(),
                    "data_interval_minutes": 5
                },
                {
                    "sensor_type": "noise",
                    "parameters": ["sound_level_db"],
                    "location": "소음원 근처",
                    "installation_date": datetime.now().isoformat(),
                    "data_interval_minutes": 1
                },
                {
                    "sensor_type": "environmental",
                    "parameters": ["temperature", "humidity", "air_velocity"],
                    "location": "환기구 근처",
                    "installation_date": datetime.now().isoformat(),
                    "data_interval_minutes": 10
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/sensors/install", json=sensor_installation_data)
        assert response.status_code == 201
        
        installation_result = response.json()
        sensor_ids = [sensor["sensor_id"] for sensor in installation_result["installed_sensors"]]
        
        # 2. 실시간 센서 데이터 시뮬레이션
        sensor_data_batches = []
        base_time = datetime.now()
        
        for i in range(60):  # 1시간 분량의 데이터
            timestamp = base_time + timedelta(minutes=i)
            
            sensor_data = {
                "timestamp": timestamp.isoformat(),
                "sensor_readings": [
                    {
                        "sensor_id": sensor_ids[0],  # 공기질 센서
                        "readings": {
                            "CO2": 400 + random.randint(-50, 100),
                            "VOCs": 0.1 + random.uniform(-0.05, 0.1),
                            "PM2.5": 10 + random.randint(-5, 15)
                        }
                    },
                    {
                        "sensor_id": sensor_ids[1],  # 소음 센서
                        "readings": {
                            "sound_level_db": 82 + random.randint(-5, 10)
                        }
                    },
                    {
                        "sensor_id": sensor_ids[2],  # 환경 센서
                        "readings": {
                            "temperature": 22 + random.uniform(-2, 3),
                            "humidity": 55 + random.randint(-10, 10),
                            "air_velocity": 0.5 + random.uniform(-0.2, 0.3)
                        }
                    }
                ]
            }
            sensor_data_batches.append(sensor_data)
        
        # 3. 배치 데이터 업로드
        response = test_client.post("/api/v1/work-environments/sensors/data/batch", json={"data_batches": sensor_data_batches})
        assert response.status_code == 201
        
        # 4. 실시간 알림 임계값 설정
        alert_config = {
            "workplace_id": workplace_id,
            "alert_rules": [
                {
                    "parameter": "sound_level_db",
                    "threshold": 85,
                    "condition": "greater_than",
                    "alert_type": "immediate",
                    "recipients": ["safety@company.com"]
                },
                {
                    "parameter": "VOCs",
                    "threshold": 0.2,
                    "condition": "greater_than",
                    "alert_type": "immediate",
                    "recipients": ["health@company.com"]
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/sensors/alerts/config", json=alert_config)
        assert response.status_code == 201
        
        # 5. 데이터 분석 및 트렌드 확인
        response = test_client.get(f"/api/v1/work-environments/workplaces/{workplace_id}/sensor-data/analysis?hours=1")
        assert response.status_code == 200
        
        analysis_result = response.json()
        assert "averages" in analysis_result
        assert "peaks" in analysis_result
        assert "trend_analysis" in analysis_result
    
    async def test_work_environment_improvement_tracking(self, test_client):
        """작업환경 개선 조치 추적 테스트"""
        
        # 1. 개선이 필요한 작업장 시나리오
        problematic_workplace = {
            "workplace_name": "B동 용접작업장",
            "department": "제조팀",
            "hazard_categories": ["용접흄", "소음", "열"],
            "current_issues": [
                "국소배기장치 성능 저하",
                "소음 노출기준 초과",
                "고온 작업환경"
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/workplaces/", json=problematic_workplace)
        workplace_id = response.json()["id"]
        
        # 2. 종합적인 개선 계획 수립
        comprehensive_improvement_plan = {
            "workplace_id": workplace_id,
            "plan_name": "B동 용접작업장 환경개선 프로젝트",
            "planning_date": datetime.now().isoformat(),
            "total_budget": 50000000,
            "improvement_items": [
                {
                    "category": "ventilation",
                    "description": "국소배기장치 교체 및 성능 향상",
                    "target_performance": "배기풍량 1500CMM 이상",
                    "budget": 20000000,
                    "timeline_days": 30,
                    "responsible_team": "시설관리팀"
                },
                {
                    "category": "noise_control",
                    "description": "방음벽 설치 및 저소음 장비 도입",
                    "target_performance": "소음 수준 85dB 이하",
                    "budget": 15000000,
                    "timeline_days": 45,
                    "responsible_team": "기술팀"
                },
                {
                    "category": "thermal_comfort",
                    "description": "냉방시설 설치 및 작업복 개선",
                    "target_performance": "작업온도 28℃ 이하 유지",
                    "budget": 10000000,
                    "timeline_days": 20,
                    "responsible_team": "총무팀"
                },
                {
                    "category": "ppe_upgrade",
                    "description": "개인보호구 업그레이드 및 자동공급시스템",
                    "target_performance": "100% 착용률 달성",
                    "budget": 5000000,
                    "timeline_days": 15,
                    "responsible_team": "안전팀"
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/improvement-plans/comprehensive", json=comprehensive_improvement_plan)
        assert response.status_code == 201
        
        plan_id = response.json()["id"]
        
        # 3. 개선 조치 진행 상황 업데이트
        progress_updates = [
            {
                "item_category": "ppe_upgrade",
                "progress_percent": 100,
                "status": "completed",
                "completion_date": datetime.now().isoformat(),
                "actual_cost": 4800000,
                "notes": "모든 개인보호구 교체 완료"
            },
            {
                "item_category": "thermal_comfort",
                "progress_percent": 80,
                "status": "in_progress",
                "actual_cost": 8500000,
                "notes": "냉방시설 설치 80% 완료, 작업복 주문 진행 중"
            },
            {
                "item_category": "ventilation",
                "progress_percent": 60,
                "status": "in_progress",
                "actual_cost": 12000000,
                "notes": "기존 배기시설 철거 완료, 신규 장비 설치 진행 중"
            },
            {
                "item_category": "noise_control",
                "progress_percent": 30,
                "status": "in_progress",
                "actual_cost": 5000000,
                "notes": "방음벽 설계 완료, 저소음 장비 선정 중"
            }
        ]
        
        for update in progress_updates:
            response = test_client.put(f"/api/v1/work-environments/improvement-plans/{plan_id}/progress", json=update)
            assert response.status_code == 200
        
        # 4. 개선 효과 검증을 위한 재측정 계획
        verification_measurement_plan = {
            "workplace_id": workplace_id,
            "improvement_plan_id": plan_id,
            "measurement_type": "improvement_verification",
            "planned_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "verification_items": [
                {
                    "parameter": "ventilation_performance",
                    "target_value": 1500,
                    "unit": "CMM",
                    "measurement_method": "풍량측정기"
                },
                {
                    "parameter": "noise_level",
                    "target_value": 85,
                    "unit": "dB(A)",
                    "measurement_method": "소음측정기"
                },
                {
                    "parameter": "temperature",
                    "target_value": 28,
                    "unit": "°C",
                    "measurement_method": "온도계"
                }
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/measurement-plans/verification", json=verification_measurement_plan)
        assert response.status_code == 201
        
        # 5. 개선 계획 종합 현황 조회
        response = test_client.get(f"/api/v1/work-environments/improvement-plans/{plan_id}/status")
        assert response.status_code == 200
        
        plan_status = response.json()
        assert plan_status["overall_progress_percent"] > 0
        assert "cost_analysis" in plan_status
        assert "timeline_status" in plan_status
    
    async def test_regulatory_compliance_reporting(self, test_client):
        """법적 규정 준수 보고 테스트"""
        
        # 1. 분기별 작업환경측정 결과 보고서 생성
        quarterly_report_data = {
            "report_period": "2024-Q2",
            "include_all_workplaces": True,
            "report_type": "comprehensive",
            "include_sections": [
                "measurement_summary",
                "exposure_assessment",
                "improvement_actions",
                "compliance_status",
                "statistical_analysis"
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/reports/quarterly", json=quarterly_report_data)
        assert response.status_code == 200
        
        quarterly_report = response.json()
        assert "report_id" in quarterly_report
        assert "measurement_summary" in quarterly_report
        assert "compliance_rate" in quarterly_report
        
        # 2. 노출기준 초과 사업장 신고
        exposure_exceeded_report = {
            "reporting_period": "2024-07",
            "exceeded_workplaces": [
                {
                    "workplace_name": "A동 화학처리실",
                    "exceeded_substances": ["소음"],
                    "measured_value": 88.5,
                    "exposure_limit": 85.0,
                    "improvement_actions": "방음벽 설치 예정"
                }
            ],
            "total_affected_workers": 8,
            "immediate_actions_taken": "개인보호구 강화, 작업시간 단축"
        }
        
        response = test_client.post("/api/v1/regulatory/exposure-exceeded-report", json=exposure_exceeded_report)
        assert response.status_code == 201
        
        # 3. 작업환경측정 기관 평가 보고서
        measurement_agency_evaluation = {
            "agency_name": "한국산업안전보건공단",
            "evaluation_period": "2024-Q2",
            "evaluation_criteria": {
                "measurement_accuracy": 95,
                "timeliness": 100,
                "report_quality": 90,
                "professional_competence": 95
            },
            "total_measurements": 24,
            "satisfactory_results": 23,
            "recommendations": [
                "측정 정확도 향상을 위한 장비 교정 주기 단축",
                "보고서 품질 개선"
            ]
        }
        
        response = test_client.post("/api/v1/work-environments/agency-evaluation", json=measurement_agency_evaluation)
        assert response.status_code == 201
        
        # 4. 년간 작업환경관리 종합 보고서
        annual_report_data = {
            "year": 2024,
            "include_trend_analysis": True,
            "include_cost_benefit_analysis": True,
            "include_benchmarking": True
        }
        
        response = test_client.post("/api/v1/work-environments/reports/annual", json=annual_report_data)
        assert response.status_code == 200
        
        annual_report = response.json()
        assert "measurement_statistics" in annual_report
        assert "improvement_effectiveness" in annual_report
        assert "cost_analysis" in annual_report


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 작업환경 측정 및 모니터링 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 작업환경 측정 및 모니터링 통합 테스트 실패")
        sys.exit(1)