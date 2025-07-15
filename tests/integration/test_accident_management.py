"""
산업재해 관리 통합 테스트
Industrial Accident Management Integration Tests
"""

import asyncio
import json
from datetime import datetime, timedelta

import pytest
from fastapi.testclient import TestClient

from src.app import create_app


class TestAccidentManagement:
    """산업재해 관리 전체 프로세스 통합 테스트"""
    
    @pytest.fixture
    def test_client(self):
        """테스트 클라이언트"""
        app = create_app()
        return TestClient(app)
    
    @pytest.fixture
    def sample_accident_data(self):
        """샘플 재해 데이터"""
        return {
            "incident_datetime": datetime.now().isoformat(),
            "report_datetime": datetime.now().isoformat(),
            "incident_location": "3층 철골 작업장",
            "incident_type": "추락",
            "severity_level": "중대재해",
            "injured_worker": {
                "name": "김작업자",
                "age": 35,
                "gender": "male",
                "employee_id": "EMP001",
                "department": "철골팀",
                "position": "기능공",
                "experience_years": 8
            },
            "injury_details": {
                "body_parts": ["머리", "왼쪽 다리"],
                "injury_type": ["좌상", "골절"],
                "severity": "중상",
                "medical_attention_required": True,
                "hospitalization_required": True,
                "estimated_recovery_days": 60
            },
            "incident_description": "3층 철골 작업 중 안전대 미착용 상태에서 발판에서 미끄러져 추락",
            "immediate_cause": "안전대 미착용",
            "environmental_factors": [
                "비 온 후 젖은 발판",
                "강풍 (풍속 15m/s)",
                "시야 불량"
            ],
            "witnesses": [
                {
                    "name": "이목격자",
                    "employee_id": "EMP002",
                    "contact": "010-1234-5678"
                }
            ],
            "reporter": {
                "name": "박현장소장",
                "position": "현장소장",
                "contact": "010-9876-5432"
            },
            "emergency_response": {
                "first_aid_provided": True,
                "ambulance_called": True,
                "hospital": "서울대학교병원",
                "emergency_contact_notified": True
            }
        }
    
    @pytest.fixture
    def sample_worker_data(self):
        """샘플 근로자 데이터"""
        return {
            "name": "김작업자",
            "gender": "male",
            "birth_date": "1989-03-15",
            "employee_id": "EMP001",
            "department": "철골팀",
            "position": "기능공",
            "hire_date": "2016-05-01",
            "phone": "010-1111-2222",
            "emergency_contact": "010-3333-4444"
        }
    
    async def test_accident_incident_reporting_flow(self, test_client, sample_worker_data, sample_accident_data):
        """산업재해 신고 전체 흐름 테스트"""
        
        # 1. 관련 근로자 사전 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        assert response.status_code == 201
        worker_id = response.json()["id"]
        
        # 2. 재해 신고 접수
        sample_accident_data["injured_worker"]["worker_id"] = worker_id
        
        response = test_client.post("/api/v1/accident-reports/", json=sample_accident_data)
        assert response.status_code == 201
        
        accident_data = response.json()
        accident_id = accident_data["id"]
        
        # 신고 데이터 검증
        assert accident_data["incident_type"] == "추락"
        assert accident_data["severity_level"] == "중대재해"
        assert accident_data["injured_worker"]["name"] == "김작업자"
        
        # 3. 재해 조회
        response = test_client.get(f"/api/v1/accident-reports/{accident_id}")
        assert response.status_code == 200
        
        retrieved_accident = response.json()
        assert retrieved_accident["id"] == accident_id
        assert retrieved_accident["incident_location"] == "3층 철골 작업장"
        
        # 4. 재해 상태 확인 (자동으로 '접수' 상태가 되어야 함)
        assert retrieved_accident["status"] == "접수"
        
        # 5. 재해 목록 조회
        response = test_client.get("/api/v1/accident-reports/")
        assert response.status_code == 200
        
        accidents_list = response.json()
        assert len(accidents_list) >= 1
        assert any(acc["id"] == accident_id for acc in accidents_list)
        
        return accident_id, worker_id
    
    async def test_24_hour_authority_notification(self, test_client, sample_worker_data, sample_accident_data):
        """24시간 내 당국 신고 자동화 테스트"""
        
        # 1. 근로자 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        # 2. 중대재해 신고
        sample_accident_data["injured_worker"]["worker_id"] = worker_id
        sample_accident_data["severity_level"] = "중대재해"
        
        response = test_client.post("/api/v1/accident-reports/", json=sample_accident_data)
        accident_id = response.json()["id"]
        
        # 3. 자동 당국 신고 프로세스 확인
        response = test_client.get(f"/api/v1/accident-reports/{accident_id}/authority-notification")
        assert response.status_code == 200
        
        notification_status = response.json()
        
        # 중대재해의 경우 자동으로 당국 신고가 예약되어야 함
        assert notification_status["required"] == True
        assert notification_status["deadline_hours"] == 24
        assert "scheduled_notification_time" in notification_status
        
        # 4. 당국 신고서 자동 생성
        response = test_client.post(f"/api/v1/accident-reports/{accident_id}/generate-authority-report")
        assert response.status_code == 200
        
        # 신고서 PDF가 생성되는지 확인
        report_data = response.json()
        assert "report_file_url" in report_data
        assert "kosha_report_number" in report_data
        
        # 5. 신고 완료 처리
        notification_completion = {
            "submitted_datetime": datetime.now().isoformat(),
            "submission_method": "온라인",
            "kosha_receipt_number": "KOSHA-2024-001234",
            "submitted_by": "박현장소장",
            "confirmation_received": True
        }
        
        response = test_client.post(f"/api/v1/accident-reports/{accident_id}/authority-notification/complete", json=notification_completion)
        assert response.status_code == 200
        
        # 6. 신고 현황 확인
        response = test_client.get(f"/api/v1/accident-reports/{accident_id}")
        updated_accident = response.json()
        
        assert updated_accident["authority_notification_status"] == "완료"
        assert updated_accident["kosha_receipt_number"] == "KOSHA-2024-001234"
    
    async def test_accident_investigation_process(self, test_client, sample_worker_data, sample_accident_data):
        """재해 조사 프로세스 테스트"""
        
        # 1. 재해 신고 및 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        sample_accident_data["injured_worker"]["worker_id"] = worker_id
        response = test_client.post("/api/v1/accident-reports/", json=sample_accident_data)
        accident_id = response.json()["id"]
        
        # 2. 조사팀 구성
        investigation_team = {
            "accident_id": accident_id,
            "team_members": [
                {
                    "name": "이안전관리자",
                    "role": "조사팀장",
                    "department": "안전관리팀",
                    "qualification": "산업안전기사"
                },
                {
                    "name": "김보건관리자",
                    "role": "조사원",
                    "department": "보건관리팀",
                    "qualification": "산업위생관리기사"
                },
                {
                    "name": "박현장소장",
                    "role": "조사원",
                    "department": "현장관리팀",
                    "qualification": "건설안전기사"
                }
            ],
            "investigation_start_date": datetime.now().isoformat(),
            "target_completion_date": (datetime.now() + timedelta(days=14)).isoformat()
        }
        
        response = test_client.post("/api/v1/accident-reports/investigation/team", json=investigation_team)
        assert response.status_code == 201
        
        team_id = response.json()["id"]
        
        # 3. 현장 조사 실시
        site_investigation = {
            "investigation_team_id": team_id,
            "investigation_date": datetime.now().isoformat(),
            "investigation_location": "3층 철골 작업장",
            "weather_conditions": {
                "temperature": 25,
                "humidity": 70,
                "wind_speed": 15,
                "precipitation": "소나기",
                "visibility": "불량"
            },
            "site_conditions": {
                "work_platform_condition": "젖음, 미끄러움",
                "safety_equipment_available": ["안전대", "안전모", "안전화"],
                "safety_equipment_used": ["안전모", "안전화"],
                "safety_equipment_not_used": ["안전대"],
                "guardrail_present": False,
                "safety_net_present": False
            },
            "equipment_inspection": {
                "tools_inspected": ["철골 크레인", "작업대"],
                "defects_found": ["작업대 미끄럼 방지 패드 노후"],
                "maintenance_records_reviewed": True
            },
            "witness_interviews": [
                {
                    "witness_name": "이목격자",
                    "interview_date": datetime.now().isoformat(),
                    "key_observations": [
                        "사고 발생 직전 강한 바람이 불었음",
                        "피재자가 안전대를 착용하지 않았음",
                        "작업대가 비에 젖어 미끄러웠음"
                    ]
                }
            ],
            "photos_taken": 15,
            "measurements_taken": [
                {
                    "measurement_type": "낙하 높이",
                    "value": "8.5m"
                },
                {
                    "measurement_type": "작업대 폭",
                    "value": "1.2m"
                }
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/investigation/site-survey", json=site_investigation)
        assert response.status_code == 201
        
        # 4. 원인 분석
        cause_analysis = {
            "accident_id": accident_id,
            "analysis_method": "원인나무분석(FTA)",
            "immediate_causes": [
                {
                    "category": "불안전한 행동",
                    "description": "안전대 미착용",
                    "contributing_factors": ["안전의식 부족", "작업 서두름"]
                }
            ],
            "basic_causes": [
                {
                    "category": "관리적 요인",
                    "description": "안전교육 부족",
                    "contributing_factors": ["정기 안전교육 미실시", "안전수칙 미준수"]
                },
                {
                    "category": "환경적 요인", 
                    "description": "악천후 작업 강행",
                    "contributing_factors": ["공기 단축 압박", "날씨 고려 부족"]
                }
            ],
            "root_causes": [
                {
                    "category": "조직문화",
                    "description": "안전보다 생산성 우선 문화",
                    "impact_level": "높음"
                }
            ],
            "human_factors": [
                "시간 압박",
                "경험 과신",
                "위험 인식 부족"
            ],
            "technical_factors": [
                "미끄럼 방지 시설 부족",
                "개인보호구 관리 소홀"
            ],
            "organizational_factors": [
                "안전관리 체계 미흡",
                "작업자 안전교육 부족"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/investigation/cause-analysis", json=cause_analysis)
        assert response.status_code == 201
        
        # 5. 조사 보고서 작성
        investigation_report = {
            "accident_id": accident_id,
            "report_title": "철골 작업 중 추락 재해 조사 보고서",
            "executive_summary": "안전대 미착용으로 인한 3층 높이 추락 재해",
            "investigation_findings": {
                "primary_cause": "안전대 미착용",
                "secondary_causes": ["악천후", "작업대 미끄러움", "안전교육 부족"],
                "contributing_factors": ["공기 단축 압박", "안전의식 부족"]
            },
            "preventive_measures": [
                {
                    "measure": "안전교육 강화",
                    "responsible_party": "안전관리팀",
                    "implementation_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "priority": "높음"
                },
                {
                    "measure": "작업대 미끄럼 방지 시설 설치",
                    "responsible_party": "시설관리팀",
                    "implementation_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "priority": "높음"
                },
                {
                    "measure": "악천후 작업 중단 기준 수립",
                    "responsible_party": "현장관리팀",
                    "implementation_date": (datetime.now() + timedelta(days=3)).isoformat(),
                    "priority": "매우 높음"
                }
            ],
            "investigation_team_conclusion": "조직적 안전관리 체계 개선 필요",
            "report_date": datetime.now().isoformat(),
            "approved_by": "이안전관리자"
        }
        
        response = test_client.post("/api/v1/accident-reports/investigation/report", json=investigation_report)
        assert response.status_code == 201
        
        report_id = response.json()["id"]
        
        # 6. 조사 완료 및 상태 업데이트
        response = test_client.put(f"/api/v1/accident-reports/{accident_id}/investigation-complete")
        assert response.status_code == 200
        
        # 재해 상태가 '조사완료'로 변경되었는지 확인
        response = test_client.get(f"/api/v1/accident-reports/{accident_id}")
        updated_accident = response.json()
        assert updated_accident["status"] == "조사완료"
    
    async def test_root_cause_analysis_documentation(self, test_client, sample_worker_data, sample_accident_data):
        """근본원인 분석 문서화 테스트"""
        
        # 1. 재해 등록
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        sample_accident_data["injured_worker"]["worker_id"] = worker_id
        response = test_client.post("/api/v1/accident-reports/", json=sample_accident_data)
        accident_id = response.json()["id"]
        
        # 2. 5-Why 분석 수행
        five_why_analysis = {
            "accident_id": accident_id,
            "analysis_date": datetime.now().isoformat(),
            "analyst": "이안전관리자",
            "problem_statement": "작업자가 3층에서 추락하여 중상을 입었다",
            "why_questions": [
                {
                    "level": 1,
                    "question": "왜 작업자가 추락했는가?",
                    "answer": "안전대를 착용하지 않았기 때문"
                },
                {
                    "level": 2,
                    "question": "왜 안전대를 착용하지 않았는가?",
                    "answer": "작업이 급해서 번거롭다고 생각했기 때문"
                },
                {
                    "level": 3,
                    "question": "왜 작업이 급했는가?",
                    "answer": "공기가 지연되어 빨리 끝내야 했기 때문"
                },
                {
                    "level": 4,
                    "question": "왜 공기가 지연되었는가?",
                    "answer": "사전 계획이 부족하고 날씨를 고려하지 않았기 때문"
                },
                {
                    "level": 5,
                    "question": "왜 사전 계획이 부족했는가?",
                    "answer": "안전보다 일정 준수를 우선시하는 조직문화 때문"
                }
            ],
            "root_cause": "안전보다 일정 준수를 우선시하는 조직문화",
            "verification_methods": [
                "과거 안전교육 기록 검토",
                "작업자 면담",
                "현장 안전점검 기록 분석"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/analysis/five-why", json=five_why_analysis)
        assert response.status_code == 201
        
        # 3. 피쉬본 다이어그램 생성
        fishbone_analysis = {
            "accident_id": accident_id,
            "problem": "작업자 추락 재해",
            "categories": {
                "사람(Man)": [
                    "안전의식 부족",
                    "경험 과신",
                    "안전교육 미흡",
                    "작업 서두름"
                ],
                "기계(Machine)": [
                    "작업대 노후",
                    "미끄럼 방지 시설 없음",
                    "안전대 보관 불량"
                ],
                "방법(Method)": [
                    "작업절차 미준수",
                    "안전점검 생략",
                    "악천후 작업 기준 없음"
                ],
                "재료(Material)": [
                    "안전대 품질 불량",
                    "미끄럼 방지 재료 부족"
                ],
                "환경(Environment)": [
                    "강풍",
                    "비로 인한 미끄러움",
                    "시야 불량"
                ],
                "관리(Management)": [
                    "안전관리 체계 미흡",
                    "일정 우선 문화",
                    "안전투자 부족"
                ]
            },
            "primary_causes": [
                "안전의식 부족",
                "작업대 노후", 
                "악천후 작업 기준 없음",
                "안전관리 체계 미흡"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/analysis/fishbone", json=fishbone_analysis)
        assert response.status_code == 201
        
        # 4. STAMP 분석 (Systems-Theoretic Accident Model)
        stamp_analysis = {
            "accident_id": accident_id,
            "system_definition": "건설현장 고소작업 안전관리 시스템",
            "control_structure": {
                "controllers": [
                    {"name": "현장소장", "level": 1, "responsibilities": ["전체 안전관리", "작업 지시"]},
                    {"name": "안전관리자", "level": 2, "responsibilities": ["안전교육", "안전점검"]},
                    {"name": "작업반장", "level": 3, "responsibilities": ["작업자 지도", "안전수칙 전달"]},
                    {"name": "작업자", "level": 4, "responsibilities": ["안전수칙 준수", "보호구 착용"]}
                ],
                "control_actions": [
                    {"from": "현장소장", "to": "안전관리자", "action": "안전관리 지시"},
                    {"from": "안전관리자", "to": "작업반장", "action": "안전교육 실시"},
                    {"from": "작업반장", "to": "작업자", "action": "안전작업 지도"}
                ],
                "feedback_loops": [
                    {"from": "작업자", "to": "작업반장", "feedback": "작업 상황 보고"},
                    {"from": "작업반장", "to": "안전관리자", "feedback": "안전 이슈 보고"}
                ]
            },
            "unsafe_control_actions": [
                {
                    "controller": "현장소장",
                    "action": "악천후 중 작업 지시",
                    "hazard": "추락 위험 증가"
                },
                {
                    "controller": "안전관리자",
                    "action": "안전교육 생략",
                    "hazard": "안전의식 저하"
                }
            ],
            "system_failures": [
                "안전관리 체계의 통제 실패",
                "피드백 루프 기능 정지",
                "안전 문화의 부재"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/analysis/stamp", json=stamp_analysis)
        assert response.status_code == 201
        
        # 5. 종합 분석 보고서 생성
        comprehensive_analysis = {
            "accident_id": accident_id,
            "analysis_methods_used": ["5-Why", "Fishbone", "STAMP"],
            "key_findings": [
                "조직문화가 가장 근본적인 원인",
                "안전관리 시스템의 다층적 실패",
                "개인과 조직 요인의 복합적 작용"
            ],
            "risk_factors_identified": [
                {
                    "factor": "안전의식 부족",
                    "impact": "높음",
                    "likelihood": "높음",
                    "risk_level": "매우 높음"
                },
                {
                    "factor": "악천후 작업",
                    "impact": "높음", 
                    "likelihood": "중간",
                    "risk_level": "높음"
                }
            ],
            "systemic_issues": [
                "안전 문화의 부재",
                "리더십의 안전 의식 부족",
                "예방 중심의 관리 체계 미흡"
            ],
            "recommendations": [
                {
                    "level": "조직차원",
                    "recommendation": "안전 우선 문화 구축",
                    "implementation_strategy": "경영진 안전 서약, 안전 성과 평가 반영"
                },
                {
                    "level": "관리차원",
                    "recommendation": "통합 안전관리 시스템 구축",
                    "implementation_strategy": "실시간 모니터링, 예측적 안전관리"
                },
                {
                    "level": "개인차원", 
                    "recommendation": "안전역량 강화",
                    "implementation_strategy": "체험형 안전교육, 개인별 안전 목표 설정"
                }
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/analysis/comprehensive", json=comprehensive_analysis)
        assert response.status_code == 201
    
    async def test_preventive_measures_implementation(self, test_client, sample_worker_data, sample_accident_data):
        """재발 방지 대책 시행 테스트"""
        
        # 1. 재해 등록 및 조사 완료
        response = test_client.post("/api/v1/workers/", json=sample_worker_data)
        worker_id = response.json()["id"]
        
        sample_accident_data["injured_worker"]["worker_id"] = worker_id
        response = test_client.post("/api/v1/accident-reports/", json=sample_accident_data)
        accident_id = response.json()["id"]
        
        # 2. 재발 방지 대책 수립
        prevention_plan = {
            "accident_id": accident_id,
            "plan_title": "추락 재해 재발 방지 종합 대책",
            "immediate_measures": [
                {
                    "measure": "고소작업 전면 중단",
                    "responsible_person": "현장소장",
                    "implementation_date": datetime.now().isoformat(),
                    "completion_date": datetime.now().isoformat(),
                    "status": "완료",
                    "priority": "긴급"
                },
                {
                    "measure": "전 작업자 응급 안전교육",
                    "responsible_person": "안전관리자",
                    "implementation_date": (datetime.now() + timedelta(days=1)).isoformat(),
                    "target_completion": (datetime.now() + timedelta(days=3)).isoformat(),
                    "status": "진행중",
                    "priority": "긴급"
                }
            ],
            "short_term_measures": [
                {
                    "measure": "작업대 미끄럼 방지 시설 설치",
                    "responsible_person": "시설관리팀장",
                    "budget_required": 5000000,
                    "implementation_date": (datetime.now() + timedelta(days=7)).isoformat(),
                    "target_completion": (datetime.now() + timedelta(days=14)).isoformat(),
                    "status": "계획",
                    "priority": "높음"
                },
                {
                    "measure": "개인보호구 관리 시스템 구축",
                    "responsible_person": "안전관리자",
                    "budget_required": 3000000,
                    "implementation_date": (datetime.now() + timedelta(days=14)).isoformat(),
                    "target_completion": (datetime.now() + timedelta(days=30)).isoformat(),
                    "status": "계획",
                    "priority": "높음"
                }
            ],
            "long_term_measures": [
                {
                    "measure": "안전문화 혁신 프로그램",
                    "responsible_person": "안전관리팀",
                    "budget_required": 20000000,
                    "implementation_date": (datetime.now() + timedelta(days=30)).isoformat(),
                    "target_completion": (datetime.now() + timedelta(days=180)).isoformat(),
                    "status": "계획",
                    "priority": "중간"
                }
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/prevention-plan", json=prevention_plan)
        assert response.status_code == 201
        
        prevention_plan_id = response.json()["id"]
        
        # 3. 대책 시행 진도 관리
        progress_updates = [
            {
                "measure_id": "immediate_1",
                "progress_date": datetime.now().isoformat(),
                "progress_percentage": 100,
                "status": "완료",
                "notes": "전 현장 고소작업 즉시 중단 완료",
                "evidence_files": ["stop_work_order.pdf"]
            },
            {
                "measure_id": "immediate_2", 
                "progress_date": (datetime.now() + timedelta(days=2)).isoformat(),
                "progress_percentage": 70,
                "status": "진행중",
                "notes": "3개 팀 교육 완료, 2개 팀 교육 예정",
                "next_milestone": "전체 교육 완료",
                "next_milestone_date": (datetime.now() + timedelta(days=3)).isoformat()
            }
        ]
        
        for update in progress_updates:
            response = test_client.post(f"/api/v1/accident-reports/prevention-plan/{prevention_plan_id}/progress", json=update)
            assert response.status_code == 201
        
        # 4. 대책 효과성 평가
        effectiveness_evaluation = {
            "prevention_plan_id": prevention_plan_id,
            "evaluation_date": (datetime.now() + timedelta(days=30)).isoformat(),
            "evaluation_period_days": 30,
            "key_metrics": [
                {
                    "metric": "안전대 착용률",
                    "baseline_value": 60,
                    "current_value": 95,
                    "target_value": 100,
                    "improvement_percentage": 58.3,
                    "measurement_method": "현장 관찰"
                },
                {
                    "metric": "고소작업 안전사고 건수",
                    "baseline_value": 3,
                    "current_value": 0,
                    "target_value": 0,
                    "improvement_percentage": 100,
                    "measurement_method": "사고 통계"
                },
                {
                    "metric": "안전교육 이수율",
                    "baseline_value": 70,
                    "current_value": 98,
                    "target_value": 100,
                    "improvement_percentage": 40,
                    "measurement_method": "교육 기록"
                }
            ],
            "overall_effectiveness": "높음",
            "continuing_measures": [
                "정기 안전점검 강화",
                "월별 안전교육 지속"
            ],
            "additional_measures_needed": [
                "날씨 모니터링 시스템 도입",
                "작업 중단 기준 명문화"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/prevention-plan/evaluation", json=effectiveness_evaluation)
        assert response.status_code == 201
        
        # 5. 재발 방지 대책 완료 보고서
        completion_report = {
            "prevention_plan_id": prevention_plan_id,
            "completion_date": (datetime.now() + timedelta(days=60)).isoformat(),
            "total_measures": 5,
            "completed_measures": 4,
            "in_progress_measures": 1,
            "completion_rate": 80,
            "budget_used": 25000000,
            "budget_planned": 28000000,
            "key_achievements": [
                "안전대 착용률 95% 달성",
                "고소작업 사고 제로 달성",
                "안전문화 인식 개선"
            ],
            "lessons_learned": [
                "즉시 대응의 중요성",
                "지속적 교육의 효과",
                "관리자 역할의 중요성"
            ],
            "recommendations_for_future": [
                "예방 중심 안전관리 체계 확립",
                "실시간 모니터링 시스템 도입",
                "안전 성과 평가 체계 구축"
            ]
        }
        
        response = test_client.post("/api/v1/accident-reports/prevention-plan/completion-report", json=completion_report)
        assert response.status_code == 201
    
    async def test_accident_statistics_and_trends(self, test_client, sample_worker_data):
        """재해 통계 및 동향 분석 테스트"""
        
        # 1. 여러 재해 사례 생성
        accident_scenarios = [
            {
                "incident_type": "추락", "severity_level": "중상", 
                "location": "3층", "month_offset": 1
            },
            {
                "incident_type": "끼임", "severity_level": "경상",
                "location": "1층", "month_offset": 2  
            },
            {
                "incident_type": "절단", "severity_level": "중상",
                "location": "작업장", "month_offset": 2
            },
            {
                "incident_type": "화상", "severity_level": "중상",
                "location": "용접장", "month_offset": 3
            },
            {
                "incident_type": "추락", "severity_level": "경상",
                "location": "2층", "month_offset": 3
            }
        ]
        
        # 근로자들 등록
        workers = []
        for i in range(5):
            worker_data = sample_worker_data.copy()
            worker_data["name"] = f"근로자{i+1}"
            worker_data["employee_id"] = f"EMP{i+1:03d}"
            
            response = test_client.post("/api/v1/workers/", json=worker_data)
            workers.append(response.json())
        
        # 재해 사례들 등록
        accidents = []
        for i, scenario in enumerate(accident_scenarios):
            accident_data = {
                "incident_datetime": (datetime.now() - timedelta(days=30*scenario["month_offset"])).isoformat(),
                "report_datetime": (datetime.now() - timedelta(days=30*scenario["month_offset"])).isoformat(),
                "incident_location": scenario["location"],
                "incident_type": scenario["incident_type"],
                "severity_level": scenario["severity_level"],
                "injured_worker": {
                    "worker_id": workers[i]["id"],
                    "name": workers[i]["name"],
                    "employee_id": workers[i]["employee_id"]
                },
                "incident_description": f"{scenario['incident_type']} 재해 발생"
            }
            
            response = test_client.post("/api/v1/accident-reports/", json=accident_data)
            assert response.status_code == 201
            accidents.append(response.json())
        
        # 2. 월별 재해 통계 조회
        response = test_client.get("/api/v1/accident-reports/statistics/monthly?year=2024")
        assert response.status_code == 200
        
        monthly_stats = response.json()
        assert "monthly_data" in monthly_stats
        assert "total_accidents" in monthly_stats
        assert "severity_breakdown" in monthly_stats
        
        # 3. 재해 유형별 통계
        response = test_client.get("/api/v1/accident-reports/statistics/by-type")
        assert response.status_code == 200
        
        type_stats = response.json()
        assert "추락" in [item["type"] for item in type_stats]
        assert "끼임" in [item["type"] for item in type_stats]
        
        # 4. 재해율 계산
        response = test_client.get("/api/v1/accident-reports/statistics/accident-rates?total_workers=100&total_work_hours=200000")
        assert response.status_code == 200
        
        rates = response.json()
        assert "frequency_rate" in rates  # 도수율
        assert "severity_rate" in rates   # 강도율
        assert "accident_rate" in rates   # 재해율
        
        # 5. 동향 분석
        response = test_client.get("/api/v1/accident-reports/analytics/trends?period=quarterly")
        assert response.status_code == 200
        
        trends = response.json()
        assert "trend_direction" in trends
        assert "peak_periods" in trends
        assert "risk_factors" in trends
        
        # 6. 예측 분석
        prediction_params = {
            "prediction_period_months": 6,
            "include_seasonal_factors": True,
            "include_work_intensity": True
        }
        
        response = test_client.post("/api/v1/accident-reports/analytics/prediction", json=prediction_params)
        assert response.status_code == 200
        
        predictions = response.json()
        assert "predicted_accidents" in predictions
        assert "confidence_interval" in predictions
        assert "risk_periods" in predictions
        
        # 7. 종합 대시보드 데이터
        response = test_client.get("/api/v1/accident-reports/dashboard")
        assert response.status_code == 200
        
        dashboard = response.json()
        assert "current_month_accidents" in dashboard
        assert "ytd_accidents" in dashboard
        assert "accident_free_days" in dashboard
        assert "top_risk_areas" in dashboard


if __name__ == "__main__":
    """인라인 테스트 실행 (Rust 스타일)"""
    import subprocess
    import sys
    
    result = subprocess.run([
        sys.executable, "-m", "pytest", __file__, "-v", "--tb=short", "-x"
    ])
    
    if result.returncode == 0:
        print("✅ 산업재해 관리 통합 테스트 모든 케이스 통과")
    else:
        print("❌ 산업재해 관리 통합 테스트 실패")
        sys.exit(1)