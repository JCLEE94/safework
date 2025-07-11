"""
Base Repository Integration Tests - Database Operations
Inline tests for core database functionality
"""

import os
import asyncio
from datetime import datetime, date
from typing import List

from sqlalchemy import select, func, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError, OperationalError

from src.models import Worker, HealthExam, WorkEnvironment, ChemicalSubstance
from src.testing import integration_test, run_inline_tests, create_test_environment, measure_performance


class IntegrationTestDatabase:
    """Database integration tests - transaction, concurrency, performance"""
    
    @integration_test
    @measure_performance
    async def test_transaction_rollback(self):
        """트랜잭션 롤백 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 트랜잭션 시작
                worker = Worker(
                    name="롤백테스트",
                    employee_id="ROLLBACK_001",
                    department="테스트부"
                )
                session.add(worker)
                await session.flush()  # ID 생성
                
                worker_id = worker.id
                assert worker_id is not None
                
                # 의도적으로 에러 발생
                try:
                    # 중복 사번으로 또 다른 근로자 생성
                    duplicate = Worker(
                        name="중복근로자",
                        employee_id="ROLLBACK_001",  # 같은 사번
                        department="테스트부"
                    )
                    session.add(duplicate)
                    await session.commit()
                    assert False, "중복 사번 에러가 발생해야 합니다"
                except IntegrityError:
                    await session.rollback()
                
                # 롤백 확인 - 첫 번째 근로자도 없어야 함
                result = await session.execute(
                    select(Worker).where(Worker.id == worker_id)
                )
                assert result.scalar() is None, "트랜잭션이 롤백되지 않았습니다"
    
    @integration_test
    async def test_concurrent_updates(self):
        """동시 업데이트 처리 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            # 테스트 근로자 생성
            async with db.get_session() as session:
                worker = Worker(
                    name="동시성테스트",
                    employee_id="CONCUR_001",
                    department="개발부",
                    health_status="정상"
                )
                session.add(worker)
                await session.commit()
                worker_id = worker.id
            
            # 두 개의 동시 세션에서 업데이트
            async def update_department(dept: str):
                async with db.get_session() as session:
                    result = await session.execute(
                        select(Worker).where(Worker.id == worker_id)
                    )
                    worker = result.scalar_one()
                    worker.department = dept
                    await asyncio.sleep(0.1)  # 동시성 시뮬레이션
                    await session.commit()
            
            async def update_health_status(status: str):
                async with db.get_session() as session:
                    result = await session.execute(
                        select(Worker).where(Worker.id == worker_id)
                    )
                    worker = result.scalar_one()
                    worker.health_status = status
                    await asyncio.sleep(0.1)  # 동시성 시뮬레이션
                    await session.commit()
            
            # 동시 실행
            await asyncio.gather(
                update_department("영업부"),
                update_health_status("요관찰")
            )
            
            # 결과 확인
            async with db.get_session() as session:
                result = await session.execute(
                    select(Worker).where(Worker.id == worker_id)
                )
                worker = result.scalar_one()
                assert worker.department == "영업부"
                assert worker.health_status == "요관찰"
    
    @integration_test
    async def test_cascade_operations(self):
        """캐스케이드 삭제 동작 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 근로자와 관련 데이터 생성
                worker = Worker(
                    name="캐스케이드테스트",
                    employee_id="CASCADE_001",
                    department="테스트부"
                )
                session.add(worker)
                await session.flush()
                
                # 건강검진 기록 추가
                exam = HealthExam(
                    worker_id=worker.id,
                    exam_date=date.today(),
                    exam_type="일반건강진단",
                    exam_agency="테스트병원",
                    overall_result="정상"
                )
                session.add(exam)
                await session.commit()
                
                worker_id = worker.id
                exam_id = exam.id
                
                # 근로자 삭제 (소프트 삭제)
                worker.deleted_at = datetime.now()
                await session.commit()
                
                # 건강검진 기록은 그대로 유지되어야 함
                result = await session.execute(
                    select(HealthExam).where(HealthExam.id == exam_id)
                )
                exam = result.scalar()
                assert exam is not None, "관련 데이터가 함께 삭제되면 안 됩니다"
    
    @integration_test
    @measure_performance
    async def test_bulk_insert_performance(self):
        """대량 삽입 성능 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 1000건 데이터 준비
                workers = []
                for i in range(1000):
                    workers.append(Worker(
                        name=f"성능테스트{i:04d}",
                        employee_id=f"PERF_{i:04d}",
                        department="성능테스트부",
                        work_type="제조",
                        employment_type="정규직"
                    ))
                
                # 대량 삽입
                start_time = datetime.now()
                session.add_all(workers)
                await session.commit()
                duration = (datetime.now() - start_time).total_seconds()
                
                # 성능 검증
                assert duration < 5.0, f"1000건 삽입이 너무 느립니다: {duration}초"
                
                # 데이터 확인
                result = await session.execute(
                    select(func.count(Worker.id)).where(
                        Worker.employee_id.like("PERF_%")
                    )
                )
                count = result.scalar()
                assert count == 1000, f"예상 1000건, 실제 {count}건"
    
    @integration_test
    async def test_complex_queries(self):
        """복잡한 쿼리 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 테스트 데이터 생성
                departments = ["건설부", "안전관리팀", "생산부"]
                for dept_idx, dept in enumerate(departments):
                    for i in range(10):
                        worker = Worker(
                            name=f"{dept}근로자{i:02d}",
                            employee_id=f"COMPLEX_{dept_idx}_{i:02d}",
                            department=dept,
                            work_type="건설" if dept == "건설부" else "제조",
                            employment_type="정규직" if i % 2 == 0 else "계약직",
                            health_status="정상" if i % 3 != 0 else "요관찰"
                        )
                        session.add(worker)
                await session.commit()
                
                # 1. 조인 쿼리
                # 각 부서별 정규직 수
                result = await session.execute(
                    select(
                        Worker.department,
                        func.count(Worker.id).label("count")
                    )
                    .where(Worker.employment_type == "정규직")
                    .group_by(Worker.department)
                    .order_by(func.count(Worker.id).desc())
                )
                dept_counts = result.all()
                assert len(dept_counts) == 3
                assert all(count == 5 for _, count in dept_counts)
                
                # 2. 서브쿼리
                # 요관찰 근로자가 있는 부서
                subquery = select(Worker.department).where(
                    Worker.health_status == "요관찰"
                ).distinct().subquery()
                
                result = await session.execute(
                    select(Worker).where(
                        Worker.department.in_(select(subquery))
                    )
                )
                workers_in_dept = result.scalars().all()
                assert len(workers_in_dept) > 0
                
                # 3. 복합 조건
                result = await session.execute(
                    select(Worker).where(
                        and_(
                            or_(
                                Worker.department == "건설부",
                                Worker.department == "안전관리팀"
                            ),
                            Worker.employment_type == "정규직",
                            Worker.health_status == "정상"
                        )
                    )
                )
                filtered_workers = result.scalars().all()
                assert all(
                    w.employment_type == "정규직" and 
                    w.health_status == "정상" and
                    w.department in ["건설부", "안전관리팀"]
                    for w in filtered_workers
                )
    
    @integration_test
    async def test_korean_text_handling(self):
        """한글 텍스트 처리 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 다양한 한글 텍스트 테스트
                test_cases = [
                    ("홍길동", "일반적인 이름"),
                    ("김수한무거북이와두루미", "긴 이름"),
                    ("ㄱㄴㄷ", "자음만"),
                    ("ㅏㅑㅓㅕ", "모음만"),
                    ("test테스트123", "영문+한글+숫자"),
                    ("🏗️건설현장👷", "이모지 포함")
                ]
                
                for idx, (name, desc) in enumerate(test_cases):
                    worker = Worker(
                        name=name,
                        employee_id=f"KOREAN_{idx:02d}",
                        department=desc,
                        notes=f"테스트: {desc}"
                    )
                    session.add(worker)
                
                await session.commit()
                
                # 검색 테스트
                for idx, (name, desc) in enumerate(test_cases):
                    result = await session.execute(
                        select(Worker).where(Worker.name == name)
                    )
                    worker = result.scalar_one()
                    assert worker.name == name
                    assert worker.department == desc
                
                # LIKE 검색
                result = await session.execute(
                    select(Worker).where(Worker.name.like("%테스트%"))
                )
                workers = result.scalars().all()
                assert len(workers) >= 1
    
    @integration_test
    async def test_date_timezone_handling(self):
        """날짜/시간대 처리 테스트"""
        async with create_test_environment() as env:
            db = env["db"]
            
            async with db.get_session() as session:
                # 다양한 날짜 입력
                test_dates = [
                    date(2024, 1, 1),
                    date(2024, 12, 31),
                    date(1990, 5, 15),
                    date.today()
                ]
                
                for idx, test_date in enumerate(test_dates):
                    worker = Worker(
                        name=f"날짜테스트{idx}",
                        employee_id=f"DATE_{idx:02d}",
                        birth_date=test_date,
                        join_date=test_date
                    )
                    session.add(worker)
                
                await session.commit()
                
                # 날짜 범위 검색
                result = await session.execute(
                    select(Worker).where(
                        Worker.birth_date.between(
                            date(2024, 1, 1),
                            date(2024, 12, 31)
                        )
                    )
                )
                workers_2024 = result.scalars().all()
                assert len(workers_2024) == 2
                
                # 타임스탬프 처리
                now = datetime.now()
                worker = Worker(
                    name="타임스탬프테스트",
                    employee_id="TIMESTAMP_001",
                    created_at=now,
                    updated_at=now
                )
                session.add(worker)
                await session.commit()
                
                # 재조회
                result = await session.execute(
                    select(Worker).where(Worker.employee_id == "TIMESTAMP_001")
                )
                worker = result.scalar_one()
                
                # 시간 정확도 (1초 이내)
                time_diff = abs((worker.created_at - now).total_seconds())
                assert time_diff < 1.0


# Run inline tests if module is executed directly
if __name__ == "__main__" or os.environ.get("RUN_INTEGRATION_TESTS"):
    if __name__ == "__main__":
        asyncio.run(run_inline_tests(__name__))