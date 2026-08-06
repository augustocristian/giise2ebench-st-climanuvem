from app.data.analysis_repository import AnalysisRepository


class FakeResult:
    def __init__(self, value=None, rows=None, row=None):
        self.value = value
        self.rows = rows or []
        self.row = row

    def scalar(self):
        return self.value

    def fetchall(self):
        return self.rows

    def fetchone(self):
        return self.row


class FakeConnection:
    def __init__(self):
        self.calls = []
        self.results = []

    def queue_result(self, result):
        self.results.append(result)

    def execute(self, query, params=None):
        self.calls.append((str(query), params))
        if self.results:
            return self.results.pop(0)
        if "SELECT id FROM clouds" in str(query):
            return FakeResult(value=42)
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

    def begin(self):
        return FakeBegin(self.connection)


def get_call(connection, index):
    assert len(connection.calls) > index
    return connection.calls[index]


def get_last_call(connection):
    assert connection.calls
    return connection.calls[len(connection.calls) - 1]


def test_save_cloud_analysis_maps_known_cloud_and_persists_box(monkeypatch):
    import app.data.analysis_repository as repository_module

    connection = FakeConnection()
    monkeypatch.setattr(repository_module, "engine", FakeEngine(connection))

    AnalysisRepository().save_cloud_analysis(
        9,
        [{"label": "cumulus", "confidence": 0.8, "box_2d": [1, 2, 3, 4]}],
    )

    insert_call = get_last_call(connection)
    assert "INSERT INTO analysis_cloud" in insert_call[0]
    assert insert_call[1] == {
        "analysis_id": 9,
        "cloud_id": 42,
        "confidence": 0.8,
        "box_ymin": 1,
        "box_xmin": 2,
        "box_ymax": 3,
        "box_xmax": 4,
    }


def test_save_cloud_analysis_ignores_unknown_labels(monkeypatch):
    import app.data.analysis_repository as repository_module

    connection = FakeConnection()
    monkeypatch.setattr(repository_module, "engine", FakeEngine(connection))

    AnalysisRepository().save_cloud_analysis(9, [{"label": "unknown"}])

    assert connection.calls == []


def test_create_analysis_inserts_and_returns_id():
    connection = FakeConnection()
    connection.queue_result(FakeResult(value=99))

    analysis_id = AnalysisRepository(connection).create_analysis(
        uid="user-1",
        image_path="/uploads/user-1/cloud.jpg",
        location="Gijón",
        latitude=43.5,
        longitude=-5.6,
        is_anon=False,
    )

    assert analysis_id == 99
    insert_call = get_call(connection, 0)
    assert "INSERT INTO analysis" in insert_call[0]
    assert insert_call[1]["uid"] == "user-1"


def test_get_history_rows_filters_by_uid():
    rows = [object()]
    connection = FakeConnection()
    connection.queue_result(FakeResult(rows=rows))

    result = AnalysisRepository(connection).get_history_rows("user-1")

    assert result == rows
    select_call = get_call(connection, 0)
    assert "FROM analysis a" in select_call[0]
    assert select_call[1] == {"uid": "user-1"}


def test_delete_user_analyses_deletes_children_and_returns_image_paths():
    row = type("Row", (), {"id": 7, "image_path": "/uploads/user/cloud.jpg"})()
    connection = FakeConnection()
    connection.queue_result(FakeResult(rows=[row]))

    image_paths = AnalysisRepository(connection).delete_user_analyses("user-1")

    assert image_paths == ["/uploads/user/cloud.jpg"]
    assert "SELECT id, image_path FROM analysis" in get_call(connection, 0)[0]
    assert "DELETE FROM analysis_cloud" in get_call(connection, 1)[0]
    assert "DELETE FROM analysis WHERE" in get_call(connection, 2)[0]


def test_delete_analysis_returns_none_when_not_found():
    connection = FakeConnection()
    connection.queue_result(FakeResult(row=None))

    image_path = AnalysisRepository(connection).delete_analysis(7, "user-1")

    assert image_path is None
    assert len(connection.calls) == 1


def test_delete_analysis_deletes_and_returns_image_path():
    row = type("Row", (), {"id": 7, "image_path": "/uploads/user/cloud.jpg"})()
    connection = FakeConnection()
    connection.queue_result(FakeResult(row=row))

    image_path = AnalysisRepository(connection).delete_analysis(7, "user-1")

    assert image_path == "/uploads/user/cloud.jpg"
    assert "DELETE FROM analysis_cloud" in get_call(connection, 1)[0]
    assert "DELETE FROM analysis WHERE" in get_call(connection, 2)[0]


def test_get_analysis_status_returns_status_from_session():
    row = type("Row", (), {"status": "analyzing"})()
    connection = FakeConnection()
    connection.queue_result(FakeResult(row=row))

    status = AnalysisRepository(connection).get_analysis_status(7)

    assert status == "analyzing"
    assert "SELECT status FROM analysis" in get_call(connection, 0)[0]


def test_cancel_analysis_reports_invalid_states_and_updates_analyzing():
    connection = FakeConnection()
    connection.queue_result(FakeResult(row=None))
    assert AnalysisRepository(connection).cancel_analysis(7, "user-1") == AnalysisRepository.CANCEL_NOT_FOUND

    done_row = type("Row", (), {"id": 7, "status": "completed"})()
    connection.queue_result(FakeResult(row=done_row))
    assert AnalysisRepository(connection).cancel_analysis(7, "user-1") == AnalysisRepository.CANCEL_INVALID_STATUS

    analyzing_row = type("Row", (), {"id": 7, "status": "analyzing"})()
    connection.queue_result(FakeResult(row=analyzing_row))
    assert AnalysisRepository(connection).cancel_analysis(7, "user-1") == AnalysisRepository.CANCEL_CANCELLED
    assert "UPDATE analysis SET status = 'cancelled'" in get_last_call(connection)[0]
