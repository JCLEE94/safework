"""
기본 리포지토리 클래스
Base repository class for common CRUD operations
"""

import logging
from typing import Any, Dict, Generic, List, Optional, Type, TypeVar

from pydantic import BaseModel
from sqlalchemy import asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import DeclarativeBase

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=DeclarativeBase)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class BaseRepository(Generic[T, CreateSchemaType, UpdateSchemaType]):
    """기본 CRUD 작업을 위한 베이스 리포지토리"""

    def __init__(self, model: Type[T]):
        self.model = model

    async def create(self, db: AsyncSession, *, obj_in: CreateSchemaType) -> T:
        """새 레코드 생성"""
        try:
            obj_data = (
                obj_in.model_dump() if hasattr(obj_in, "model_dump") else obj_in.dict()
            )
            db_obj = self.model(**obj_data)
            db.add(db_obj)
            await db.commit()
            await db.refresh(db_obj)
            logger.info(f"{self.model.__name__} 생성 완료: ID {db_obj.id}")
            return db_obj
        except Exception as e:
            await db.rollback()
            logger.error(f"{self.model.__name__} 생성 실패: {e}")
            raise

    async def get_by_id(self, db: AsyncSession, *, id: int) -> Optional[T]:
        """ID로 단일 레코드 조회"""
        try:
            result = await db.execute(select(self.model).where(self.model.id == id))
            return result.scalar_one_or_none()
        except Exception as e:
            logger.error(f"{self.model.__name__} ID {id} 조회 실패: {e}")
            return None

    async def get_multi(
        self,
        db: AsyncSession,
        *,
        skip: int = 0,
        limit: int = 100,
        filters: Optional[Dict[str, Any]] = None,
        order_by: Optional[str] = None,
        order_direction: str = "asc",
    ) -> tuple[List[T], int]:
        """여러 레코드 조회 (페이징 및 필터링 지원)"""
        try:
            # 기본 쿼리
            query = select(self.model)
            count_query = select(func.count(self.model.id))

            # 필터 적용
            if filters:
                for field, value in filters.items():
                    if hasattr(self.model, field) and value is not None:
                        if isinstance(value, str) and value.strip():
                            # 문자열 필드는 LIKE 검색
                            query = query.where(
                                getattr(self.model, field).ilike(f"%{value}%")
                            )
                            count_query = count_query.where(
                                getattr(self.model, field).ilike(f"%{value}%")
                            )
                        else:
                            # 정확한 일치 검색
                            query = query.where(getattr(self.model, field) == value)
                            count_query = count_query.where(
                                getattr(self.model, field) == value
                            )

            # 정렬 적용
            if order_by and hasattr(self.model, order_by):
                order_func = desc if order_direction.lower() == "desc" else asc
                query = query.order_by(order_func(getattr(self.model, order_by)))
            else:
                # 기본 정렬: ID 내림차순
                query = query.order_by(desc(self.model.id))

            # 페이징 적용
            query = query.offset(skip).limit(limit)

            # 실행
            result = await db.execute(query)
            count_result = await db.execute(count_query)

            items = result.scalars().all()
            total = count_result.scalar()

            logger.info(
                f"{self.model.__name__} 조회 완료: {len(items)}개 (전체 {total}개)"
            )
            return items, total

        except Exception as e:
            logger.error(f"{self.model.__name__} 다중 조회 실패: {e}")
            return [], 0

    async def update(
        self, db: AsyncSession, *, db_obj: T, obj_in: UpdateSchemaType
    ) -> T:
        """기존 레코드 업데이트"""
        try:
            obj_data = (
                obj_in.model_dump(exclude_unset=True)
                if hasattr(obj_in, "model_dump")
                else obj_in.dict(exclude_unset=True)
            )

            for field, value in obj_data.items():
                if hasattr(db_obj, field):
                    setattr(db_obj, field, value)

            await db.commit()
            await db.refresh(db_obj)
            logger.info(f"{self.model.__name__} ID {db_obj.id} 업데이트 완료")
            return db_obj

        except Exception as e:
            await db.rollback()
            logger.error(f"{self.model.__name__} 업데이트 실패: {e}")
            raise

    async def delete(self, db: AsyncSession, *, id: int) -> bool:
        """레코드 삭제"""
        try:
            obj = await self.get_by_id(db, id=id)
            if obj:
                await db.delete(obj)
                await db.commit()
                logger.info(f"{self.model.__name__} ID {id} 삭제 완료")
                return True
            else:
                logger.warning(f"{self.model.__name__} ID {id} 찾을 수 없음")
                return False

        except Exception as e:
            await db.rollback()
            logger.error(f"{self.model.__name__} 삭제 실패: {e}")
            return False

    async def get_statistics(self, db: AsyncSession) -> Dict[str, Any]:
        """기본 통계 정보 조회"""
        try:
            # 전체 개수
            total_result = await db.execute(select(func.count(self.model.id)))
            total = total_result.scalar()

            return {"total": total, "model": self.model.__name__}

        except Exception as e:
            logger.error(f"{self.model.__name__} 통계 조회 실패: {e}")
            return {"total": 0, "model": self.model.__name__}

    async def search(
        self,
        db: AsyncSession,
        *,
        search_term: str,
        search_fields: List[str],
        skip: int = 0,
        limit: int = 100,
    ) -> tuple[List[T], int]:
        """텍스트 검색"""
        try:
            if not search_term.strip():
                return await self.get_multi(db, skip=skip, limit=limit)

            # 검색 조건 구성
            query = select(self.model)
            count_query = select(func.count(self.model.id))

            search_conditions = []
            for field in search_fields:
                if hasattr(self.model, field):
                    search_conditions.append(
                        getattr(self.model, field).ilike(f"%{search_term}%")
                    )

            if search_conditions:
                from sqlalchemy import or_

                search_filter = or_(*search_conditions)
                query = query.where(search_filter)
                count_query = count_query.where(search_filter)

            # 정렬 및 페이징
            query = query.order_by(desc(self.model.id)).offset(skip).limit(limit)

            # 실행
            result = await db.execute(query)
            count_result = await db.execute(count_query)

            items = result.scalars().all()
            total = count_result.scalar()

            logger.info(
                f"{self.model.__name__} 검색 완료: '{search_term}' -> {len(items)}개 결과"
            )
            return items, total

        except Exception as e:
            logger.error(f"{self.model.__name__} 검색 실패: {e}")
            return [], 0
