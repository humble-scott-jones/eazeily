"""Merge multiple heads

Revision ID: 2c65709d5f3f
Revises: 20260102_add_created_at_users, 33685cedaea7
Create Date: 2026-01-06 00:56:14.512579

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2c65709d5f3f'
down_revision = ('20260102_add_created_at_users', '33685cedaea7')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
