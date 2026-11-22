"""push notifications: tokens, alert state, parent preferences

Revision ID: 0002
Revises: 0001
"""
from alembic import op
import sqlalchemy as sa

revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("parents", sa.Column("notify_offline", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("parents", sa.Column("notify_low_battery", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.add_column("devices", sa.Column("stale_alert_sent_at", sa.DateTime(), nullable=True))
    op.add_column("devices", sa.Column("low_battery_alert_sent_at", sa.DateTime(), nullable=True))
    op.create_table(
        "push_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("token", sa.String(512), nullable=False),
        sa.Column("platform", sa.String(20), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_push_tokens_parent_id", "push_tokens", ["parent_id"])
    op.create_index("ix_push_tokens_token", "push_tokens", ["token"], unique=True)


def downgrade():
    op.drop_index("ix_push_tokens_token", table_name="push_tokens")
    op.drop_index("ix_push_tokens_parent_id", table_name="push_tokens")
    op.drop_table("push_tokens")
    with op.batch_alter_table("devices") as b:
        b.drop_column("low_battery_alert_sent_at")
        b.drop_column("stale_alert_sent_at")
    with op.batch_alter_table("parents") as b:
        b.drop_column("notify_low_battery")
        b.drop_column("notify_offline")
