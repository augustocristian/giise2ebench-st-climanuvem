import logging
import os
from datetime import datetime, timedelta, timezone

from alembic import command
from alembic.config import Config
from sqlalchemy import text

logger = logging.getLogger(__name__)

DATABASE_DIR = os.path.dirname(__file__)
APP_DIR = os.path.abspath(os.path.join(DATABASE_DIR, "..", ".."))
UPLOADS_DIR = os.path.abspath(os.path.join(APP_DIR, "..", "uploads"))
MIGRATIONS_DIR = os.path.join(DATABASE_DIR, "migrations")


def _read_sql(filename: str) -> str:
    path = os.path.join(DATABASE_DIR, filename)
    with open(path, encoding="utf-8") as f:
        return f.read()


def _remove_upload_file(image_path: str):
    if not image_path:
        return

    rel_path = image_path.replace("/uploads/", "")
    file_path = os.path.join(UPLOADS_DIR, rel_path)
    if os.path.exists(file_path):
        try:
            os.remove(file_path)
        except Exception as e:
            logger.exception("Error deleting obsolete file at %s: %s", file_path, e)


def cleanup_obsolete_analyses(conn):
    if conn.dialect.name == "sqlite":
        cutoff = datetime.now(timezone.utc) - timedelta(days=3)
        obsolete_analyses = conn.execute(
            text("""
                SELECT id, image_path
                FROM analysis
                WHERE is_anon = 1 AND datetime < :cutoff
            """),
            {"cutoff": cutoff.replace(tzinfo=None)},
        ).fetchall()
    else:
        obsolete_analyses = conn.execute(
            text("""
                SELECT id, image_path
                FROM analysis
                WHERE is_anon = TRUE AND datetime < NOW() - INTERVAL '3 days'
            """)
        ).fetchall()

    for row in obsolete_analyses:
        _remove_upload_file(row.image_path)
        conn.execute(text("DELETE FROM analysis_cloud WHERE analysis_id = :id"), {"id": row.id})
        conn.execute(text("DELETE FROM analysis WHERE id = :id"), {"id": row.id})


def run_migrations(database_url: str):
    alembic_config = Config()
    alembic_config.set_main_option("script_location", MIGRATIONS_DIR)
    alembic_config.set_main_option("sqlalchemy.url", database_url)
    command.upgrade(alembic_config, "head")


def bootstrap_database(engine):
    run_migrations(engine.url.render_as_string(hide_password=False))

    with engine.begin() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM clouds"))
        if result.scalar() == 0:
            conn.execute(text(_read_sql("seed_clouds.sql")))

        cleanup_obsolete_analyses(conn)
