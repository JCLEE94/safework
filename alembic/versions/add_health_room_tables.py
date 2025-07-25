"""Add health room tables

Revision ID: add_health_room_001
Revises: 
Create Date: 2025-01-26 07:55:00

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_health_room_001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create medication_records table
    op.create_table('medication_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('medication_name', sa.String(length=200), nullable=False),
        sa.Column('dosage', sa.String(length=100), nullable=False),
        sa.Column('quantity', sa.Integer(), nullable=False),
        sa.Column('purpose', sa.String(length=500), nullable=True),
        sa.Column('symptoms', sa.Text(), nullable=True),
        sa.Column('administered_at', sa.DateTime(), nullable=False),
        sa.Column('administered_by', sa.String(length=100), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_medication_records_id'), 'medication_records', ['id'], unique=False)

    # Create vital_sign_records table
    op.create_table('vital_sign_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('systolic_bp', sa.Integer(), nullable=True),
        sa.Column('diastolic_bp', sa.Integer(), nullable=True),
        sa.Column('blood_sugar', sa.Integer(), nullable=True),
        sa.Column('blood_sugar_type', sa.String(length=20), nullable=True),
        sa.Column('heart_rate', sa.Integer(), nullable=True),
        sa.Column('body_temperature', sa.Float(), nullable=True),
        sa.Column('oxygen_saturation', sa.Integer(), nullable=True),
        sa.Column('measured_at', sa.DateTime(), nullable=False),
        sa.Column('measured_by', sa.String(length=100), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_vital_sign_records_id'), 'vital_sign_records', ['id'], unique=False)

    # Create inbody_records table
    op.create_table('inbody_records',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('height', sa.Float(), nullable=False),
        sa.Column('weight', sa.Float(), nullable=False),
        sa.Column('bmi', sa.Float(), nullable=False),
        sa.Column('body_fat_mass', sa.Float(), nullable=True),
        sa.Column('body_fat_percentage', sa.Float(), nullable=True),
        sa.Column('muscle_mass', sa.Float(), nullable=True),
        sa.Column('lean_body_mass', sa.Float(), nullable=True),
        sa.Column('total_body_water', sa.Float(), nullable=True),
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
        sa.Column('visceral_fat_level', sa.Integer(), nullable=True),
        sa.Column('basal_metabolic_rate', sa.Integer(), nullable=True),
        sa.Column('body_age', sa.Integer(), nullable=True),
        sa.Column('measured_at', sa.DateTime(), nullable=False),
        sa.Column('device_model', sa.String(length=100), nullable=True),
        sa.Column('evaluation', sa.Text(), nullable=True),
        sa.Column('recommendations', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_inbody_records_id'), 'inbody_records', ['id'], unique=False)

    # Create health_room_visits table
    op.create_table('health_room_visits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('worker_id', sa.Integer(), nullable=False),
        sa.Column('visit_date', sa.DateTime(), nullable=False),
        sa.Column('visit_reason', sa.String(length=500), nullable=False),
        sa.Column('chief_complaint', sa.Text(), nullable=True),
        sa.Column('treatment_provided', sa.Text(), nullable=True),
        sa.Column('medication_given', sa.Boolean(), nullable=True),
        sa.Column('measurement_taken', sa.Boolean(), nullable=True),
        sa.Column('follow_up_required', sa.Boolean(), nullable=True),
        sa.Column('referral_required', sa.Boolean(), nullable=True),
        sa.Column('referral_location', sa.String(length=200), nullable=True),
        sa.Column('status', sa.String(length=50), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_health_room_visits_id'), 'health_room_visits', ['id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_health_room_visits_id'), table_name='health_room_visits')
    op.drop_table('health_room_visits')
    op.drop_index(op.f('ix_inbody_records_id'), table_name='inbody_records')
    op.drop_table('inbody_records')
    op.drop_index(op.f('ix_vital_sign_records_id'), table_name='vital_sign_records')
    op.drop_table('vital_sign_records')
    op.drop_index(op.f('ix_medication_records_id'), table_name='medication_records')
    op.drop_table('medication_records')