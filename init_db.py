#!/usr/bin/env python
"""
데이터베이스 테이블 생성 스크립트
"""
import logging
from sqlalchemy import create_engine
from src.config.database import Base
from src.models.worker import Worker, HealthConsultation

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables():
    """동기적으로 테이블 생성"""
    try:
        # 일반 PostgreSQL URL 사용
        database_url = "postgresql://admin:password@health-postgres:5432/health_management"
        
        # 동기 엔진 생성
        engine = create_engine(database_url, echo=True)
        
        logger.info("데이터베이스 연결 중...")
        
        # 테이블 생성
        logger.info("테이블 생성 시작...")
        Base.metadata.create_all(bind=engine)
        
        logger.info("테이블 생성 완료!")
        
        # 생성된 테이블 확인
        from sqlalchemy import inspect
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        logger.info(f"생성된 테이블: {tables}")
        
    except Exception as e:
        logger.error(f"테이블 생성 실패: {e}")
        raise

if __name__ == "__main__":
    create_tables()