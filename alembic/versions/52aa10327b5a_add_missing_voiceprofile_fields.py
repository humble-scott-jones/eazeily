"""Add missing VoiceProfile fields

Revision ID: 52aa10327b5a
Revises: 2c65709d5f3f
Create Date: 2026-01-06 00:56:49.781502

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '52aa10327b5a'
down_revision = '2c65709d5f3f'
branch_labels = None
depends_on = None


def upgrade():
    bind = op.get_bind()
    dialect = bind.engine.dialect.name
    inspector = sa.inspect(bind)
    has_table = inspector.has_table('voice_profile')

    if not has_table:
        # Create the full table if it doesn't exist (fixes broken local dev envs)
        op.create_table('voice_profile',
            sa.Column('id', sa.Integer(), nullable=False),
            sa.Column('user_id', sa.Integer(), nullable=False),
            sa.Column('industry', sa.String(length=255), nullable=True),
            sa.Column('business_name', sa.String(length=255), nullable=True),
            sa.Column('defaults', sa.Text(), nullable=True),
            sa.Column('examples', sa.Text(), nullable=True),
            sa.Column('target_audience', sa.Text(), nullable=True),
            sa.Column('brand_voice', sa.String(length=255), nullable=True),
            sa.Column('key_offer', sa.Text(), nullable=True),
            sa.Column('voice_rules', sa.Text(), nullable=True),
            sa.Column('writing_samples', sa.Text(), nullable=True),
            sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
            sa.PrimaryKeyConstraint('id')
        )
        return

    # If table exists, check for missing columns (fixes staging/prod envs)
    if dialect == 'sqlite':
        # SQLite: Check existing columns via PRAGMA
        from sqlalchemy import text
        existing_cols = [c[1] for c in bind.execute(text("PRAGMA table_info('voice_profile')")).fetchall()]
        
        if 'target_audience' not in existing_cols:
            op.add_column('voice_profile', sa.Column('target_audience', sa.Text(), nullable=True))
        if 'brand_voice' not in existing_cols:
            op.add_column('voice_profile', sa.Column('brand_voice', sa.String(length=255), nullable=True))
        if 'key_offer' not in existing_cols:
            op.add_column('voice_profile', sa.Column('key_offer', sa.Text(), nullable=True))
        if 'voice_rules' not in existing_cols:
            op.add_column('voice_profile', sa.Column('voice_rules', sa.Text(), nullable=True))
        if 'writing_samples' not in existing_cols:
            op.add_column('voice_profile', sa.Column('writing_samples', sa.Text(), nullable=True))
            
    else:
        # Postgres/Other: Try adding columns safely
        try:
            op.add_column('voice_profile', sa.Column('target_audience', sa.Text(), nullable=True))
        except Exception: pass
        
        try:
            op.add_column('voice_profile', sa.Column('brand_voice', sa.String(length=255), nullable=True))
        except Exception: pass
            
        try:
            op.add_column('voice_profile', sa.Column('key_offer', sa.Text(), nullable=True))
        except Exception: pass
            
        try:
            op.add_column('voice_profile', sa.Column('voice_rules', sa.Text(), nullable=True))
        except Exception: pass
            
        try:
            op.add_column('voice_profile', sa.Column('writing_samples', sa.Text(), nullable=True))
        except Exception: pass


def downgrade():
    op.drop_column('voice_profile', 'writing_samples')
    op.drop_column('voice_profile', 'voice_rules')
    op.drop_column('voice_profile', 'key_offer')
    op.drop_column('voice_profile', 'brand_voice')
    op.drop_column('voice_profile', 'target_audience')
