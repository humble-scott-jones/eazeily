"""Initial schema.

Revision ID: 20241005_01_initial
Revises: 
Create Date: 2024-10-05
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = "20241005_01_initial"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Users
    op.create_table(
        "users",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("email", sa.Text(), unique=True),
        sa.Column("password_hash", sa.Text()),
        sa.Column("is_paid", sa.Integer(), server_default=sa.text("0")),
        sa.Column("free_sample_used", sa.Integer(), server_default=sa.text("0")),
        sa.Column("stripe_customer_id", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Profiles
    op.create_table(
        "profiles",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("industry", sa.Text()),
        sa.Column("tone", sa.Text()),
        sa.Column("platforms", sa.Text()),
        sa.Column("brand_keywords", sa.Text()),
        sa.Column("niche_keywords", sa.Text()),
        sa.Column("goals", sa.Text()),
        sa.Column("company", sa.Text()),
        sa.Column("include_images", sa.Integer(), server_default=sa.text("1")),
        sa.Column("details", sa.Text()),
        sa.Column("voice_profile", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Feedback
    op.create_table(
        "feedback",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("profile_id", sa.Text()),
        sa.Column("post_day", sa.Integer()),
        sa.Column("platform", sa.Text()),
        sa.Column("rating", sa.Integer()),
        sa.Column("note", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Subscriptions
    op.create_table(
        "subscriptions",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text()),
        sa.Column("stripe_subscription_id", sa.Text()),
        sa.Column("status", sa.Text()),
        sa.Column("current_period_end", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Reconcile Jobs
    op.create_table(
        "reconcile_jobs",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("status", sa.Text()),
        sa.Column("result", sa.Text()),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("finished_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Password Reset Tokens
    op.create_table(
        "password_reset_tokens",
        sa.Column("token", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text()),
        sa.Column("expires_at", sa.DateTime(timezone=True)),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Generation Usage
    op.create_table(
        "generation_usage",
        sa.Column("id", sa.Text(), primary_key=True),
        sa.Column("user_id", sa.Text()),
        sa.Column("period", sa.Text()),
        sa.Column("reels_generated", sa.Integer(), server_default=sa.text("0")),
    )

    # Waitlist
    op.create_table(
        "waitlist",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("email", sa.Text(), unique=True),
        sa.Column("confirmed", sa.Integer(), server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )

    # Team Members
    op.create_table(
        "team_members",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("owner_user_id", sa.Text(), nullable=False),
        sa.Column("member_email", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("CURRENT_TIMESTAMP")),
    )
    op.create_index("idx_team_members_owner_email", "team_members", ["owner_user_id", "member_email"], unique=True)


def downgrade():
    op.drop_index("idx_team_members_owner_email", table_name="team_members")
    op.drop_table("team_members")
    op.drop_table("waitlist")
    op.drop_table("generation_usage")
    op.drop_table("password_reset_tokens")
    op.drop_table("reconcile_jobs")
    op.drop_table("subscriptions")
    op.drop_table("feedback")
    op.drop_table("profiles")
    op.drop_table("users")
