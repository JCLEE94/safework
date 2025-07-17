"""add QR registration tables

Revision ID: 20250717_001
Revises: 20250704_001
Create Date: 2025-07-17 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '20250717_001'
down_revision = '20250704_001'
branch_labels = None
depends_on = None


def upgrade():
    # Create QR registration status enum
    op.execute("CREATE TYPE registrationstatus AS ENUM ('pending', 'completed', 'expired', 'failed', 'cancelled')")
    
    # Create qr_registration_tokens table
    op.create_table(
        'qr_registration_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='고유 ID'),
        sa.Column('token', sa.String(255), nullable=False, unique=True, index=True, comment='등록 토큰'),
        sa.Column('qr_code_data', sa.Text(), nullable=False, comment='QR 코드 데이터 (Base64)'),
        sa.Column('worker_data', sa.Text(), nullable=False, comment='근로자 데이터 (JSON)'),
        sa.Column('department', sa.String(100), nullable=False, comment='부서'),
        sa.Column('position', sa.String(100), nullable=True, comment='직책'),
        sa.Column('status', postgresql.ENUM('pending', 'completed', 'expired', 'failed', 'cancelled', name='registrationstatus'), nullable=False, server_default='pending', comment='등록 상태'),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False, comment='만료 시간'),
        sa.Column('worker_id', sa.Integer(), nullable=True, comment='생성된 근로자 ID'),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True, comment='완료 시간'),
        sa.Column('error_message', sa.Text(), nullable=True, comment='오류 메시지'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 시간'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='수정 시간'),
        sa.Column('created_by', sa.String(100), nullable=False, comment='생성자'),
        sa.ForeignKeyConstraint(['worker_id'], ['workers.id'], ondelete='SET NULL'),
    )
    
    # Create indexes
    op.create_index('ix_qr_registration_tokens_token', 'qr_registration_tokens', ['token'], unique=True)
    op.create_index('ix_qr_registration_tokens_status', 'qr_registration_tokens', ['status'])
    op.create_index('ix_qr_registration_tokens_expires_at', 'qr_registration_tokens', ['expires_at'])
    op.create_index('ix_qr_registration_tokens_created_at', 'qr_registration_tokens', ['created_at'])
    
    # Create qr_registration_logs table
    op.create_table(
        'qr_registration_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()'), comment='고유 ID'),
        sa.Column('token_id', postgresql.UUID(as_uuid=True), nullable=False, comment='토큰 ID'),
        sa.Column('action', sa.String(50), nullable=False, comment='액션'),
        sa.Column('status', sa.String(20), nullable=False, comment='상태'),
        sa.Column('message', sa.Text(), nullable=True, comment='메시지'),
        sa.Column('metadata', postgresql.JSON(astext_type=sa.Text()), nullable=True, comment='메타데이터'),
        sa.Column('user_agent', sa.Text(), nullable=True, comment='사용자 에이전트'),
        sa.Column('ip_address', sa.String(45), nullable=True, comment='IP 주소'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False, comment='생성 시간'),
        sa.Column('created_by', sa.String(100), nullable=False, comment='생성자'),
        sa.ForeignKeyConstraint(['token_id'], ['qr_registration_tokens.id'], ondelete='CASCADE'),
    )
    
    # Create indexes for logs
    op.create_index('ix_qr_registration_logs_token_id', 'qr_registration_logs', ['token_id'])
    op.create_index('ix_qr_registration_logs_action', 'qr_registration_logs', ['action'])
    op.create_index('ix_qr_registration_logs_status', 'qr_registration_logs', ['status'])
    op.create_index('ix_qr_registration_logs_created_at', 'qr_registration_logs', ['created_at'])


def downgrade():
    # Drop tables in reverse order
    op.drop_table('qr_registration_logs')
    op.drop_table('qr_registration_tokens')
    
    # Drop enum
    op.execute('DROP TYPE IF EXISTS registrationstatus')