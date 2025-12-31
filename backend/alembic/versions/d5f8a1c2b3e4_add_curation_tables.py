"""Add curation_decisions and curation_rules tables

Revision ID: d5f8a1c2b3e4
Revises: c4d78e9f1a2b
Create Date: 2025-12-31

Curation Learning System P0:
- curation_decisions: 큐레이션 결정 기록 (학습용)
- curation_rules: 학습된 큐레이션 규칙
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'd5f8a1c2b3e4'
down_revision = 'c4d78e9f1a2b'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enums
    op.execute("CREATE TYPE curationdecisiontype AS ENUM ('normal', 'campaign', 'rejected')")
    op.execute("CREATE TYPE curationruletype AS ENUM ('auto_normal', 'auto_campaign', 'auto_reject', 'recommend')")
    
    curation_decision_type = postgresql.ENUM('normal', 'campaign', 'rejected', name='curationdecisiontype', create_type=False)
    curation_rule_type = postgresql.ENUM('auto_normal', 'auto_campaign', 'auto_reject', 'recommend', name='curationruletype', create_type=False)
    
    # curation_rules table (created first due to FK dependency)
    op.create_table(
        'curation_rules',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('rule_name', sa.String(200), nullable=False),
        sa.Column('rule_type', curation_rule_type, nullable=False, index=True),
        sa.Column('conditions', postgresql.JSONB(), nullable=False),
        sa.Column('source', sa.String(50), nullable=False, server_default='learned'),
        sa.Column('sample_size', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('match_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('follow_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('accuracy', sa.Float(), nullable=True),
        sa.Column('priority', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default='true'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=True),
    )
    
    # curation_decisions table
    op.create_table(
        'curation_decisions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('outlier_item_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('outlier_items.id'), nullable=False, index=True),
        sa.Column('remix_node_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('remix_nodes.id'), nullable=True),
        sa.Column('curator_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False, index=True),
        sa.Column('decision_type', curation_decision_type, nullable=False, index=True),
        sa.Column('decision_at', sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column('vdg_snapshot', postgresql.JSONB(), nullable=True),
        sa.Column('extracted_features', postgresql.JSONB(), nullable=True),
        sa.Column('curator_notes', sa.Text(), nullable=True),
        sa.Column('matched_rule_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('curation_rules.id'), nullable=True),
        sa.Column('rule_followed', sa.Boolean(), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_curation_decisions_decision_at', 'curation_decisions', ['decision_at'])
    op.create_index('ix_curation_rules_is_active', 'curation_rules', ['is_active'])


def downgrade() -> None:
    op.drop_index('ix_curation_rules_is_active', 'curation_rules')
    op.drop_index('ix_curation_decisions_decision_at', 'curation_decisions')
    
    op.drop_table('curation_decisions')
    op.drop_table('curation_rules')
    
    op.execute("DROP TYPE IF EXISTS curationdecisiontype")
    op.execute("DROP TYPE IF EXISTS curationruletype")
