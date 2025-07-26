#!/usr/bin/env python3
"""
SafeWork Pro 마이그레이션 검증 스크립트
마이그레이션 후 데이터 무결성 및 표준화 검증
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import create_engine, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# 데이터베이스 설정
ASYNC_DATABASE_URL = "postgresql+asyncpg://admin:password@localhost:5432/health_management"

# 검증 결과
validation_results = []

def log_validation(check: str, status: str, details: dict = None):
    """검증 로그 기록"""
    result = {
        "timestamp": datetime.now().isoformat(),
        "check": check,
        "status": status,
        "details": details or {}
    }
    validation_results.append(result)
    
    icon = "✅" if status == "PASS" else "❌"
    print(f"{icon} {check}: {status}")
    if details:
        for key, value in details.items():
            print(f"   - {key}: {value}")

async def check_table_exists(session: AsyncSession, table_name: str) -> bool:
    """테이블 존재 여부 확인"""
    result = await session.execute(text("""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = :table_name
        )
    """), {"table_name": table_name})
    
    return result.scalar()

async def validate_standard_tables(session: AsyncSession):
    """표준 테이블 검증"""
    required_tables = [
        "status_codes",
        "code_categories",
        "departments",
        "positions",
        "work_types"
    ]
    
    all_exist = True
    missing_tables = []
    
    for table in required_tables:
        exists = await check_table_exists(session, table)
        if not exists:
            all_exist = False
            missing_tables.append(table)
    
    log_validation(
        "Standard Tables",
        "PASS" if all_exist else "FAIL",
        {
            "total": len(required_tables),
            "missing": missing_tables if missing_tables else "None"
        }
    )

async def validate_code_data(session: AsyncSession):
    """코드 데이터 검증"""
    
    # 1. 코드 카테고리 검증
    result = await session.execute(text("""
        SELECT COUNT(*) FROM code_categories
    """))
    category_count = result.scalar()
    
    # 2. 상태 코드 검증
    result = await session.execute(text("""
        SELECT category, COUNT(*) as count
        FROM status_codes
        GROUP BY category
        ORDER BY category
    """))
    status_codes = result.all()
    
    status_dict = {row[0]: row[1] for row in status_codes}
    
    log_validation(
        "Code Data",
        "PASS" if category_count >= 8 and len(status_codes) >= 4 else "FAIL",
        {
            "categories": category_count,
            "status_codes": status_dict
        }
    )

async def validate_master_data(session: AsyncSession):
    """마스터 데이터 검증"""
    
    # 1. 부서 데이터
    result = await session.execute(text("SELECT COUNT(*) FROM departments"))
    dept_count = result.scalar()
    
    # 2. 직위 데이터
    result = await session.execute(text("SELECT COUNT(*) FROM positions"))
    pos_count = result.scalar()
    
    # 3. 작업 유형 데이터
    result = await session.execute(text("SELECT COUNT(*) FROM work_types"))
    work_type_count = result.scalar()
    
    log_validation(
        "Master Data",
        "PASS" if all([dept_count > 0, pos_count > 0, work_type_count > 0]) else "FAIL",
        {
            "departments": dept_count,
            "positions": pos_count,
            "work_types": work_type_count
        }
    )

async def validate_data_mapping(session: AsyncSession):
    """데이터 매핑 검증"""
    
    # 1. workers 테이블의 코드 매핑 확인
    result = await session.execute(text("""
        SELECT 
            COUNT(*) as total,
            COUNT(department_code) as with_dept_code,
            COUNT(position_code) as with_pos_code,
            COUNT(work_type_code) as with_work_type_code
        FROM workers
    """))
    
    mapping = result.one()
    
    # 2. 매핑 비율 계산
    total = mapping.total or 1
    dept_rate = (mapping.with_dept_code / total) * 100 if total > 0 else 0
    pos_rate = (mapping.with_pos_code / total) * 100 if total > 0 else 0
    work_rate = (mapping.with_work_type_code / total) * 100 if total > 0 else 0
    
    log_validation(
        "Data Mapping",
        "PASS" if all([dept_rate >= 90, pos_rate >= 90, work_rate >= 90]) else "FAIL",
        {
            "total_workers": total,
            "department_mapping": f"{dept_rate:.1f}%",
            "position_mapping": f"{pos_rate:.1f}%",
            "work_type_mapping": f"{work_rate:.1f}%"
        }
    )

async def validate_foreign_keys(session: AsyncSession):
    """외래 키 무결성 검증"""
    
    # 1. workers의 department_code 검증
    result = await session.execute(text("""
        SELECT COUNT(*)
        FROM workers w
        WHERE w.department_code IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM departments d
            WHERE d.code = w.department_code
        )
    """))
    invalid_dept = result.scalar()
    
    # 2. workers의 position_code 검증
    result = await session.execute(text("""
        SELECT COUNT(*)
        FROM workers w
        WHERE w.position_code IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM positions p
            WHERE p.code = w.position_code
        )
    """))
    invalid_pos = result.scalar()
    
    # 3. workers의 work_type_code 검증
    result = await session.execute(text("""
        SELECT COUNT(*)
        FROM workers w
        WHERE w.work_type_code IS NOT NULL
        AND NOT EXISTS (
            SELECT 1 FROM work_types wt
            WHERE wt.code = w.work_type_code
        )
    """))
    invalid_work = result.scalar()
    
    log_validation(
        "Foreign Key Integrity",
        "PASS" if all([invalid_dept == 0, invalid_pos == 0, invalid_work == 0]) else "FAIL",
        {
            "invalid_departments": invalid_dept,
            "invalid_positions": invalid_pos,
            "invalid_work_types": invalid_work
        }
    )

async def validate_indexes(session: AsyncSession):
    """인덱스 검증"""
    
    result = await session.execute(text("""
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = 'public'
        AND tablename IN ('workers', 'health_exams', 'status_codes', 'departments', 'positions', 'work_types')
        AND indexname LIKE 'idx_%'
    """))
    
    indexes = [row[0] for row in result.all()]
    
    expected_indexes = [
        "idx_workers_department_code",
        "idx_workers_position_code",
        "idx_workers_work_type_code",
        "idx_health_exams_exam_type_code",
        "idx_status_codes_category_code",
        "idx_departments_code",
        "idx_positions_code",
        "idx_work_types_code"
    ]
    
    missing_indexes = [idx for idx in expected_indexes if idx not in indexes]
    
    log_validation(
        "Database Indexes",
        "PASS" if len(missing_indexes) == 0 else "FAIL",
        {
            "total_indexes": len(indexes),
            "missing": missing_indexes if missing_indexes else "None"
        }
    )

async def validate_data_consistency(session: AsyncSession):
    """데이터 일관성 검증"""
    
    # 1. 중복 코드 확인
    result = await session.execute(text("""
        SELECT category, code, COUNT(*) as cnt
        FROM status_codes
        GROUP BY category, code
        HAVING COUNT(*) > 1
    """))
    duplicate_codes = result.all()
    
    # 2. 고아 레코드 확인 (부서가 없는 근로자)
    result = await session.execute(text("""
        SELECT COUNT(*)
        FROM workers
        WHERE department IS NOT NULL
        AND department_code IS NULL
    """))
    orphan_workers = result.scalar()
    
    # 3. 특수건강진단 대상자 일관성
    result = await session.execute(text("""
        SELECT COUNT(*)
        FROM workers w
        JOIN work_types wt ON w.work_type_code = wt.code
        WHERE wt.special_health_exam_required = true
        AND NOT EXISTS (
            SELECT 1 FROM health_exams he
            WHERE he.worker_id = w.id
            AND he.exam_type_code = 'special'
        )
    """))
    missing_special_exams = result.scalar()
    
    log_validation(
        "Data Consistency",
        "PASS" if all([len(duplicate_codes) == 0, orphan_workers == 0]) else "WARN",
        {
            "duplicate_codes": len(duplicate_codes),
            "orphan_workers": orphan_workers,
            "workers_needing_special_exam": missing_special_exams
        }
    )

async def generate_validation_report(session: AsyncSession):
    """검증 보고서 생성"""
    
    # 통계 수집
    stats = {}
    
    # 각 테이블의 레코드 수
    tables = ["workers", "health_exams", "departments", "positions", "work_types", "status_codes"]
    for table in tables:
        result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
        stats[f"{table}_count"] = result.scalar()
    
    # 표준화 비율
    result = await session.execute(text("""
        SELECT 
            (COUNT(department_code)::float / NULLIF(COUNT(*), 0) * 100) as dept_rate,
            (COUNT(position_code)::float / NULLIF(COUNT(*), 0) * 100) as pos_rate,
            (COUNT(work_type_code)::float / NULLIF(COUNT(*), 0) * 100) as work_rate
        FROM workers
    """))
    rates = result.one()
    
    stats["standardization_rates"] = {
        "department": f"{rates.dept_rate:.1f}%",
        "position": f"{rates.pos_rate:.1f}%",
        "work_type": f"{rates.work_rate:.1f}%"
    }
    
    return stats

async def main():
    """메인 검증 함수"""
    print("🔍 SafeWork Pro 마이그레이션 검증 시작...")
    print("=" * 50)
    
    engine = create_async_engine(ASYNC_DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    try:
        async with async_session() as session:
            # 1. 표준 테이블 검증
            await validate_standard_tables(session)
            
            # 2. 코드 데이터 검증
            await validate_code_data(session)
            
            # 3. 마스터 데이터 검증
            await validate_master_data(session)
            
            # 4. 데이터 매핑 검증
            await validate_data_mapping(session)
            
            # 5. 외래 키 무결성 검증
            await validate_foreign_keys(session)
            
            # 6. 인덱스 검증
            await validate_indexes(session)
            
            # 7. 데이터 일관성 검증
            await validate_data_consistency(session)
            
            # 8. 통계 보고서
            stats = await generate_validation_report(session)
        
        print("\n" + "=" * 50)
        print("📊 검증 통계:")
        print(json.dumps(stats, indent=2, ensure_ascii=False))
        
        # 검증 결과 저장
        report_file = Path(__file__).parent / f"validation_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_file, "w", encoding="utf-8") as f:
            json.dump({
                "validation_results": validation_results,
                "statistics": stats,
                "timestamp": datetime.now().isoformat()
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n📄 검증 보고서 저장: {report_file}")
        
        # 최종 결과
        failed = [r for r in validation_results if r["status"] == "FAIL"]
        warned = [r for r in validation_results if r["status"] == "WARN"]
        
        if failed:
            print(f"\n❌ 검증 실패: {len(failed)}개 항목")
        elif warned:
            print(f"\n⚠️  검증 완료 (경고: {len(warned)}개)")
        else:
            print("\n✅ 모든 검증 통과!")
            
    except Exception as e:
        print(f"\n❌ 검증 중 오류 발생: {e}")
        raise
    finally:
        await engine.dispose()

if __name__ == "__main__":
    asyncio.run(main())