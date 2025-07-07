"""
보고서 및 대시보드 통합 테스트
Reporting and Dashboard Integration Tests
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from fastapi.testclient import TestClient
import json
import pandas as pd
import io

from src.app import create_app


class TestReportingDashboard:
    """보고서 생성 및 대시보드 시각화 전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_dashboard_config(self):
        """샘플 대시보드 설정"""
        return {
            "dashboard_name": "안전보건 종합 대시보드",
            "refresh_interval_seconds": 300,
            "widgets": [
                {
                    "widget_id": "worker_health_status",
                    "type": "pie_chart",
                    "title": "근로자 건강 상태 분포",
                    "data_source": "workers_health_summary",
                    "position": {"x": 0, "y": 0, "width": 6, "height": 4}
                },
                {
                    "widget_id": "monthly_incidents",
                    "type": "line_chart",
                    "title": "월별 재해 발생 추이",
                    "data_source": "incidents_monthly_trend",
                    "position": {"x": 6, "y": 0, "width": 6, "height": 4}
                },
                {
                    "widget_id": "chemical_inventory",
                    "type": "table",
                    "title": "화학물질 재고 현황",
                    "data_source": "chemical_substances_inventory",
                    "position": {"x": 0, "y": 4, "width": 12, "height": 3}
                },
                {
                    "widget_id": "env_monitoring",
                    "type": "gauge_chart",
                    "title": "실시간 환경 모니터링",
                    "data_source": "realtime_environmental_data",
                    "position": {"x": 0, "y": 7, "width": 4, "height": 3}
                }
            ],
            "filters": [
                {
                    "filter_id": "date_range",
                    "type": "date_range_picker",
                    "default": "last_30_days"
                },
                {
                    "filter_id": "department",
                    "type": "multi_select",
                    "options": ["생산팀", "안전관리팀", "화학처리팀", "용접팀"]
                }
            ]
        }
    
    async def test_dashboard_configuration_and_creation(self, test_client, sample_dashboard_config):
        """대시보드 구성 및 생성 테스트"""
        
        # 1. 새 대시보드 생성
        response = test_client.post("/api/v1/dashboards/", json=sample_dashboard_config)
        assert response.status_code == 201
        
        dashboard_data = response.json()
        dashboard_id = dashboard_data["id"]
        
        # 생성된 데이터 검증
        assert dashboard_data["dashboard_name"] == sample_dashboard_config["dashboard_name"]
        assert len(dashboard_data["widgets"]) == 4
        
        # 2. 대시보드 상세 조회
        response = test_client.get(f"/api/v1/dashboards/{dashboard_id}")
        assert response.status_code == 200
        
        dashboard_detail = response.json()
        assert dashboard_detail["id"] == dashboard_id
        assert dashboard_detail["refresh_interval_seconds"] == 300
        
        # 3. 대시보드 목록 조회
        response = test_client.get("/api/v1/dashboards/")
        assert response.status_code == 200
        
        dashboards = response.json()
        assert len(dashboards) >= 1
        assert any(d["id"] == dashboard_id for d in dashboards)
        
        # 4. 위젯 데이터 로드
        response = test_client.get(f"/api/v1/dashboards/{dashboard_id}/data")
        assert response.status_code == 200
        
        dashboard_data = response.json()
        assert "worker_health_status" in dashboard_data
        assert "monthly_incidents" in dashboard_data
        assert "chemical_inventory" in dashboard_data
        assert "env_monitoring" in dashboard_data
        
        # 5. 대시보드 권한 설정
        permission_data = {
            "dashboard_id": dashboard_id,
            "permissions": [
                {
                    "role": "manager",
                    "access_level": "full"
                },
                {
                    "role": "worker",
                    "access_level": "view_only"
                },
                {
                    "department": "안전관리팀",
                    "access_level": "edit"
                }
            ]
        }
        
        response = test_client.post(f"/api/v1/dashboards/{dashboard_id}/permissions", json=permission_data)
        assert response.status_code == 200
        
        return dashboard_id
    
    async def test_comprehensive_health_report_generation(self, test_client):
        """종합 건강관리 보고서 생성 테스트"""
        
        # 1. 월간 건강관리 보고서 생성
        monthly_report_params = {
            "report_type": "monthly_health_management",
            "period": "2024-07",
            "sections": [
                "executive_summary",
                "worker_health_status",
                "health_examinations",
                "abnormal_findings",
                "health_education",
                "improvement_actions",
                "compliance_status"
            ],
            "format": "pdf",
            "include_charts": True,
            "language": "korean"
        }
        
        response = test_client.post("/api/v1/reports/generate", json=monthly_report_params)
        assert response.status_code == 200
        
        # PDF 응답 검증
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 10000  # 충분한 크기의 PDF
        
        # 2. 분기별 안전보건 통계 보고서
        quarterly_report_params = {
            "report_type": "quarterly_safety_statistics",
            "year": 2024,
            "quarter": 2,
            "metrics": [
                "incident_rate",
                "lost_time_injuries",
                "near_miss_events",
                "safety_training_hours",
                "ppe_compliance",
                "environmental_measurements"
            ],
            "comparison": {
                "compare_previous_quarter": True,
                "compare_previous_year": True,
                "industry_benchmark": True
            },
            "format": "excel"
        }
        
        response = test_client.post("/api/v1/reports/generate", json=quarterly_report_params)
        assert response.status_code == 200
        
        # Excel 응답 검증
        assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        
        # 3. 연간 종합 보고서
        annual_report_params = {
            "report_type": "annual_comprehensive",
            "year": 2024,
            "executive_summary": True,
            "detailed_sections": [
                {
                    "section": "health_management",
                    "include_trends": True,
                    "include_comparisons": True
                },
                {
                    "section": "safety_performance",
                    "kpi_analysis": True,
                    "root_cause_analysis": True
                },
                {
                    "section": "regulatory_compliance",
                    "audit_results": True,
                    "corrective_actions": True
                }
            ],
            "appendices": [
                "detailed_statistics",
                "incident_case_studies",
                "improvement_recommendations"
            ]
        }
        
        response = test_client.post("/api/v1/reports/generate", json=annual_report_params)
        assert response.status_code == 200
    
    async def test_custom_report_builder(self, test_client):
        """맞춤형 보고서 빌더 테스트"""
        
        # 1. 보고서 템플릿 생성
        custom_template = {
            "template_name": "부서별 건강관리 현황",
            "description": "부서별 건강관리 상세 현황 보고서",
            "data_sources": [
                {
                    "source": "workers",
                    "filters": {"active": True},
                    "fields": ["name", "department", "health_status", "last_exam_date"]
                },
                {
                    "source": "health_exams",
                    "filters": {"date_range": "last_6_months"},
                    "aggregations": ["count_by_department", "avg_health_score"]
                }
            ],
            "layout": {
                "sections": [
                    {
                        "title": "요약",
                        "type": "summary_statistics",
                        "components": ["total_workers", "health_status_distribution"]
                    },
                    {
                        "title": "부서별 상세",
                        "type": "detailed_table",
                        "grouping": "department",
                        "sorting": "health_score_desc"
                    },
                    {
                        "title": "추이 분석",
                        "type": "charts",
                        "charts": [
                            {
                                "type": "line",
                                "data": "monthly_health_trends",
                                "title": "월별 건강 지표 추이"
                            }
                        ]
                    }
                ]
            }
        }
        
        response = test_client.post("/api/v1/reports/templates/", json=custom_template)
        assert response.status_code == 201
        
        template_id = response.json()["id"]
        
        # 2. 템플릿을 사용한 보고서 생성
        report_generation_params = {
            "template_id": template_id,
            "parameters": {
                "start_date": "2024-01-01",
                "end_date": "2024-07-31",
                "departments": ["생산팀", "화학처리팀"]
            },
            "output_format": "html",
            "send_email": False
        }
        
        response = test_client.post("/api/v1/reports/generate-from-template", json=report_generation_params)
        assert response.status_code == 200
        
        # HTML 응답 검증
        assert response.headers["content-type"] == "text/html; charset=utf-8"
        
        # 3. 보고서 스케줄링
        schedule_data = {
            "template_id": template_id,
            "schedule_type": "recurring",
            "frequency": "monthly",
            "day_of_month": 5,
            "time": "09:00",
            "recipients": ["manager@company.com", "safety@company.com"],
            "format": "pdf",
            "active": True
        }
        
        response = test_client.post("/api/v1/reports/schedules/", json=schedule_data)
        assert response.status_code == 201
        
        schedule_id = response.json()["id"]
        
        # 4. 예약된 보고서 목록 조회
        response = test_client.get("/api/v1/reports/schedules/")
        assert response.status_code == 200
        
        schedules = response.json()
        assert len(schedules) >= 1
        assert any(s["id"] == schedule_id for s in schedules)
    
    async def test_data_visualization_and_analytics(self, test_client):
        """데이터 시각화 및 분석 테스트"""
        
        # 1. 건강 지표 트렌드 분석
        trend_analysis_params = {
            "analysis_type": "health_indicator_trends",
            "indicators": [
                "average_bmi",
                "blood_pressure_normal_rate",
                "abnormal_findings_rate",
                "health_exam_compliance"
            ],
            "period": "last_12_months",
            "granularity": "monthly",
            "breakdown_by": ["department", "age_group"],
            "include_forecast": True
        }
        
        response = test_client.post("/api/v1/analytics/trend-analysis", json=trend_analysis_params)
        assert response.status_code == 200
        
        trend_data = response.json()
        assert "trends" in trend_data
        assert "forecast" in trend_data
        assert "statistical_summary" in trend_data
        
        # 2. 위험 요인 상관 분석
        correlation_analysis_params = {
            "analysis_type": "risk_factor_correlation",
            "target_variable": "incident_occurrence",
            "potential_factors": [
                "overtime_hours",
                "safety_training_completion",
                "health_status",
                "work_environment_score",
                "experience_years"
            ],
            "statistical_methods": ["pearson", "spearman", "chi_square"],
            "significance_level": 0.05
        }
        
        response = test_client.post("/api/v1/analytics/correlation-analysis", json=correlation_analysis_params)
        assert response.status_code == 200
        
        correlation_results = response.json()
        assert "correlations" in correlation_results
        assert "significant_factors" in correlation_results
        assert "visualization_data" in correlation_results
        
        # 3. 예측 모델링
        predictive_model_params = {
            "model_type": "health_risk_prediction",
            "target": "future_health_issues",
            "features": [
                "age",
                "work_type",
                "exposure_history",
                "health_exam_results",
                "lifestyle_factors"
            ],
            "prediction_period": "next_6_months",
            "confidence_interval": 0.95
        }
        
        response = test_client.post("/api/v1/analytics/predictive-model", json=predictive_model_params)
        assert response.status_code == 200
        
        predictions = response.json()
        assert "risk_scores" in predictions
        assert "high_risk_workers" in predictions
        assert "recommended_interventions" in predictions
        
        # 4. 히트맵 생성
        heatmap_params = {
            "visualization_type": "risk_heatmap",
            "dimensions": {
                "x_axis": "work_location",
                "y_axis": "time_of_day"
            },
            "metric": "incident_frequency",
            "color_scale": "red_yellow_green",
            "include_annotations": True
        }
        
        response = test_client.post("/api/v1/analytics/generate-heatmap", json=heatmap_params)
        assert response.status_code == 200
        
        heatmap_data = response.json()
        assert "matrix_data" in heatmap_data
        assert "color_mapping" in heatmap_data
        assert "annotations" in heatmap_data
    
    async def test_executive_dashboard_kpis(self, test_client):
        """경영진 대시보드 KPI 테스트"""
        
        # 1. KPI 정의 및 목표 설정
        kpi_definitions = {
            "kpis": [
                {
                    "kpi_id": "ltifr",
                    "name": "Lost Time Injury Frequency Rate",
                    "formula": "(lost_time_injuries / total_hours_worked) * 1000000",
                    "target": 1.5,
                    "threshold_good": 1.0,
                    "threshold_warning": 2.0,
                    "frequency": "monthly"
                },
                {
                    "kpi_id": "health_exam_compliance",
                    "name": "건강진단 수검률",
                    "formula": "(completed_exams / required_exams) * 100",
                    "target": 100,
                    "threshold_good": 95,
                    "threshold_warning": 90,
                    "frequency": "quarterly"
                },
                {
                    "kpi_id": "safety_training_hours",
                    "name": "인당 안전교육 시간",
                    "formula": "total_training_hours / total_workers",
                    "target": 24,
                    "threshold_good": 20,
                    "threshold_warning": 16,
                    "frequency": "annual"
                }
            ]
        }
        
        response = test_client.post("/api/v1/dashboards/kpis/define", json=kpi_definitions)
        assert response.status_code == 201
        
        # 2. KPI 실시간 계산 및 조회
        response = test_client.get("/api/v1/dashboards/kpis/current")
        assert response.status_code == 200
        
        current_kpis = response.json()
        assert "ltifr" in current_kpis
        assert "health_exam_compliance" in current_kpis
        assert "safety_training_hours" in current_kpis
        
        # 각 KPI 상태 확인
        for kpi_id, kpi_data in current_kpis.items():
            assert "value" in kpi_data
            assert "status" in kpi_data  # good, warning, critical
            assert "trend" in kpi_data  # up, down, stable
            assert "vs_target_percent" in kpi_data
        
        # 3. KPI 스코어카드 생성
        scorecard_params = {
            "period": "2024-Q2",
            "include_trends": True,
            "include_benchmarks": True,
            "format": "interactive_html"
        }
        
        response = test_client.post("/api/v1/dashboards/kpis/scorecard", json=scorecard_params)
        assert response.status_code == 200
        
        # 4. KPI 드릴다운 분석
        drilldown_params = {
            "kpi_id": "ltifr",
            "breakdown_dimensions": ["department", "shift", "incident_type"],
            "time_period": "last_12_months",
            "include_root_causes": True
        }
        
        response = test_client.post("/api/v1/dashboards/kpis/drilldown", json=drilldown_params)
        assert response.status_code == 200
        
        drilldown_data = response.json()
        assert "breakdown_data" in drilldown_data
        assert "contributing_factors" in drilldown_data
        assert "improvement_opportunities" in drilldown_data
    
    async def test_mobile_dashboard_optimization(self, test_client):
        """모바일 대시보드 최적화 테스트"""
        
        # 1. 모바일 대시보드 설정
        mobile_dashboard_config = {
            "dashboard_type": "mobile",
            "layout": "responsive",
            "widgets": [
                {
                    "widget_id": "quick_stats",
                    "type": "summary_cards",
                    "priority": 1,
                    "data": ["today_incidents", "workers_on_site", "pending_actions"]
                },
                {
                    "widget_id": "alerts",
                    "type": "notification_list",
                    "priority": 2,
                    "max_items": 5,
                    "auto_refresh": True
                },
                {
                    "widget_id": "mini_charts",
                    "type": "sparklines",
                    "priority": 3,
                    "charts": ["weekly_trend", "monthly_comparison"]
                }
            ],
            "optimization": {
                "lazy_loading": True,
                "data_compression": True,
                "cache_duration": 300,
                "offline_mode": True
            }
        }
        
        response = test_client.post("/api/v1/dashboards/mobile/", json=mobile_dashboard_config)
        assert response.status_code == 201
        
        mobile_dashboard_id = response.json()["id"]
        
        # 2. 모바일 최적화된 데이터 요청
        response = test_client.get(
            f"/api/v1/dashboards/mobile/{mobile_dashboard_id}/data",
            headers={"X-Device-Type": "mobile", "X-Screen-Size": "small"}
        )
        assert response.status_code == 200
        
        mobile_data = response.json()
        assert "quick_stats" in mobile_data
        assert "data_size_kb" in mobile_data["_metadata"]
        assert mobile_data["_metadata"]["optimized"] == True
        
        # 3. 오프라인 데이터 패키지
        response = test_client.get(f"/api/v1/dashboards/mobile/{mobile_dashboard_id}/offline-package")
        assert response.status_code == 200
        
        offline_package = response.json()
        assert "cached_data" in offline_package
        assert "sync_timestamp" in offline_package
        assert "expiry_time" in offline_package
        
        # 4. 푸시 알림 설정
        push_config = {
            "dashboard_id": mobile_dashboard_id,
            "notifications": [
                {
                    "trigger": "critical_alert",
                    "conditions": {"severity": "critical"},
                    "message_template": "긴급: {alert_type} - {location}"
                },
                {
                    "trigger": "daily_summary",
                    "schedule": "18:00",
                    "message_template": "오늘의 안전보건 현황: 재해 {incidents}건, 점검 {inspections}건"
                }
            ],
            "device_tokens": ["device_token_1", "device_token_2"]
        }
        
        response = test_client.post("/api/v1/dashboards/mobile/push-notifications", json=push_config)
        assert response.status_code == 201
    
    async def test_report_export_and_sharing(self, test_client):
        """보고서 내보내기 및 공유 테스트"""
        
        # 1. 다양한 형식으로 보고서 내보내기
        export_formats = ["pdf", "excel", "csv", "json", "powerpoint"]
        
        for format in export_formats:
            export_params = {
                "report_type": "monthly_summary",
                "period": "2024-07",
                "format": format,
                "include_raw_data": format in ["excel", "csv", "json"]
            }
            
            response = test_client.post("/api/v1/reports/export", json=export_params)
            assert response.status_code == 200
            
            # 각 형식별 content-type 확인
            if format == "pdf":
                assert response.headers["content-type"] == "application/pdf"
            elif format == "excel":
                assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif format == "csv":
                assert response.headers["content-type"] == "text/csv"
            elif format == "json":
                assert response.headers["content-type"] == "application/json"
            elif format == "powerpoint":
                assert response.headers["content-type"] == "application/vnd.openxmlformats-officedocument.presentationml.presentation"
        
        # 2. 보고서 공유 링크 생성
        share_params = {
            "report_id": "monthly_report_2024_07",
            "access_type": "password_protected",
            "password": "secure123",
            "expiry_days": 7,
            "allowed_downloads": 5,
            "watermark": True,
            "track_access": True
        }
        
        response = test_client.post("/api/v1/reports/share", json=share_params)
        assert response.status_code == 201
        
        share_data = response.json()
        assert "share_link" in share_data
        assert "expiry_date" in share_data
        assert "access_code" in share_data
        
        # 3. 이메일 배포
        email_distribution = {
            "report_id": "monthly_report_2024_07",
            "recipients": [
                {"email": "ceo@company.com", "role": "executive"},
                {"email": "safety@company.com", "role": "manager"},
                {"email": "hr@company.com", "role": "viewer"}
            ],
            "subject": "2024년 7월 안전보건 월간 보고서",
            "body": "이번 달 안전보건 현황을 보고드립니다.",
            "attachments": ["pdf", "excel"],
            "schedule": "immediate"
        }
        
        response = test_client.post("/api/v1/reports/distribute", json=email_distribution)
        assert response.status_code == 200
        
        distribution_result = response.json()
        assert distribution_result["sent_count"] == 3
        assert "delivery_status" in distribution_result


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import sys
    import subprocess
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 보고서 및 대시보드 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 보고서 및 대시보드 통합 테스트 실패")
        sys.exit(1)