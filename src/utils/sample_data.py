"""
샘플 데이터 생성 스크립트
Sample data generation script for all modules
"""

import asyncio
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from src.config.database import init_db, get_db
from src.models import (
    Worker, HealthExam, WorkEnvironment, HealthEducation,
    ChemicalSubstance, AccidentReport, HealthConsultation
)


async def create_sample_data():
    """모든 모듈의 샘플 데이터 생성"""
    await init_db()
    
    async for db in get_db():
        try:
            # 1. Workers (이미 존재하는지 확인)
            result = await db.execute(select(Worker).where(Worker.employee_id == "EMP001"))
            worker = result.scalar_one_or_none()
            
            if not worker:
                worker = Worker(
                    name="김철수",
                    employee_id="EMP001", 
                    gender="male",
                    department="건설팀",
                    position="주임",
                    employment_type="regular",
                    work_type="construction",
                    hire_date=datetime.now().date(),
                    birth_date=datetime(1990, 1, 15).date(),
                    phone="010-1234-9999",
                    health_status="normal",
                    is_active=True
                )
                db.add(worker)
                await db.flush()
            
            # 2. Health Exams
            result = await db.execute(select(HealthExam).where(HealthExam.worker_id == worker.id))
            if not result.scalar_one_or_none():
                health_exam = HealthExam(
                    worker_id=worker.id,
                    exam_type="general",
                    exam_date=datetime.now().date(),
                    medical_institution="서울대학교병원",
                    exam_result="normal",
                    findings="정상소견",
                    recommendations="정기검진 지속",
                    next_exam_date=(datetime.now() + timedelta(days=365)).date(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(health_exam)
            
            # 3. Work Environment
            result = await db.execute(select(WorkEnvironment))
            if not result.scalar_one_or_none():
                work_env = WorkEnvironment(
                    measurement_date=datetime.now().date(),
                    location="1층 작업장",
                    measurement_type="noise",
                    measured_value=85.5,
                    unit="dB",
                    standard_value=90.0,
                    status="normal",
                    measuring_institution="한국산업안전보건공단",
                    next_measurement_date=(datetime.now() + timedelta(days=180)).date(),
                    remarks="정상 범위 내",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(work_env)
            
            # 4. Health Education
            result = await db.execute(select(HealthEducation))
            if not result.scalar_one_or_none():
                health_edu = HealthEducation(
                    education_date=datetime.now().date(),
                    education_type="safety",
                    topic="건설현장 안전교육",
                    duration_hours=2,
                    instructor="김안전",
                    location="2층 회의실",
                    attendees_count=25,
                    materials="안전수칙 매뉴얼",
                    completion_rate=100.0,
                    effectiveness_score=4.5,
                    next_education_date=(datetime.now() + timedelta(days=90)).date(),
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(health_edu)
            
            # 5. Chemical Substances
            result = await db.execute(select(ChemicalSubstance))
            if not result.scalar_one_or_none():
                chemical = ChemicalSubstance(
                    substance_name="톨루엔",
                    cas_number="108-88-3",
                    category="organic_solvent",
                    hazard_classification="인화성액체",
                    exposure_limit_twa=50.0,
                    exposure_limit_stel=150.0,
                    unit="ppm",
                    health_effects="중추신경계 억제, 피부염",
                    safety_measures="환기설비 가동, 보호장비 착용",
                    storage_conditions="서늘하고 건조한 곳",
                    usage_location="도장작업장",
                    supplier="한국화학",
                    msds_file_path="/uploads/msds/toluene_msds.pdf",
                    last_updated=datetime.now().date(),
                    status="active",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(chemical)
            
            # 6. Accident Reports
            result = await db.execute(select(AccidentReport))
            if not result.scalar_one_or_none():
                accident = AccidentReport(
                    report_date=datetime.now().date(),
                    incident_date=datetime.now().date(),
                    incident_time=datetime.now().time(),
                    location="3층 작업장",
                    accident_type="cut",
                    severity="minor",
                    injured_worker_id=worker.id,
                    description="작업 중 날카로운 도구에 의한 경미한 절상",
                    immediate_cause="부주의",
                    root_cause="안전장비 미착용",
                    corrective_actions="안전교육 강화, 보호장비 점검",
                    reported_by="현장관리자",
                    investigation_status="completed",
                    lost_time_days=0,
                    medical_treatment="응급처치",
                    cost_estimate=50000.0,
                    prevention_measures="작업 전 안전점검 의무화",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(accident)
            
            # 7. Health Consultations
            result = await db.execute(select(HealthConsultation))
            if not result.scalar_one_or_none():
                consultation = HealthConsultation(
                    consultation_date=datetime.now().date(),
                    worker_id=worker.id,
                    consultation_type="individual",
                    symptoms="어깨 통증",
                    diagnosis="근골격계 질환 의심",
                    treatment_plan="물리치료, 작업자세 교정",
                    medication="소염진통제",
                    follow_up_date=(datetime.now() + timedelta(days=14)).date(),
                    consultant_name="이의사",
                    recommendations="정기적인 스트레칭, 작업환경 개선",
                    status="ongoing",
                    created_at=datetime.now(),
                    updated_at=datetime.now()
                )
                db.add(consultation)
            
            await db.commit()
            print("✅ 모든 모듈의 샘플 데이터 생성 완료!")
            break
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 샘플 데이터 생성 실패: {e}")
            raise


async def clear_all_data():
    """모든 데이터 삭제 (테스트용)"""
    await init_db()
    
    async for db in get_db():
        try:
            # 외래키 순서를 고려하여 삭제 (자식 테이블부터)
            tables_to_clear = [
                HealthConsultation,
                AccidentReport, 
                ChemicalSubstance,
                HealthEducation,
                WorkEnvironment,
                HealthExam,
                Worker
            ]
            
            for table in tables_to_clear:
                await db.execute(f"DELETE FROM {table.__tablename__}")
            
            await db.commit()
            print("✅ 모든 데이터 삭제 완료!")
            break
            
        except Exception as e:
            await db.rollback()
            print(f"❌ 데이터 삭제 실패: {e}")
            raise


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "clear":
        asyncio.run(clear_all_data())
    else:
        asyncio.run(create_sample_data())