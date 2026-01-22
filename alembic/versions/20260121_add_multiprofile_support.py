"""Add multi-profile support fields

Revision ID: 20260121_add_multiprofile
Revises: 20260120_add_content_history
Create Date: 2026-01-21 22:58:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '20260121_add_multiprofile'
down_revision = '20260120_add_content_history'
branch_labels = None
depends_on = None


def upgrade():
    """Add is_default and profile_name fields to voice_profile table."""
    # Add is_default column
    op.add_column('voice_profile', sa.Column('is_default', sa.Boolean(), nullable=False, server_default='false'))
    op.create_index(op.f('ix_voice_profile_is_default'), 'voice_profile', ['is_default'], unique=False)
    
    # Add profile_name column
    op.add_column('voice_profile', sa.Column('profile_name', sa.String(length=100), nullable=True))
    
    # Set existing profiles as default and give them a name based on business_name
    op.execute("""
        UPDATE voice_profile 
        SET is_default = true, 
            profile_name = COALESCE(business_name, 'Main Profile')
        WHERE is_default = false
    """)


def downgrade():
    """Remove multi-profile support fields."""
    op.drop_index(op.f('ix_voice_profile_is_default'), table_name='voice_profile')
    op.drop_column('voice_profile', 'profile_name')
    op.drop_column('voice_profile', 'is_default')
