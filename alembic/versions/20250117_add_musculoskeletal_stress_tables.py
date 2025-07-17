"""Add musculoskeletal and job stress assessment tables

Revision ID: add_musculoskeletal_20250117
Revises: add_at_risk_employee_20250117
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_musculoskeletal_20250117'
down_revision = 'add_at_risk_employee_20250117'
branch_labels = None
depends_on = None


def upgrade():
    # Create enums
    op.execute("CREATE TYPE bodypart AS ENUM ('목', '어깨(좌)', '어깨(우)', '팔꿈치(좌)', '팔꿈치(우)', '손목(좌)', '손목(우)', '손(좌)', '손(우)', '등(상부)', '허리', '엉덩이', '무릎(좌)', '무릎(우)', '발목(좌)', '발목(우)', '발(좌)', '발(우)')")
    op.execute("CREATE TYPE painlevel AS ENUM ('없음', '약함', '보통', '심함', '매우심함')")
    op.execute("CREATE TYPE assessmenttype AS ENUM ('최초평가', '정기평가', '추적평가', '특별평가')")
    
    # Create musculoskeletal_assessments table
    op.create_table(
        'musculoskeletal_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('assessment_type', sa.Enum('최초평가', '정기평가', '추적평가', '특별평가', name='assessmenttype'), nullable=False),
        sa.Column('assessor_name', sa.String(length=100), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('job_title', sa.String(length=100), nullable=True),
        sa.Column('work_years', sa.Float(), nullable=True),
        sa.Column('work_hours_per_day', sa.Float(), nullable=True),
        sa.Column('symptoms_data', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_pain_score', sa.Float(), nullable=True),
        sa.Column('most_painful_parts', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('pain_affecting_work', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('pain_affecting_daily_life', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('work_characteristics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_factors_identified', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('ergonomic_risk_score', sa.Float(), nullable=True),
        sa.Column('risk_level', sa.Enum('낮음', '중간', '높음', '매우높음', name='risklevel'), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('work_improvement_needed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('medical_referral_needed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_date', sa.Date(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create ergonomic_evaluations table
    op.create_table(
        'ergonomic_evaluations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('musculoskeletal_assessment_id', sa.Integer(), nullable=True),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('evaluation_date', sa.Date(), nullable=False),
        sa.Column('evaluator_name', sa.String(length=100), nullable=True),
        sa.Column('evaluation_method', sa.String(length=100), nullable=True),
        sa.Column('task_name', sa.String(length=200), nullable=True),
        sa.Column('task_description', sa.Text(), nullable=True),
        sa.Column('task_frequency', sa.String(length=100), nullable=True),
        sa.Column('task_duration', sa.String(length=100), nullable=True),
        sa.Column('posture_analysis', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('load_assessment', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('evaluation_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('overall_risk_level', sa.Enum('낮음', '중간', '높음', '매우높음', name='risklevel'), nullable=True),
        sa.Column('immediate_action_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('improvement_suggestions', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('photo_paths', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('video_path', sa.String(length=500), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['musculoskeletal_assessment_id'], ['musculoskeletal_assessments.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create job_stress_assessments table
    op.create_table(
        'job_stress_assessments',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('assessment_date', sa.Date(), nullable=False),
        sa.Column('assessment_type', sa.Enum('최초평가', '정기평가', '추적평가', '특별평가', name='assessmenttype'), nullable=False),
        sa.Column('assessment_tool', sa.String(length=100), nullable=True),
        sa.Column('age_group', sa.String(length=50), nullable=True),
        sa.Column('gender', sa.String(length=10), nullable=True),
        sa.Column('marital_status', sa.String(length=50), nullable=True),
        sa.Column('education_level', sa.String(length=50), nullable=True),
        sa.Column('job_demand_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('job_demand_total', sa.Float(), nullable=True),
        sa.Column('job_control_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('job_control_total', sa.Float(), nullable=True),
        sa.Column('interpersonal_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('interpersonal_total', sa.Float(), nullable=True),
        sa.Column('job_insecurity_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('job_insecurity_total', sa.Float(), nullable=True),
        sa.Column('organizational_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('organizational_total', sa.Float(), nullable=True),
        sa.Column('reward_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('reward_total', sa.Float(), nullable=True),
        sa.Column('workplace_culture_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('workplace_culture_total', sa.Float(), nullable=True),
        sa.Column('total_score', sa.Float(), nullable=True),
        sa.Column('stress_level', sa.Enum('낮음', '중간', '높음', '매우높음', name='risklevel'), nullable=True),
        sa.Column('high_risk_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('burnout_score', sa.Float(), nullable=True),
        sa.Column('depression_screening', sa.String(length=50), nullable=True),
        sa.Column('anxiety_screening', sa.String(length=50), nullable=True),
        sa.Column('coping_resources', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('counseling_needed', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('stress_management_program', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('work_environment_improvement', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('followup_date', sa.Date(), nullable=True),
        sa.Column('referral_made', sa.String(length=200), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create stress_interventions table
    op.create_table(
        'stress_interventions',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('job_stress_assessment_id', sa.Integer(), nullable=True),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('program_name', sa.String(length=200), nullable=False),
        sa.Column('program_type', sa.String(length=100), nullable=True),
        sa.Column('start_date', sa.Date(), nullable=False),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column('total_sessions_planned', sa.Integer(), nullable=True),
        sa.Column('sessions_completed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('attendance_rate', sa.Float(), nullable=True),
        sa.Column('intervention_goals', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('intervention_methods', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('session_records', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('pre_intervention_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('post_intervention_scores', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_areas', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('participant_satisfaction', sa.Float(), nullable=True),
        sa.Column('participant_feedback', sa.Text(), nullable=True),
        sa.Column('outcome_achieved', sa.Boolean(), nullable=True),
        sa.Column('outcome_summary', sa.Text(), nullable=True),
        sa.Column('provider_name', sa.String(length=100), nullable=True),
        sa.Column('provider_qualification', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['job_stress_assessment_id'], ['job_stress_assessments.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create musculoskeletal_statistics table
    op.create_table(
        'musculoskeletal_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('total_assessments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('workers_assessed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('symptom_prevalence', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('risk_distribution', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('by_work_characteristics', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('intervention_effectiveness', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('improvement_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create job_stress_statistics table
    op.create_table(
        'job_stress_statistics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('year', sa.Integer(), nullable=False),
        sa.Column('month', sa.Integer(), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('total_assessments', sa.Integer(), server_default='0', nullable=True),
        sa.Column('workers_assessed', sa.Integer(), server_default='0', nullable=True),
        sa.Column('stress_level_distribution', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('factor_averages', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('high_risk_count', sa.Integer(), server_default='0', nullable=True),
        sa.Column('high_risk_factors', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('intervention_participation', sa.Integer(), server_default='0', nullable=True),
        sa.Column('intervention_completion_rate', sa.Float(), nullable=True),
        sa.Column('stress_reduction_rate', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes
    op.create_index('idx_musculo_worker', 'musculoskeletal_assessments', ['worker_id'])
    op.create_index('idx_musculo_date', 'musculoskeletal_assessments', ['assessment_date'])
    op.create_index('idx_musculo_risk', 'musculoskeletal_assessments', ['risk_level'])
    op.create_index('idx_musculo_followup', 'musculoskeletal_assessments', ['followup_required', 'followup_date'])
    
    op.create_index('idx_ergo_worker', 'ergonomic_evaluations', ['worker_id'])
    op.create_index('idx_ergo_assessment', 'ergonomic_evaluations', ['musculoskeletal_assessment_id'])
    op.create_index('idx_ergo_risk', 'ergonomic_evaluations', ['overall_risk_level'])
    op.create_index('idx_ergo_immediate', 'ergonomic_evaluations', ['immediate_action_required'])
    
    op.create_index('idx_stress_worker', 'job_stress_assessments', ['worker_id'])
    op.create_index('idx_stress_date', 'job_stress_assessments', ['assessment_date'])
    op.create_index('idx_stress_level', 'job_stress_assessments', ['stress_level'])
    op.create_index('idx_stress_followup', 'job_stress_assessments', ['followup_required', 'followup_date'])
    
    op.create_index('idx_intervention_worker', 'stress_interventions', ['worker_id'])
    op.create_index('idx_intervention_assessment', 'stress_interventions', ['job_stress_assessment_id'])
    op.create_index('idx_intervention_active', 'stress_interventions', ['end_date'])
    
    op.create_index('idx_musculo_stats_year_month', 'musculoskeletal_statistics', ['year', 'month'])
    op.create_index('idx_stress_stats_year_month', 'job_stress_statistics', ['year', 'month'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_stress_stats_year_month', 'job_stress_statistics')
    op.drop_index('idx_musculo_stats_year_month', 'musculoskeletal_statistics')
    op.drop_index('idx_intervention_active', 'stress_interventions')
    op.drop_index('idx_intervention_assessment', 'stress_interventions')
    op.drop_index('idx_intervention_worker', 'stress_interventions')
    op.drop_index('idx_stress_followup', 'job_stress_assessments')
    op.drop_index('idx_stress_level', 'job_stress_assessments')
    op.drop_index('idx_stress_date', 'job_stress_assessments')
    op.drop_index('idx_stress_worker', 'job_stress_assessments')
    op.drop_index('idx_ergo_immediate', 'ergonomic_evaluations')
    op.drop_index('idx_ergo_risk', 'ergonomic_evaluations')
    op.drop_index('idx_ergo_assessment', 'ergonomic_evaluations')
    op.drop_index('idx_ergo_worker', 'ergonomic_evaluations')
    op.drop_index('idx_musculo_followup', 'musculoskeletal_assessments')
    op.drop_index('idx_musculo_risk', 'musculoskeletal_assessments')
    op.drop_index('idx_musculo_date', 'musculoskeletal_assessments')
    op.drop_index('idx_musculo_worker', 'musculoskeletal_assessments')
    
    # Drop tables
    op.drop_table('job_stress_statistics')
    op.drop_table('musculoskeletal_statistics')
    op.drop_table('stress_interventions')
    op.drop_table('job_stress_assessments')
    op.drop_table('ergonomic_evaluations')
    op.drop_table('musculoskeletal_assessments')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS bodypart')
    op.execute('DROP TYPE IF EXISTS painlevel')
    op.execute('DROP TYPE IF EXISTS assessmenttype')