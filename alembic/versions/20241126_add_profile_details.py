"""Add profile details placeholder migration.

Revision ID: 20241126_add_profile_details
Revises: 20241010_01_add_voice_profile
Create Date: 2024-11-26
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241126_add_profile_details"
down_revision = "20241010_01_add_voice_profile"
branch_labels = None
depends_on = None


def upgrade():
    # This is an empty placeholder migration to satisfy deployments where
    # the DB references this revision but the file was accidentally removed.
    # No schema changes required here; keep idempotent.
    pass


def downgrade():
    # No-op downgrade
    pass
