"""places: arrive/leave alerts

Revision ID: 0003
Revises: 0002
"""
from alembic import op
import sqlalchemy as sa

revision = "0003"
down_revision = "0002"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("parents", sa.Column("notify_places", sa.Boolean(), nullable=False, server_default=sa.true()))
    op.create_table(
        "places",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("child_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(60), nullable=False),
        sa.Column("lat", sa.Float(), nullable=False),
        sa.Column("lng", sa.Float(), nullable=False),
        sa.Column("radius_m", sa.Integer(), nullable=False),
        sa.Column("inside", sa.Boolean(), nullable=True),
        sa.Column("state_changed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("lat BETWEEN -90 AND 90", name="ck_place_lat"),
        sa.CheckConstraint("lng BETWEEN -180 AND 180", name="ck_place_lng"),
        sa.CheckConstraint("radius_m BETWEEN 50 AND 2000", name="ck_place_radius"),
        sa.ForeignKeyConstraint(["child_id"], ["children.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_places_child_id", "places", ["child_id"])


def downgrade():
    op.drop_index("ix_places_child_id", table_name="places")
    op.drop_table("places")
    with op.batch_alter_table("parents") as b:
        b.drop_column("notify_places")
