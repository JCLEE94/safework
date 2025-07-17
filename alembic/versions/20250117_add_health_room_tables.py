"""Add health room management tables

Revision ID: add_health_room_tables_20250117
Revises: add_new_features_20250704
Create Date: 2025-01-17

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = 'add_health_room_tables_20250117'
down_revision = 'add_new_features_20250704'
branch_labels = None
depends_on = None


def upgrade():
    # Create medications table
    op.create_table(
        'medications',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('type', sa.Enum('진통제', '감기약', '소화제', '항생제', '응급처치약품', '처방약', '기타', 
                                 name='medicationtype'), nullable=False),
        sa.Column('manufacturer', sa.String(length=100), nullable=True),
        sa.Column('unit', sa.String(length=20), nullable=True),
        sa.Column('current_stock', sa.Integer(), server_default='0', nullable=True),
        sa.Column('minimum_stock', sa.Integer(), server_default='10', nullable=True),
        sa.Column('maximum_stock', sa.Integer(), server_default='100', nullable=True),
        sa.Column('expiration_date', sa.Date(), nullable=True),
        sa.Column('lot_number', sa.String(length=50), nullable=True),
        sa.Column('storage_location', sa.String(length=100), nullable=True),
        sa.Column('storage_conditions', sa.String(length=200), nullable=True),
        sa.Column('dosage_instructions', sa.Text(), nullable=True),
        sa.Column('precautions', sa.Text(), nullable=True),
        sa.Column('is_active', sa.Boolean(), server_default='true', nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create medication_dispensing table
    op.create_table(
        'medication_dispensing',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('symptoms', sa.Text(), nullable=True),
        sa.Column('dispensed_by', sa.String(length=50), nullable=True),
        sa.Column('dispensed_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create medication_inventory table
    op.create_table(
        'medication_inventory',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('medication_id', sa.Integer(), nullable=False),
        sa.Column('transaction_type', sa.String(length=20), nullable=True),
        sa.Column('quantity_change', sa.Integer(), nullable=True),
        sa.Column('quantity_after', sa.Integer(), nullable=True),
        sa.Column('reason', sa.Text(), nullable=True),
        sa.Column('reference_number', sa.String(length=50), nullable=True),
        sa.Column('created_by', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['medication_id'], ['medications.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_measurements table
    op.create_table(
        'health_measurements',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('measurement_type', sa.Enum('혈압', '혈당', '체온', '산소포화도', '체성분', '신장체중', '시력', '청력',
                                            name='measurementtype'), nullable=False),
        sa.Column('measured_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('measured_by', sa.String(length=50), nullable=True),
        sa.Column('values', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('is_normal', sa.Boolean(), nullable=True),
        sa.Column('abnormal_findings', sa.Text(), nullable=True),
        sa.Column('action_taken', sa.Text(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('follow_up_date', sa.Date(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create body_composition_analysis table
    op.create_table(
        'body_composition_analysis',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('measurement_id', sa.Integer(), nullable=True),
        sa.Column('measured_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('device_model', sa.String(length=50), nullable=True),
        sa.Column('height', sa.Float(), nullable=True),
        sa.Column('weight', sa.Float(), nullable=True),
        sa.Column('bmi', sa.Float(), nullable=True),
        sa.Column('muscle_mass', sa.Float(), nullable=True),
        sa.Column('body_fat_mass', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('visceral_fat_level', sa.Integer(), nullable=True),
        sa.Column('total_body_water', sa.Float(), nullable=True),
        sa.Column('protein_mass', sa.Float(), nullable=True),
        sa.Column('mineral_mass', sa.Float(), nullable=True),
        sa.Column('right_arm_muscle', sa.Float(), nullable=True),
        sa.Column('left_arm_muscle', sa.Float(), nullable=True),
        sa.Column('trunk_muscle', sa.Float(), nullable=True),
        sa.Column('right_leg_muscle', sa.Float(), nullable=True),
        sa.Column('left_leg_muscle', sa.Float(), nullable=True),
        sa.Column('right_arm_fat', sa.Float(), nullable=True),
        sa.Column('left_arm_fat', sa.Float(), nullable=True),
        sa.Column('trunk_fat', sa.Float(), nullable=True),
        sa.Column('right_leg_fat', sa.Float(), nullable=True),
        sa.Column('left_leg_fat', sa.Float(), nullable=True),
        sa.Column('basal_metabolic_rate', sa.Float(), nullable=True),
        sa.Column('waist_hip_ratio', sa.Float(), nullable=True),
        sa.Column('fitness_score', sa.Float(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['measurement_id'], ['health_measurements.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create health_room_visits table
    op.create_table(
        'health_room_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('visit_datetime', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('treatment_provided', sa.Text(), nullable=True),
        sa.Column('medications_given', sa.Text(), nullable=True),
        sa.Column('measurements_taken', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('measurement_ids', postgresql.JSON(astext_type=sa.Text()), nullable=True),
        sa.Column('rest_taken', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('rest_duration_minutes', sa.Integer(), nullable=True),
        sa.Column('referred_to_hospital', sa.Boolean(), server_default='false', nullable=True),
        sa.Column('hospital_name', sa.String(length=100), nullable=True),
        sa.Column('work_related', sa.Boolean(), nullable=True),
        sa.Column('accident_report_id', sa.Integer(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('treated_by', sa.String(length=50), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=True),
        sa.ForeignKeyConstraint(['accident_report_id'], ['accident_reports.id'], ),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('idx_medications_active', 'medications', ['is_active'])
    op.create_index('idx_medications_expiry', 'medications', ['expiration_date'])
    op.create_index('idx_dispensing_worker', 'medication_dispensing', ['worker_id'])
    op.create_index('idx_dispensing_medication', 'medication_dispensing', ['medication_id'])
    op.create_index('idx_measurements_worker', 'health_measurements', ['worker_id'])
    op.create_index('idx_measurements_type', 'health_measurements', ['measurement_type'])
    op.create_index('idx_body_comp_worker', 'body_composition_analysis', ['worker_id'])
    op.create_index('idx_visits_worker', 'health_room_visits', ['worker_id'])
    op.create_index('idx_visits_date', 'health_room_visits', ['visit_datetime'])


def downgrade():
    # Drop indexes
    op.drop_index('idx_visits_date', 'health_room_visits')
    op.drop_index('idx_visits_worker', 'health_room_visits')
    op.drop_index('idx_body_comp_worker', 'body_composition_analysis')
    op.drop_index('idx_measurements_type', 'health_measurements')
    op.drop_index('idx_measurements_worker', 'health_measurements')
    op.drop_index('idx_dispensing_medication', 'medication_dispensing')
    op.drop_index('idx_dispensing_worker', 'medication_dispensing')
    op.drop_index('idx_medications_expiry', 'medications')
    op.drop_index('idx_medications_active', 'medications')
    
    # Drop tables
    op.drop_table('health_room_visits')
    op.drop_table('body_composition_analysis')
    op.drop_table('health_measurements')
    op.drop_table('medication_inventory')
    op.drop_table('medication_dispensing')
    op.drop_table('medications')
    
    # Drop enums
    op.execute('DROP TYPE IF EXISTS medicationtype')
    op.execute('DROP TYPE IF EXISTS measurementtype')