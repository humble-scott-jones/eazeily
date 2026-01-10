"""Add brand profile fields to voice_profile table.

Revision ID: 20260110_add_brand_profile_fields
Revises: 52aa10327b5a
Create Date: 2026-01-10
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260110_add_brand_profile_fields"
down_revision = "52aa10327b5a"
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns to voice_profile table for brand profile wizard."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check voice_profile table exists
    if 'voice_profile' not in inspector.get_table_names():
        print("WARNING: voice_profile table does not exist, skipping migration")
        return
    
    # Get existing columns
    columns = [c['name'] for c in inspector.get_columns('voice_profile')]
    
    # Add new columns if they don't exist
    # Note: brand_inspirations, brand_anti_inspirations, and vibe_preset 
    # were already added in 20251214_01_add_brand_inspirations migration
    
    if 'tone' not in columns:
        op.add_column('voice_profile', sa.Column('tone', sa.String(255)))
    
    if 'platforms' not in columns:
        op.add_column('voice_profile', sa.Column('platforms', sa.Text()))
    
    if 'timezone' not in columns:
        op.add_column('voice_profile', sa.Column('timezone', sa.String(100)))
    
    if 'brand_keywords' not in columns:
        op.add_column('voice_profile', sa.Column('brand_keywords', sa.Text()))
    
    if 'niche_keywords' not in columns:
        op.add_column('voice_profile', sa.Column('niche_keywords', sa.Text()))
    
    if 'goals' not in columns:
        op.add_column('voice_profile', sa.Column('goals', sa.Text()))
    
    # These fields are already added by 20251214_01_add_brand_inspirations
    # but we check anyway for safety
    if 'brand_inspirations' not in columns:
        op.add_column('voice_profile', sa.Column('brand_inspirations', sa.Text()))
    
    if 'brand_anti_inspirations' not in columns:
        op.add_column('voice_profile', sa.Column('brand_anti_inspirations', sa.Text()))
    
    if 'vibe_preset' not in columns:
        op.add_column('voice_profile', sa.Column('vibe_preset', sa.String(255)))
    
    if 'include_images' not in columns:
        op.add_column('voice_profile', sa.Column('include_images', sa.Boolean(), server_default='false'))


def downgrade():
    """
    We don't drop columns in downgrade to avoid data loss.
    Columns can be safely ignored by older code versions.
    """
    pass
