"""Add content history and usage tracking.

Revision ID: 20260120_add_content_history
Revises: 20260111_add_scraper_fields
Create Date: 2026-01-20
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260120_add_content_history"
down_revision = "20260111_add_scraper_fields"
branch_labels = None
depends_on = None


def upgrade():
    """Add subscription fields to users and create content_history table."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    dialect = conn.dialect.name
    
    # Add user subscription fields if users table exists
    if 'users' in inspector.get_table_names():
        columns = [c['name'] for c in inspector.get_columns('users')]
        
        if 'subscription_tier' not in columns:
            op.add_column('users', sa.Column('subscription_tier', sa.String(20), server_default='free'))
        
        if 'generation_count_month' not in columns:
            op.add_column('users', sa.Column('generation_count_month', sa.Integer(), server_default='0'))
        
        if 'generation_reset_date' not in columns:
            op.add_column('users', sa.Column('generation_reset_date', sa.DateTime()))
    
    # Create content_history table if it doesn't exist
    if 'content_history' not in inspector.get_table_names():
        # Use JSONB for PostgreSQL, JSON for others (like SQLite in tests)
        json_type = JSONB() if dialect == 'postgresql' else sa.JSON()
        
        op.create_table(
            'content_history',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
            sa.Column('profile_id', sa.Integer(), sa.ForeignKey('voice_profile.id', ondelete='SET NULL')),
            sa.Column('task_type', sa.String(50), nullable=False),
            sa.Column('platform', sa.String(50)),
            sa.Column('topic', sa.Text()),
            sa.Column('generated_content', sa.Text(), nullable=False),
            sa.Column('parameters', json_type),
            sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
            sa.Column('starred', sa.Boolean(), server_default='false'),
            sa.Column('deleted_at', sa.DateTime()),
        )
        
        # Create indexes
        op.create_index('idx_content_history_user', 'content_history', ['user_id', 'created_at'])
        
        # Create partial index for starred items (PostgreSQL only)
        if dialect == 'postgresql':
            op.create_index(
                'idx_content_history_starred', 
                'content_history', 
                ['user_id', 'starred'],
                postgresql_where=sa.text('starred = true')
            )


def downgrade():
    """
    We don't drop tables or columns in downgrade to avoid data loss.
    Tables and columns can be safely ignored by older code versions.
    """
    pass
