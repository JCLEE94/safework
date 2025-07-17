"""Add at-risk employee management tables

Revision ID: add_at_risk_employee_20250117
Revises: add_health_exam_mgmt_20250117
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_at_risk_employee_20250117'
down_revision = 'add_health_exam_mgmt_20250117'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    op.execute("CREATE TYPE riskcategory AS ENUM ('직업병의심', '일반질병의심', '청력이상', '호흡기이상', '근골격계이상', '심혈관계이상', '정신건강이상', '화학물질노출', '물리적유해인자', '인간공학적위험', '야간작업', '고스트레스')")
    op.execute("CREATE TYPE managementlevel AS ENUM ('관찰', '집중관리', '의료관리', '작업제한')")
    op.execute("CREATE TYPE interventiontype AS ENUM ('보건상담', '의료기관의뢰', '작업환경개선', '개인보호구', '작업전환', '작업제한', '보건교육', '생활습관지도', '스트레스관리', '재활프로그램')")
    
    # Create at_risk_employees table
    op.create_table(
        'at_risk_employees',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('registration_date', sa.Date(), nullable=False),
        sa.Column('registered_by', sa.String(length=100), nullable=True),
        sa.Column('risk_categories', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('primary_risk_category', sa.Enum('직업병의심', '일반질병의심', '청력이상', '호흡기이상', '근골격계이상', 
                                                  '심혈관계이상', '정신건강이상', '화학물질노출', '물리적유해인자', 
                                                  '인간공학적위험', '야간작업', '고스트레스', name='riskcategory'), nullable=False),
        sa.Column('management_level', sa.Enum('관찰', '집중관리', '의료관리', '작업제한', name='managementlevel'), nullable=False),
        sa.Column('detection_source', sa.String(length=100), nullable=True),
        sa.Column('detection_date', sa.Date(), nullable=True),
        sa.Column('related_exam_id', sa.Integer(), nullable=True),
        sa.Column('risk_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('current_status', sa.String(length=50), server_default='active', nullable=True),
        sa.Column('severity_score', sa.Float(), nullable=True),
        sa.Column('work_fitness_status', sa.String(length=100), nullable=True),
        sa.Column('work_restrictions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('management_goals', sa.Text(), nullable=True),
        sa.Column('target_improvement_date', sa.Date(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('resolution_date', sa.Date(), nullable=True),
        sa.Column('resolution_reason', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['related_exam_id'], ['health_exams.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create risk_management_plans table
    op.create_table(
        'risk_management_plans',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('at_risk_employee_id', sa.Integer(), nullable=False),
        sa.Column('plan_name', sa.String(length=200), nullable=False),
        sa.Column('plan_period_start', sa.Date(), nullable=False),
        sa.Column('plan_period_end', sa.Date(), nullable=False),
        sa.Column('primary_goal', sa.Text(), nullable=True),
        sa.Column('specific_objectives', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('planned_interventions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('monitoring_schedule', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('success_criteria', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluation_methods', sa.Text(), nullable=True),
        sa.Column('primary_manager', sa.String(length=100), nullable=True),
        sa.Column('support_team', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('status', sa.String(length=50), server_default='active', nullable=True),
        sa.Column('approved_by', sa.String(length=100), nullable=True),
        sa.Column('approved_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['at_risk_employee_id'], ['at_risk_employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create risk_interventions table
    op.create_table(
        'risk_interventions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('at_risk_employee_id', sa.Integer(), nullable=False),
        sa.Column('management_plan_id', sa.Integer(), nullable=True),
        sa.Column('intervention_type', sa.Enum('보건상담', '의료기관의뢰', '작업환경개선', '개인보호구', '작업전환', 
                                              '작업제한', '보건교육', '생활습관지도', '스트레스관리', '재활프로그램',
                                              name='interventiontype'), nullable=False),
        sa.Column('intervention_date', sa.DateTime(), nullable=False),
        sa.Column('duration_minutes', sa.Integer(), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=True),
        sa.Column('provider_role', sa.String(length=50), nullable=True),
        sa.Column('intervention_content', sa.Text(), nullable=True),
        sa.Column('methods_used', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('materials_provided', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('worker_response', sa.Text(), nullable=True),
        sa.Column('engagement_level', sa.String(length=50), nullable=True),
        sa.Column('immediate_outcome', sa.Text(), nullable=True),
        sa.Column('issues_identified', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('referrals_made', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('followup_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_date', sa.Date(), nullable=True),
        sa.Column('followup_notes', sa.Text(), nullable=True),
        sa.Column('attachments', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['at_risk_employee_id'], ['at_risk_employees.id'], ),
        sa.ForeignKeyConstraint(['management_plan_id'], ['risk_management_plans.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create risk_monitoring table
    op.create_table(
        'risk_monitoring',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('at_risk_employee_id', sa.Integer(), nullable=False),
        sa.Column('monitoring_date', sa.Date(), nullable=False),
        sa.Column('monitoring_type', sa.String(length=100), nullable=True),
        sa.Column('health_indicators', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('work_performance', sa.String(length=50), nullable=True),
        sa.Column('work_incidents', sa.Integer(), server_default='0', nullable=True),
        sa.Column('ppe_compliance', sa.String(length=50), nullable=True),
        sa.Column('reported_symptoms', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('symptom_severity', sa.Float(), nullable=True),
        sa.Column('lifestyle_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_status', sa.String(length=50), nullable=True),
        sa.Column('goal_achievement', sa.Float(), nullable=True),
        sa.Column('actions_taken', sa.Text(), nullable=True),
        sa.Column('plan_adjustments', sa.Text(), nullable=True),
        sa.Column('next_monitoring_date', sa.Date(), nullable=True),
        sa.Column('next_monitoring_focus', sa.Text(), nullable=True),
        sa.Column('monitored_by', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['at_risk_employee_id'], ['at_risk_employees.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create risk_employee_statistics table
    op.create_table(
        'risk_employee_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('total_at_risk', sa.Integer(), server_default='0', nullable=True),
        sa.Column('new_registrations', sa.Integer(), server_default='0', nullable=True),
        sa.Column('resolved_cases', sa.Integer(), server_default='0', nullable=True),
        sa.Column('category_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('management_level_breakdown', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('total_interventions', sa.Integer(), server_default='0', nullable=True),
        sa.Column('intervention_types', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_rate', sa.Float(), nullable=True),
        sa.Column('compliance_rate', sa.Float(), nullable=True),
        sa.Column('total_cost', sa.Float(), nullable=True),
        sa.Column('cost_per_employee', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_at_risk_active', 'at_risk_employees', ['is_active'])
    op.create_index('idx_at_risk_worker', 'at_risk_employees', ['worker_id'])
    op.create_index('idx_at_risk_category', 'at_risk_employees', ['primary_risk_category'])
    op.create_index('idx_at_risk_level', 'at_risk_employees', ['management_level'])
    op.create_index('idx_at_risk_severity', 'at_risk_employees', ['severity_score'])
    op.create_index('idx_risk_plans_employee', 'risk_management_plans', ['at_risk_employee_id'])
    op.create_index('idx_risk_plans_status', 'risk_management_plans', ['status'])
    op.create_index('idx_interventions_employee', 'risk_interventions', ['at_risk_employee_id'])
    op.create_index('idx_interventions_date', 'risk_interventions', ['intervention_date'])
    op.create_index('idx_interventions_type', 'risk_interventions', ['intervention_type'])
    op.create_index('idx_interventions_followup', 'risk_interventions', ['followup_required', 'followup_date'])
    op.create_index('idx_monitoring_employee', 'risk_monitoring', ['at_risk_employee_id'])
    op.create_index('idx_monitoring_date', 'risk_monitoring', ['monitoring_date'])
    op.create_index('idx_risk_stats_year_month', 'risk_employee_statistics', ['year', 'month'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_risk_stats_year_month', 'risk_employee_statistics')
    op.drop_index('idx_monitoring_date', 'risk_monitoring')
    op.drop_index('idx_monitoring_employee', 'risk_monitoring')
    op.drop_index('idx_interventions_followup', 'risk_interventions')
    op.drop_index('idx_interventions_type', 'risk_interventions')
    op.drop_index('idx_interventions_date', 'risk_interventions')
    op.drop_index('idx_interventions_employee', 'risk_interventions')
    op.drop_index('idx_risk_plans_status', 'risk_management_plans')
    op.drop_index('idx_risk_plans_employee', 'risk_management_plans')
    op.drop_index('idx_at_risk_severity', 'at_risk_employees')
    op.drop_index('idx_at_risk_level', 'at_risk_employees')
    op.drop_index('idx_at_risk_category', 'at_risk_employees')
    op.drop_index('idx_at_risk_worker', 'at_risk_employees')
    op.drop_index('idx_at_risk_active', 'at_risk_employees')
    
    # Drop tables
    op.drop_table('risk_employee_statistics')
    op.drop_table('risk_monitoring')
    op.drop_table('risk_interventions')
    op.drop_table('risk_management_plans')
    op.drop_table('at_risk_employees')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS riskcategory')
    op.execute('DROP TYPE IF EXISTS managementlevel')
    op.execute('DROP TYPE IF EXISTS interventiontype')