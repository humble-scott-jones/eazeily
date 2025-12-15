"""Add brand inspirations fields.

Revision ID: 20251214_01_add_brand_inspirations
Revises: 20251211_01_fix_profiles
Create Date: 2025-12-14
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20251214_01_add_brand_inspirations"
down_revision = "20251211_01_fix_profiles"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Add brand_inspirations to profiles table
    profiles_columns = [c['name'] for c in inspector.get_columns('profiles')]
    if 'brand_inspirations' not in profiles_columns:
        op.add_column('profiles', sa.Column('brand_inspirations', sa.Text()))
    if 'brand_anti_inspirations' not in profiles_columns:
        op.add_column('profiles', sa.Column('brand_anti_inspirations', sa.Text()))
    if 'vibe_preset' not in profiles_columns:
        op.add_column('profiles', sa.Column('vibe_preset', sa.Text()))
    
    # Add brand_inspirations to users table (for user-level settings)
    users_columns = [c['name'] for c in inspector.get_columns('users')]
    if 'brand_inspirations' not in users_columns:
        op.add_column('users', sa.Column('brand_inspirations', sa.Text()))
    if 'brand_anti_inspirations' not in users_columns:
        op.add_column('users', sa.Column('brand_anti_inspirations', sa.Text()))
    if 'vibe_preset' not in users_columns:
        op.add_column('users', sa.Column('vibe_preset', sa.Text()))


def downgrade():
    # We don't want to drop columns in downgrade as it might lose data
    pass
