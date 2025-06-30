"""
근로자 리포지토리
Worker repository with specialized business logic
"""

from typing import List, Dict, Any, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_
from datetime import datetime, date

from .base import BaseRepository
from ..models.worker import Worker
from ..schemas.worker import WorkerCreate, WorkerUpdate
import logging

logger = logging.getLogger(__name__)


class WorkerRepository(BaseRepository[Worker, WorkerCreate, WorkerUpdate]):
    """근로자 전용 리포지토리"""
    
    def __init__(self):
        super().__init__(Worker)
    
    async def get_by_employee_id(self, db: AsyncSession, *, employee_id: str) -> Optional[Worker]:
        """사번으로 근로자 조회"""
        try:
            result = await db.execute(
                select(Worker).where(Worker.employee_id == employee_id)
            )
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"사번 {employee_id} 조회 실패: {e}")
            return None
    
    async def get_workers_by_department(
        self, 
        db: AsyncSession, 
        *, 
        department: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Worker], int]:
        """부서별 근로자 조회"""
        try:
            query = select(Worker).where(Worker.department.ilike(f"%{department}%"))
            count_query = select(func.count(Worker.id)).where(Worker.department.ilike(f"%{department}%"))
            
            query = query.offset(skip).limit(limit).order_by(Worker.name)
            
            result = await db.execute(query)
            count_result = await db.execute(count_query)
            
            workers = result.scalars().all()
            total = count_result.scalar()
            
            logger.info(f"부서 '{department}' 근로자 조회: {len(workers)}명")
            return workers, total
            
        except Exception as e:
            logger.error(f"부서별 근로자 조회 실패: {e}")
            return [], 0
    
    async def get_workers_by_health_status(
        self, 
        db: AsyncSession, 
        *, 
        health_status: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Worker], int]:
        """건강 상태별 근로자 조회"""
        try:
            query = select(Worker).where(Worker.health_status == health_status)
            count_query = select(func.count(Worker.id)).where(Worker.health_status == health_status)
            
            query = query.offset(skip).limit(limit).order_by(Worker.name)
            
            result = await db.execute(query)
            count_result = await db.execute(count_query)
            
            workers = result.scalars().all()
            total = count_result.scalar()
            
            logger.info(f"건강상태 '{health_status}' 근로자 조회: {len(workers)}명")
            return workers, total
            
        except Exception as e:
            logger.error(f"건강상태별 근로자 조회 실패: {e}")
            return [], 0
    
    async def get_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """근로자 통계 정보"""
        try:
            # 기본 통계
            total_result = await db.execute(select(func.count(Worker.id)))
            total = total_result.scalar()
            
            # 성별 통계
            gender_stats = await db.execute(
                select(Worker.gender, func.count(Worker.id))
                .group_by(Worker.gender)
            )
            gender_counts = {row[0] or "미분류": row[1] for row in gender_stats.fetchall()}
            
            # 고용형태별 통계
            employment_stats = await db.execute(
                select(Worker.employment_type, func.count(Worker.id))
                .group_by(Worker.employment_type)
            )
            employment_counts = {row[0]: row[1] for row in employment_stats.fetchall()}
            
            # 건강상태별 통계
            health_stats = await db.execute(
                select(Worker.health_status, func.count(Worker.id))
                .group_by(Worker.health_status)
            )
            health_counts = {row[0]: row[1] for row in health_stats.fetchall()}
            
            # 작업유형별 통계
            work_stats = await db.execute(
                select(Worker.work_type, func.count(Worker.id))
                .group_by(Worker.work_type)
            )
            work_counts = {row[0]: row[1] for row in work_stats.fetchall()}
            
            # 부서별 통계 (상위 5개)
            dept_stats = await db.execute(
                select(Worker.department, func.count(Worker.id))
                .where(Worker.department.is_not(None))
                .group_by(Worker.department)
                .order_by(func.count(Worker.id).desc())
                .limit(5)
            )
            dept_counts = {row[0]: row[1] for row in dept_stats.fetchall()}
            
            logger.info(f"근로자 통계 조회 완료: 총 {total}명")
            
            return {
                "total": total,
                "by_gender": gender_counts,
                "by_employment_type": employment_counts,
                "by_health_status": health_counts,
                "by_work_type": work_counts,
                "by_department": dept_counts,
                "model": "Worker"
            }
            
        except Exception as e:
            logger.error(f"근로자 통계 조회 실패: {e}")
            return {
                "total": 0,
                "by_gender": {},
                "by_employment_type": {},
                "by_health_status": {},
                "by_work_type": {},
                "by_department": {},
                "model": "Worker"
            }
    
    async def search_workers(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        skip: int = 0,
        limit: int = 100
    ) -> tuple[List[Worker], int]:
        """근로자 통합 검색 (이름, 사번, 부서, 직책)"""
        try:
            if not search_term.strip():
                return await self.get_multi(db, skip=skip, limit=limit)
            
            search_filter = or_(
                Worker.name.ilike(f"%{search_term}%"),
                Worker.employee_id.ilike(f"%{search_term}%"),
                Worker.department.ilike(f"%{search_term}%"),
                Worker.position.ilike(f"%{search_term}%")
            )
            
            query = select(Worker).where(search_filter)
            count_query = select(func.count(Worker.id)).where(search_filter)
            
            query = query.order_by(Worker.name).offset(skip).limit(limit)
            
            result = await db.execute(query)
            count_result = await db.execute(count_query)
            
            workers = result.scalars().all()
            total = count_result.scalar()
            
            logger.info(f"근로자 검색 완료: '{search_term}' -> {len(workers)}명")
            return workers, total
            
        except Exception as e:
            logger.error(f"근로자 검색 실패: {e}")
            return [], 0
    
    async def get_workers_needing_health_exam(
        self, 
        db: AsyncSession,
        *, 
        months_since_last_exam: int = 12
    ) -> List[Worker]:
        """건강진단이 필요한 근로자 조회"""
        try:
            # 현재 날짜에서 지정된 개월 수를 뺀 날짜
            cutoff_date = datetime.now().date()
            # 단순화: last_health_exam 필드가 있다고 가정
            
            query = select(Worker).where(
                or_(
                    Worker.last_health_exam.is_(None),
                    Worker.last_health_exam < cutoff_date
                )
            ).order_by(Worker.last_health_exam.asc())
            
            result = await db.execute(query)
            workers = result.scalars().all()
            
            logger.info(f"건강진단 필요 근로자: {len(workers)}명")
            return workers
            
        except Exception as e:
            logger.error(f"건강진단 필요 근로자 조회 실패: {e}")
            return []
    
    async def update_health_status(
        self,
        db: AsyncSession,
        *,
        worker_id: int,
        new_status: str,
        notes: Optional[str] = None
    ) -> Optional[Worker]:
        """근로자 건강상태 업데이트"""
        try:
            worker = await self.get_by_id(db, id=worker_id)
            if not worker:
                return None
            
            worker.health_status = new_status
            if notes:
                # 건강상태 변경 이력을 notes에 추가
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
                new_note = f"[{timestamp}] 건강상태 변경: {new_status}"
                if notes:
                    new_note += f" - {notes}"
                
                if worker.notes:
                    worker.notes = f"{worker.notes}\n{new_note}"
                else:
                    worker.notes = new_note
            
            await db.commit()
            await db.refresh(worker)
            
            logger.info(f"근로자 {worker.name}({worker.employee_id}) 건강상태 업데이트: {new_status}")
            return worker
            
        except Exception as e:
            await db.rollback()
            logger.error(f"건강상태 업데이트 실패: {e}")
            return None


# 싱글톤 인스턴스
worker_repository = WorkerRepository()