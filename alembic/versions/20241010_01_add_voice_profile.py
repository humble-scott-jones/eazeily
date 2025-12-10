"""Add voice_profile to users.

Revision ID: 20241010_01_add_voice_profile
Revises: 20241009_01_team_extras
Create Date: 2024-10-10
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241010_01_add_voice_profile"
down_revision = "20241009_01_team_extras"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("users", sa.Column("voice_profile", sa.Text()))


def downgrade():
    op.drop_column("users", "voice_profile")
