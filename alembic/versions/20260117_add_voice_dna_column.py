"""Add voice_dna column to voice_profile

Revision ID: 20260117_add_voice_dna
Revises: 52aa10327b5a
Create Date: 2026-01-17 12:26:28

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260117_add_voice_dna'
down_revision = '52aa10327b5a'
branch_labels = None
depends_on = None


def upgrade():
    # Add voice_dna column to voice_profile table
    op.add_column('voice_profile', sa.Column('voice_dna', sa.Text(), nullable=True))


def downgrade():
    # Remove voice_dna column from voice_profile table
    op.drop_column('voice_profile', 'voice_dna')
