"""
데이터베이스 모델 최적화 마이그레이션
Database model optimization migration
"""

from sqlalchemy import text
from src.config.database import get_db_engine

def create_optimized_indexes():
    """최적화된 인덱스들을 생성합니다."""
    engine = get_db_engine()
    
    # Worker 테이블 인덱스
    worker_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_workers_name_search ON workers USING gin(to_tsvector('korean', name))",
        "CREATE INDEX IF NOT EXISTS ix_workers_dept_active ON workers (department, is_active)",
        "CREATE INDEX IF NOT EXISTS ix_workers_type_status ON workers (employment_type, health_status)",
        "CREATE INDEX IF NOT EXISTS ix_workers_work_special ON workers (work_type, is_special_exam_target)",
        "CREATE INDEX IF NOT EXISTS ix_workers_name_active ON workers (name, is_active)",
    ]
    
    # HealthExam 테이블 인덱스
    health_exam_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_health_exams_worker_date ON health_exams (worker_id, exam_date)",
        "CREATE INDEX IF NOT EXISTS ix_health_exams_type_result ON health_exams (exam_type, exam_result)",
        "CREATE INDEX IF NOT EXISTS ix_health_exams_followup ON health_exams (is_followup_required, followup_date)",
        "CREATE INDEX IF NOT EXISTS ix_health_exams_date_range ON health_exams (exam_date) WHERE exam_date >= CURRENT_DATE - INTERVAL '2 years'",
    ]
    
    # WorkEnvironment 테이블 인덱스
    work_env_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_work_env_date_type ON work_environments (measurement_date, measurement_type)",
        "CREATE INDEX IF NOT EXISTS ix_work_env_location_result ON work_environments (location, result)",
        "CREATE INDEX IF NOT EXISTS ix_work_env_remeasure ON work_environments (re_measurement_required, re_measurement_date)",
        "CREATE INDEX IF NOT EXISTS ix_work_env_recent ON work_environments (measurement_date) WHERE measurement_date >= CURRENT_DATE - INTERVAL '1 year'",
    ]
    
    # ChemicalSubstance 테이블 인덱스
    chemical_indexes = [
        "CREATE INDEX IF NOT EXISTS ix_chemicals_name_search ON chemical_substances USING gin(to_tsvector('korean', korean_name))",
        "CREATE INDEX IF NOT EXISTS ix_chemicals_name_status ON chemical_substances (korean_name, status)",
        "CREATE INDEX IF NOT EXISTS ix_chemicals_hazard_special ON chemical_substances (hazard_class, special_management_material)",
        "CREATE INDEX IF NOT EXISTS ix_chemicals_location_quantity ON chemical_substances (storage_location, current_quantity)",
        "CREATE INDEX IF NOT EXISTS ix_chemicals_safety_flags ON chemical_substances (carcinogen, mutagen, reproductive_toxin)",
    ]
    
    all_indexes = worker_indexes + health_exam_indexes + work_env_indexes + chemical_indexes
    
    with engine.connect() as conn:
        for index_sql in all_indexes:
            try:
                conn.execute(text(index_sql))
                print(f"Created index: {index_sql.split(' ON ')[0].split(' ')[-1]}")
            except Exception as e:
                print(f"Error creating index: {e}")
        conn.commit()

def analyze_tables():
    """테이블 통계를 업데이트합니다."""
    engine = get_db_engine()
    
    tables = [
        'workers', 'health_exams', 'vital_signs', 'lab_results',
        'work_environments', 'chemical_substances', 'health_consultations'
    ]
    
    with engine.connect() as conn:
        for table in tables:
            try:
                conn.execute(text(f"ANALYZE {table}"))
                print(f"Analyzed table: {table}")
            except Exception as e:
                print(f"Error analyzing table {table}: {e}")
        conn.commit()

def optimize_database():
    """데이터베이스 최적화를 실행합니다."""
    print("Starting database optimization...")
    
    # 인덱스 생성
    create_optimized_indexes()
    
    # 테이블 분석
    analyze_tables()
    
    print("Database optimization completed!")

if __name__ == "__main__":
    optimize_database()