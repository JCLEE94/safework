#!/usr/bin/env python3
"""
SafeWork Pro 데이터 마이그레이션 스크립트
기존 데이터베이스 구조를 새로운 표준화된 구조로 마이그레이션
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import json

# 프로젝트 루트 경로 추가
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import asyncpg

# 데이터베이스 설정
DATABASE_URL = "postgresql://admin:password@localhost:5432/health_management"
ASYNC_DATABASE_URL = "postgresql+asyncpg://admin:password@localhost:5432/health_management"

# 마이그레이션 로그
migration_log = []

def log_migration(table: str, action: str, count: int = 0, error: str = None):
    """마이그레이션 로그 기록"""
    entry = {
        "timestamp": datetime.now().isoformat(),
        "table": table,
        "action": action,
        "count": count,
        "error": error
    }
    migration_log.append(entry)
    
    if error:
        print(f"❌ [{table}] {action}: {error}")
    else:
        print(f"✅ [{table}] {action}: {count} records")

async def create_standardized_tables(session: AsyncSession):
    """표준화된 테이블 생성"""
    
    # 1. 표준 상태 코드 테이블
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS status_codes (
            id SERIAL PRIMARY KEY,
            category VARCHAR(50) NOT NULL,
            code VARCHAR(50) NOT NULL,
            name_ko VARCHAR(100) NOT NULL,
            name_en VARCHAR(100) NOT NULL,
            description TEXT,
            sort_order INTEGER DEFAULT 0,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(category, code)
        );
    """))
    
    # 2. 표준 코드 분류 테이블
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS code_categories (
            id SERIAL PRIMARY KEY,
            category_code VARCHAR(50) UNIQUE NOT NULL,
            category_name VARCHAR(100) NOT NULL,
            description TEXT,
            parent_category VARCHAR(50),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 3. 부서 마스터 테이블
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS departments (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            parent_code VARCHAR(50),
            manager_id INTEGER,
            location VARCHAR(200),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 4. 직위/직급 마스터 테이블
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS positions (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            level INTEGER,
            category VARCHAR(50),
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    # 5. 작업 유형 마스터 테이블
    await session.execute(text("""
        CREATE TABLE IF NOT EXISTS work_types (
            id SERIAL PRIMARY KEY,
            code VARCHAR(50) UNIQUE NOT NULL,
            name VARCHAR(100) NOT NULL,
            category VARCHAR(50),
            hazard_level VARCHAR(20),
            special_health_exam_required BOOLEAN DEFAULT false,
            description TEXT,
            is_active BOOLEAN DEFAULT true,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """))
    
    await session.commit()
    log_migration("standardized_tables", "created", 5)

async def insert_standard_codes(session: AsyncSession):
    """표준 코드 데이터 삽입"""
    
    # 1. 코드 카테고리 삽입
    categories = [
        ("EXAM_PLAN_STATUS", "검진계획상태", "건강검진 계획 상태 코드"),
        ("EXAM_STATUS", "검진상태", "건강검진 진행 상태 코드"),
        ("ACCIDENT_STATUS", "사고상태", "사고 처리 상태 코드"),
        ("EDUCATION_STATUS", "교육상태", "교육 진행 상태 코드"),
        ("EXAM_TYPE", "검진종류", "건강검진 종류 코드"),
        ("ACCIDENT_TYPE", "사고유형", "사고 유형 분류 코드"),
        ("EMPLOYMENT_TYPE", "고용형태", "근로자 고용 형태 코드"),
        ("SEVERITY", "심각도", "사고 심각도 분류 코드"),
    ]
    
    for code, name, desc in categories:
        await session.execute(text("""
            INSERT INTO code_categories (category_code, category_name, description)
            VALUES (:code, :name, :desc)
            ON CONFLICT (category_code) DO NOTHING
        """), {"code": code, "name": name, "desc": desc})
    
    # 2. 상태 코드 삽입
    status_codes = [
        # 검진계획 상태
        ("EXAM_PLAN_STATUS", "draft", "초안", "Draft", 1),
        ("EXAM_PLAN_STATUS", "pending_approval", "승인대기", "Pending Approval", 2),
        ("EXAM_PLAN_STATUS", "approved", "승인됨", "Approved", 3),
        ("EXAM_PLAN_STATUS", "in_progress", "진행중", "In Progress", 4),
        ("EXAM_PLAN_STATUS", "completed", "완료", "Completed", 5),
        ("EXAM_PLAN_STATUS", "cancelled", "취소됨", "Cancelled", 6),
        
        # 검진 상태
        ("EXAM_STATUS", "scheduled", "예정", "Scheduled", 1),
        ("EXAM_STATUS", "completed", "완료", "Completed", 2),
        ("EXAM_STATUS", "overdue", "기한초과", "Overdue", 3),
        ("EXAM_STATUS", "cancelled", "취소됨", "Cancelled", 4),
        
        # 사고 상태
        ("ACCIDENT_STATUS", "reported", "신고됨", "Reported", 1),
        ("ACCIDENT_STATUS", "investigating", "조사중", "Investigating", 2),
        ("ACCIDENT_STATUS", "resolved", "해결됨", "Resolved", 3),
        ("ACCIDENT_STATUS", "closed", "종료", "Closed", 4),
        
        # 교육 상태
        ("EDUCATION_STATUS", "planned", "계획됨", "Planned", 1),
        ("EDUCATION_STATUS", "in_progress", "진행중", "In Progress", 2),
        ("EDUCATION_STATUS", "completed", "완료", "Completed", 3),
        ("EDUCATION_STATUS", "cancelled", "취소됨", "Cancelled", 4),
    ]
    
    for category, code, name_ko, name_en, order in status_codes:
        await session.execute(text("""
            INSERT INTO status_codes (category, code, name_ko, name_en, sort_order)
            VALUES (:category, :code, :name_ko, :name_en, :order)
            ON CONFLICT (category, code) DO NOTHING
        """), {
            "category": category,
            "code": code,
            "name_ko": name_ko,
            "name_en": name_en,
            "order": order
        })
    
    await session.commit()
    log_migration("standard_codes", "inserted", len(categories) + len(status_codes))

async def migrate_departments(session: AsyncSession):
    """부서 데이터 마이그레이션"""
    
    # 기존 workers 테이블에서 부서 추출
    result = await session.execute(text("""
        SELECT DISTINCT department 
        FROM workers 
        WHERE department IS NOT NULL 
        ORDER BY department
    """))
    
    departments = result.scalars().all()
    
    count = 0
    for dept in departments:
        await session.execute(text("""
            INSERT INTO departments (code, name)
            VALUES (:code, :name)
            ON CONFLICT (code) DO NOTHING
        """), {"code": dept.replace(" ", "_").upper(), "name": dept})
        count += 1
    
    await session.commit()
    log_migration("departments", "migrated", count)

async def migrate_positions(session: AsyncSession):
    """직위 데이터 마이그레이션"""
    
    # 기존 workers 테이블에서 직위 추출
    result = await session.execute(text("""
        SELECT DISTINCT position 
        FROM workers 
        WHERE position IS NOT NULL 
        ORDER BY position
    """))
    
    positions = result.scalars().all()
    
    # 직위별 레벨 매핑
    level_map = {
        "사원": 1, "주임": 2, "대리": 3, "과장": 4,
        "차장": 5, "부장": 6, "이사": 7, "대표": 8
    }
    
    count = 0
    for pos in positions:
        level = level_map.get(pos, 1)
        await session.execute(text("""
            INSERT INTO positions (code, name, level)
            VALUES (:code, :name, :level)
            ON CONFLICT (code) DO NOTHING
        """), {
            "code": pos.replace(" ", "_").upper(),
            "name": pos,
            "level": level
        })
        count += 1
    
    await session.commit()
    log_migration("positions", "migrated", count)

async def migrate_work_types(session: AsyncSession):
    """작업 유형 데이터 마이그레이션"""
    
    # 기존 workers 테이블에서 작업 유형 추출
    result = await session.execute(text("""
        SELECT DISTINCT work_type 
        FROM workers 
        WHERE work_type IS NOT NULL 
        ORDER BY work_type
    """))
    
    work_types = result.scalars().all()
    
    # 특수건강진단 대상 작업
    special_exam_types = ["용접", "화학물질취급", "소음", "분진", "진동"]
    
    count = 0
    for wt in work_types:
        special_required = any(s in wt for s in special_exam_types)
        await session.execute(text("""
            INSERT INTO work_types (code, name, special_health_exam_required)
            VALUES (:code, :name, :special)
            ON CONFLICT (code) DO NOTHING
        """), {
            "code": wt.replace(" ", "_").upper(),
            "name": wt,
            "special": special_required
        })
        count += 1
    
    await session.commit()
    log_migration("work_types", "migrated", count)

async def update_foreign_keys(session: AsyncSession):
    """외래 키 관계 업데이트"""
    
    # 1. workers 테이블에 표준화된 코드 컬럼 추가
    await session.execute(text("""
        ALTER TABLE workers 
        ADD COLUMN IF NOT EXISTS department_code VARCHAR(50),
        ADD COLUMN IF NOT EXISTS position_code VARCHAR(50),
        ADD COLUMN IF NOT EXISTS work_type_code VARCHAR(50);
    """))
    
    # 2. 코드 매핑 업데이트
    await session.execute(text("""
        UPDATE workers w
        SET 
            department_code = d.code,
            position_code = p.code,
            work_type_code = wt.code
        FROM 
            departments d,
            positions p,
            work_types wt
        WHERE 
            w.department = d.name
            AND w.position = p.name
            AND w.work_type = wt.name;
    """))
    
    # 3. health_exams 테이블 상태 코드 표준화
    await session.execute(text("""
        ALTER TABLE health_exams
        ADD COLUMN IF NOT EXISTS exam_type_code VARCHAR(50),
        ADD COLUMN IF NOT EXISTS result_status_code VARCHAR(50);
    """))
    
    # 4. 검진 유형 매핑
    exam_type_map = {
        "일반건강진단": "general",
        "특수건강진단": "special",
        "배치전건강진단": "placement",
        "복직건강진단": "return_to_work"
    }
    
    for ko, en in exam_type_map.items():
        await session.execute(text("""
            UPDATE health_exams
            SET exam_type_code = :code
            WHERE exam_type = :type
        """), {"code": en, "type": ko})
    
    await session.commit()
    log_migration("foreign_keys", "updated", 4)

async def create_indexes(session: AsyncSession):
    """인덱스 생성"""
    
    indexes = [
        "CREATE INDEX IF NOT EXISTS idx_workers_department_code ON workers(department_code)",
        "CREATE INDEX IF NOT EXISTS idx_workers_position_code ON workers(position_code)",
        "CREATE INDEX IF NOT EXISTS idx_workers_work_type_code ON workers(work_type_code)",
        "CREATE INDEX IF NOT EXISTS idx_health_exams_exam_type_code ON health_exams(exam_type_code)",
        "CREATE INDEX IF NOT EXISTS idx_status_codes_category_code ON status_codes(category, code)",
        "CREATE INDEX IF NOT EXISTS idx_departments_code ON departments(code)",
        "CREATE INDEX IF NOT EXISTS idx_positions_code ON positions(code)",
        "CREATE INDEX IF NOT EXISTS idx_work_types_code ON work_types(code)",
    ]
    
    for idx in indexes:
        await session.execute(text(idx))
    
    await session.commit()
    log_migration("indexes", "created", len(indexes))

async def main():
    """메인 마이그레이션 함수"""
    print("🚀 SafeWork Pro 데이터 마이그레이션 시작...")
    print("=" * 50)
    
    # 비동기 엔진 생성
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # 1. 표준화된 테이블 생성
            await create_standardized_tables(session)
            
            # 2. 표준 코드 삽입
            await insert_standard_codes(session)
            
            # 3. 부서 마이그레이션
            await migrate_departments(session)
            
            # 4. 직위 마이그레이션
            await migrate_positions(session)
            
            # 5. 작업 유형 마이그레이션
            await migrate_work_types(session)
            
            # 6. 외래 키 관계 업데이트
            await update_foreign_keys(session)
            
            # 7. 인덱스 생성
            await create_indexes(session)
        
        print("\n" + "=" * 50)
        print("✅ 마이그레이션 완료!")
        
        # 로그 저장
        log_file = Path(__file__).parent / f"migration_log_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(log_file, "w", encoding="utf-8") as f:
            json.dump(migration_log, f, ensure_ascii=False, indent=2)
        
        print(f"📄 마이그레이션 로그 저장: {log_file}")
        
    except Exception as e:
        print(f"\n❌ 마이그레이션 중 오류 발생: {e}")
        log_migration("main", "error", error=str(e))
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())