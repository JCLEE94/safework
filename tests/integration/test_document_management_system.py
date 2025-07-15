"""
문서 관리 및 PDF 생성 시스템 통합 테스트
Document Management and PDF Generation System Integration Tests
"""

import asyncio
import base64
import io
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestDocumentManagementSystem:
    """문서 관리부터 PDF 생성까지 전체 시스템 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_worker_data(self):
        """샘플 근로자 데이터"""
        return {
            "name": "김문서",
            "gender": "male",
            "birth_date": "1988-03-25",
            "employee_id": "EMP003",
            "department": "문서관리팀",
            "position": "문서관리자",
            "hire_date": "2021-01-01",
            "phone": "010-3333-4444",
            "email": "kim.document@company.com"
        }
    
    @pytest.fixture
    def sample_health_exam_data(self):
        """샘플 건강진단 데이터"""
        return {
            "exam_type": "general",
            "exam_date": datetime.now().isoformat(),
            "overall_result": "정상",
            "detailed_results": {
                "신장": "175cm",
                "체중": "70kg",
                "혈압": "120/80",
                "혈당": "85mg/dL"
            },
            "doctor_opinion": "건강 상태 양호",
            "medical_institution": "서울대학교병원"
        }
    
    async def test_pdf_form_generation_workflow(self, test_client, sample_worker_data, sample_health_exam_data):
        """PDF 양식 생성 워크플로우 테스트"""
        
        # 1. 근로자 및 건강진단 데이터 준비
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        exam_data = sample_health_exam_data.copy()
        exam_data["worker_id"] = worker_id
        
        response = test_client.post("/api/v1/health-exams/", json=exam_data)
        assert response.status_code == 201
        exam_id = response.json()["id"]
        
        # 2. 건강진단 결과서 PDF 생성
        pdf_generation_data = {
            "form_type": "health_checkup_report",
            "data_source": {
                "worker_id": worker_id,
                "health_exam_id": exam_id
            },
            "options": {
                "include_company_header": True,
                "include_qr_code": True,
                "language": "korean",
                "format": "A4"
            }
        }
        
        response = test_client.post("/api/v1/documents/generate-pdf", json=pdf_generation_data)
        assert response.status_code == 200
        
        # PDF 응답 검증
        assert response.headers["content-type"] == "application/pdf"
        assert len(response.content) > 1000  # PDF 파일이 생성되었는지 확인
        
        # 3. 작업환경측정 결과서 PDF 생성
        measurement_pdf_data = {
            "form_type": "work_environment_measurement_report",
            "data_source": {
                "workplace_id": 1,
                "measurement_date": "2024-07-01"
            },
            "options": {
                "include_charts": True,
                "include_recommendations": True,
                "digital_signature": True
            }
        }
        
        response = test_client.post("/api/v1/documents/generate-pdf", json=measurement_pdf_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # 4. 화학물질 MSDS 요약서 PDF 생성
        msds_pdf_data = {
            "form_type": "chemical_msds_summary",
            "data_source": {
                "chemical_id": 1
            },
            "options": {
                "include_ghs_pictograms": True,
                "include_emergency_procedures": True,
                "language": "korean"
            }
        }
        
        response = test_client.post("/api/v1/documents/generate-pdf", json=msds_pdf_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
        
        # 5. 산업재해 신고서 PDF 생성
        accident_pdf_data = {
            "form_type": "industrial_accident_report",
            "data_source": {
                "accident_id": 1,
                "worker_id": worker_id
            },
            "options": {
                "include_photos": True,
                "include_witness_statements": True,
                "official_seal": True
            }
        }
        
        response = test_client.post("/api/v1/documents/generate-pdf", json=accident_pdf_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    async def test_document_template_management(self, test_client):
        """문서 템플릿 관리 테스트"""
        
        # 1. 새로운 문서 템플릿 등록
        template_data = {
            "template_name": "건강관리대장",
            "template_type": "health_management_ledger",
            "description": "근로자 건강관리 현황을 기록하는 대장",
            "fields": [
                {
                    "field_name": "worker_name",
                    "field_type": "text",
                    "required": True,
                    "coordinates": {"x": 100, "y": 200},
                    "max_length": 20
                },
                {
                    "field_name": "employee_id",
                    "field_type": "text",
                    "required": True,
                    "coordinates": {"x": 250, "y": 200},
                    "max_length": 10
                },
                {
                    "field_name": "health_exam_date",
                    "field_type": "date",
                    "required": True,
                    "coordinates": {"x": 350, "y": 200},
                    "format": "YYYY-MM-DD"
                },
                {
                    "field_name": "health_status",
                    "field_type": "select",
                    "required": True,
                    "coordinates": {"x": 450, "y": 200},
                    "options": ["정상", "요관찰", "유소견자"]
                }
            ],
            "page_size": "A4",
            "orientation": "portrait",
            "margins": {"top": 20, "bottom": 20, "left": 20, "right": 20}
        }
        
        response = test_client.post("/api/v1/documents/templates/", json=template_data)
        assert response.status_code == 201
        
        template_id = response.json()["id"]
        
        # 2. 템플릿 상세 조회
        response = test_client.get(f"/api/v1/documents/templates/{template_id}")
        assert response.status_code == 200
        
        template_detail = response.json()
        assert template_detail["template_name"] == "건강관리대장"
        assert len(template_detail["fields"]) == 4
        
        # 3. 템플릿 목록 조회
        response = test_client.get("/api/v1/documents/templates/")
        assert response.status_code == 200
        
        templates = response.json()
        assert len(templates) >= 1
        assert any(t["id"] == template_id for t in templates)
        
        # 4. 템플릿 수정
        update_data = {
            "description": "근로자 건강관리 현황을 상세히 기록하는 대장 (개정판)",
            "fields": template_data["fields"] + [
                {
                    "field_name": "follow_up_required",
                    "field_type": "checkbox",
                    "required": False,
                    "coordinates": {"x": 550, "y": 200}
                }
            ]
        }
        
        response = test_client.put(f"/api/v1/documents/templates/{template_id}", json=update_data)
        assert response.status_code == 200
        
        # 5. 템플릿을 사용한 문서 생성
        document_data = {
            "template_id": template_id,
            "data": {
                "worker_name": "김문서",
                "employee_id": "EMP003",
                "health_exam_date": "2024-07-01",
                "health_status": "정상",
                "follow_up_required": False
            }
        }
        
        response = test_client.post("/api/v1/documents/generate-from-template", json=document_data)
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
    
    async def test_document_version_control_and_approval(self, test_client):
        """문서 버전 관리 및 승인 워크플로우 테스트"""
        
        # 1. 문서 초안 생성
        draft_document_data = {
            "document_type": "safety_policy",
            "title": "화학물질 취급 안전정책",
            "content": {
                "sections": [
                    {
                        "title": "1. 목적",
                        "content": "본 정책은 화학물질 취급 시 안전을 확보하기 위함"
                    },
                    {
                        "title": "2. 적용 범위",
                        "content": "모든 화학물질 취급 작업자에게 적용"
                    },
                    {
                        "title": "3. 안전 절차",
                        "content": "화학물질 취급 전 MSDS 확인 필수"
                    }
                ]
            },
            "author": "안전관리자",
            "department": "안전관리팀",
            "status": "draft"
        }
        
        response = test_client.post("/api/v1/documents/create-draft", json=draft_document_data)
        assert response.status_code == 201
        
        document_id = response.json()["id"]
        version = response.json()["version"]
        
        # 2. 문서 검토 요청
        review_request_data = {
            "document_id": document_id,
            "reviewers": [
                {
                    "reviewer_id": "reviewer_001",
                    "reviewer_name": "김검토자",
                    "review_type": "technical_review",
                    "due_date": (datetime.now() + timedelta(days=7)).isoformat()
                },
                {
                    "reviewer_id": "reviewer_002",
                    "reviewer_name": "박승인자",
                    "review_type": "managerial_review",
                    "due_date": (datetime.now() + timedelta(days=10)).isoformat()
                }
            ],
            "review_instructions": "화학물질 관련 최신 법규 준수 여부 확인"
        }
        
        response = test_client.post("/api/v1/documents/request-review", json=review_request_data)
        assert response.status_code == 201
        
        # 3. 검토 의견 제출
        review_feedback_data = {
            "document_id": document_id,
            "reviewer_id": "reviewer_001",
            "review_result": "approved_with_changes",
            "comments": [
                {
                    "section": "3. 안전 절차",
                    "comment": "개인보호구 착용 절차 추가 필요",
                    "type": "modification_required"
                },
                {
                    "section": "2. 적용 범위",
                    "comment": "외부 업체 작업자도 포함하도록 수정",
                    "type": "modification_required"
                }
            ],
            "overall_rating": 4,
            "review_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/documents/submit-review", json=review_feedback_data)
        assert response.status_code == 201
        
        # 4. 문서 수정 및 새 버전 생성
        revised_content = {
            "sections": [
                {
                    "title": "1. 목적",
                    "content": "본 정책은 화학물질 취급 시 안전을 확보하기 위함"
                },
                {
                    "title": "2. 적용 범위",
                    "content": "모든 화학물질 취급 작업자 및 외부 업체 작업자에게 적용"
                },
                {
                    "title": "3. 안전 절차",
                    "content": "화학물질 취급 전 MSDS 확인 및 개인보호구 착용 필수"
                },
                {
                    "title": "4. 개인보호구",
                    "content": "화학물질별 적절한 개인보호구 선택 및 착용"
                }
            ]
        }
        
        revision_data = {
            "document_id": document_id,
            "content": revised_content,
            "revision_notes": "검토 의견 반영: 적용 범위 확장, 개인보호구 절차 추가",
            "revised_by": "안전관리자"
        }
        
        response = test_client.post("/api/v1/documents/create-revision", json=revision_data)
        assert response.status_code == 201
        
        new_version = response.json()["version"]
        assert new_version > version
        
        # 5. 최종 승인
        approval_data = {
            "document_id": document_id,
            "version": new_version,
            "approver_id": "approver_001",
            "approver_name": "이승인자",
            "approval_decision": "approved",
            "approval_date": datetime.now().isoformat(),
            "effective_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "approval_comments": "모든 검토 의견이 적절히 반영됨"
        }
        
        response = test_client.post("/api/v1/documents/approve", json=approval_data)
        assert response.status_code == 200
        
        # 6. 문서 이력 조회
        response = test_client.get(f"/api/v1/documents/{document_id}/history")
        assert response.status_code == 200
        
        document_history = response.json()
        assert len(document_history) >= 2  # 초안 + 수정본
        assert document_history[-1]["status"] == "approved"
    
    async def test_digital_signature_and_security(self, test_client):
        """전자서명 및 보안 테스트"""
        
        # 1. 전자서명 인증서 등록
        certificate_data = {
            "certificate_type": "digital_signature",
            "owner_id": "signer_001",
            "owner_name": "김서명자",
            "certificate_data": "-----BEGIN CERTIFICATE-----\nMIIC...(인증서 데이터)...-----END CERTIFICATE-----",
            "private_key_hash": "SHA256_HASH_VALUE",
            "valid_from": datetime.now().isoformat(),
            "valid_until": (datetime.now() + timedelta(days=365)).isoformat(),
            "issuer": "한국전자인증",
            "serial_number": "CERT123456789"
        }
        
        response = test_client.post("/api/v1/documents/certificates/register", json=certificate_data)
        assert response.status_code == 201
        
        certificate_id = response.json()["id"]
        
        # 2. 문서에 전자서명 적용
        signature_data = {
            "document_id": 1,
            "certificate_id": certificate_id,
            "signature_position": {"page": 1, "x": 400, "y": 100},
            "signature_reason": "문서 승인",
            "signature_location": "서울사무소",
            "timestamp_server": "http://timestamp.ca.go.kr"
        }
        
        response = test_client.post("/api/v1/documents/apply-signature", json=signature_data)
        assert response.status_code == 200
        
        signed_document = response.json()
        assert signed_document["signature_applied"] == True
        assert "signature_id" in signed_document
        
        # 3. 서명 검증
        verification_data = {
            "document_id": 1,
            "signature_id": signed_document["signature_id"]
        }
        
        response = test_client.post("/api/v1/documents/verify-signature", json=verification_data)
        assert response.status_code == 200
        
        verification_result = response.json()
        assert verification_result["signature_valid"] == True
        assert verification_result["certificate_valid"] == True
        assert verification_result["document_integrity"] == True
        
        # 4. 문서 암호화
        encryption_data = {
            "document_id": 1,
            "encryption_level": "AES-256",
            "access_control": {
                "authorized_users": ["user_001", "user_002"],
                "authorized_roles": ["manager", "safety_officer"],
                "expiry_date": (datetime.now() + timedelta(days=30)).isoformat()
            },
            "password_protection": True
        }
        
        response = test_client.post("/api/v1/documents/encrypt", json=encryption_data)
        assert response.status_code == 200
        
        # 5. 감사 로그 조회
        response = test_client.get(f"/api/v1/documents/1/audit-log")
        assert response.status_code == 200
        
        audit_log = response.json()
        assert len(audit_log) > 0
        assert any(log["action"] == "signature_applied" for log in audit_log)
        assert any(log["action"] == "document_encrypted" for log in audit_log)
    
    async def test_document_archival_and_retention(self, test_client):
        """문서 보관 및 보존 기간 관리 테스트"""
        
        # 1. 문서 보존 정책 설정
        retention_policy_data = {
            "document_type": "health_examination_records",
            "retention_period_years": 30,
            "legal_basis": "산업안전보건법 시행규칙 제98조",
            "archival_schedule": {
                "active_period_years": 3,
                "inactive_storage_years": 27,
                "destruction_allowed": False
            },
            "storage_requirements": {
                "format": "digital",
                "backup_required": True,
                "access_control": "restricted",
                "audit_trail": True
            }
        }
        
        response = test_client.post("/api/v1/documents/retention-policies/", json=retention_policy_data)
        assert response.status_code == 201
        
        policy_id = response.json()["id"]
        
        # 2. 보존 기간이 임박한 문서 조회
        response = test_client.get("/api/v1/documents/retention/expiring?days=30")
        assert response.status_code == 200
        
        expiring_documents = response.json()
        
        # 3. 문서 아카이브 처리
        archive_data = {
            "document_ids": [1, 2, 3],
            "archive_reason": "보존 기간 만료",
            "archive_location": "장기보관소",
            "archive_date": datetime.now().isoformat(),
            "access_restrictions": {
                "approval_required": True,
                "authorized_personnel": ["archivist", "legal_officer"]
            }
        }
        
        response = test_client.post("/api/v1/documents/archive", json=archive_data)
        assert response.status_code == 200
        
        archive_result = response.json()
        assert archive_result["archived_count"] == 3
        
        # 4. 아카이브된 문서 조회
        response = test_client.get("/api/v1/documents/archived")
        assert response.status_code == 200
        
        archived_documents = response.json()
        assert len(archived_documents) >= 3
        
        # 5. 문서 파기 승인 프로세스
        destruction_request_data = {
            "document_ids": [10, 11, 12],
            "destruction_reason": "보존 기간 만료",
            "legal_review_required": True,
            "requested_by": "records_manager",
            "request_date": datetime.now().isoformat()
        }
        
        response = test_client.post("/api/v1/documents/request-destruction", json=destruction_request_data)
        assert response.status_code == 201
        
        destruction_request_id = response.json()["id"]
        
        # 파기 승인
        destruction_approval_data = {
            "request_id": destruction_request_id,
            "approval_decision": "approved",
            "legal_reviewer": "legal_officer",
            "approval_date": datetime.now().isoformat(),
            "conditions": ["감사 로그 보존", "파기 인증서 발급"]
        }
        
        response = test_client.post("/api/v1/documents/approve-destruction", json=destruction_approval_data)
        assert response.status_code == 200
    
    async def test_document_search_and_analytics(self, test_client):
        """문서 검색 및 분석 테스트"""
        
        # 1. 고급 문서 검색
        search_criteria = {
            "query": "화학물질 안전",
            "document_types": ["policy", "procedure", "msds"],
            "date_range": {
                "from": "2024-01-01",
                "to": "2024-12-31"
            },
            "departments": ["안전관리팀", "화학처리팀"],
            "status": ["approved", "active"],
            "tags": ["화학안전", "개인보호구"],
            "full_text_search": True,
            "include_archived": False
        }
        
        response = test_client.post("/api/v1/documents/search", json=search_criteria)
        assert response.status_code == 200
        
        search_results = response.json()
        assert "documents" in search_results
        assert "total_count" in search_results
        assert "facets" in search_results
        
        # 2. 문서 사용 통계
        response = test_client.get("/api/v1/documents/analytics/usage-statistics")
        assert response.status_code == 200
        
        usage_stats = response.json()
        assert "most_accessed_documents" in usage_stats
        assert "access_trends" in usage_stats
        assert "user_activity" in usage_stats
        
        # 3. 문서 생성 트렌드 분석
        response = test_client.get("/api/v1/documents/analytics/creation-trends?period=monthly")
        assert response.status_code == 200
        
        creation_trends = response.json()
        assert "monthly_data" in creation_trends
        assert "document_type_distribution" in creation_trends
        
        # 4. 문서 품질 분석
        quality_analysis_data = {
            "analysis_criteria": [
                "completeness",
                "accuracy",
                "timeliness",
                "accessibility",
                "compliance"
            ],
            "document_sample_size": 100,
            "include_recommendations": True
        }
        
        response = test_client.post("/api/v1/documents/analytics/quality-analysis", json=quality_analysis_data)
        assert response.status_code == 200
        
        quality_analysis = response.json()
        assert "quality_scores" in quality_analysis
        assert "improvement_recommendations" in quality_analysis
        
        # 5. 규정 준수 모니터링
        compliance_check_data = {
            "regulatory_framework": "korean_osh_law",
            "check_categories": [
                "document_retention",
                "required_documentation",
                "approval_workflows",
                "access_controls"
            ]
        }
        
        response = test_client.post("/api/v1/documents/compliance-check", json=compliance_check_data)
        assert response.status_code == 200
        
        compliance_report = response.json()
        assert "compliance_score" in compliance_report
        assert "non_compliant_items" in compliance_report
        assert "corrective_actions" in compliance_report


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 문서 관리 및 PDF 생성 시스템 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 문서 관리 및 PDF 생성 시스템 통합 테스트 실패")
        sys.exit(1)