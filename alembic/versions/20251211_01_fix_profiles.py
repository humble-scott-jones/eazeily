"""Fix profiles schema.

Revision ID: 20251211_01_fix_profiles
Revises: 20241010_01_add_voice_profile
Create Date: 2025-12-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20251211_01_fix_profiles"
down_revision = "20241010_01_add_voice_profile"
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check profiles table
    columns = [c['name'] for c in inspector.get_columns('profiles')]
    if 'voice_profile' not in columns:
        op.add_column('profiles', sa.Column('voice_profile', sa.Text()))

    # Check users table (just in case)
    columns = [c['name'] for c in inspector.get_columns('users')]
    if 'voice_profile' not in columns:
        op.add_column('users', sa.Column('voice_profile', sa.Text()))


def downgrade():
    # We don't want to drop columns in downgrade as it might lose data
    pass
