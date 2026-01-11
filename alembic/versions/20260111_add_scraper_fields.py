"""Add scraper fields to voice_profile table.

Revision ID: 20260111_add_scraper_fields
Revises: 20260110_add_brand_profile_fields
Create Date: 2026-01-11
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

# revision identifiers, used by Alembic.
revision = "20260111_add_scraper_fields"
down_revision = "20260110_add_brand_profile_fields"
branch_labels = None
depends_on = None


def upgrade():
    """Add new columns to voice_profile table for URL scraping functionality."""
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    
    # Check voice_profile table exists
    if 'voice_profile' not in inspector.get_table_names():
        print("WARNING: voice_profile table does not exist, skipping migration")
        return
    
    # Get existing columns
    columns = [c['name'] for c in inspector.get_columns('voice_profile')]
    
    # Add new scraper-related columns if they don't exist
    if 'scraped_url' not in columns:
        op.add_column('voice_profile', sa.Column('scraped_url', sa.Text()))
    
    if 'scraped_meta' not in columns:
        op.add_column('voice_profile', sa.Column('scraped_meta', sa.Text()))
    
    if 'customers' not in columns:
        op.add_column('voice_profile', sa.Column('customers', sa.Text()))
    
    if 'scraped_at' not in columns:
        op.add_column('voice_profile', sa.Column('scraped_at', sa.DateTime()))
    
    if 'scrape_status' not in columns:
        op.add_column('voice_profile', sa.Column('scrape_status', sa.String(50), server_default='none'))


def downgrade():
    """
    We don't drop columns in downgrade to avoid data loss.
    Columns can be safely ignored by older code versions.
    """
    pass
