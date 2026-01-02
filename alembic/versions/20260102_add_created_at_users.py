"""
Add created_at column to users table (if missing)

Revision ID: 20260102_add_created_at_users
Revises: 
Create Date: 2026-01-02 00:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '20260102_add_created_at_users'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    dialect = bind.engine.dialect.name

    if dialect == 'postgresql':
        # Safe in Postgres: IF NOT EXISTS prevents errors
        op.execute(
            "ALTER TABLE users ADD COLUMN IF NOT EXISTS created_at TIMESTAMP WITHOUT TIME ZONE DEFAULT now();"
        )
    elif dialect == 'sqlite':
        # SQLite: ALTER TABLE supports adding a column; ignore if already exists by checking pragma
        cols = [c['name'] for c in bind.execute("PRAGMA table_info('users')").fetchall()]
        if 'created_at' not in cols:
            op.execute("ALTER TABLE users ADD COLUMN created_at DATETIME;")
    else:
        # Generic fallback - try adding column and ignore failures
        try:
            op.add_column('users', sa.Column('created_at', sa.DateTime(), nullable=True))
        except Exception:
            pass


def downgrade() -> None:
    bind = op.get_bind()
    dialect = bind.engine.dialect.name
    if dialect == 'postgresql':
        op.execute("ALTER TABLE users DROP COLUMN IF EXISTS created_at;")
    elif dialect == 'sqlite':
        # SQLite doesn't support DROP COLUMN; leave as-is for downgrade
        pass
    else:
        try:
            op.drop_column('users', 'created_at')
        except Exception:
            pass
