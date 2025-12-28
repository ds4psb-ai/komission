"""
P0-6: Add Pattern Recurrence Links and Cluster Lineage

Temporal Recurrence / Pattern Lineage (v1)
- NEW: pattern_recurrence_links table for tracking pattern recurrence relationships
- MODIFY: pattern_clusters table with lineage fields

Revision ID: 2249e3214282
Revises: 1640492a1506
Create Date: 2025-12-28
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '2249e3214282'
down_revision = '1640492a1506'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ### 1. Add lineage fields to pattern_clusters ###
    op.add_column('pattern_clusters', sa.Column('ancestor_cluster_id', sa.String(100), nullable=True))
    op.add_column('pattern_clusters', sa.Column('recurrence_score', sa.Float(), nullable=True))
    op.add_column('pattern_clusters', sa.Column('recurrence_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('pattern_clusters', sa.Column('origin_cluster_id', sa.String(100), nullable=True))
    op.add_column('pattern_clusters', sa.Column('last_recurrence_at', sa.DateTime(), nullable=True))
    
    # Index for ancestor_cluster_id
    op.create_index('ix_pattern_clusters_ancestor_cluster_id', 'pattern_clusters', ['ancestor_cluster_id'])
    
    # ### 2. Create RecurrenceLinkStatus enum ###
    recurrence_link_status_enum = postgresql.ENUM('candidate', 'confirmed', 'rejected', name='recurrencelinkstatus', create_type=False)
    recurrence_link_status_enum.create(op.get_bind(), checkfirst=True)
    
    # ### 3. Create pattern_recurrence_links table ###
    op.create_table(
        'pattern_recurrence_links',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        
        # Cluster relationships (no index=True here, explicit indexes below)
        sa.Column('cluster_id_current', sa.String(100), nullable=False),
        sa.Column('cluster_id_ancestor', sa.String(100), nullable=False),
        
        # Status
        sa.Column('status', sa.Enum('candidate', 'confirmed', 'rejected', name='recurrencelinkstatus'), 
                  nullable=False, server_default='candidate'),
        
        # Recurrence Score and features (v1 formula)
        sa.Column('recurrence_score', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('microbeat_sim', sa.Float(), nullable=True),
        sa.Column('hook_genome_sim', sa.Float(), nullable=True),
        sa.Column('focus_window_sim', sa.Float(), nullable=True),
        sa.Column('audio_format_sim', sa.Float(), nullable=True),
        sa.Column('comment_signature_sim', sa.Float(), nullable=True),
        sa.Column('product_slot_sim', sa.Float(), nullable=True),
        
        # Evidence
        sa.Column('evidence_count', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('trigger_run_id', postgresql.UUID(as_uuid=True), 
                  sa.ForeignKey('runs.id'), nullable=True),
        sa.Column('feature_snapshot', postgresql.JSONB(), nullable=True),
        
        # Promotion info
        sa.Column('promotion_reason', sa.String(255), nullable=True),
        
        # Timestamps
        sa.Column('first_seen_at', sa.DateTime(), nullable=False),
        sa.Column('last_seen_at', sa.DateTime(), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
    )
    
    # ### 4. Create indexes for common queries ###
    op.create_index('ix_pattern_recurrence_links_cluster_current', 'pattern_recurrence_links', ['cluster_id_current'])
    op.create_index('ix_pattern_recurrence_links_cluster_ancestor', 'pattern_recurrence_links', ['cluster_id_ancestor'])
    op.create_index('ix_pattern_recurrence_links_status', 'pattern_recurrence_links', ['status'])
    op.create_index('ix_pattern_recurrence_links_score', 'pattern_recurrence_links', ['recurrence_score'])
    
    # ### 5. Unique constraint to prevent duplicate cluster pairs ###
    op.create_unique_constraint(
        'uq_pattern_recurrence_links_cluster_pair',
        'pattern_recurrence_links',
        ['cluster_id_current', 'cluster_id_ancestor']
    )


def downgrade() -> None:
    # Drop unique constraint first
    op.drop_constraint('uq_pattern_recurrence_links_cluster_pair', 'pattern_recurrence_links', type_='unique')
    
    # Drop indexes
    op.drop_index('ix_pattern_recurrence_links_score', 'pattern_recurrence_links')
    op.drop_index('ix_pattern_recurrence_links_status', 'pattern_recurrence_links')
    op.drop_index('ix_pattern_recurrence_links_cluster_ancestor', 'pattern_recurrence_links')
    op.drop_index('ix_pattern_recurrence_links_cluster_current', 'pattern_recurrence_links')
    op.drop_table('pattern_recurrence_links')
    
    # Drop enum
    op.execute("DROP TYPE IF EXISTS recurrencelinkstatus")
    
    # Remove lineage fields from pattern_clusters
    op.drop_index('ix_pattern_clusters_ancestor_cluster_id', 'pattern_clusters')
    op.drop_column('pattern_clusters', 'last_recurrence_at')
    op.drop_column('pattern_clusters', 'origin_cluster_id')
    op.drop_column('pattern_clusters', 'recurrence_count')
    op.drop_column('pattern_clusters', 'recurrence_score')
    op.drop_column('pattern_clusters', 'ancestor_cluster_id')
