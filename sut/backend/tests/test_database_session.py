from app.infrastructure.database import database


def test_postgres_urls_force_utc_session_timezone():
    for url in ("postgresql://u:p@h/db", "postgresql+psycopg2://u:p@h/db", "postgres://u:p@h/db"):
        assert database.build_engine_kwargs(url) == {"connect_args": {"options": "-c timezone=utc"}}


def test_non_postgres_urls_get_no_extra_engine_options():
    assert database.build_engine_kwargs("sqlite:///x.db") == {}
    assert database.build_engine_kwargs(None) == {}


def test_get_db_closes_session(monkeypatch):
    class FakeSession:
        def __init__(self):
            self.closed = False

        def close(self):
            self.closed = True

    session = FakeSession()
    monkeypatch.setattr(database, "SessionLocal", lambda: session)

    generator = database.get_db()

    assert next(generator) is session

    try:
        next(generator)
    except StopIteration:
        pass

    assert session.closed is True
