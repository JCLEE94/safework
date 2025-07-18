"""add confined space tables

Revision ID: add_confined_space_tables
Revises: add_qr_registration_tables
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_confined_space_tables'
down_revision = 'add_qr_registration_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Create enum types
    op.execute("""
        CREATE TYPE confinedspacetype AS ENUM (
            '탱크', '맨홀', '배관', '피트', '사일로', 
            '터널', '보일러', '용광로', '용기', '기타'
        )
    """)
    
    op.execute("""
        CREATE TYPE hazardtype AS ENUM (
            '산소결핍', '유독가스', '가연성가스', '익사', '매몰',
            '고온', '저온', '감전', '기계적위험', '기타'
        )
    """)
    
    op.execute("""
        CREATE TYPE workpermitstatus AS ENUM (
            '작성중', '제출됨', '승인됨', '작업중', 
            '완료됨', '취소됨', '만료됨'
        )
    """)
    
    # Create confined_spaces table
    op.create_table(
        'confined_spaces',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('name', sa.String(100), nullable=False, comment='밀폐공간명'),
        sa.Column('location', sa.String(200), nullable=False, comment='위치'),
        sa.Column('type', postgresql.ENUM('탱크', '맨홀', '배관', '피트', '사일로', '터널', '보일러', '용광로', '용기', '기타', name='confinedspacetype'), nullable=False, comment='밀폐공간 유형'),
        sa.Column('description', sa.Text, comment='설명'),
        
        # 공간 특성
        sa.Column('volume', sa.Float, comment='용적(m³)'),
        sa.Column('depth', sa.Float, comment='깊이(m)'),
        sa.Column('entry_points', sa.Integer, default=1, comment='출입구 수'),
        sa.Column('ventilation_type', sa.String(50), comment='환기 방식'),
        
        # 위험 요인
        sa.Column('hazards', sa.JSON, comment='위험 요인 목록'),
        sa.Column('oxygen_level_normal', sa.Float, comment='정상 산소 농도(%)'),
        
        # 관리 정보
        sa.Column('responsible_person', sa.String(50), comment='관리책임자'),
        sa.Column('last_inspection_date', sa.DateTime, comment='최근 점검일'),
        sa.Column('inspection_cycle_days', sa.Integer, default=30, comment='점검주기(일)'),
        
        # 상태
        sa.Column('is_active', sa.Boolean, default=True, comment='사용 가능 여부'),
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), comment='생성일시'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()'), comment='수정일시'),
        sa.Column('created_by', sa.String(50), comment='생성자')
    )
    
    # Create confined_space_work_permits table
    op.create_table(
        'confined_space_work_permits',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('permit_number', sa.String(50), unique=True, nullable=False, comment='허가서 번호'),
        sa.Column('confined_space_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('confined_spaces.id'), nullable=False),
        
        # 작업 정보
        sa.Column('work_description', sa.Text, nullable=False, comment='작업 내용'),
        sa.Column('work_purpose', sa.String(200), comment='작업 목적'),
        sa.Column('contractor', sa.String(100), comment='작업 업체'),
        
        # 작업 일정
        sa.Column('scheduled_start', sa.DateTime, nullable=False, comment='작업 시작 예정일시'),
        sa.Column('scheduled_end', sa.DateTime, nullable=False, comment='작업 종료 예정일시'),
        sa.Column('actual_start', sa.DateTime, comment='실제 시작일시'),
        sa.Column('actual_end', sa.DateTime, comment='실제 종료일시'),
        
        # 작업자 정보
        sa.Column('supervisor_name', sa.String(50), nullable=False, comment='작업 감독자'),
        sa.Column('supervisor_contact', sa.String(20), comment='감독자 연락처'),
        sa.Column('workers', sa.JSON, comment='작업자 목록'),
        
        # 안전 조치
        sa.Column('hazard_assessment', sa.JSON, comment='위험성 평가'),
        sa.Column('safety_measures', sa.JSON, comment='안전 조치 사항'),
        sa.Column('required_ppe', sa.JSON, comment='필수 보호구'),
        
        # 가스 측정
        sa.Column('gas_test_required', sa.Boolean, default=True, comment='가스 측정 필요 여부'),
        sa.Column('gas_test_interval_minutes', sa.Integer, default=60, comment='가스 측정 주기(분)'),
        sa.Column('gas_test_results', sa.JSON, comment='가스 측정 결과'),
        
        # 비상 대응
        sa.Column('emergency_contact', sa.String(20), comment='비상 연락처'),
        sa.Column('emergency_procedures', sa.Text, comment='비상 대응 절차'),
        sa.Column('rescue_equipment', sa.JSON, comment='구조 장비 목록'),
        
        # 승인 정보
        sa.Column('status', postgresql.ENUM('작성중', '제출됨', '승인됨', '작업중', '완료됨', '취소됨', '만료됨', name='workpermitstatus'), default='작성중', comment='상태'),
        sa.Column('submitted_by', sa.String(50), comment='제출자'),
        sa.Column('submitted_at', sa.DateTime, comment='제출일시'),
        sa.Column('approved_by', sa.String(50), comment='승인자'),
        sa.Column('approved_at', sa.DateTime, comment='승인일시'),
        
        # 메타데이터
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), comment='생성일시'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()'), comment='수정일시')
    )
    
    # Create confined_space_gas_measurements table
    op.create_table(
        'confined_space_gas_measurements',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('work_permit_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('confined_space_work_permits.id'), nullable=False),
        
        # 측정 정보
        sa.Column('measurement_time', sa.DateTime, nullable=False, server_default=sa.text('now()'), comment='측정 시간'),
        sa.Column('measurement_location', sa.String(100), comment='측정 위치'),
        sa.Column('measured_by', sa.String(50), nullable=False, comment='측정자'),
        
        # 측정값
        sa.Column('oxygen_level', sa.Float, comment='산소 농도(%)'),
        sa.Column('carbon_monoxide', sa.Float, comment='일산화탄소(ppm)'),
        sa.Column('hydrogen_sulfide', sa.Float, comment='황화수소(ppm)'),
        sa.Column('methane', sa.Float, comment='메탄(%LEL)'),
        sa.Column('other_gases', sa.JSON, comment='기타 가스 측정값'),
        
        # 판정
        sa.Column('is_safe', sa.Boolean, nullable=False, comment='안전 여부'),
        sa.Column('remarks', sa.Text, comment='비고'),
        
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), comment='생성일시')
    )
    
    # Create confined_space_safety_checklists table
    op.create_table(
        'confined_space_safety_checklists',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('confined_space_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('confined_spaces.id'), nullable=False),
        
        # 점검 정보
        sa.Column('inspection_date', sa.DateTime, nullable=False, server_default=sa.text('now()'), comment='점검일시'),
        sa.Column('inspector_name', sa.String(50), nullable=False, comment='점검자'),
        
        # 체크리스트 항목
        sa.Column('checklist_items', sa.JSON, nullable=False, comment='체크리스트 항목'),
        
        # 전체 평가
        sa.Column('overall_status', sa.String(20), comment='전체 상태'),
        sa.Column('corrective_actions', sa.JSON, comment='시정 조치 사항'),
        
        # 서명
        sa.Column('inspector_signature', sa.Text, comment='점검자 서명'),
        sa.Column('reviewer_name', sa.String(50), comment='검토자'),
        sa.Column('reviewer_signature', sa.Text, comment='검토자 서명'),
        
        sa.Column('created_at', sa.DateTime, server_default=sa.text('now()'), comment='생성일시'),
        sa.Column('updated_at', sa.DateTime, server_default=sa.text('now()'), onupdate=sa.text('now()'), comment='수정일시')
    )
    
    # Create indexes
    op.create_index('idx_confined_spaces_active', 'confined_spaces', ['is_active'])
    op.create_index('idx_confined_spaces_location', 'confined_spaces', ['location'])
    op.create_index('idx_work_permits_space_id', 'confined_space_work_permits', ['confined_space_id'])
    op.create_index('idx_work_permits_status', 'confined_space_work_permits', ['status'])
    op.create_index('idx_work_permits_scheduled', 'confined_space_work_permits', ['scheduled_start', 'scheduled_end'])
    op.create_index('idx_gas_measurements_permit_id', 'confined_space_gas_measurements', ['work_permit_id'])
    op.create_index('idx_safety_checklists_space_id', 'confined_space_safety_checklists', ['confined_space_id'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_safety_checklists_space_id')
    op.drop_index('idx_gas_measurements_permit_id')
    op.drop_index('idx_work_permits_scheduled')
    op.drop_index('idx_work_permits_status')
    op.drop_index('idx_work_permits_space_id')
    op.drop_index('idx_confined_spaces_location')
    op.drop_index('idx_confined_spaces_active')
    
    # Drop tables
    op.drop_table('confined_space_safety_checklists')
    op.drop_table('confined_space_gas_measurements')
    op.drop_table('confined_space_work_permits')
    op.drop_table('confined_spaces')
    
    # Drop enum types
    op.execute('DROP TYPE IF EXISTS workpermitstatus')
    op.execute('DROP TYPE IF EXISTS hazardtype')
    op.execute('DROP TYPE IF EXISTS confinedspacetype')