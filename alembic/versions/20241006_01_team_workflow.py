"""Team collaboration approvals tables.

Revision ID: 20241006_01_team_workflow
Revises: 20241005_01_initial
Create Date: 2024-10-06
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241006_01_team_workflow"
down_revision = "20241005_01_initial"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "team_approvals",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("owner_user_id", sa.Text(), nullable=False),
        sa.Column("submitter_user_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("content_ref", sa.Text()),
        sa.Column("state", sa.Text(), server_default=sa.text("'pending'")),
        sa.Column("reviewers", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_approvals_owner_state", "team_approvals", ["owner_user_id", "state"])

    op.create_table(
        "team_approval_events",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("approval_id", sa.Text(), nullable=False),
        sa.Column("actor_user_id", sa.Text(), nullable=False),
        sa.Column("action", sa.Text(), nullable=False),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    op.drop_table("team_approval_events")
    op.drop_index("idx_team_approvals_owner_state", table_name="team_approvals")
    op.drop_table("team_approvals")
