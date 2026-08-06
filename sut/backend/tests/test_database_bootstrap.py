from app.infrastructure.database import bootstrap


class FakeResult:
    def __init__(self, value=None, rows=None):
        self.value = value
        self.rows = rows or []

    def scalar(self):
        return self.value

    def fetchall(self):
        return self.rows


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.count = 0

    def execute(self, query, params=None):
        self.calls.append((str(query), params))
        if "SELECT COUNT(*) FROM clouds" in str(query):
            return FakeResult(value=self.count)
        return FakeResult()


class FakeBegin:
    def __init__(self, connection):
        self.connection = connection

    def __enter__(self):
        return self.connection

    def __exit__(self, exc_type, exc, tb):
        return False


class FakeEngine:
    def __init__(self, connection):
        self.connection = connection
        self.url = FakeUrl()

    def begin(self):
        return FakeBegin(self.connection)


class FakeUrl:
    def __str__(self):
        return "postgresql://user:***@db:5432/app"

    def render_as_string(self, hide_password=True):
        if hide_password:
            return "postgresql://user:***@db:5432/app"
        return "postgresql://user:secret@db:5432/app"


def test_bootstrap_database_executes_schema_seed_and_cleanup(monkeypatch):
    connection = FakeConnection()
    cleanup_calls = []
    migration_calls = []

    monkeypatch.setattr(bootstrap, "_read_sql", lambda filename: f"-- {filename}")
    monkeypatch.setattr(bootstrap, "cleanup_obsolete_analyses", lambda conn: cleanup_calls.append(conn))
    monkeypatch.setattr(bootstrap, "run_migrations", lambda database_url: migration_calls.append(database_url))

    bootstrap.bootstrap_database(FakeEngine(connection))

    executed_sql = [call[0] for call in connection.calls]
    assert "-- seed_clouds.sql" in executed_sql
    assert migration_calls == ["postgresql://user:secret@db:5432/app"]
    assert cleanup_calls == [connection]


def test_bootstrap_database_skips_seed_when_clouds_exist(monkeypatch):
    connection = FakeConnection()
    connection.count = 3

    monkeypatch.setattr(bootstrap, "_read_sql", lambda filename: f"-- {filename}")
    monkeypatch.setattr(bootstrap, "cleanup_obsolete_analyses", lambda conn: None)
    monkeypatch.setattr(bootstrap, "run_migrations", lambda database_url: None)

    bootstrap.bootstrap_database(FakeEngine(connection))

    executed_sql = [call[0] for call in connection.calls]
    assert "-- seed_clouds.sql" not in executed_sql
