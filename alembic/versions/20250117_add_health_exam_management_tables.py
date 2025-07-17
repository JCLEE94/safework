"""Add health exam management tables

Revision ID: add_health_exam_mgmt_20250117
Revises: add_health_room_tables_20250117
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_health_exam_mgmt_20250117'
down_revision = 'add_health_room_tables_20250117'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    op.execute("CREATE TYPE examplanstatus AS ENUM ('draft', 'approved', 'in_progress', 'completed', 'cancelled')")
    op.execute("CREATE TYPE examcategory AS ENUM ('일반건강진단_정기', '일반건강진단_임시', '특수건강진단_정기', '특수건강진단_임시', '배치전건강진단', '직무전환건강진단', '야간작업건강진단')")
    op.execute("CREATE TYPE resultdeliverymethod AS ENUM ('직접수령', '우편발송', '이메일', '모바일', '회사일괄')")
    
    # Create health_exam_plans table
    op.create_table(
        'health_exam_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_year', sa.Integer(), nullable=False),
        sa.Column('plan_name', sa.String(length=200), nullable=False),
        sa.Column('plan_status', sa.Enum('draft', 'approved', 'in_progress', 'completed', 'cancelled', 
                                        name='examplanstatus'), server_default='draft', nullable=True),
        sa.Column('total_workers', sa.Integer(), server_default='0', nullable=True),
        sa.Column('general_exam_targets', sa.Integer(), server_default='0', nullable=True),
        sa.Column('special_exam_targets', sa.Integer(), server_default='0', nullable=True),
        sa.Column('night_work_targets', sa.Integer(), server_default='0', nullable=True),
        sa.Column('plan_start_date', sa.Date(), nullable=True),
        sa.Column('plan_end_date', sa.Date(), nullable=True),
        sa.Column('primary_institution', sa.String(length=200), nullable=True),
        sa.Column('secondary_institutions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('estimated_budget', sa.Float(), nullable=True),
        sa.Column('budget_per_person', sa.Float(), nullable=True),
        sa.Column('harmful_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_targets table
    op.create_table(
        'health_exam_targets',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('exam_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('general_exam_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('general_exam_date', sa.Date(), nullable=True),
        sa.Column('special_exam_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('special_exam_harmful_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('special_exam_date', sa.Date(), nullable=True),
        sa.Column('night_work_exam_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('night_work_months', sa.Integer(), nullable=True),
        sa.Column('night_work_exam_date', sa.Date(), nullable=True),
        sa.Column('exam_cycle_months', sa.Integer(), server_default='12', nullable=True),
        sa.Column('last_exam_date', sa.Date(), nullable=True),
        sa.Column('next_exam_due_date', sa.Date(), nullable=True),
        sa.Column('reservation_status', sa.String(length=50), nullable=True),
        sa.Column('reserved_date', sa.Date(), nullable=True),
        sa.Column('is_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('completed_date', sa.Date(), nullable=True),
        sa.Column('special_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['health_exam_plans.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_schedules table
    op.create_table(
        'health_exam_schedules',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('plan_id', sa.Integer(), nullable=False),
        sa.Column('schedule_date', sa.Date(), nullable=False),
        sa.Column('start_time', sa.String(length=10), nullable=True),
        sa.Column('end_time', sa.String(length=10), nullable=True),
        sa.Column('institution_name', sa.String(length=200), nullable=False),
        sa.Column('institution_address', sa.Text(), nullable=True),
        sa.Column('institution_contact', sa.String(length=50), nullable=True),
        sa.Column('exam_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_capacity', sa.Integer(), server_default='50', nullable=True),
        sa.Column('reserved_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('available_slots', sa.Integer(), server_default='50', nullable=True),
        sa.Column('group_code', sa.String(length=50), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('is_full', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('special_requirements', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['plan_id'], ['health_exam_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_reservations table
    op.create_table(
        'health_exam_reservations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('reservation_number', sa.String(length=50), unique=True, nullable=True),
        sa.Column('reserved_exam_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reserved_time', sa.String(length=10), nullable=True),
        sa.Column('estimated_duration', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='reserved', nullable=True),
        sa.Column('check_in_time', sa.DateTime(), nullable=True),
        sa.Column('check_out_time', sa.DateTime(), nullable=True),
        sa.Column('fasting_required', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('special_preparations', sa.Text(), nullable=True),
        sa.Column('contact_phone', sa.String(length=20), nullable=True),
        sa.Column('contact_email', sa.String(length=100), nullable=True),
        sa.Column('result_delivery_method', sa.Enum('직접수령', '우편발송', '이메일', '모바일', '회사일괄',
                                                   name='resultdeliverymethod'), nullable=True),
        sa.Column('result_delivery_address', sa.Text(), nullable=True),
        sa.Column('reminder_sent', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('reminder_sent_at', sa.DateTime(), nullable=True),
        sa.Column('is_cancelled', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('cancelled_at', sa.DateTime(), nullable=True),
        sa.Column('cancellation_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['schedule_id'], ['health_exam_schedules.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_charts table
    op.create_table(
        'health_exam_charts',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('reservation_id', sa.Integer(), nullable=True),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('exam_date', sa.Date(), nullable=False),
        sa.Column('chart_number', sa.String(length=50), unique=True, nullable=True),
        sa.Column('exam_type', sa.String(length=50), nullable=True),
        sa.Column('medical_history', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('lifestyle_habits', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('symptoms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('work_environment', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('special_exam_questionnaire', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('female_health_info', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('exam_day_condition', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('worker_signature', sa.Text(), nullable=True),
        sa.Column('signed_at', sa.DateTime(), nullable=True),
        sa.Column('doctor_notes', sa.Text(), nullable=True),
        sa.Column('nurse_notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['reservation_id'], ['health_exam_reservations.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_results table
    op.create_table(
        'health_exam_results',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('chart_id', sa.Integer(), nullable=True),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('health_exam_id', sa.Integer(), nullable=True),
        sa.Column('result_received_date', sa.Date(), nullable=True),
        sa.Column('result_delivery_method', sa.String(length=50), nullable=True),
        sa.Column('overall_result', sa.String(length=50), nullable=True),
        sa.Column('overall_opinion', sa.Text(), nullable=True),
        sa.Column('exam_summary', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('abnormal_findings', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('followup_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_items', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('followup_deadline', sa.Date(), nullable=True),
        sa.Column('work_fitness', sa.String(length=100), nullable=True),
        sa.Column('work_restrictions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('health_guidance', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('worker_confirmed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('worker_confirmed_at', sa.DateTime(), nullable=True),
        sa.Column('worker_feedback', sa.Text(), nullable=True),
        sa.Column('company_action_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('company_actions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('action_completed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['chart_id'], ['health_exam_charts.id'], ),
        sa.ForeignKeyConstraint(['health_exam_id'], ['health_exams.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_exam_statistics table
    op.create_table(
        'health_exam_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('total_targets', sa.Integer(), server_default='0', nullable=True),
        sa.Column('completed_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('completion_rate', sa.Float(), server_default='0.0', nullable=True),
        sa.Column('general_exam_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('special_exam_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('night_work_exam_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('result_a_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('result_b_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('result_c_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('result_d_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('result_r_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('abnormal_findings_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('followup_required_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('work_restriction_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('disease_statistics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('average_cost_per_person', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_exam_plans_year', 'health_exam_plans', ['plan_year'])
    op.create_index('idx_exam_targets_plan_worker', 'health_exam_targets', ['plan_id', 'worker_id'])
    op.create_index('idx_exam_targets_completed', 'health_exam_targets', ['is_completed'])
    op.create_index('idx_exam_schedules_date', 'health_exam_schedules', ['schedule_date'])
    op.create_index('idx_exam_reservations_worker', 'health_exam_reservations', ['worker_id'])
    op.create_index('idx_exam_reservations_schedule', 'health_exam_reservations', ['schedule_id'])
    op.create_index('idx_exam_charts_worker', 'health_exam_charts', ['worker_id'])
    op.create_index('idx_exam_results_worker', 'health_exam_results', ['worker_id'])
    op.create_index('idx_exam_results_followup', 'health_exam_results', ['followup_required'])
    op.create_index('idx_exam_stats_year_month', 'health_exam_statistics', ['year', 'month'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_exam_stats_year_month', 'health_exam_statistics')
    op.drop_index('idx_exam_results_followup', 'health_exam_results')
    op.drop_index('idx_exam_results_worker', 'health_exam_results')
    op.drop_index('idx_exam_charts_worker', 'health_exam_charts')
    op.drop_index('idx_exam_reservations_schedule', 'health_exam_reservations')
    op.drop_index('idx_exam_reservations_worker', 'health_exam_reservations')
    op.drop_index('idx_exam_schedules_date', 'health_exam_schedules')
    op.drop_index('idx_exam_targets_completed', 'health_exam_targets')
    op.drop_index('idx_exam_targets_plan_worker', 'health_exam_targets')
    op.drop_index('idx_exam_plans_year', 'health_exam_plans')
    
    # Drop tables
    op.drop_table('health_exam_statistics')
    op.drop_table('health_exam_results')
    op.drop_table('health_exam_charts')
    op.drop_table('health_exam_reservations')
    op.drop_table('health_exam_schedules')
    op.drop_table('health_exam_targets')
    op.drop_table('health_exam_plans')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS examplanstatus')
    op.execute('DROP TYPE IF EXISTS examcategory')
    op.execute('DROP TYPE IF EXISTS resultdeliverymethod')