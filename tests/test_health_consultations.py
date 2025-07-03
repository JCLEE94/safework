"""
보건상담 관리 API 테스트
Health Consultation Management API Tests
"""

import pytest
import pytest_asyncio
from datetime import datetime, date, timedelta
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.health_consultation import HealthConsultation, ConsultationType, ConsultationStatus, HealthIssueCategory
from src.models.worker import Worker
from src.schemas.health_consultation import HealthConsultationCreate, HealthConsultationUpdate


@pytest_asyncio.fixture
async def test_worker(async_session: AsyncSession):
    """테스트용 근로자 생성"""
    worker = Worker(
        employee_id="TEST001",
        name="김건강",
        birth_date=date(1985, 1, 1),
        gender="male",
        employment_type="regular",
        work_type="construction",
        hire_date=date(2020, 1, 1),
        department="건설팀",
        position="기술자",
        is_active=True
    )
    async_session.add(worker)
    await async_session.commit()
    await async_session.refresh(worker)
    return worker


@pytest_asyncio.fixture
async def test_consultation(async_session: AsyncSession, test_worker: Worker):
    """테스트용 보건상담 생성"""
    consultation = HealthConsultation(
        worker_id=test_worker.id,
        consultation_date=datetime.now(),
        consultation_type=ConsultationType.ROUTINE,
        chief_complaint="두통과 어지러움 증상",
        symptoms="하루 종일 지속되는 두통",
        consultation_location="현장 사무실",
        consultant_name="이보건",
        consultation_content="근로자가 두통을 호소하여 상담 진행",
        recommendations="충분한 휴식과 수분섭취 권고",
        status=ConsultationStatus.COMPLETED,
        health_issue_category=HealthIssueCategory.OTHER,
        work_related=True,
        referral_needed=False,
        follow_up_needed=True,
        follow_up_date=date.today() + timedelta(days=7)
    )
    async_session.add(consultation)
    await async_session.commit()
    await async_session.refresh(consultation)
    return consultation


class TestHealthConsultationAPI:
    """보건상담 API 테스트"""

    async def test_create_consultation(self, async_client, test_worker: Worker):
        """보건상담 등록 테스트"""
        consultation_data = {
            "worker_id": test_worker.id,
            "consultation_date": datetime.now().isoformat(),
            "consultation_type": "정기상담",
            "chief_complaint": "목과 어깨 결림",
            "symptoms": "장시간 작업으로 인한 근육 경직",
            "consultation_location": "현장 사무실",
            "consultant_name": "박보건",
            "consultation_content": "근골격계 문제로 상담 진행",
            "recommendations": "스트레칭과 자세 교정 지도",
            "status": "완료",
            "health_issue_category": "근골격계",
            "work_related": True,
            "referral_needed": False,
            "follow_up_needed": True,
            "follow_up_date": (date.today() + timedelta(days=14)).isoformat()
        }

        response = await async_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["worker_id"] == test_worker.id
        assert data["consultation_type"] == "정기상담"
        assert data["chief_complaint"] == "목과 어깨 결림"
        assert data["work_related"] is True
        assert data["follow_up_needed"] is True

    async def test_get_consultations(self, async_client, test_consultation: HealthConsultation):
        """보건상담 목록 조회 테스트"""
        response = await async_client.get("/api/v1/health-consultations/")
        assert response.status_code == 200
        
        data = response.json()
        assert "items" in data
        assert data["total"] >= 1
        assert len(data["items"]) >= 1
        
        consultation = data["items"][0]
        assert consultation["id"] == test_consultation.id
        assert "worker_name" in consultation
        assert "consultation_date" in consultation

    async def test_get_consultation_by_id(self, async_client, test_consultation: HealthConsultation):
        """특정 보건상담 조회 테스트"""
        response = await async_client.get(f"/api/v1/health-consultations/{test_consultation.id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["id"] == test_consultation.id
        assert data["consultation_type"] == test_consultation.consultation_type.value
        assert data["chief_complaint"] == test_consultation.chief_complaint

    async def test_update_consultation(self, async_client, test_consultation: HealthConsultation):
        """보건상담 수정 테스트"""
        update_data = {
            "chief_complaint": "수정된 호소사항",
            "consultation_content": "수정된 상담 내용",
            "recommendations": "수정된 권고사항",
            "status": "완료"
        }

        response = await async_client.put(f"/api/v1/health-consultations/{test_consultation.id}", json=update_data)
        assert response.status_code == 200
        
        data = response.json()
        assert data["chief_complaint"] == "수정된 호소사항"
        assert data["consultation_details"] == "수정된 상담 내용"
        assert data["action_taken"] == "수정된 권고사항"

    async def test_delete_consultation(self, async_client, test_consultation: HealthConsultation):
        """보건상담 삭제 테스트"""
        response = await async_client.delete(f"/api/v1/health-consultations/{test_consultation.id}")
        assert response.status_code == 204

        # 삭제 확인
        response = await async_client.get(f"/api/v1/health-consultations/{test_consultation.id}")
        assert response.status_code == 404

    async def test_filter_consultations_by_type(self, async_client, test_consultation: HealthConsultation):
        """상담유형별 필터링 테스트"""
        response = await async_client.get(f"/api/v1/health-consultations/?consultation_type={test_consultation.consultation_type.value}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["consultation_type"] == test_consultation.consultation_type.value

    async def test_filter_consultations_by_worker(self, async_client, test_consultation: HealthConsultation):
        """근로자별 필터링 테스트"""
        response = await async_client.get(f"/api/v1/health-consultations/?worker_id={test_consultation.worker_id}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1
        for item in data["items"]:
            assert item["worker_id"] == test_consultation.worker_id

    async def test_filter_consultations_by_date_range(self, async_client, test_consultation: HealthConsultation):
        """날짜 범위별 필터링 테스트"""
        start_date = (date.today() - timedelta(days=1)).isoformat()
        end_date = (date.today() + timedelta(days=1)).isoformat()
        
        response = await async_client.get(f"/api/v1/health-consultations/?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1

    async def test_search_consultations(self, async_client, test_consultation: HealthConsultation):
        """상담 검색 테스트"""
        # 근로자명으로 검색
        response = await async_client.get("/api/v1/health-consultations/?search=김건강")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1
        
        # 상담내용으로 검색
        response = await async_client.get("/api/v1/health-consultations/?search=두통")
        assert response.status_code == 200
        
        data = response.json()
        assert data["total"] >= 1

    async def test_consultation_statistics(self, async_client, test_consultation: HealthConsultation):
        """보건상담 통계 테스트"""
        response = await async_client.get("/api/v1/health-consultations/statistics/summary")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_consultations" in data
        assert "consultation_types" in data
        assert "monthly_statistics" in data
        assert data["total_consultations"] >= 1

    async def test_consultation_statistics_with_date_filter(self, async_client, test_consultation: HealthConsultation):
        """날짜 필터가 적용된 통계 테스트"""
        start_date = (date.today() - timedelta(days=30)).isoformat()
        end_date = date.today().isoformat()
        
        response = await async_client.get(f"/api/v1/health-consultations/statistics/summary?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        
        data = response.json()
        assert "total_consultations" in data
        assert "period" in data
        assert data["period"]["start_date"] == start_date
        assert data["period"]["end_date"] == end_date

    async def test_create_consultation_invalid_worker(self, async_client):
        """존재하지 않는 근로자로 상담 등록 테스트"""
        consultation_data = {
            "worker_id": 99999,  # 존재하지 않는 ID
            "consultation_date": datetime.now().isoformat(),
            "consultation_type": "정기상담",
            "chief_complaint": "테스트",
            "consultation_location": "현장 사무실",
            "consultant_name": "테스트",
            "consultation_content": "테스트 내용",
            "status": "예정"
        }

        response = await async_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 404

    async def test_create_consultation_missing_required_fields(self, async_client, test_worker: Worker):
        """필수 필드 누락 시 상담 등록 테스트"""
        consultation_data = {
            "worker_id": test_worker.id,
            # consultation_date 누락
            "consultation_type": "정기상담"
        }

        response = await async_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 422

    async def test_update_nonexistent_consultation(self, async_client):
        """존재하지 않는 상담 수정 테스트"""
        update_data = {
            "chief_complaint": "수정된 호소사항"
        }

        response = await async_client.put("/api/v1/health-consultations/99999", json=update_data)
        assert response.status_code == 404

    async def test_delete_nonexistent_consultation(self, async_client):
        """존재하지 않는 상담 삭제 테스트"""
        response = await async_client.delete("/api/v1/health-consultations/99999")
        assert response.status_code == 404

    async def test_consultation_with_follow_up(self, async_client, test_worker: Worker):
        """추적관찰이 필요한 상담 등록 테스트"""
        consultation_data = {
            "worker_id": test_worker.id,
            "consultation_date": datetime.now().isoformat(),
            "consultation_type": "건강문제",
            "chief_complaint": "지속적인 기침",
            "consultation_location": "의무실",
            "consultant_name": "이의사",
            "consultation_content": "호흡기 증상으로 추적관찰 필요",
            "recommendations": "금연 및 정기 검진 권고",
            "status": "완료",
            "health_issue_category": "호흡기",
            "follow_up_needed": True,
            "follow_up_date": (date.today() + timedelta(days=30)).isoformat(),
            "follow_up_notes": "1개월 후 증상 재확인"
        }

        response = await async_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["follow_up_needed"] is True
        assert data["follow_up_date"] is not None

    async def test_consultation_with_referral(self, async_client, test_worker: Worker):
        """의료기관 의뢰가 필요한 상담 등록 테스트"""
        consultation_data = {
            "worker_id": test_worker.id,
            "consultation_date": datetime.now().isoformat(),
            "consultation_type": "응급상담",
            "chief_complaint": "심한 복통",
            "consultation_location": "현장",
            "consultant_name": "응급의료진",
            "consultation_content": "급성 복통으로 병원 이송 필요",
            "recommendations": "즉시 병원 진료 권고",
            "status": "완료",
            "referral_needed": True,
            "referral_details": "○○병원 응급실 이송"
        }

        response = await async_client.post("/api/v1/health-consultations/", json=consultation_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["referral_needed"] is True


class TestHealthConsultationModel:
    """보건상담 모델 테스트"""

    async def test_consultation_creation(self, async_session: AsyncSession, test_worker: Worker):
        """보건상담 생성 테스트"""
        consultation = HealthConsultation(
            worker_id=test_worker.id,
            consultation_date=datetime.now(),
            consultation_type=ConsultationType.HEALTH_ISSUE,
            chief_complaint="피부 발진",
            consultation_location="의무실",
            consultant_name="피부과전문의",
            consultation_content="작업 중 화학물질 접촉으로 인한 피부 문제",
            status=ConsultationStatus.COMPLETED,
            health_issue_category=HealthIssueCategory.SKIN
        )

        async_session.add(consultation)
        await async_session.commit()
        await async_session.refresh(consultation)

        assert consultation.id is not None
        assert consultation.worker_id == test_worker.id
        assert consultation.consultation_type == ConsultationType.HEALTH_ISSUE
        assert consultation.health_issue_category == HealthIssueCategory.SKIN

    async def test_consultation_worker_relationship(self, async_session: AsyncSession, test_consultation: HealthConsultation):
        """보건상담-근로자 관계 테스트"""
        # 관계 로딩 확인
        await async_session.refresh(test_consultation, attribute_names=['worker'])
        
        assert test_consultation.worker is not None
        assert test_consultation.worker.name == "김건강"
        assert test_consultation.worker.employee_id == "TEST001"

    async def test_consultation_enum_values(self, async_session: AsyncSession, test_worker: Worker):
        """보건상담 열거형 값 테스트"""
        consultation = HealthConsultation(
            worker_id=test_worker.id,
            consultation_date=datetime.now(),
            consultation_type=ConsultationType.OCCUPATIONAL_DISEASE,
            chief_complaint="직업병 의심 증상",
            consultation_location="병원",
            consultant_name="산업의학전문의",
            consultation_content="직업병 관련 정밀 검사 필요",
            status=ConsultationStatus.IN_PROGRESS,
            health_issue_category=HealthIssueCategory.RESPIRATORY
        )

        async_session.add(consultation)
        await async_session.commit()

        assert consultation.consultation_type == ConsultationType.OCCUPATIONAL_DISEASE
        assert consultation.status == ConsultationStatus.IN_PROGRESS
        assert consultation.health_issue_category == HealthIssueCategory.RESPIRATORY


class TestHealthConsultationSchema:
    """보건상담 스키마 테스트"""

    def test_consultation_create_schema(self):
        """보건상담 생성 스키마 테스트"""
        data = {
            "worker_id": 1,
            "consultation_date": datetime.now(),
            "consultation_type": "정기상담",
            "chief_complaint": "두통",
            "consultation_location": "현장 사무실",
            "consultant_name": "보건관리자",
            "consultation_content": "두통 상담",
            "status": "완료"
        }

        schema = HealthConsultationCreate(**data)
        assert schema.worker_id == 1
        assert schema.consultation_type == "정기상담"
        assert schema.chief_complaint == "두통"

    def test_consultation_update_schema(self):
        """보건상담 수정 스키마 테스트"""
        data = {
            "chief_complaint": "수정된 호소사항",
            "recommendations": "새로운 권고사항"
        }

        schema = HealthConsultationUpdate(**data)
        assert schema.chief_complaint == "수정된 호소사항"
        assert schema.recommendations == "새로운 권고사항"

    def test_consultation_schema_optional_fields(self):
        """보건상담 스키마 선택적 필드 테스트"""
        # 최소 필수 필드만으로 생성
        data = {
            "worker_id": 1,
            "consultation_date": datetime.now(),
            "consultation_type": "정기상담",
            "chief_complaint": "두통",
            "consultation_location": "현장 사무실",
            "consultant_name": "보건관리자",
            "consultation_content": "두통 상담"
        }

        schema = HealthConsultationCreate(**data)
        assert schema.symptoms is None
        assert schema.health_issue_category is None
        assert schema.referral_needed is False
        assert schema.follow_up_needed is False