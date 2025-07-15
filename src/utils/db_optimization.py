"""
데이터베이스 최적화 유틸리티
Database optimization utilities for performance improvement
"""

import asyncio
from typing import Any, Dict, List, Optional

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import contains_eager, joinedload, selectinload
from sqlalchemy.sql import Select

from ..config.database import async_engine
from ..utils.logger import logger


class DatabaseOptimizer:
    """데이터베이스 최적화 클래스"""

    @staticmethod
    async def create_indexes(session: AsyncSession):
        """
        성능 향상을 위한 인덱스 생성
        Create indexes for performance improvement
        """
        indexes = [
            # Workers table indexes
            "CREATE INDEX IF NOT EXISTS idx_workers_employee_number ON workers(employee_number);",
            "CREATE INDEX IF NOT EXISTS idx_workers_name ON workers(name);",
            "CREATE INDEX IF NOT EXISTS idx_workers_work_type ON workers(work_type);",
            "CREATE INDEX IF NOT EXISTS idx_workers_health_status ON workers(health_status);",
            "CREATE INDEX IF NOT EXISTS idx_workers_hire_date ON workers(hire_date);",
            # Health exams indexes
            "CREATE INDEX IF NOT EXISTS idx_health_exams_worker_id ON health_exams(worker_id);",
            "CREATE INDEX IF NOT EXISTS idx_health_exams_exam_date ON health_exams(exam_date);",
            "CREATE INDEX IF NOT EXISTS idx_health_exams_exam_type ON health_exams(exam_type);",
            "CREATE INDEX IF NOT EXISTS idx_health_exams_next_exam_date ON health_exams(next_exam_date);",
            # Work environments indexes
            "CREATE INDEX IF NOT EXISTS idx_work_environments_measurement_date ON work_environments(measurement_date);",
            "CREATE INDEX IF NOT EXISTS idx_work_environments_measurement_type ON work_environments(measurement_type);",
            "CREATE INDEX IF NOT EXISTS idx_work_environments_status ON work_environments(status);",
            # Health education indexes
            "CREATE INDEX IF NOT EXISTS idx_health_education_education_date ON health_education(education_date);",
            "CREATE INDEX IF NOT EXISTS idx_health_education_status ON health_education(status);",
            # Chemical substances indexes
            "CREATE INDEX IF NOT EXISTS idx_chemical_substances_name ON chemical_substances(name);",
            "CREATE INDEX IF NOT EXISTS idx_chemical_substances_cas_number ON chemical_substances(cas_number);",
            "CREATE INDEX IF NOT EXISTS idx_chemical_substances_danger_grade ON chemical_substances(danger_grade);",
            # Accident reports indexes
            "CREATE INDEX IF NOT EXISTS idx_accident_reports_worker_id ON accident_reports(worker_id);",
            "CREATE INDEX IF NOT EXISTS idx_accident_reports_accident_date ON accident_reports(accident_date);",
            "CREATE INDEX IF NOT EXISTS idx_accident_reports_severity ON accident_reports(severity);",
            # Composite indexes for common queries
            "CREATE INDEX IF NOT EXISTS idx_workers_composite ON workers(work_type, health_status);",
            "CREATE INDEX IF NOT EXISTS idx_health_exams_composite ON health_exams(worker_id, exam_date DESC);",
            "CREATE INDEX IF NOT EXISTS idx_work_env_composite ON work_environments(measurement_type, status, measurement_date DESC);",
        ]

        try:
            for index_sql in indexes:
                await session.execute(text(index_sql))
                logger.info(
                    f"Index created/verified: {index_sql.split('idx_')[1].split(' ')[0]}"
                )

            await session.commit()
            logger.info("All indexes created successfully")

        except Exception as e:
            logger.error(f"Error creating indexes: {e}")
            await session.rollback()
            raise

    @staticmethod
    async def analyze_tables(session: AsyncSession):
        """
        테이블 통계 분석 및 업데이트
        Analyze table statistics for query optimizer
        """
        tables = [
            "workers",
            "health_exams",
            "work_environments",
            "health_education",
            "chemical_substances",
            "accident_reports",
        ]

        try:
            for table in tables:
                await session.execute(text(f"ANALYZE {table};"))
                logger.info(f"Analyzed table: {table}")

            await session.commit()
            logger.info("All tables analyzed successfully")

        except Exception as e:
            logger.error(f"Error analyzing tables: {e}")
            await session.rollback()

    @staticmethod
    async def vacuum_tables(session: AsyncSession):
        """
        테이블 정리 및 공간 회수
        Vacuum tables to reclaim space and update statistics
        """
        # Note: VACUUM cannot run inside a transaction block
        # This needs to be run separately with autocommit
        try:
            await session.execute(text("COMMIT;"))  # End any existing transaction

            # Run VACUUM on each table
            tables = [
                "workers",
                "health_exams",
                "work_environments",
                "health_education",
                "chemical_substances",
                "accident_reports",
            ]

            for table in tables:
                await session.execute(text(f"VACUUM ANALYZE {table};"))
                logger.info(f"Vacuumed table: {table}")

        except Exception as e:
            logger.error(f"Error vacuuming tables: {e}")

    @staticmethod
    def optimize_query_for_pagination(
        query: Select, page: int, page_size: int
    ) -> Select:
        """
        페이지네이션을 위한 쿼리 최적화
        Optimize query for pagination with offset/limit
        """
        offset = (page - 1) * page_size
        return query.offset(offset).limit(page_size)

    @staticmethod
    def add_eager_loading(query: Select, relationships: List[str]) -> Select:
        """
        Eager loading을 통한 N+1 문제 해결
        Solve N+1 problem with eager loading
        """
        for rel in relationships:
            if "." in rel:
                # Nested relationship
                parts = rel.split(".")
                query = query.options(selectinload(parts[0]).selectinload(parts[1]))
            else:
                # Direct relationship
                query = query.options(selectinload(rel))

        return query

    @staticmethod
    async def get_query_plan(session: AsyncSession, query: str) -> List[Dict[str, Any]]:
        """
        쿼리 실행 계획 분석
        Analyze query execution plan
        """
        try:
            result = await session.execute(text(f"EXPLAIN ANALYZE {query}"))

            plan = []
            for row in result:
                plan.append({"plan": row[0]})

            return plan

        except Exception as e:
            logger.error(f"Error getting query plan: {e}")
            return []

    @staticmethod
    async def optimize_connection_pool():
        """
        연결 풀 최적화 설정
        Optimize connection pool settings
        """
        # This is typically done in the engine configuration
        # but we can adjust runtime parameters
        async with async_engine.begin() as conn:
            # Set statement timeout
            await conn.execute(text("SET statement_timeout = '30s';"))

            # Set work_mem for better sorting performance
            await conn.execute(text("SET work_mem = '16MB';"))

            # Enable parallel queries
            await conn.execute(text("SET max_parallel_workers_per_gather = 2;"))

            logger.info("Connection pool optimized")

    @staticmethod
    async def create_materialized_views(session: AsyncSession):
        """
        자주 사용되는 복잡한 쿼리를 위한 Materialized View 생성
        Create materialized views for complex frequently-used queries
        """
        views = [
            # Worker health summary view
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS worker_health_summary AS
            SELECT 
                w.id,
                w.name,
                w.employee_number,
                w.work_type,
                w.health_status,
                COUNT(DISTINCT he.id) as total_exams,
                MAX(he.exam_date) as last_exam_date,
                MIN(he.next_exam_date) as next_exam_date
            FROM workers w
            LEFT JOIN health_exams he ON w.id = he.worker_id
            GROUP BY w.id, w.name, w.employee_number, w.work_type, w.health_status;
            """,
            # Monthly statistics view
            """
            CREATE MATERIALIZED VIEW IF NOT EXISTS monthly_statistics AS
            SELECT 
                DATE_TRUNC('month', exam_date) as month,
                COUNT(*) as exam_count,
                COUNT(DISTINCT worker_id) as unique_workers,
                SUM(CASE WHEN exam_result = 'normal' THEN 1 ELSE 0 END) as normal_count,
                SUM(CASE WHEN exam_result != 'normal' THEN 1 ELSE 0 END) as abnormal_count
            FROM health_exams
            GROUP BY DATE_TRUNC('month', exam_date);
            """,
        ]

        try:
            for view_sql in views:
                await session.execute(text(view_sql))

            # Create indexes on materialized views
            await session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_worker_health_summary_id ON worker_health_summary(id);"
                )
            )
            await session.execute(
                text(
                    "CREATE INDEX IF NOT EXISTS idx_monthly_statistics_month ON monthly_statistics(month);"
                )
            )

            await session.commit()
            logger.info("Materialized views created successfully")

        except Exception as e:
            logger.error(f"Error creating materialized views: {e}")
            await session.rollback()

    @staticmethod
    async def refresh_materialized_views(session: AsyncSession):
        """
        Materialized View 새로고침
        Refresh materialized views
        """
        views = ["worker_health_summary", "monthly_statistics"]

        try:
            for view in views:
                await session.execute(
                    text(f"REFRESH MATERIALIZED VIEW CONCURRENTLY {view};")
                )
                logger.info(f"Refreshed materialized view: {view}")

            await session.commit()

        except Exception as e:
            logger.error(f"Error refreshing materialized views: {e}")
            await session.rollback()


# Initialize optimization on startup
async def initialize_db_optimization():
    """
    데이터베이스 최적화 초기화
    Initialize database optimization
    """
    try:
        from ..config.database import get_async_session

        async for session in get_async_session():
            optimizer = DatabaseOptimizer()

            # Create indexes
            await optimizer.create_indexes(session)

            # Analyze tables
            await optimizer.analyze_tables(session)

            # Create materialized views
            await optimizer.create_materialized_views(session)

            # Optimize connection pool
            await optimizer.optimize_connection_pool()

            logger.info("Database optimization completed successfully")
            break

    except Exception as e:
        logger.error(f"Database optimization failed: {e}")
        # Don't raise - optimization is not critical for startup
