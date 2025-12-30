"""Add coaching session log tables

Revision ID: c4d78e9f1a2b
Revises: 0034103f8b37
Create Date: 2025-12-31

Proof Playbook v1.0:
- coaching_sessions: 세션 메타데이터
- coaching_interventions: 개입 기록
- coaching_outcomes: 행동 변화 기록
- coaching_upload_outcomes: 업로드 결과
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'c4d78e9f1a2b'
down_revision = '0034103f8b37'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    coaching_assignment = postgresql.ENUM('coached', 'control', name='coachingassignment', create_type=False)
    coaching_mode = postgresql.ENUM('homage', 'mutation', 'campaign', name='coachingmode', create_type=False)
    evidence_type = postgresql.ENUM('frame', 'audio', 'text', name='evidencetype', create_type=False)
    compliance_result = postgresql.ENUM('complied', 'violated', 'unknown', name='complianceresult', create_type=False)
    
    # Create enum types
    op.execute("CREATE TYPE coachingassignment AS ENUM ('coached', 'control')")
    op.execute("CREATE TYPE coachingmode AS ENUM ('homage', 'mutation', 'campaign')")
    op.execute("CREATE TYPE evidencetype AS ENUM ('frame', 'audio', 'text')")
    op.execute("CREATE TYPE complianceresult AS ENUM ('complied', 'violated', 'unknown')")
    
    # coaching_sessions table
    op.create_table(
        'coaching_sessions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), unique=True, index=True, nullable=False),
        sa.Column('user_id_hash', sa.String(64), index=True, nullable=False),
        sa.Column('mode', coaching_mode, nullable=False, server_default='homage'),
        sa.Column('pattern_id', sa.String(100), index=True, nullable=False),
        sa.Column('pack_id', sa.String(100), index=True, nullable=False),
        sa.Column('pack_hash', sa.String(64), nullable=True),
        sa.Column('assignment', coaching_assignment, nullable=False, server_default='coached'),
        sa.Column('holdout_group', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('started_at', sa.DateTime(), nullable=False),
        sa.Column('ended_at', sa.DateTime(), nullable=True),
        sa.Column('duration_sec', sa.Float(), nullable=True),
        sa.Column('device_type', sa.String(50), nullable=True),
        sa.Column('intervention_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('compliance_rate', sa.Float(), nullable=True),
        sa.Column('unknown_rate', sa.Float(), nullable=True),
    )
    
    # coaching_interventions table
    op.create_table(
        'coaching_interventions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('coaching_sessions.session_id'), index=True, nullable=False),
        sa.Column('t_sec', sa.Float(), nullable=False),
        sa.Column('rule_id', sa.String(100), index=True, nullable=False),
        sa.Column('ap_id', sa.String(100), nullable=True),
        sa.Column('evidence_id', sa.String(100), nullable=False),
        sa.Column('evidence_type', evidence_type, nullable=False, server_default='frame'),
        sa.Column('coach_line_id', sa.String(50), nullable=False),
        sa.Column('coach_line_text', sa.Text(), nullable=True),
        sa.Column('metric_value', sa.Float(), nullable=True),
        sa.Column('metric_threshold', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # coaching_outcomes table
    op.create_table(
        'coaching_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('coaching_sessions.session_id'), index=True, nullable=False),
        sa.Column('t_sec', sa.Float(), nullable=False),
        sa.Column('rule_id', sa.String(100), index=True, nullable=False),
        sa.Column('compliance', compliance_result, nullable=False, server_default='unknown'),
        sa.Column('compliance_unknown_reason', sa.String(50), nullable=True),
        sa.Column('metric_value_after', sa.Float(), nullable=True),
        sa.Column('metric_delta', sa.Float(), nullable=True),
        sa.Column('latency_sec', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
    )
    
    # coaching_upload_outcomes table
    op.create_table(
        'coaching_upload_outcomes',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('session_id', sa.String(100), sa.ForeignKey('coaching_sessions.session_id'), unique=True, index=True, nullable=False),
        sa.Column('uploaded', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('upload_platform', sa.String(50), nullable=True),
        sa.Column('early_views_bucket', sa.String(20), nullable=True),
        sa.Column('early_likes_bucket', sa.String(20), nullable=True),
        sa.Column('self_rating', sa.Integer(), nullable=True),
        sa.Column('self_rating_reason', sa.Text(), nullable=True),
        sa.Column('recorded_at', sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table('coaching_upload_outcomes')
    op.drop_table('coaching_outcomes')
    op.drop_table('coaching_interventions')
    op.drop_table('coaching_sessions')
    
    op.execute("DROP TYPE IF EXISTS complianceresult")
    op.execute("DROP TYPE IF EXISTS evidencetype")
    op.execute("DROP TYPE IF EXISTS coachingmode")
    op.execute("DROP TYPE IF EXISTS coachingassignment")
