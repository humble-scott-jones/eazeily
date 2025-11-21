"""Team draft inbox + comments.

Revision ID: 20241008_01_team_drafts
Revises: 20241006_01_team_workflow
Create Date: 2024-10-08
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241008_01_team_drafts"
down_revision = "20241006_01_team_workflow"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "team_drafts",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("owner_user_id", sa.Text(), nullable=False),
        sa.Column("title", sa.Text()),
        sa.Column("campaign", sa.Text()),
        sa.Column("status", sa.Text(), server_default=sa.text("'draft'")),
        sa.Column("assignee_email", sa.Text()),
        sa.Column("due_date", sa.DateTime(timezone=True)),
        sa.Column("content", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_drafts_owner_status", "team_drafts", ["owner_user_id", "status"])

    op.create_table(
        "team_draft_comments",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("draft_id", sa.Text(), nullable=False),
        sa.Column("paragraph_id", sa.Text()),
        sa.Column("author_user_id", sa.Text(), nullable=False),
        sa.Column("body", sa.Text()),
        sa.Column("thread_id", sa.Text(), nullable=False),
        sa.Column("parent_id", sa.Text()),
        sa.Column("mentions", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_draft_comments_draft", "team_draft_comments", ["draft_id"])

    op.create_table(
        "team_draft_revisions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("draft_id", sa.Text(), nullable=False),
        sa.Column("author_user_id", sa.Text(), nullable=False),
        sa.Column("summary", sa.Text()),
        sa.Column("kind", sa.Text(), server_default=sa.text("'revision'")),
        sa.Column("details", sa.Text()),
        sa.Column("content_snapshot", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_draft_revisions_draft", "team_draft_revisions", ["draft_id"])


def downgrade():
    op.drop_index("idx_team_draft_revisions_draft", table_name="team_draft_revisions")
    op.drop_table("team_draft_revisions")
    op.drop_index("idx_team_draft_comments_draft", table_name="team_draft_comments")
    op.drop_table("team_draft_comments")
    op.drop_index("idx_team_drafts_owner_status", table_name="team_drafts")
    op.drop_table("team_drafts")
