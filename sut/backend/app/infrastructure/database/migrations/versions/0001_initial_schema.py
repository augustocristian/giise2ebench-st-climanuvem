"""Initial schema and indexes.

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-07-05
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial_schema"
down_revision = None
branch_labels = None
depends_on = None


def _has_table(bind, table_name: str) -> bool:
    return sa.inspect(bind).has_table(table_name)


def upgrade():
    bind = op.get_bind()

    if not _has_table(bind, "analysis"):
        op.create_table(
            "analysis",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("uid", sa.Text),
            sa.Column("image_path", sa.Text),
            sa.Column("datetime", sa.DateTime, nullable=False, server_default=sa.text("CURRENT_TIMESTAMP")),
            sa.Column("location", sa.Text),
            sa.Column("latitude", sa.Float),
            sa.Column("longitude", sa.Float),
            sa.Column("is_anon", sa.Boolean, nullable=False, server_default=sa.false()),
            sa.Column("status", sa.Text, nullable=False, server_default="completed"),
        )

    if not _has_table(bind, "clouds"):
        op.create_table(
            "clouds",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("name", sa.Text, nullable=False, unique=True),
            sa.Column("forecast", sa.Text),
            sa.Column("warning", sa.Text),
            sa.Column("warning_level", sa.Integer),
        )

    if not _has_table(bind, "analysis_cloud"):
        op.create_table(
            "analysis_cloud",
            sa.Column("id", sa.Integer, primary_key=True),
            sa.Column("analysis_id", sa.Integer, sa.ForeignKey("analysis.id", ondelete="CASCADE")),
            sa.Column("cloud_id", sa.Integer, sa.ForeignKey("clouds.id")),
            sa.Column("confidence", sa.Float),
            sa.Column("box_ymin", sa.Float),
            sa.Column("box_xmin", sa.Float),
            sa.Column("box_ymax", sa.Float),
            sa.Column("box_xmax", sa.Float),
        )

    op.execute("CREATE INDEX IF NOT EXISTS ix_analysis_uid_datetime ON analysis (uid, datetime DESC)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_analysis_is_anon_datetime ON analysis (is_anon, datetime)")


def downgrade():
    op.execute("DROP INDEX IF EXISTS ix_analysis_is_anon_datetime")
    op.execute("DROP INDEX IF EXISTS ix_analysis_uid_datetime")
