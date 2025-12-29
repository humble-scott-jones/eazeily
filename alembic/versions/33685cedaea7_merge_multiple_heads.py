"""Merge multiple heads

Revision ID: 33685cedaea7
Revises: 20241126_add_profile_details, 20251214_01_add_brand_inspirations
Create Date: 2025-12-29 00:12:42.951174

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '33685cedaea7'
down_revision = ('20241126_add_profile_details', '20251214_01_add_brand_inspirations')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
