"""Team extras and fixes.

Revision ID: 20241009_01_team_extras
Revises: 20241008_01_team_drafts
Create Date: 2024-10-09
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241009_01_team_extras"
down_revision = "20241008_01_team_drafts"
branch_labels = None
depends_on = None


def upgrade():
    # Add missing column to team_draft_revisions
    op.add_column("team_draft_revisions", sa.Column("changelog_note", sa.Text()))

    # Create team_approver_defaults
    op.create_table(
        "team_approver_defaults",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("owner_user_id", sa.Text(), nullable=False),
        sa.Column("campaign", sa.Text()),
        sa.Column("channel", sa.Text()),
        sa.Column("approver_email", sa.Text()),
        sa.Column("allow_any", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_approver_defaults_owner", "team_approver_defaults", ["owner_user_id"])

    # Create team_draft_notifications
    op.create_table(
        "team_draft_notifications",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("draft_id", sa.Text(), nullable=False),
        sa.Column("channel", sa.Text()),
        sa.Column("message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )


def downgrade():
    op.drop_table("team_draft_notifications")
    op.drop_index("idx_team_approver_defaults_owner", table_name="team_approver_defaults")
    op.drop_table("team_approver_defaults")
    op.drop_column("team_draft_revisions", "changelog_note")
