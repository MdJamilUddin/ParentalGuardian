"""initial schema

Revision ID: 0001
Revises:
"""
from alembic import op
import sqlalchemy as sa

revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "parents",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_parents_email", "parents", ["email"], unique=True)

    op.create_table(
        "children",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(["parent_id"], ["parents.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_children_parent_id", "children", ["parent_id"])

    op.create_table(
        "devices",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("token_hash", sa.String(64), nullable=False),
        sa.Column("revoked", sa.Boolean(), nullable=False),
        sa.Column("paired_at", sa.DateTime(), nullable=False),
        sa.Column("last_seen", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_devices_child_id", "devices", ["child_id"])
    op.create_index("ix_devices_token_hash", "devices", ["token_hash"], unique=True)

    op.create_table(
        "pairing_codes",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("code_hash", sa.String(64), nullable=False),
        sa.Column("expires_at", sa.DateTime(), nullable=False),
        sa.Column("used", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_pairing_codes_child_id", "pairing_codes", ["child_id"])
    op.create_index("ix_pairing_codes_code_hash", "pairing_codes", ["code_hash"], unique=True)

    op.create_table(
        "location_points",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("accuracy_m", sa.Float(), nullable=True),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("lat BETWEEN -90 AND 90", name="ck_location_lat"),
        sa.CheckConstraint("lng BETWEEN -180 AND 180", name="ck_location_lng"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_location_device_time", "location_points", ["device_id", "recorded_at"])

    op.create_table(
        "usage_records",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("package", sa.String(255), nullable=False),
        sa.Column("app_label", sa.String(255), nullable=True),
        sa.Column("day", sa.String(10), nullable=False),
        sa.Column("seconds", sa.Integer(), nullable=False),
        sa.CheckConstraint("seconds BETWEEN 0 AND 86400", name="ck_usage_seconds"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("device_id", "package", "day"),
    )
    op.create_index("ix_usage_device_day", "usage_records", ["device_id", "day"])

    op.create_table(
        "battery_readings",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("device_id", sa.Integer(), nullable=False),
        sa.Column("level", sa.Integer(), nullable=False),
        sa.Column("charging", sa.Boolean(), nullable=False),
        sa.Column("recorded_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("level BETWEEN 0 AND 100", name="ck_battery_level"),
        sa.ForeignKeyConstraint(["device_id"], ["devices.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_battery_device_time", "battery_readings", ["device_id", "recorded_at"])


def downgrade():
    op.drop_index("ix_battery_device_time", table_name="battery_readings")
    op.drop_table("battery_readings")
    op.drop_index("ix_usage_device_day", table_name="usage_records")
    op.drop_table("usage_records")
    op.drop_index("ix_location_device_time", table_name="location_points")
    op.drop_table("location_points")
    op.drop_index("ix_pairing_codes_code_hash", table_name="pairing_codes")
    op.drop_index("ix_pairing_codes_child_id", table_name="pairing_codes")
    op.drop_table("pairing_codes")
    op.drop_index("ix_devices_token_hash", table_name="devices")
    op.drop_index("ix_devices_child_id", table_name="devices")
    op.drop_table("devices")
    op.drop_index("ix_children_parent_id", table_name="children")
    op.drop_table("children")
    op.drop_index("ix_parents_email", table_name="parents")
    op.drop_table("parents")
