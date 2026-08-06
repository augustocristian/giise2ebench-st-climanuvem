from app.infrastructure.database import database


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
