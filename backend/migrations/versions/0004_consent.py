"""record the parent's acceptance of the privacy policy and terms

Revision ID: 0004
Revises: 0003
"""
from alembic import op
import sqlalchemy as sa

revision = "0004"
down_revision = "0003"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column("parents", sa.Column("terms_accepted_at", sa.DateTime(), nullable=True))
    op.add_column("parents", sa.Column("terms_version", sa.String(20), nullable=True))


def downgrade():
    with op.batch_alter_table("parents") as b:
        b.drop_column("terms_version")
        b.drop_column("terms_accepted_at")
