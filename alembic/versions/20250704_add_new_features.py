"""add new features - checklist, special materials, settings, legal forms

Revision ID: 20250704_001
Revises: 
Create Date: 2025-07-04 02:50:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250704_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    op.execute("CREATE TYPE checklisttype AS ENUM ('safety_management', 'risk_assessment', 'accident_response', 'health_management', 'education_training', 'facility_inspection', 'environment_monitoring', 'chemical_management', 'emergency_response', 'compliance_check')")
    op.execute("CREATE TYPE checkliststatus AS ENUM ('pending', 'in_progress', 'completed', 'overdue', 'cancelled')")
    op.execute("CREATE TYPE checklistpriority AS ENUM ('high', 'medium', 'low')")
    op.execute("CREATE TYPE specialmaterialtype AS ENUM ('carcinogen', 'mutagen', 'reproductive_toxin', 'respiratory_sensitizer', 'skin_sensitizer', 'toxic_gas', 'asbestos', 'silica', 'heavy_metal', 'organic_solvent')")
    op.execute("CREATE TYPE exposurelevel AS ENUM ('none', 'low', 'medium', 'high', 'critical')")
    op.execute("CREATE TYPE controlmeasuretype AS ENUM ('engineering', 'administrative', 'ppe', 'substitution', 'elimination')")
    op.execute("CREATE TYPE monitoringstatus AS ENUM ('pending', 'in_progress', 'completed', 'overdue', 'cancelled')")
    op.execute("CREATE TYPE legalformstatus AS ENUM ('draft', 'pending_review', 'approved', 'rejected', 'in_progress', 'completed', 'archived')")
    op.execute("CREATE TYPE legalformpriority AS ENUM ('urgent', 'high', 'medium', 'low')")
    op.execute("CREATE TYPE legalformcategory AS ENUM ('health_management_plan', 'measurement_result', 'health_checkup', 'emergency_response', 'education_record', 'accident_report', 'chemical_inventory', 'protective_equipment', 'compliance_report', 'other')")
    op.execute("CREATE TYPE backupfrequency AS ENUM ('daily', 'weekly', 'monthly')")
    op.execute("CREATE TYPE reportlanguage AS ENUM ('ko', 'en', 'both')")
    op.execute("CREATE TYPE dashboardlayout AS ENUM ('default', 'compact', 'detailed')")
    op.execute("CREATE TYPE theme AS ENUM ('light', 'dark', 'auto')")
    op.execute("CREATE TYPE language AS ENUM ('ko', 'en')")

    # Create checklist_templates table
    op.create_table('checklist_templates',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='템플릿명'),
        sa.Column('name_korean', sa.String(length=255), nullable=False, comment='한글명'),
        sa.Column('type', postgresql.ENUM('safety_management', 'risk_assessment', 'accident_response', 'health_management', 'education_training', 'facility_inspection', 'environment_monitoring', 'chemical_management', 'emergency_response', 'compliance_check', name='checklisttype'), nullable=False, comment='체크리스트 유형'),
        sa.Column('description', sa.Text(), nullable=True, comment='설명'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='활성 상태'),
        sa.Column('is_mandatory', sa.Boolean(), nullable=False, server_default='false', comment='필수 여부'),
        sa.Column('frequency_days', sa.Integer(), nullable=True, comment='주기(일)'),
        sa.Column('legal_basis', sa.String(length=500), nullable=True, comment='법적 근거'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_templates_id'), 'checklist_templates', ['id'], unique=False)

    # Create checklist_template_items table
    op.create_table('checklist_template_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('item_code', sa.String(length=50), nullable=False, comment='항목 코드'),
        sa.Column('item_name', sa.String(length=255), nullable=False, comment='항목명'),
        sa.Column('description', sa.Text(), nullable=True, comment='상세 설명'),
        sa.Column('check_method', sa.Text(), nullable=True, comment='점검 방법'),
        sa.Column('order_index', sa.Integer(), nullable=False, server_default='0', comment='순서'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='분류'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='true', comment='필수 항목'),
        sa.Column('weight', sa.Integer(), nullable=False, server_default='1', comment='가중치'),
        sa.Column('max_score', sa.Integer(), nullable=False, server_default='1', comment='최대 점수'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['template_id'], ['checklist_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_template_items_id'), 'checklist_template_items', ['id'], unique=False)

    # Create checklist_instances table
    op.create_table('checklist_instances',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False, comment='제목'),
        sa.Column('assignee', sa.String(length=100), nullable=False, comment='담당자'),
        sa.Column('department', sa.String(length=100), nullable=True, comment='담당 부서'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False, comment='예정일'),
        sa.Column('due_date', sa.DateTime(), nullable=True, comment='마감일'),
        sa.Column('started_at', sa.DateTime(), nullable=True, comment='시작일시'),
        sa.Column('completed_at', sa.DateTime(), nullable=True, comment='완료일시'),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'overdue', 'cancelled', name='checkliststatus'), nullable=False, server_default='pending', comment='상태'),
        sa.Column('priority', postgresql.ENUM('high', 'medium', 'low', name='checklistpriority'), nullable=False, server_default='medium', comment='우선순위'),
        sa.Column('total_score', sa.Integer(), nullable=True, comment='총점'),
        sa.Column('max_total_score', sa.Integer(), nullable=True, comment='최대 총점'),
        sa.Column('completion_rate', sa.Integer(), nullable=True, comment='완료율(%)'),
        sa.Column('notes', sa.Text(), nullable=True, comment='비고'),
        sa.Column('location', sa.String(length=255), nullable=True, comment='점검 장소'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.ForeignKeyConstraint(['template_id'], ['checklist_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_instances_id'), 'checklist_instances', ['id'], unique=False)

    # Create checklist_instance_items table
    op.create_table('checklist_instance_items',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_item_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_checked', sa.Boolean(), nullable=False, server_default='false', comment='점검 완료'),
        sa.Column('is_compliant', sa.Boolean(), nullable=True, comment='적합 여부'),
        sa.Column('score', sa.Integer(), nullable=True, comment='점수'),
        sa.Column('checked_at', sa.DateTime(), nullable=True, comment='점검일시'),
        sa.Column('checked_by', sa.String(length=100), nullable=True, comment='점검자'),
        sa.Column('findings', sa.Text(), nullable=True, comment='점검 결과'),
        sa.Column('corrective_action', sa.Text(), nullable=True, comment='시정조치사항'),
        sa.Column('corrective_due_date', sa.DateTime(), nullable=True, comment='시정조치 마감일'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['instance_id'], ['checklist_instances.id'], ),
        sa.ForeignKeyConstraint(['template_item_id'], ['checklist_template_items.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_instance_items_id'), 'checklist_instance_items', ['id'], unique=False)

    # Create checklist_attachments table
    op.create_table('checklist_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('instance_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='파일명'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='파일 경로'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='파일 크기'),
        sa.Column('file_type', sa.String(length=100), nullable=False, comment='파일 타입'),
        sa.Column('uploaded_by', sa.String(length=100), nullable=False, comment='업로드자'),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='업로드일시'),
        sa.Column('description', sa.Text(), nullable=True, comment='설명'),
        sa.ForeignKeyConstraint(['instance_id'], ['checklist_instances.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_attachments_id'), 'checklist_attachments', ['id'], unique=False)

    # Create checklist_schedules table
    op.create_table('checklist_schedules',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('template_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('name', sa.String(length=255), nullable=False, comment='스케줄명'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='활성 상태'),
        sa.Column('frequency_type', sa.String(length=20), nullable=False, comment='반복 유형 (daily/weekly/monthly/yearly)'),
        sa.Column('frequency_value', sa.Integer(), nullable=False, server_default='1', comment='반복 값'),
        sa.Column('default_assignee', sa.String(length=100), nullable=True, comment='기본 담당자'),
        sa.Column('default_department', sa.String(length=100), nullable=True, comment='기본 담당 부서'),
        sa.Column('auto_create_days_before', sa.Integer(), nullable=False, server_default='7', comment='자동 생성 일수 (사전)'),
        sa.Column('reminder_days_before', sa.Integer(), nullable=False, server_default='3', comment='알림 일수 (사전)'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('last_created_at', sa.DateTime(), nullable=True, comment='마지막 생성일시'),
        sa.Column('next_scheduled_at', sa.DateTime(), nullable=True, comment='다음 예정일시'),
        sa.ForeignKeyConstraint(['template_id'], ['checklist_templates.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_checklist_schedules_id'), 'checklist_schedules', ['id'], unique=False)

    # Create special_materials table
    op.create_table('special_materials',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_code', sa.String(length=50), nullable=False, comment='물질 코드'),
        sa.Column('material_name', sa.String(length=255), nullable=False, comment='물질명'),
        sa.Column('material_name_korean', sa.String(length=255), nullable=False, comment='한글명'),
        sa.Column('cas_number', sa.String(length=50), nullable=True, comment='CAS 번호'),
        sa.Column('material_type', postgresql.ENUM('carcinogen', 'mutagen', 'reproductive_toxin', 'respiratory_sensitizer', 'skin_sensitizer', 'toxic_gas', 'asbestos', 'silica', 'heavy_metal', 'organic_solvent', name='specialmaterialtype'), nullable=False, comment='물질 유형'),
        sa.Column('hazard_classification', sa.String(length=500), nullable=True, comment='유해성 분류'),
        sa.Column('ghs_classification', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='GHS 분류'),
        sa.Column('occupational_exposure_limit', sa.Numeric(precision=10, scale=6), nullable=True, comment='작업환경측정 기준(ppm/mg/m³)'),
        sa.Column('short_term_exposure_limit', sa.Numeric(precision=10, scale=6), nullable=True, comment='단기노출기준'),
        sa.Column('ceiling_limit', sa.Numeric(precision=10, scale=6), nullable=True, comment='최고노출기준'),
        sa.Column('biological_exposure_index', sa.Numeric(precision=10, scale=6), nullable=True, comment='생물학적 노출지수'),
        sa.Column('is_prohibited', sa.Boolean(), nullable=False, server_default='false', comment='사용금지 여부'),
        sa.Column('requires_permit', sa.Boolean(), nullable=False, server_default='true', comment='허가 필요 여부'),
        sa.Column('monitoring_frequency_days', sa.Integer(), nullable=False, server_default='180', comment='측정 주기(일)'),
        sa.Column('health_exam_frequency_months', sa.Integer(), nullable=False, server_default='12', comment='건강진단 주기(월)'),
        sa.Column('physical_state', sa.String(length=50), nullable=True, comment='물리적 상태'),
        sa.Column('molecular_weight', sa.Numeric(precision=10, scale=3), nullable=True, comment='분자량'),
        sa.Column('boiling_point', sa.Numeric(precision=10, scale=2), nullable=True, comment='끓는점(℃)'),
        sa.Column('melting_point', sa.Numeric(precision=10, scale=2), nullable=True, comment='녹는점(℃)'),
        sa.Column('vapor_pressure', sa.Numeric(precision=15, scale=6), nullable=True, comment='증기압(mmHg)'),
        sa.Column('target_organs', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='표적장기'),
        sa.Column('health_effects', sa.Text(), nullable=True, comment='건강 영향'),
        sa.Column('exposure_routes', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='노출 경로'),
        sa.Column('first_aid_measures', sa.Text(), nullable=True, comment='응급처치 요령'),
        sa.Column('safety_precautions', sa.Text(), nullable=True, comment='안전 주의사항'),
        sa.Column('storage_requirements', sa.Text(), nullable=True, comment='저장 요구사항'),
        sa.Column('disposal_methods', sa.Text(), nullable=True, comment='폐기 방법'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('material_code')
    )
    op.create_index(op.f('ix_special_materials_id'), 'special_materials', ['id'], unique=False)

    # Create special_material_usage table
    op.create_table('special_material_usage',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('usage_date', sa.DateTime(), nullable=False, comment='사용일시'),
        sa.Column('usage_location', sa.String(length=255), nullable=False, comment='사용 장소'),
        sa.Column('usage_purpose', sa.String(length=500), nullable=False, comment='사용 목적'),
        sa.Column('work_process', sa.String(length=500), nullable=True, comment='작업 공정'),
        sa.Column('quantity_used', sa.Numeric(precision=15, scale=3), nullable=False, comment='사용량'),
        sa.Column('unit', sa.String(length=20), nullable=False, comment='단위'),
        sa.Column('concentration', sa.Numeric(precision=10, scale=6), nullable=True, comment='농도(%)'),
        sa.Column('worker_id', sa.Integer(), nullable=True),
        sa.Column('worker_count', sa.Integer(), nullable=False, server_default='1', comment='작업자 수'),
        sa.Column('exposure_duration_hours', sa.Numeric(precision=5, scale=2), nullable=True, comment='노출 시간(시간)'),
        sa.Column('control_measures', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='관리 조치'),
        sa.Column('ppe_used', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='사용 개인보호구'),
        sa.Column('ventilation_type', sa.String(length=100), nullable=True, comment='환기 방식'),
        sa.Column('approved_by', sa.String(length=100), nullable=True, comment='승인자'),
        sa.Column('approval_date', sa.DateTime(), nullable=True, comment='승인일시'),
        sa.Column('permit_number', sa.String(length=100), nullable=True, comment='허가번호'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('recorded_by', sa.String(length=100), nullable=False, comment='기록자'),
        sa.ForeignKeyConstraint(['material_id'], ['special_materials.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_special_material_usage_id'), 'special_material_usage', ['id'], unique=False)

    # Create exposure_assessments table
    op.create_table('exposure_assessments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assessment_date', sa.DateTime(), nullable=False, comment='평가일시'),
        sa.Column('assessment_type', sa.String(length=100), nullable=False, comment='평가 유형'),
        sa.Column('assessment_location', sa.String(length=255), nullable=False, comment='평가 장소'),
        sa.Column('work_activity', sa.String(length=500), nullable=False, comment='작업 활동'),
        sa.Column('measured_concentration', sa.Numeric(precision=15, scale=6), nullable=True, comment='측정 농도'),
        sa.Column('measurement_unit', sa.String(length=20), nullable=True, comment='측정 단위'),
        sa.Column('sampling_duration_minutes', sa.Integer(), nullable=True, comment='시료채취 시간(분)'),
        sa.Column('sampling_method', sa.String(length=200), nullable=True, comment='시료채취 방법'),
        sa.Column('analysis_method', sa.String(length=200), nullable=True, comment='분석 방법'),
        sa.Column('exposure_level', postgresql.ENUM('none', 'low', 'medium', 'high', 'critical', name='exposurelevel'), nullable=False, comment='노출 수준'),
        sa.Column('exposure_route', sa.String(length=100), nullable=True, comment='주요 노출 경로'),
        sa.Column('risk_score', sa.Numeric(precision=5, scale=2), nullable=True, comment='위험도 점수'),
        sa.Column('recommended_controls', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='권고 관리 조치'),
        sa.Column('priority_level', sa.String(length=20), nullable=False, server_default='medium', comment='우선순위'),
        sa.Column('follow_up_required', sa.Boolean(), nullable=False, server_default='false', comment='후속조치 필요'),
        sa.Column('follow_up_date', sa.DateTime(), nullable=True, comment='후속조치 예정일'),
        sa.Column('assessor_name', sa.String(length=100), nullable=False, comment='평가자명'),
        sa.Column('assessor_qualification', sa.String(length=200), nullable=True, comment='평가자 자격'),
        sa.Column('assessment_organization', sa.String(length=200), nullable=True, comment='평가기관'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['material_id'], ['special_materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_exposure_assessments_id'), 'exposure_assessments', ['id'], unique=False)

    # Create special_material_monitoring table
    op.create_table('special_material_monitoring',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('monitoring_date', sa.DateTime(), nullable=False, comment='모니터링 일시'),
        sa.Column('monitoring_type', sa.String(length=100), nullable=False, comment='모니터링 유형'),
        sa.Column('location', sa.String(length=255), nullable=False, comment='모니터링 장소'),
        sa.Column('status', postgresql.ENUM('pending', 'in_progress', 'completed', 'overdue', 'cancelled', name='monitoringstatus'), nullable=False, server_default='pending', comment='상태'),
        sa.Column('scheduled_date', sa.DateTime(), nullable=False, comment='예정일'),
        sa.Column('frequency_type', sa.String(length=50), nullable=False, comment='주기 유형'),
        sa.Column('next_monitoring_date', sa.DateTime(), nullable=True, comment='다음 모니터링 예정일'),
        sa.Column('measurement_results', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='측정 결과'),
        sa.Column('compliance_status', sa.Boolean(), nullable=True, comment='기준 준수 여부'),
        sa.Column('exceedance_factor', sa.Numeric(precision=10, scale=2), nullable=True, comment='기준 초과배수'),
        sa.Column('corrective_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='시정조치사항'),
        sa.Column('action_due_date', sa.DateTime(), nullable=True, comment='시정조치 마감일'),
        sa.Column('action_responsible', sa.String(length=100), nullable=True, comment='시정조치 담당자'),
        sa.Column('action_status', sa.String(length=50), nullable=True, comment='시정조치 상태'),
        sa.Column('monitor_name', sa.String(length=100), nullable=False, comment='모니터링 담당자'),
        sa.Column('monitor_organization', sa.String(length=200), nullable=True, comment='모니터링 기관'),
        sa.Column('report_number', sa.String(length=100), nullable=True, comment='보고서 번호'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.ForeignKeyConstraint(['material_id'], ['special_materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_special_material_monitoring_id'), 'special_material_monitoring', ['id'], unique=False)

    # Create control_measures table
    op.create_table('control_measures',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('material_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('measure_type', postgresql.ENUM('engineering', 'administrative', 'ppe', 'substitution', 'elimination', name='controlmeasuretype'), nullable=False, comment='조치 유형'),
        sa.Column('measure_name', sa.String(length=255), nullable=False, comment='조치명'),
        sa.Column('description', sa.Text(), nullable=False, comment='상세 설명'),
        sa.Column('implementation_date', sa.DateTime(), nullable=False, comment='시행일'),
        sa.Column('effectiveness_rating', sa.Integer(), nullable=True, comment='효과성 등급(1-5)'),
        sa.Column('cost_estimate', sa.Numeric(precision=15, scale=2), nullable=True, comment='예상 비용'),
        sa.Column('maintenance_frequency', sa.String(length=100), nullable=True, comment='유지보수 주기'),
        sa.Column('responsible_person', sa.String(length=100), nullable=False, comment='책임자'),
        sa.Column('responsible_department', sa.String(length=100), nullable=True, comment='담당 부서'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='활성 상태'),
        sa.Column('last_inspection_date', sa.DateTime(), nullable=True, comment='마지막 점검일'),
        sa.Column('next_inspection_date', sa.DateTime(), nullable=True, comment='다음 점검 예정일'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.ForeignKeyConstraint(['material_id'], ['special_materials.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_control_measures_id'), 'control_measures', ['id'], unique=False)

    # Create legal_forms table
    op.create_table('legal_forms',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_code', sa.String(length=50), nullable=False, comment='서식 코드'),
        sa.Column('form_name_korean', sa.String(length=255), nullable=False, comment='한글 서식명'),
        sa.Column('form_name_english', sa.String(length=255), nullable=True, comment='영문 서식명'),
        sa.Column('category', postgresql.ENUM('health_management_plan', 'measurement_result', 'health_checkup', 'emergency_response', 'education_record', 'accident_report', 'chemical_inventory', 'protective_equipment', 'compliance_report', 'other', name='legalformcategory'), nullable=False, comment='서식 분류'),
        sa.Column('legal_basis', sa.Text(), nullable=True, comment='법적 근거'),
        sa.Column('status', postgresql.ENUM('draft', 'pending_review', 'approved', 'rejected', 'in_progress', 'completed', 'archived', name='legalformstatus'), nullable=False, server_default='draft', comment='상태'),
        sa.Column('priority', postgresql.ENUM('urgent', 'high', 'medium', 'low', name='legalformpriority'), nullable=False, server_default='medium', comment='우선순위'),
        sa.Column('form_fields', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='서식 필드 정의'),
        sa.Column('required_documents', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='필요 문서 목록'),
        sa.Column('processing_notes', sa.Text(), nullable=True, comment='처리 참고사항'),
        sa.Column('submission_deadline', sa.DateTime(), nullable=True, comment='제출 기한'),
        sa.Column('submitted_date', sa.DateTime(), nullable=True, comment='제출일'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.Column('updated_by', sa.String(length=100), nullable=True, comment='수정자'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('form_code')
    )
    op.create_index(op.f('ix_legal_forms_id'), 'legal_forms', ['id'], unique=False)

    # Create legal_form_fields table
    op.create_table('legal_form_fields',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('field_name', sa.String(length=100), nullable=False, comment='필드명'),
        sa.Column('field_label', sa.String(length=255), nullable=False, comment='필드 라벨'),
        sa.Column('field_type', sa.String(length=50), nullable=False, comment='필드 유형'),
        sa.Column('is_required', sa.Boolean(), nullable=False, server_default='false', comment='필수 여부'),
        sa.Column('field_order', sa.Integer(), nullable=False, server_default='0', comment='필드 순서'),
        sa.Column('validation_rules', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='유효성 검사 규칙'),
        sa.Column('default_value', sa.Text(), nullable=True, comment='기본값'),
        sa.Column('options', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='선택 옵션'),
        sa.Column('help_text', sa.Text(), nullable=True, comment='도움말'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['form_id'], ['legal_forms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_form_fields_id'), 'legal_form_fields', ['id'], unique=False)

    # Create legal_form_attachments table
    op.create_table('legal_form_attachments',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=False, comment='파일명'),
        sa.Column('file_path', sa.String(length=500), nullable=False, comment='파일 경로'),
        sa.Column('file_size', sa.Integer(), nullable=False, comment='파일 크기'),
        sa.Column('file_type', sa.String(length=100), nullable=False, comment='파일 타입'),
        sa.Column('uploaded_by', sa.String(length=100), nullable=False, comment='업로드자'),
        sa.Column('uploaded_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='업로드일시'),
        sa.Column('description', sa.Text(), nullable=True, comment='설명'),
        sa.ForeignKeyConstraint(['form_id'], ['legal_forms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_form_attachments_id'), 'legal_form_attachments', ['id'], unique=False)

    # Create legal_form_approvals table
    op.create_table('legal_form_approvals',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('form_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('approver', sa.String(length=100), nullable=False, comment='승인자'),
        sa.Column('approval_level', sa.Integer(), nullable=False, comment='승인 단계'),
        sa.Column('approval_status', sa.String(length=20), nullable=False, comment='승인 상태'),
        sa.Column('approved_at', sa.DateTime(), nullable=True, comment='승인일시'),
        sa.Column('comments', sa.Text(), nullable=True, comment='승인 의견'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.ForeignKeyConstraint(['form_id'], ['legal_forms.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_legal_form_approvals_id'), 'legal_form_approvals', ['id'], unique=False)

    # Create unified_documents table
    op.create_table('unified_documents',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('document_code', sa.String(length=50), nullable=False, comment='문서 코드'),
        sa.Column('document_name', sa.String(length=255), nullable=False, comment='문서명'),
        sa.Column('document_type', sa.String(length=50), nullable=False, comment='문서 유형'),
        sa.Column('category', sa.String(length=100), nullable=True, comment='분류'),
        sa.Column('status', sa.String(length=20), nullable=False, server_default='draft', comment='상태'),
        sa.Column('content', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='문서 내용'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='메타데이터'),
        sa.Column('version', sa.Integer(), nullable=False, server_default='1', comment='버전'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true', comment='활성 상태'),
        sa.Column('generated_at', sa.DateTime(), nullable=True, comment='생성일시'),
        sa.Column('exported_at', sa.DateTime(), nullable=True, comment='내보내기일시'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('created_by', sa.String(length=100), nullable=False, comment='생성자'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('document_code')
    )
    op.create_index(op.f('ix_unified_documents_id'), 'unified_documents', ['id'], unique=False)

    # Create system_settings table
    op.create_table('system_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('company_name', sa.String(length=255), nullable=False, comment='회사명'),
        sa.Column('company_registration_number', sa.String(length=50), nullable=True, comment='사업자등록번호'),
        sa.Column('company_address', sa.String(length=500), nullable=True, comment='회사 주소'),
        sa.Column('company_phone', sa.String(length=50), nullable=True, comment='회사 전화번호'),
        sa.Column('company_email', sa.String(length=255), nullable=True, comment='회사 이메일'),
        sa.Column('representative_name', sa.String(length=100), nullable=True, comment='대표자명'),
        sa.Column('health_manager_name', sa.String(length=100), nullable=True, comment='보건관리자명'),
        sa.Column('health_manager_license', sa.String(length=100), nullable=True, comment='보건관리자 자격번호'),
        sa.Column('workplace_name', sa.String(length=255), nullable=True, comment='사업장명'),
        sa.Column('workplace_address', sa.String(length=500), nullable=True, comment='사업장 주소'),
        sa.Column('total_employees', sa.Integer(), nullable=True, comment='총 근로자수'),
        sa.Column('construction_employees', sa.Integer(), nullable=True, comment='건설업 근로자수'),
        sa.Column('industry_type', sa.String(length=100), nullable=True, comment='업종'),
        sa.Column('business_type', sa.String(length=100), nullable=True, comment='사업 유형'),
        sa.Column('smtp_host', sa.String(length=255), nullable=True, comment='SMTP 호스트'),
        sa.Column('smtp_port', sa.Integer(), nullable=True, comment='SMTP 포트'),
        sa.Column('smtp_username', sa.String(length=255), nullable=True, comment='SMTP 사용자명'),
        sa.Column('smtp_password', sa.String(length=255), nullable=True, comment='SMTP 비밀번호'),
        sa.Column('smtp_use_tls', sa.Boolean(), nullable=True, server_default='true', comment='TLS 사용'),
        sa.Column('notification_email', sa.String(length=255), nullable=True, comment='알림 수신 이메일'),
        sa.Column('backup_enabled', sa.Boolean(), nullable=True, server_default='true', comment='백업 활성화'),
        sa.Column('backup_frequency', postgresql.ENUM('daily', 'weekly', 'monthly', name='backupfrequency'), nullable=True, comment='백업 주기'),
        sa.Column('backup_retention_days', sa.Integer(), nullable=True, server_default='30', comment='백업 보관일수'),
        sa.Column('backup_path', sa.String(length=500), nullable=True, comment='백업 경로'),
        sa.Column('report_logo_path', sa.String(length=500), nullable=True, comment='보고서 로고 경로'),
        sa.Column('report_header_text', sa.Text(), nullable=True, comment='보고서 머리글'),
        sa.Column('report_footer_text', sa.Text(), nullable=True, comment='보고서 바닥글'),
        sa.Column('report_default_language', postgresql.ENUM('ko', 'en', 'both', name='reportlanguage'), nullable=True, server_default='ko', comment='보고서 기본 언어'),
        sa.Column('timezone', sa.String(length=50), nullable=True, server_default='Asia/Seoul', comment='시간대'),
        sa.Column('date_format', sa.String(length=50), nullable=True, server_default='YYYY-MM-DD', comment='날짜 형식'),
        sa.Column('time_format', sa.String(length=50), nullable=True, server_default='HH:mm:ss', comment='시간 형식'),
        sa.Column('currency', sa.String(length=10), nullable=True, server_default='KRW', comment='통화'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.Column('updated_by', sa.String(length=100), nullable=True, comment='수정자'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_system_settings_id'), 'system_settings', ['id'], unique=False)

    # Create user_settings table
    op.create_table('user_settings',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', sa.String(length=100), nullable=False, comment='사용자 ID'),
        sa.Column('dashboard_layout', postgresql.ENUM('default', 'compact', 'detailed', name='dashboardlayout'), nullable=True, server_default='default', comment='대시보드 레이아웃'),
        sa.Column('theme', postgresql.ENUM('light', 'dark', 'auto', name='theme'), nullable=True, server_default='auto', comment='테마'),
        sa.Column('language', postgresql.ENUM('ko', 'en', name='language'), nullable=True, server_default='ko', comment='언어'),
        sa.Column('items_per_page', sa.Integer(), nullable=True, server_default='20', comment='페이지당 항목 수'),
        sa.Column('email_notifications', sa.Boolean(), nullable=True, server_default='true', comment='이메일 알림'),
        sa.Column('sms_notifications', sa.Boolean(), nullable=True, server_default='false', comment='SMS 알림'),
        sa.Column('push_notifications', sa.Boolean(), nullable=True, server_default='true', comment='푸시 알림'),
        sa.Column('notification_frequency', sa.String(length=50), nullable=True, server_default='immediate', comment='알림 주기'),
        sa.Column('sidebar_collapsed', sa.Boolean(), nullable=True, server_default='false', comment='사이드바 접힘'),
        sa.Column('table_density', sa.String(length=20), nullable=True, server_default='normal', comment='테이블 밀도'),
        sa.Column('show_tooltips', sa.Boolean(), nullable=True, server_default='true', comment='도움말 표시'),
        sa.Column('custom_shortcuts', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='사용자 단축키'),
        sa.Column('pinned_menus', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='고정 메뉴'),
        sa.Column('recent_searches', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='최근 검색'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='생성일시'),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='수정일시'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_user_settings_id'), 'user_settings', ['id'], unique=False)

    # Create settings_history table
    op.create_table('settings_history',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('setting_type', sa.String(length=50), nullable=False, comment='설정 유형'),
        sa.Column('setting_id', postgresql.UUID(as_uuid=True), nullable=False, comment='설정 ID'),
        sa.Column('field_name', sa.String(length=100), nullable=False, comment='필드명'),
        sa.Column('old_value', sa.Text(), nullable=True, comment='이전 값'),
        sa.Column('new_value', sa.Text(), nullable=True, comment='새 값'),
        sa.Column('changed_by', sa.String(length=100), nullable=False, comment='변경자'),
        sa.Column('changed_at', sa.DateTime(), server_default=sa.text('now()'), nullable=True, comment='변경일시'),
        sa.Column('change_reason', sa.Text(), nullable=True, comment='변경 사유'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_settings_history_id'), 'settings_history', ['id'], unique=False)

    # Add consultation_type column to health_consultations if it doesn't exist
    op.execute("ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS consultation_type VARCHAR(50) NOT NULL DEFAULT 'general'")
    
    # Add follow_up_required column to health_consultations if it doesn't exist
    op.execute("ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS follow_up_required BOOLEAN NOT NULL DEFAULT false")
    
    # Add follow_up_notes column to health_consultations if it doesn't exist
    op.execute("ALTER TABLE health_consultations ADD COLUMN IF NOT EXISTS follow_up_notes TEXT")

    # Create health_consultation_follow_ups table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS health_consultation_follow_ups (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            consultation_id UUID NOT NULL REFERENCES health_consultations(id),
            follow_up_date TIMESTAMP NOT NULL,
            follow_up_type VARCHAR(50) NOT NULL,
            status VARCHAR(20) NOT NULL DEFAULT 'pending',
            notes TEXT,
            completed_at TIMESTAMP,
            completed_by VARCHAR(100),
            created_at TIMESTAMP DEFAULT now(),
            updated_at TIMESTAMP DEFAULT now()
        )
    """)

    # Create health_consultation_attachments table if it doesn't exist
    op.execute("""
        CREATE TABLE IF NOT EXISTS health_consultation_attachments (
            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
            consultation_id UUID NOT NULL REFERENCES health_consultations(id),
            file_name VARCHAR(255) NOT NULL,
            file_path VARCHAR(500) NOT NULL,
            file_size INTEGER NOT NULL,
            file_type VARCHAR(100) NOT NULL,
            uploaded_by VARCHAR(100) NOT NULL,
            uploaded_at TIMESTAMP DEFAULT now(),
            description TEXT
        )
    """)


def downgrade():
    # Drop tables in reverse order
    op.drop_table('settings_history')
    op.drop_table('user_settings')
    op.drop_table('system_settings')
    op.drop_table('unified_documents')
    op.drop_table('legal_form_approvals')
    op.drop_table('legal_form_attachments')
    op.drop_table('legal_form_fields')
    op.drop_table('legal_forms')
    op.drop_table('control_measures')
    op.drop_table('special_material_monitoring')
    op.drop_table('exposure_assessments')
    op.drop_table('special_material_usage')
    op.drop_table('special_materials')
    op.drop_table('checklist_schedules')
    op.drop_table('checklist_attachments')
    op.drop_table('checklist_instance_items')
    op.drop_table('checklist_instances')
    op.drop_table('checklist_template_items')
    op.drop_table('checklist_templates')
    
    # Drop consultation tables
    op.drop_table('health_consultation_attachments')
    op.drop_table('health_consultation_follow_ups')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS checklisttype')
    op.execute('DROP TYPE IF EXISTS checkliststatus')
    op.execute('DROP TYPE IF EXISTS checklistpriority')
    op.execute('DROP TYPE IF EXISTS specialmaterialtype')
    op.execute('DROP TYPE IF EXISTS exposurelevel')
    op.execute('DROP TYPE IF EXISTS controlmeasuretype')
    op.execute('DROP TYPE IF EXISTS monitoringstatus')
    op.execute('DROP TYPE IF EXISTS legalformstatus')
    op.execute('DROP TYPE IF EXISTS legalformpriority')
    op.execute('DROP TYPE IF EXISTS legalformcategory')
    op.execute('DROP TYPE IF EXISTS backupfrequency')
    op.execute('DROP TYPE IF EXISTS reportlanguage')
    op.execute('DROP TYPE IF EXISTS dashboardlayout')
    op.execute('DROP TYPE IF EXISTS theme')
    op.execute('DROP TYPE IF EXISTS language')