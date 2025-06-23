"""
근로자 서비스 레이어
Worker service layer for business logic
"""

from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, date
import logging

from ..repositories.worker import worker_repository
from ..models.worker import Worker
from ..schemas.worker import WorkerCreate, WorkerUpdate, WorkerResponse
from .translation import translation_service

logger = logging.getLogger(__name__)


class WorkerService:
    """근로자 비즈니스 로직 서비스"""
    
    def __init__(self):
        self.repository = worker_repository
        self.translator = translation_service
    
    async def create_worker(
        self, 
        db: AsyncSession, 
        worker_data: WorkerCreate
    ) -> Worker:
        """근로자 생성 (비즈니스 로직 포함)"""
        try:
            # 1. 사번 중복 검사
            existing_worker = await self.repository.get_by_employee_id(
                db, employee_id=worker_data.employee_id
            )
            
            if existing_worker:
                raise ValueError(f"이미 존재하는 사번입니다: {worker_data.employee_id}")
            
            # 2. 데이터 번역 (한국어 -> 영어)
            worker_dict = worker_data.model_dump()
            translated_data = self.translator.translate_worker_data(
                worker_dict, to_english=True
            )
            
            # 3. 비즈니스 규칙 적용
            translated_data = self._apply_business_rules(translated_data)
            
            # 4. 근로자 생성
            create_schema = WorkerCreate(**translated_data)
            worker = await self.repository.create(db, obj_in=create_schema)
            
            logger.info(f"근로자 생성 완료: {worker.name}({worker.employee_id})")
            return worker
            
        except Exception as e:
            logger.error(f"근로자 생성 서비스 오류: {e}")
            raise
    
    async def get_worker_list(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        search: Optional[str] = None,
        filters: Optional[Dict[str, Any]] = None
    ) -> Tuple[List[Worker], int]:
        """근로자 목록 조회 (검색 및 필터링)"""
        try:
            if search:
                return await self.repository.search_workers(
                    db, search_term=search, skip=skip, limit=limit
                )
            else:
                return await self.repository.get_multi(
                    db, skip=skip, limit=limit, filters=filters or {}
                )
                
        except Exception as e:
            logger.error(f"근로자 목록 조회 서비스 오류: {e}")
            raise
    
    async def update_worker(
        self,
        db: AsyncSession,
        *,
        worker_id: int,
        worker_data: WorkerUpdate
    ) -> Optional[Worker]:
        """근로자 정보 업데이트"""
        try:
            # 1. 기존 근로자 조회
            worker = await self.repository.get_by_id(db, id=worker_id)
            if not worker:
                return None
            
            # 2. 데이터 번역
            update_dict = worker_data.model_dump(exclude_unset=True)
            translated_data = self.translator.translate_worker_data(
                update_dict, to_english=True
            )
            
            # 3. 비즈니스 규칙 적용
            translated_data = self._apply_business_rules(translated_data, is_update=True)
            
            # 4. 업데이트
            update_schema = WorkerUpdate(**translated_data)
            updated_worker = await self.repository.update(
                db, db_obj=worker, obj_in=update_schema
            )
            
            logger.info(f"근로자 정보 업데이트 완료: {updated_worker.name}({updated_worker.employee_id})")
            return updated_worker
            
        except Exception as e:
            logger.error(f"근로자 업데이트 서비스 오류: {e}")
            raise
    
    async def get_workers_by_department(
        self,
        db: AsyncSession,
        *,
        department: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Worker], int]:
        """부서별 근로자 조회"""
        try:
            return await self.repository.get_workers_by_department(
                db, department=department, skip=skip, limit=limit
            )
        except Exception as e:
            logger.error(f"부서별 근로자 조회 서비스 오류: {e}")
            raise
    
    async def get_workers_by_health_status(
        self,
        db: AsyncSession,
        *,
        health_status: str,
        skip: int = 0,
        limit: int = 100
    ) -> Tuple[List[Worker], int]:
        """건강상태별 근로자 조회"""
        try:
            # 한국어 상태를 영어로 번역
            english_status = self.translator.translate_health_status(health_status)
            
            return await self.repository.get_workers_by_health_status(
                db, health_status=english_status, skip=skip, limit=limit
            )
        except Exception as e:
            logger.error(f"건강상태별 근로자 조회 서비스 오류: {e}")
            raise
    
    async def update_health_status(
        self,
        db: AsyncSession,
        *,
        worker_id: int,
        new_status: str,
        notes: Optional[str] = None,
        updated_by: Optional[str] = None
    ) -> Optional[Worker]:
        """근로자 건강상태 업데이트 (이력 관리)"""
        try:
            # 한국어 상태를 영어로 번역
            english_status = self.translator.translate_health_status(new_status)
            
            # 이력 노트 생성
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            korean_status = self.translator.get_korean_label("health_status", english_status)
            
            history_note = f"[{timestamp}] 건강상태 변경: {korean_status}"
            if updated_by:
                history_note += f" (변경자: {updated_by})"
            if notes:
                history_note += f" - {notes}"
            
            return await self.repository.update_health_status(
                db, worker_id=worker_id, new_status=english_status, notes=history_note
            )
            
        except Exception as e:
            logger.error(f"건강상태 업데이트 서비스 오류: {e}")
            raise
    
    async def get_workers_needing_health_exam(
        self,
        db: AsyncSession,
        *,
        months_since_last_exam: int = 12
    ) -> List[Worker]:
        """건강진단이 필요한 근로자 조회"""
        try:
            return await self.repository.get_workers_needing_health_exam(
                db, months_since_last_exam=months_since_last_exam
            )
        except Exception as e:
            logger.error(f"건강진단 대상자 조회 서비스 오류: {e}")
            raise
    
    async def get_comprehensive_statistics(
        self,
        db: AsyncSession
    ) -> Dict[str, Any]:
        """종합 통계 정보 조회 (대시보드용)"""
        try:
            # 기본 통계
            stats = await self.repository.get_statistics(db)
            
            # 건강진단 대상자
            health_exam_needed = await self.get_workers_needing_health_exam(db)
            
            # 통계 데이터에 한국어 라벨 추가
            enhanced_stats = {
                "total_workers": stats["total"],
                "by_employment_type": self._add_korean_labels(
                    stats["by_employment_type"], "employment_type"
                ),
                "by_work_type": self._add_korean_labels(
                    stats["by_work_type"], "work_type"
                ),
                "by_health_status": self._add_korean_labels(
                    stats["by_health_status"], "health_status"
                ),
                "by_gender": self._add_korean_labels(
                    stats["by_gender"], "gender"
                ),
                "by_department": stats["by_department"],
                "health_exam_needed": len(health_exam_needed),
                "health_exam_needed_list": [
                    {"id": w.id, "name": w.name, "employee_id": w.employee_id, 
                     "last_exam": w.last_health_exam}
                    for w in health_exam_needed[:10]  # 상위 10명만
                ],
                "updated_at": datetime.now().isoformat()
            }
            
            return enhanced_stats
            
        except Exception as e:
            logger.error(f"종합 통계 조회 서비스 오류: {e}")
            raise
    
    def _apply_business_rules(
        self, 
        data: Dict[str, Any], 
        is_update: bool = False
    ) -> Dict[str, Any]:
        """비즈니스 규칙 적용"""
        try:
            # 1. 기본값 설정
            if not is_update:
                data.setdefault("is_active", True)
                data.setdefault("health_status", "normal")
                data.setdefault("hire_date", date.today())
                data.setdefault("is_special_exam_target", False)
            
            # 2. 특수건강진단 대상 자동 판정
            if "work_type" in data:
                hazardous_work_types = ["chemical", "welding", "painting", "electrical"]
                if data["work_type"] in hazardous_work_types:
                    data["is_special_exam_target"] = True
            
            # 3. 이름 정규화
            if "name" in data and data["name"]:
                data["name"] = data["name"].strip()
            
            # 4. 사번 정규화
            if "employee_id" in data and data["employee_id"]:
                data["employee_id"] = data["employee_id"].strip().upper()
            
            # 5. 전화번호 정규화
            if "phone" in data and data["phone"]:
                data["phone"] = self._normalize_phone(data["phone"])
            
            return data
            
        except Exception as e:
            logger.error(f"비즈니스 규칙 적용 오류: {e}")
            return data
    
    def _normalize_phone(self, phone: str) -> str:
        """전화번호 정규화"""
        if not phone:
            return phone
        
        # 숫자만 추출
        digits = ''.join(filter(str.isdigit, phone))
        
        # 국내 휴대폰 번호 형식으로 변환
        if len(digits) == 11 and digits.startswith('010'):
            return f"{digits[:3]}-{digits[3:7]}-{digits[7:]}"
        elif len(digits) == 10:
            return f"{digits[:3]}-{digits[3:6]}-{digits[6:]}"
        
        return phone
    
    def _add_korean_labels(
        self, 
        stats: Dict[str, int], 
        field_type: str
    ) -> Dict[str, Dict[str, Any]]:
        """통계 데이터에 한국어 라벨 추가"""
        labeled_stats = {}
        
        for key, count in stats.items():
            korean_label = self.translator.get_korean_label(field_type, key)
            labeled_stats[key] = {
                "count": count,
                "label": korean_label,
                "english": key
            }
        
        return labeled_stats


# 싱글톤 인스턴스
worker_service = WorkerService()