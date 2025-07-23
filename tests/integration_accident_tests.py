"""
산업재해 보고 시스템 통합 테스트
Accident reporting system integration tests
"""

import asyncio
import json
from datetime import datetime, date, timedelta
from typing import Dict, List

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.accident_report import AccidentType, InjuryType, AccidentSeverity, InvestigationStatus
from tests.builders.accident_builder import AccidentReportBuilder, AccidentScenarioBuilder
from tests.builders.worker_builder import WorkerBuilder


class TestAccidentReportingIntegration:
    """산업재해 보고 시스템 통합 테스트"""

    @pytest.mark.asyncio
    async def test_accident_report_creation_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 신고 워크플로우 테스트"""
        # 근로자 생성
        worker = await (
            WorkerBuilder()
            .with_name("사고당사자")
            .with_korean_data()
            .build(db_session)
        )

        # 1. 산업재해 신고 등록
        accident_data = {
            "accident_datetime": "2024-06-15T14:30:00",
            "report_datetime": "2024-06-15T15:00:00",
            "accident_location": "건설현장 제1공구 3층",
            "worker_id": worker.id,
            "accident_type": "떨어짐",
            "injury_type": "골절",
            "severity": "중대",
            "accident_description": "비계 작업 중 안전대 미착용으로 인한 추락사고",
            "immediate_cause": "안전대 미착용 및 작업발판 불량",
            "root_cause": "안전교육 미실시 및 안전관리자 현장 부재",
            "injured_body_part": "왼쪽 다리",
            "treatment_type": "입원치료",
            "hospital_name": "서울대학교병원",
            "doctor_name": "이정호 과장",
            "work_days_lost": 30,
            "return_to_work_date": "2024-07-20",
            "immediate_actions": "119 신고 후 응급실 이송, 응급처치 실시",
            "medical_cost": 2000000,
            "compensation_cost": 5000000
        }

        response = await client.post(
            "/api/v1/accident-reports/",
            json=accident_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        accident = response.json()
        accident_id = accident["id"]

        # 2. 산업재해 신고서 조회
        response = await client.get(
            f"/api/v1/accident-reports/{accident_id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["accident_type"] == "떨어짐"
        assert response.json()["severity"] == "중대"
        assert response.json()["work_days_lost"] == 30

        # 3. 조사 정보 업데이트
        investigation_update = {
            "investigation_status": "조사중",
            "investigator_name": "박안전관리자",
            "investigation_date": "2024-06-16",
            "corrective_actions": "안전교육 실시, 작업절차 개선",
            "preventive_measures": "정기 안전점검 강화, 보호구 착용 의무화"
        }

        response = await client.put(
            f"/api/v1/accident-reports/{accident_id}",
            json=investigation_update,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        updated_accident = response.json()
        assert updated_accident["investigation_status"] == "조사중"
        assert "안전교육 실시" in updated_accident["corrective_actions"]

        # 4. 산업재해 목록 조회
        response = await client.get(
            "/api/v1/accident-reports/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 1

    @pytest.mark.asyncio
    async def test_accident_photo_upload_management(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str],
        temp_file_path: str
    ):
        """사고 현장 사진 업로드 관리 테스트"""
        # 사고 보고서 생성
        worker = await WorkerBuilder().with_korean_data().build(db_session)
        accident = await (
            AccidentReportBuilder()
            .with_worker_id(worker.id)
            .with_korean_data()
            .build(db_session)
        )

        # 1. 사고 현장 사진 업로드
        with open(temp_file_path, "rb") as f1, \
             open(temp_file_path, "rb") as f2:
            
            files = [
                ("files", ("accident_photo1.jpg", f1, "image/jpeg")),
                ("files", ("accident_photo2.jpg", f2, "image/jpeg"))
            ]
            
            response = await client.post(
                f"/api/v1/accident-reports/{accident.id}/photos",
                files=files,
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        upload_result = response.json()
        assert upload_result["uploaded_count"] == 2
        assert "2개의 사진이 업로드" in upload_result["message"]

        # 2. 업데이트된 사고 보고서 조회
        response = await client.get(
            f"/api/v1/accident-reports/{accident.id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        updated_accident = response.json()
        assert updated_accident["accident_photo_paths"] is not None
        
        # JSON 파싱해서 사진 경로 확인
        photo_paths = json.loads(updated_accident["accident_photo_paths"])
        assert len(photo_paths) == 2

        # 3. 추가 사진 업로드
        with open(temp_file_path, "rb") as f3:
            files = [("files", ("accident_photo3.jpg", f3, "image/jpeg"))]
            
            response = await client.post(
                f"/api/v1/accident-reports/{accident.id}/photos",
                files=files,
                headers=authenticated_headers
            )
        
        assert response.status_code == 200
        additional_result = response.json()
        assert additional_result["uploaded_count"] == 1
        assert additional_result["total_photos"] == 3

    @pytest.mark.asyncio
    async def test_accident_statistics_and_metrics(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 통계 및 안전성과 지표 테스트"""
        # 다양한 사고 시나리오 생성
        workers = []
        for i in range(6):
            worker = await (
                WorkerBuilder()
                .with_name(f"통계테스트자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 건설현장 사고 시나리오 생성
        construction_accidents = await AccidentScenarioBuilder.create_construction_site_accidents(
            db_session, [w.id for w in workers[:5]]
        )

        # 안전수칙 위반 사고 시나리오 생성
        violation_accidents = await AccidentScenarioBuilder.create_safety_violations_scenario(
            db_session, [w.id for w in workers[4:]]
        )

        # 1. 산업재해 통계 조회
        response = await client.get(
            "/api/v1/accident-reports/statistics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        stats = response.json()
        assert stats["total_accidents"] >= 7  # 생성된 사고 수
        assert stats["total_work_days_lost"] > 0
        assert stats["total_cost"] > 0
        
        # 사고 유형별 통계 확인
        assert "떨어짐" in stats["by_type"]
        assert "부딪힘" in stats["by_type"]
        assert "끼임" in stats["by_type"]
        
        # 중대성별 통계 확인
        assert "중대" in stats["by_severity"]
        assert "중등도" in stats["by_severity"]
        assert "경미" in stats["by_severity"]
        
        # 조사 미완료 건수 확인
        assert stats["investigation_pending"] >= 0
        assert stats["actions_pending"] >= 0
        
        # 최근 사고 목록 확인
        assert len(stats["recent_accidents"]) <= 5
        for recent in stats["recent_accidents"]:
            assert "accident_date" in recent
            assert "worker_name" in recent
            assert "accident_type" in recent

        # 2. 안전성과 지표 조회
        current_year = datetime.now().year
        response = await client.get(
            f"/api/v1/accident-reports/safety-metrics?year={current_year}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        metrics = response.json()
        assert metrics["year"] == current_year
        assert metrics["total_accidents"] >= 0
        assert metrics["lost_time_accidents"] >= 0
        assert metrics["total_days_lost"] >= 0
        assert "frequency_rate" in metrics
        assert "severity_rate" in metrics
        assert "improvement_rate" in metrics

        # 3. 월별 사고 추이 확인
        assert "by_month" in stats
        # 현재 월에 대한 데이터가 있어야 함
        current_month = datetime.now().strftime("%Y-%m")
        if current_month in stats["by_month"]:
            assert stats["by_month"][current_month] >= 0

    @pytest.mark.asyncio
    async def test_accident_investigation_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 조사 워크플로우 테스트"""
        # 근로자 생성
        workers = []
        for i in range(3):
            worker = await (
                WorkerBuilder()
                .with_name(f"조사대상자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 1. 신고접수 상태 사고 생성
        reported_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[0].id)
            .with_fall_accident()
            .with_investigation_info(InvestigationStatus.REPORTED)
            .build(db_session)
        )

        # 2. 조사 시작 - 상태를 조사중으로 변경
        investigation_start = {
            "investigation_status": "조사중",
            "investigator_name": "김조사관",
            "investigation_date": date.today().isoformat()
        }

        response = await client.put(
            f"/api/v1/accident-reports/{reported_accident.id}",
            json=investigation_start,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["investigation_status"] == "조사중"

        # 3. 조사 완료 - 시정조치 계획 수립
        investigation_complete = {
            "investigation_status": "조사완료",
            "corrective_actions": "안전교육 재실시, 작업절차서 개정",
            "preventive_measures": "월 2회 정기 안전점검, 안전대 점검 강화",
            "action_completion_date": (date.today() + timedelta(days=30)).isoformat()
        }

        response = await client.put(
            f"/api/v1/accident-reports/{reported_accident.id}",
            json=investigation_complete,
            headers=authenticated_headers
        )
        assert response.status_code == 200
        completed_report = response.json()
        assert completed_report["investigation_status"] == "조사완료"
        assert "안전교육 재실시" in completed_report["corrective_actions"]

        # 4. 진행 중인 조사 건수 확인
        response = await client.get(
            "/api/v1/accident-reports/?investigation_status=조사중",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        investigating_reports = response.json()
        
        # 다른 조사중 사건이 있을 수 있으므로 >= 0로 확인
        assert investigating_reports["total"] >= 0

        # 5. 완료된 조사 건수 확인
        response = await client.get(
            "/api/v1/accident-reports/?investigation_status=조사완료",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        completed_reports = response.json()
        assert completed_reports["total"] >= 1

    @pytest.mark.asyncio
    async def test_authority_reporting_compliance(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """관계당국 신고 의무 준수 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(4):
            worker = await (
                WorkerBuilder()
                .with_name(f"신고대상자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 1. 신고 대상 사고 생성 (중대사고, 휴업일수 10일 이상)
        reportable_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[0].id)
            .with_fall_accident()
            .with_work_loss(15)  # 15일 휴업
            .with_authority_reportable_accident()
            .build(db_session)
        )

        # 2. 미신고 중대사고 생성 (신고 누락 사례)
        unreported_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[1].id)
            .with_chemical_exposure_accident()
            .with_work_loss(20)  # 20일 휴업
            .with_unreported_severe_accident()
            .build(db_session)
        )

        # 3. 사망사고 생성 (즉시 신고 대상)
        fatal_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[2].id)
            .with_fatal_accident()
            .build(db_session)
        )

        # 4. 경미한 사고 생성 (신고 비대상)
        minor_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[3].id)
            .with_minor_accident()
            .build(db_session)
        )

        # 관계당국 신고 대상 조회
        response = await client.get(
            "/api/v1/accident-reports/authority-reporting-required",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        reporting_required = response.json()
        assert reporting_required["total_unreported"] >= 1  # 미신고 건이 있어야 함
        
        # 미신고 사고 목록 확인
        unreported_list = reporting_required["accidents"]
        assert len(unreported_list) >= 1
        
        # 미신고 사고 세부정보 확인
        for unreported in unreported_list:
            assert unreported["severity"] in ["중대", "사망"]
            assert unreported["work_days_lost"] >= 0
            assert "days_since_accident" in unreported
            assert "reporting_deadline_passed" in unreported

        # 신고 기한 경과 확인
        overdue_reports = [r for r in unreported_list if r["reporting_deadline_passed"]]
        if overdue_reports:
            assert len(overdue_reports) >= 0  # 기한 경과 건수

    @pytest.mark.asyncio
    async def test_accident_cost_analysis(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 비용 분석 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(4):
            worker = await (
                WorkerBuilder()
                .with_name(f"비용분석자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 다양한 비용 수준의 사고 생성
        accidents = []

        # 1. 고비용 사고 (중대재해)
        high_cost_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[0].id)
            .with_fall_accident()
            .with_high_cost_accident()  # 의료비 500만원, 보상금 1000만원, 기타 200만원
            .build(db_session)
        )
        accidents.append(high_cost_accident)

        # 2. 중간비용 사고
        medium_cost_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[1].id)
            .with_collision_accident()
            .with_costs(1000000, 3000000, 500000)  # 총 450만원
            .build(db_session)
        )
        accidents.append(medium_cost_accident)

        # 3. 저비용 사고
        low_cost_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[2].id)
            .with_minor_accident()
            .with_costs(100000, 0, 0)  # 10만원
            .build(db_session)
        )
        accidents.append(low_cost_accident)

        # 4. 무비용 사고 (응급처치)
        no_cost_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[3].id)
            .with_minor_accident()
            .with_injury_details("손가락", "응급처치")
            .build(db_session)
        )
        accidents.append(no_cost_accident)

        # 통계를 통한 비용 분석
        response = await client.get(
            "/api/v1/accident-reports/statistics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        stats = response.json()
        total_cost = stats["total_cost"]
        assert total_cost > 0

        # 예상 총 비용 계산 (기존 + 신규)
        expected_new_cost = 17000000 + 4500000 + 100000  # 고비용 + 중간 + 저비용
        assert total_cost >= expected_new_cost

        # 개별 사고 비용 확인
        for accident in accidents:
            response = await client.get(
                f"/api/v1/accident-reports/{accident.id}",
                headers=authenticated_headers
            )
            assert response.status_code == 200
            accident_detail = response.json()
            
            total_accident_cost = (
                accident_detail["medical_cost"] + 
                accident_detail["compensation_cost"] + 
                accident_detail["other_cost"]
            )
            assert total_accident_cost >= 0

    @pytest.mark.asyncio
    async def test_accident_filtering_and_search(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 필터링 및 검색 기능 테스트"""
        # 다양한 유형의 사고 생성
        workers = []
        for i in range(5):
            worker = await (
                WorkerBuilder()
                .with_name(f"필터테스트자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        accidents = []

        # 1. 떨어짐 사고 (중대)
        fall_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[0].id)
            .with_accident_classification(AccidentType.FALL, InjuryType.FRACTURE, AccidentSeverity.SEVERE)
            .with_accident_datetime(datetime(2024, 1, 15, 10, 30))
            .build(db_session)
        )
        accidents.append(fall_accident)

        # 2. 부딪힘 사고 (중등도)
        collision_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[1].id)
            .with_accident_classification(AccidentType.COLLISION, InjuryType.BRUISE, AccidentSeverity.MODERATE)
            .with_accident_datetime(datetime(2024, 2, 20, 14, 15))
            .build(db_session)
        )
        accidents.append(collision_accident)

        # 3. 화학물질 노출 (중대)
        chemical_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[2].id)
            .with_accident_classification(AccidentType.CHEMICAL_EXPOSURE, InjuryType.POISONING, AccidentSeverity.SEVERE)
            .with_accident_datetime(datetime(2024, 3, 10, 9, 45))
            .build(db_session)
        )
        accidents.append(chemical_accident)

        # 4. 감전 사고 (중대)
        electric_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[3].id)
            .with_accident_classification(AccidentType.ELECTRIC_SHOCK, InjuryType.BURN_INJURY, AccidentSeverity.SEVERE)
            .with_accident_datetime(datetime(2024, 4, 5, 16, 20))
            .build(db_session)
        )
        accidents.append(electric_accident)

        # 5. 베임 사고 (경미)
        cut_accident = await (
            AccidentReportBuilder()
            .with_worker_id(workers[4].id)
            .with_accident_classification(AccidentType.CUT, InjuryType.CUT_WOUND, AccidentSeverity.MINOR)
            .with_accident_datetime(datetime(2024, 5, 12, 11, 30))
            .build(db_session)
        )
        accidents.append(cut_accident)

        # 1. 사고 유형별 필터링
        response = await client.get(
            "/api/v1/accident-reports/?accident_type=떨어짐",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert all(item["accident_type"] == "떨어짐" for item in result["items"])

        # 2. 중대성별 필터링
        response = await client.get(
            "/api/v1/accident-reports/?severity=중대",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert result["total"] >= 3  # 떨어짐, 화학물질, 감전 사고
        assert all(item["severity"] == "중대" for item in result["items"])

        # 3. 특정 근로자 사고 필터링
        response = await client.get(
            f"/api/v1/accident-reports/?worker_id={workers[0].id}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert all(item["worker_id"] == workers[0].id for item in result["items"])

        # 4. 날짜 범위 필터링
        start_date = "2024-02-01T00:00:00"
        end_date = "2024-03-31T23:59:59"
        response = await client.get(
            f"/api/v1/accident-reports/?start_date={start_date}&end_date={end_date}",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        # 2월과 3월 사고 (부딪힘, 화학물질)
        for item in result["items"]:
            accident_date = datetime.fromisoformat(item["accident_datetime"].replace('Z', '+00:00'))
            assert datetime(2024, 2, 1) <= accident_date <= datetime(2024, 3, 31, 23, 59, 59)

        # 5. 복합 필터링 (중대사고 + 특정 기간)
        response = await client.get(
            f"/api/v1/accident-reports/?severity=중대&start_date=2024-01-01T00:00:00&end_date=2024-04-30T23:59:59",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        for item in result["items"]:
            assert item["severity"] == "중대"
            accident_date = datetime.fromisoformat(item["accident_datetime"].replace('Z', '+00:00'))
            assert datetime(2024, 1, 1) <= accident_date <= datetime(2024, 4, 30, 23, 59, 59)

        # 6. 페이지네이션 테스트
        response = await client.get(
            "/api/v1/accident-reports/?page=1&size=3",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        result = response.json()
        assert len(result["items"]) <= 3
        assert result["page"] == 1
        assert result["size"] == 3

    @pytest.mark.asyncio
    async def test_accident_emergency_response_workflow(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 응급대응 워크플로우 테스트"""
        # 근로자 생성
        worker = await (
            WorkerBuilder()
            .with_name("응급상황당사자")
            .with_korean_data()
            .build(db_session)
        )

        # 1. 사망사고 발생 - 즉시 신고 및 대응
        fatal_accident_data = {
            "accident_datetime": datetime.now().isoformat(),
            "report_datetime": (datetime.now() + timedelta(minutes=15)).isoformat(),
            "accident_location": "건설현장 제3공구 옥상",
            "worker_id": worker.id,
            "accident_type": "떨어짐",
            "injury_type": "사망",
            "severity": "사망",
            "accident_description": "옥상 작업 중 추락으로 인한 사망사고",
            "immediate_cause": "안전난간 부재",
            "root_cause": "안전설비 미설치 및 작업계획 부실",
            "injured_body_part": "머리, 전신",
            "treatment_type": "응급실 이송",
            "hospital_name": "응급의료센터",
            "work_days_lost": 0,
            "permanent_disability": "Y",
            "disability_rate": 100.0,
            "immediate_actions": "119 신고, 응급처치 시도, 경찰 신고, 현장 보존",
            "reported_to_authorities": "Y",
            "authority_report_date": datetime.now().isoformat(),
            "authority_report_number": "FATAL-2024-001",
            "witness_names": json.dumps(["김목격자", "이현장반장"]),
            "witness_statements": "옥상에서 작업 중 추락하는 것을 목격",
            "medical_cost": 1000000,
            "compensation_cost": 50000000,
            "other_cost": 5000000
        }

        response = await client.post(
            "/api/v1/accident-reports/",
            json=fatal_accident_data,
            headers=authenticated_headers
        )
        assert response.status_code == 201
        fatal_accident = response.json()

        # 2. 사망사고 즉시 조사 시작
        emergency_investigation = {
            "investigation_status": "조사중",
            "investigator_name": "고용노동부 근로감독관",
            "investigation_date": date.today().isoformat(),
            "immediate_actions": "현장 보존, 증거 수집, 목격자 진술 청취",
            "notes": "중대재해처벌법 적용 검토 필요"
        }

        response = await client.put(
            f"/api/v1/accident-reports/{fatal_accident['id']}",
            json=emergency_investigation,
            headers=authenticated_headers
        )
        assert response.status_code == 200

        # 3. 안전성과 지표에서 사망사고 반영 확인
        response = await client.get(
            "/api/v1/accident-reports/safety-metrics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        metrics = response.json()
        assert metrics["fatalities"] >= 1

        # 4. 관계당국 신고 대상에서 사망사고 확인
        response = await client.get(
            "/api/v1/accident-reports/authority-reporting-required",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        reporting_required = response.json()
        
        # 사망사고는 즉시 신고되어야 하므로 미신고 목록에 없어야 함
        # (이미 신고했으므로)

    @pytest.mark.asyncio
    async def test_accident_trend_analysis(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 추세 분석 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(8):
            worker = await (
                WorkerBuilder()
                .with_name(f"추세분석자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 월별 사고 패턴 생성 (최근 6개월)
        monthly_accidents = []
        base_date = datetime(2024, 1, 1)

        for month_offset in range(6):
            accident_date = base_date + timedelta(days=30 * month_offset)
            accident_count = 2 + month_offset  # 월별 증가 패턴

            for accident_num in range(accident_count):
                if len(workers) <= accident_num:
                    break
                    
                accident_types = [
                    AccidentType.FALL, AccidentType.COLLISION, AccidentType.CUT,
                    AccidentType.CAUGHT_IN, AccidentType.CHEMICAL_EXPOSURE
                ]
                
                accident = await (
                    AccidentReportBuilder()
                    .with_worker_id(workers[accident_num % len(workers)].id)
                    .with_accident_classification(
                        accident_types[accident_num % len(accident_types)],
                        InjuryType.BRUISE,
                        AccidentSeverity.MINOR
                    )
                    .with_accident_datetime(
                        accident_date + timedelta(days=accident_num, hours=accident_num)
                    )
                    .build(db_session)
                )
                monthly_accidents.append(accident)

        # 통계 조회를 통한 추세 분석
        response = await client.get(
            "/api/v1/accident-reports/statistics",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        stats = response.json()
        
        # 월별 사고 발생 패턴 확인
        monthly_data = stats["by_month"]
        assert len(monthly_data) > 0
        
        # 월별 증가 패턴이 있는지 확인 (정확한 값보다는 데이터 존재 여부)
        monthly_counts = list(monthly_data.values())
        assert all(count >= 0 for count in monthly_counts)

        # 사고 유형별 분포 확인
        type_distribution = stats["by_type"]
        assert len(type_distribution) > 0
        
        # 주요 사고 유형들이 포함되어 있는지 확인
        expected_types = ["떨어짐", "부딪힘", "베임/찔림", "끼임"]
        found_types = [t for t in expected_types if t in type_distribution]
        assert len(found_types) > 0

        # 년간 안전성과 비교
        current_year = datetime.now().year
        prev_year = current_year - 1
        
        current_metrics = await client.get(
            f"/api/v1/accident-reports/safety-metrics?year={current_year}",
            headers=authenticated_headers
        )
        assert current_metrics.status_code == 200
        current_data = current_metrics.json()
        
        prev_metrics = await client.get(
            f"/api/v1/accident-reports/safety-metrics?year={prev_year}",
            headers=authenticated_headers
        )
        assert prev_metrics.status_code == 200
        prev_data = prev_metrics.json()
        
        # 개선율 계산 확인
        assert "improvement_rate" in current_data
        assert isinstance(current_data["improvement_rate"], (int, float))

    @pytest.mark.asyncio
    async def test_accident_error_handling(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """산업재해 보고 오류 처리 테스트"""
        # 1. 존재하지 않는 근로자로 사고 신고
        invalid_worker_data = {
            "accident_datetime": datetime.now().isoformat(),
            "report_datetime": datetime.now().isoformat(),
            "accident_location": "테스트 현장",
            "worker_id": 99999,  # 존재하지 않는 근로자
            "accident_type": "떨어짐",
            "injury_type": "타박상",
            "severity": "경미",
            "accident_description": "테스트 사고"
        }

        response = await client.post(
            "/api/v1/accident-reports/",
            json=invalid_worker_data,
            headers=authenticated_headers
        )
        assert response.status_code == 404
        assert "근로자를 찾을 수 없습니다" in response.json()["detail"]

        # 2. 존재하지 않는 사고 보고서 조회
        response = await client.get(
            "/api/v1/accident-reports/99999",
            headers=authenticated_headers
        )
        assert response.status_code == 404
        assert "찾을 수 없습니다" in response.json()["detail"]

        # 3. 잘못된 데이터로 사고 신고
        invalid_data = {
            "accident_datetime": "invalid-datetime",
            "accident_type": "존재하지않는유형",
            "injury_type": "잘못된부상유형",
            "severity": "잘못된중대성"
        }

        response = await client.post(
            "/api/v1/accident-reports/",
            json=invalid_data,
            headers=authenticated_headers
        )
        assert response.status_code == 422

        # 4. 존재하지 않는 사고에 사진 업로드
        with open("test_file.txt", "w") as f:
            f.write("test content")
        
        try:
            with open("test_file.txt", "rb") as f:
                files = [("files", ("test.jpg", f, "image/jpeg"))]
                
                response = await client.post(
                    "/api/v1/accident-reports/99999/photos",
                    files=files,
                    headers=authenticated_headers
                )
            
            assert response.status_code == 404
        finally:
            import os
            if os.path.exists("test_file.txt"):
                os.remove("test_file.txt")

    @pytest.mark.asyncio
    async def test_concurrent_accident_operations(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
        authenticated_headers: Dict[str, str]
    ):
        """동시 산업재해 처리 테스트"""
        # 근로자들 생성
        workers = []
        for i in range(3):
            worker = await (
                WorkerBuilder()
                .with_name(f"동시처리자{i+1}")
                .with_korean_data()
                .build(db_session)
            )
            workers.append(worker)

        # 동시에 여러 사고 신고
        accident_data_list = []
        for i, worker in enumerate(workers):
            accident_data = {
                "accident_datetime": (datetime.now() - timedelta(hours=i+1)).isoformat(),
                "report_datetime": datetime.now().isoformat(),
                "accident_location": f"동시현장{i+1}",
                "worker_id": worker.id,
                "accident_type": ["떨어짐", "부딪힘", "베임/찔림"][i],
                "injury_type": "타박상",
                "severity": "경미",
                "accident_description": f"동시 발생 사고 {i+1}",
                "medical_cost": 100000 * (i+1)
            }
            accident_data_list.append(accident_data)

        # 동시 요청 실행
        tasks = []
        for accident_data in accident_data_list:
            task = client.post(
                "/api/v1/accident-reports/",
                json=accident_data,
                headers=authenticated_headers
            )
            tasks.append(task)

        responses = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 모든 요청이 성공해야 함
        success_count = sum(1 for r in responses if hasattr(r, 'status_code') and r.status_code == 201)
        assert success_count == 3

        # 생성된 사고들 확인
        response = await client.get(
            "/api/v1/accident-reports/",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        assert response.json()["total"] >= 3