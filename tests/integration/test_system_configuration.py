"""
시스템 설정 및 관리 통합 테스트
System Configuration and Management Integration Tests
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestSystemConfiguration:
    """시스템 설정, 사용자 관리, 권한 설정 등 전체 시스템 구성 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_system_config(self):
        """샘플 시스템 설정"""
        return {
            "general": {
                "company_name": "안전건설(주)",
                "business_registration": "123-45-67890",
                "industry_type": "construction",
                "employee_count": 150,
                "timezone": "Asia/Seoul",
                "language": "ko",
                "date_format": "YYYY-MM-DD",
                "currency": "KRW"
            },
            "safety_health": {
                "safety_manager": "김안전",
                "health_manager": "이보건",
                "emergency_contact": "119",
                "hospital_contact": "02-1234-5678",
                "kosha_registration": "2024-001234",
                "certification_date": "2024-01-15"
            },
            "compliance": {
                "health_exam_cycle_months": 12,
                "special_exam_cycle_months": 6,
                "safety_education_hours": 16,
                "document_retention_years": 30,
                "audit_frequency": "quarterly"
            },
            "notifications": {
                "email_enabled": True,
                "sms_enabled": True,
                "push_enabled": True,
                "webhook_enabled": False,
                "default_recipients": ["safety@company.com", "hr@company.com"]
            }
        }
    
    async def test_system_initial_setup_workflow(self, test_client, sample_system_config):
        """시스템 초기 설정 워크플로우 테스트"""
        
        # 1. 시스템 초기화 상태 확인
        response = test_client.get("/api/v1/system/setup-status")
        assert response.status_code == 200
        
        setup_status = response.json()
        
        # 2. 기본 시스템 설정
        response = test_client.post("/api/v1/system/configure", json=sample_system_config)
        assert response.status_code == 201
        
        config_result = response.json()
        assert config_result["status"] == "configured"
        assert config_result["company_name"] == "안전건설(주)"
        
        # 3. 관리자 계정 생성
        admin_account = {
            "username": "admin",
            "password": "SecurePassword123!",
            "email": "admin@company.com",
            "full_name": "시스템 관리자",
            "role": "system_admin",
            "department": "IT팀",
            "permissions": ["all"]
        }
        
        response = test_client.post("/api/v1/users/create-admin", json=admin_account)
        assert response.status_code == 201
        
        admin_data = response.json()
        admin_id = admin_data["id"]
        assert admin_data["role"] == "system_admin"
        
        # 4. 부서 구조 설정
        departments = {
            "departments": [
                {
                    "name": "경영지원팀",
                    "code": "MGT",
                    "manager": "김경영",
                    "parent": None
                },
                {
                    "name": "안전관리팀",
                    "code": "SAF",
                    "manager": "김안전",
                    "parent": "MGT"
                },
                {
                    "name": "생산1팀",
                    "code": "PRD1",
                    "manager": "이생산",
                    "parent": None
                },
                {
                    "name": "생산2팀",
                    "code": "PRD2",
                    "manager": "박생산",
                    "parent": None
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/departments", json=departments)
        assert response.status_code == 201
        
        # 5. 초기 설정 완료
        response = test_client.post("/api/v1/system/complete-setup")
        assert response.status_code == 200
        
        completion_result = response.json()
        assert completion_result["setup_completed"] == True
        assert "setup_timestamp" in completion_result
    
    async def test_user_management_and_roles(self, test_client):
        """사용자 관리 및 역할 설정 테스트"""
        
        # 1. 역할 정의
        roles = [
            {
                "role_name": "safety_manager",
                "display_name": "안전관리자",
                "permissions": [
                    "view_all_workers",
                    "manage_incidents",
                    "create_reports",
                    "manage_safety_education",
                    "view_dashboards"
                ],
                "data_access_level": "all_departments"
            },
            {
                "role_name": "health_manager",
                "display_name": "보건관리자",
                "permissions": [
                    "view_all_workers",
                    "manage_health_exams",
                    "manage_abnormal_findings",
                    "create_health_reports",
                    "view_dashboards"
                ],
                "data_access_level": "all_departments"
            },
            {
                "role_name": "department_manager",
                "display_name": "부서장",
                "permissions": [
                    "view_department_workers",
                    "approve_requests",
                    "view_department_reports",
                    "manage_department_schedule"
                ],
                "data_access_level": "own_department"
            },
            {
                "role_name": "worker",
                "display_name": "일반직원",
                "permissions": [
                    "view_own_data",
                    "submit_requests",
                    "view_education_schedule"
                ],
                "data_access_level": "self_only"
            }
        ]
        
        created_roles = []
        for role in roles:
            response = test_client.post("/api/v1/roles/", json=role)
            assert response.status_code == 201
            created_roles.append(response.json())
        
        # 2. 사용자 일괄 등록
        bulk_users = {
            "users": [
                {
                    "username": "kim.safety",
                    "email": "kim.safety@company.com",
                    "full_name": "김안전",
                    "department": "안전관리팀",
                    "role": "safety_manager",
                    "employee_id": "EMP001"
                },
                {
                    "username": "lee.health",
                    "email": "lee.health@company.com",
                    "full_name": "이보건",
                    "department": "안전관리팀",
                    "role": "health_manager",
                    "employee_id": "EMP002"
                },
                {
                    "username": "park.prod",
                    "email": "park.prod@company.com",
                    "full_name": "박생산",
                    "department": "생산1팀",
                    "role": "department_manager",
                    "employee_id": "EMP003"
                }
            ],
            "send_welcome_email": True,
            "temporary_password": True
        }
        
        response = test_client.post("/api/v1/users/bulk-create", json=bulk_users)
        assert response.status_code == 201
        
        bulk_result = response.json()
        assert bulk_result["created_count"] == 3
        assert len(bulk_result["created_users"]) == 3
        
        # 3. 사용자 권한 커스터마이징
        custom_permissions = {
            "user_id": bulk_result["created_users"][0]["id"],
            "additional_permissions": [
                "manage_chemical_substances",
                "approve_purchase_orders"
            ],
            "restricted_permissions": [
                "delete_records"
            ],
            "expiry_date": (datetime.now() + timedelta(days=90)).isoformat()
        }
        
        response = test_client.post("/api/v1/users/custom-permissions", json=custom_permissions)
        assert response.status_code == 200
        
        # 4. 사용자 그룹 생성
        user_group = {
            "group_name": "안전보건위원회",
            "description": "산업안전보건위원회 구성원",
            "members": [
                bulk_result["created_users"][0]["id"],
                bulk_result["created_users"][1]["id"]
            ],
            "group_permissions": [
                "view_all_reports",
                "create_meeting_minutes",
                "approve_safety_policies"
            ]
        }
        
        response = test_client.post("/api/v1/users/groups", json=user_group)
        assert response.status_code == 201
        
        group_id = response.json()["id"]
        
        # 5. 접근 제어 매트릭스 조회
        response = test_client.get("/api/v1/system/access-matrix")
        assert response.status_code == 200
        
        access_matrix = response.json()
        assert "roles" in access_matrix
        assert "permissions" in access_matrix
        assert "data_access_levels" in access_matrix
    
    async def test_system_preferences_and_localization(self, test_client):
        """시스템 환경설정 및 현지화 테스트"""
        
        # 1. 전역 환경설정
        global_preferences = {
            "locale": {
                "language": "ko",
                "country": "KR",
                "timezone": "Asia/Seoul",
                "date_format": "YYYY년 MM월 DD일",
                "time_format": "24h",
                "number_format": {
                    "decimal_separator": ".",
                    "thousand_separator": ",",
                    "currency_symbol": "₩",
                    "currency_position": "prefix"
                }
            },
            "working_hours": {
                "start_time": "08:00",
                "end_time": "17:00",
                "lunch_start": "12:00",
                "lunch_end": "13:00",
                "working_days": ["월", "화", "수", "목", "금"],
                "holidays": [
                    {"date": "2024-01-01", "name": "신정"},
                    {"date": "2024-02-09", "name": "설날연휴"},
                    {"date": "2024-02-10", "name": "설날"},
                    {"date": "2024-02-11", "name": "설날연휴"}
                ]
            },
            "ui_preferences": {
                "theme": "light",
                "sidebar_collapsed": False,
                "notification_position": "top-right",
                "table_rows_per_page": 20,
                "chart_animations": True
            }
        }
        
        response = test_client.put("/api/v1/system/preferences", json=global_preferences)
        assert response.status_code == 200
        
        # 2. 알림 템플릿 설정
        notification_templates = {
            "templates": [
                {
                    "template_id": "health_exam_reminder",
                    "name": "건강진단 알림",
                    "channel": "email",
                    "subject": "[{company_name}] {worker_name}님, 건강진단 예정일 안내",
                    "body": """
                    안녕하세요, {worker_name}님.
                    
                    귀하의 건강진단 예정일이 {exam_date}입니다.
                    장소: {medical_institution}
                    시간: {exam_time}
                    
                    준비사항: {preparation_notes}
                    
                    문의사항은 보건관리자에게 연락 주시기 바랍니다.
                    """,
                    "variables": ["worker_name", "exam_date", "medical_institution", "exam_time", "preparation_notes"]
                },
                {
                    "template_id": "incident_alert",
                    "name": "재해 발생 긴급 알림",
                    "channel": "sms",
                    "body": "[긴급] {incident_location}에서 {incident_type} 발생. 상세: {brief_description}",
                    "variables": ["incident_location", "incident_type", "brief_description"]
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/notification-templates", json=notification_templates)
        assert response.status_code == 201
        
        # 3. 커스텀 필드 정의
        custom_fields = {
            "entity": "worker",
            "fields": [
                {
                    "field_name": "blood_type",
                    "display_name": "혈액형",
                    "field_type": "select",
                    "options": ["A", "B", "O", "AB"],
                    "required": False,
                    "category": "medical_info"
                },
                {
                    "field_name": "safety_certification",
                    "display_name": "안전관리 자격증",
                    "field_type": "text",
                    "max_length": 100,
                    "required": False,
                    "category": "qualifications"
                },
                {
                    "field_name": "emergency_contact_relationship",
                    "display_name": "비상연락처 관계",
                    "field_type": "text",
                    "required": True,
                    "category": "emergency_info"
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/custom-fields", json=custom_fields)
        assert response.status_code == 201
        
        # 4. 용어 사전 설정 (산업안전보건 전문용어)
        terminology = {
            "terms": [
                {
                    "term": "LTIFR",
                    "korean": "휴업재해율",
                    "definition": "100만 근로시간당 휴업재해 발생 건수",
                    "category": "safety_metrics"
                },
                {
                    "term": "MSDS",
                    "korean": "물질안전보건자료",
                    "definition": "화학물질의 유해·위험성, 응급조치요령, 취급방법 등을 설명한 자료",
                    "category": "chemical_safety"
                },
                {
                    "term": "TWA",
                    "korean": "시간가중평균노출기준",
                    "definition": "1일 8시간 작업을 기준으로 한 평균 노출 농도",
                    "category": "exposure_limits"
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/terminology", json=terminology)
        assert response.status_code == 201
    
    async def test_integration_and_api_management(self, test_client):
        """외부 시스템 통합 및 API 관리 테스트"""
        
        # 1. API 키 생성
        api_key_request = {
            "name": "ERP 시스템 연동",
            "description": "인사 정보 동기화를 위한 API 키",
            "permissions": [
                "read_workers",
                "read_departments",
                "write_attendance"
            ],
            "ip_whitelist": ["192.168.1.100", "192.168.1.101"],
            "rate_limit": {
                "requests_per_minute": 60,
                "requests_per_day": 10000
            },
            "expiry_date": (datetime.now() + timedelta(days=365)).isoformat()
        }
        
        response = test_client.post("/api/v1/system/api-keys", json=api_key_request)
        assert response.status_code == 201
        
        api_key_data = response.json()
        api_key = api_key_data["key"]
        assert len(api_key) >= 32
        
        # 2. 웹훅 설정
        webhook_config = {
            "webhooks": [
                {
                    "name": "재해 발생 알림",
                    "url": "https://external-system.com/incident-webhook",
                    "events": ["incident_created", "incident_updated"],
                    "headers": {
                        "X-API-Key": "external-system-key"
                    },
                    "retry_policy": {
                        "max_retries": 3,
                        "retry_interval_seconds": 60
                    }
                },
                {
                    "name": "건강진단 결과 동기화",
                    "url": "https://hr-system.com/health-exam-webhook",
                    "events": ["health_exam_completed"],
                    "payload_template": {
                        "worker_id": "{{worker.employee_id}}",
                        "exam_result": "{{exam.overall_result}}",
                        "exam_date": "{{exam.exam_date}}"
                    }
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/webhooks", json=webhook_config)
        assert response.status_code == 201
        
        webhook_ids = [w["id"] for w in response.json()["webhooks"]]
        
        # 3. 외부 시스템 연동 설정
        integration_config = {
            "integrations": [
                {
                    "system": "kosha_reporting",
                    "type": "api",
                    "config": {
                        "base_url": "https://api.kosha.or.kr",
                        "auth_type": "oauth2",
                        "client_id": "company_client_id",
                        "sync_frequency": "daily",
                        "data_mappings": {
                            "worker_id": "employee_number",
                            "incident_type": "accident_classification"
                        }
                    }
                },
                {
                    "system": "hospital_ehr",
                    "type": "sftp",
                    "config": {
                        "host": "hospital-sftp.com",
                        "port": 22,
                        "username": "company_user",
                        "directory": "/health_exam_results/",
                        "file_pattern": "*.xml",
                        "polling_interval_minutes": 30
                    }
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/integrations", json=integration_config)
        assert response.status_code == 201
        
        # 4. API 사용량 모니터링
        response = test_client.get(f"/api/v1/system/api-keys/{api_key}/usage")
        assert response.status_code == 200
        
        usage_data = response.json()
        assert "total_requests" in usage_data
        assert "requests_today" in usage_data
        assert "rate_limit_status" in usage_data
        
        # 5. 통합 상태 확인
        response = test_client.get("/api/v1/system/integrations/status")
        assert response.status_code == 200
        
        integration_status = response.json()
        assert "kosha_reporting" in integration_status
        assert "hospital_ehr" in integration_status
    
    async def test_backup_and_recovery_configuration(self, test_client):
        """백업 및 복구 설정 테스트"""
        
        # 1. 백업 정책 설정
        backup_policy = {
            "automatic_backup": {
                "enabled": True,
                "schedule": {
                    "daily": {
                        "time": "02:00",
                        "retention_days": 7
                    },
                    "weekly": {
                        "day": "sunday",
                        "time": "03:00",
                        "retention_weeks": 4
                    },
                    "monthly": {
                        "day": 1,
                        "time": "04:00",
                        "retention_months": 12
                    }
                },
                "backup_items": [
                    "database",
                    "uploaded_files",
                    "configuration",
                    "audit_logs"
                ],
                "storage_location": {
                    "type": "s3",
                    "bucket": "company-backups",
                    "region": "ap-northeast-2",
                    "encryption": True
                }
            },
            "notifications": {
                "on_success": ["admin@company.com"],
                "on_failure": ["admin@company.com", "it@company.com"]
            }
        }
        
        response = test_client.post("/api/v1/system/backup-policy", json=backup_policy)
        assert response.status_code == 201
        
        # 2. 수동 백업 실행
        manual_backup = {
            "backup_type": "full",
            "description": "시스템 업그레이드 전 백업",
            "include_items": ["database", "configuration"],
            "compress": True,
            "encrypt": True
        }
        
        response = test_client.post("/api/v1/system/backup/manual", json=manual_backup)
        assert response.status_code == 202  # Accepted
        
        backup_job_id = response.json()["job_id"]
        
        # 3. 백업 진행 상태 확인
        response = test_client.get(f"/api/v1/system/backup/status/{backup_job_id}")
        assert response.status_code == 200
        
        backup_status = response.json()
        assert "progress_percent" in backup_status
        assert "estimated_completion" in backup_status
        
        # 4. 백업 이력 조회
        response = test_client.get("/api/v1/system/backup/history?limit=10")
        assert response.status_code == 200
        
        backup_history = response.json()
        assert len(backup_history) >= 1
        assert backup_history[0]["job_id"] == backup_job_id
        
        # 5. 복구 계획 수립
        recovery_plan = {
            "plan_name": "재해 복구 계획",
            "rto_hours": 4,  # Recovery Time Objective
            "rpo_hours": 1,  # Recovery Point Objective
            "priority_systems": [
                "authentication",
                "worker_database",
                "incident_reporting"
            ],
            "recovery_steps": [
                {
                    "step": 1,
                    "action": "인프라 복구",
                    "responsible": "IT팀",
                    "estimated_minutes": 30
                },
                {
                    "step": 2,
                    "action": "데이터베이스 복원",
                    "responsible": "DBA",
                    "estimated_minutes": 60
                },
                {
                    "step": 3,
                    "action": "애플리케이션 재시작",
                    "responsible": "DevOps",
                    "estimated_minutes": 30
                }
            ],
            "test_schedule": "quarterly"
        }
        
        response = test_client.post("/api/v1/system/recovery-plan", json=recovery_plan)
        assert response.status_code == 201
    
    async def test_audit_and_compliance_configuration(self, test_client):
        """감사 및 규정 준수 설정 테스트"""
        
        # 1. 감사 로그 설정
        audit_config = {
            "enabled": True,
            "log_level": "detailed",
            "tracked_events": [
                "user_login",
                "user_logout",
                "data_access",
                "data_modification",
                "configuration_change",
                "permission_change",
                "report_generation",
                "data_export"
            ],
            "retention_days": 2555,  # 7년 (법적 요구사항)
            "storage": {
                "type": "database_and_file",
                "database_table": "audit_logs",
                "file_location": "/var/log/safework/audit/",
                "rotation": "daily",
                "compression": True
            },
            "alerts": {
                "suspicious_activity": {
                    "enabled": True,
                    "rules": [
                        {
                            "rule": "multiple_failed_logins",
                            "threshold": 5,
                            "time_window_minutes": 10
                        },
                        {
                            "rule": "unusual_access_pattern",
                            "ml_based": True
                        }
                    ],
                    "notify": ["security@company.com"]
                }
            }
        }
        
        response = test_client.put("/api/v1/system/audit-config", json=audit_config)
        assert response.status_code == 200
        
        # 2. 규정 준수 체크리스트
        compliance_checklist = {
            "regulations": [
                {
                    "name": "산업안전보건법",
                    "version": "2024",
                    "requirements": [
                        {
                            "requirement_id": "OSH_001",
                            "description": "안전보건관리책임자 선임",
                            "compliance_status": "compliant",
                            "evidence": "선임 공문 및 신고 접수증"
                        },
                        {
                            "requirement_id": "OSH_002",
                            "description": "정기 안전교육 실시",
                            "compliance_status": "compliant",
                            "evidence": "교육 실시 기록 및 수료증"
                        }
                    ]
                },
                {
                    "name": "개인정보보호법",
                    "version": "2024",
                    "requirements": [
                        {
                            "requirement_id": "PIPA_001",
                            "description": "개인정보 처리방침 공개",
                            "compliance_status": "compliant",
                            "evidence": "홈페이지 게시"
                        }
                    ]
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/compliance-checklist", json=compliance_checklist)
        assert response.status_code == 201
        
        # 3. 정기 감사 일정
        audit_schedule = {
            "internal_audits": [
                {
                    "audit_type": "system_security",
                    "frequency": "quarterly",
                    "next_date": "2024-10-01",
                    "auditor": "IT보안팀"
                },
                {
                    "audit_type": "data_integrity",
                    "frequency": "monthly",
                    "next_date": "2024-08-01",
                    "auditor": "품질관리팀"
                }
            ],
            "external_audits": [
                {
                    "audit_type": "kosha_certification",
                    "frequency": "annual",
                    "next_date": "2025-01-15",
                    "auditor": "한국산업안전보건공단"
                }
            ]
        }
        
        response = test_client.post("/api/v1/system/audit-schedule", json=audit_schedule)
        assert response.status_code == 201
        
        # 4. 감사 보고서 생성
        audit_report_request = {
            "report_type": "quarterly_audit",
            "period": {
                "start_date": "2024-04-01",
                "end_date": "2024-06-30"
            },
            "include_sections": [
                "access_logs_summary",
                "data_modifications",
                "security_incidents",
                "compliance_status",
                "recommendations"
            ]
        }
        
        response = test_client.post("/api/v1/system/audit-report", json=audit_report_request)
        assert response.status_code == 200
        
        # 5. 규정 준수 대시보드 데이터
        response = test_client.get("/api/v1/system/compliance-dashboard")
        assert response.status_code == 200
        
        compliance_data = response.json()
        assert "overall_compliance_score" in compliance_data
        assert "by_regulation" in compliance_data
        assert "upcoming_audits" in compliance_data
        assert "action_items" in compliance_data


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 시스템 설정 및 관리 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 시스템 설정 및 관리 통합 테스트 실패")
        sys.exit(1)