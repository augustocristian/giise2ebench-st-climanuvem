import os
from datetime import datetime, timezone

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.bootstrap import bootstrap_database
from app.infrastructure.database.database import get_db
from app.infrastructure.queue import analysis_queue
from app.presentation.dependencies.auth_dependency import get_current_user
from app.presentation.error_handlers import register_exception_handlers
from app.presentation.routes import analysis_routes

BASE = "/api/v1/analyses"
JPG = ("cloud.jpg", b"\xff\xd8\xff\xe0image-bytes", "image/jpeg")


def _drain_analysis_queue():
    while not analysis_queue.empty():
        analysis_queue.get_nowait()
        analysis_queue.task_done()


def _build_app(tmp_path, monkeypatch, override_auth=True):
    db_path = tmp_path / "integration.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    bootstrap_database(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    monkeypatch.setattr(analysis_routes, "UPLOADS_BASE_DIR", str(tmp_path / "uploads"))

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(analysis_routes.router, prefix=BASE)

    def override_user():
        return {"uid": "test-user", "firebase": {"sign_in_provider": "custom"}}

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    if override_auth:
        app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db
    return app


@pytest.fixture
def client(tmp_path, monkeypatch):
    _drain_analysis_queue()
    return TestClient(_build_app(tmp_path, monkeypatch))


def _upload(client, **data):
    return client.post(BASE, files={"file": JPG}, data={"location": "Gijon", **data})


def _assert_problem(response, status, detail):
    assert response.status_code == status
    assert response.headers["content-type"].startswith("application/problem+json")
    body = response.json()
    assert body["type"] == "about:blank"
    assert body["status"] == status
    assert body["detail"] == detail
    assert isinstance(body["title"], str) and body["title"]
    return body


def test_upload_returns_202_with_location_and_minimal_body(client):
    response = _upload(client, latitude="43.5", longitude="-5.6", fcmToken="tok", includeExplainability="true")

    assert response.status_code == 202
    body = response.json()
    assert set(body) == {"id", "status"}
    assert isinstance(body["id"], int)
    assert body["status"] == "analyzing"
    assert response.headers["location"] == f"{BASE}/{body['id']}"

    task = analysis_queue.get_nowait()
    assert task.fcm_token == "tok"
    assert task.explainability is True
    analysis_queue.task_done()

    name, ext = os.path.splitext(os.path.basename(task.file_path))
    assert ext == ".jpg" and len(name) == 32 and all(c in "0123456789abcdef" for c in name)


def test_get_single_analysis_and_utc_date(client):
    before = datetime.now(timezone.utc).replace(tzinfo=None)
    analysis_id = _upload(client).json()["id"]
    after = datetime.now(timezone.utc).replace(tzinfo=None)

    response = client.get(f"{BASE}/{analysis_id}")
    assert response.status_code == 200
    body = response.json()
    assert body["id"] == analysis_id
    assert body["status"] == "analyzing"
    assert body["location"] == "Gijon"
    assert set(body["results"]) == {"cloudTypes", "cloudDetails", "forecast", "warnings"}
    assert body["date"].endswith("Z")
    stored = datetime.fromisoformat(body["date"][:-1])
    assert before <= stored <= after


def test_get_single_analysis_not_found(client):
    _assert_problem(client.get(f"{BASE}/9999"), 404, "ANALYSIS_NOT_FOUND")


def test_history_pagination_and_total_count_header(client):
    ids = [_upload(client).json()["id"] for _ in range(3)]

    response = client.get(BASE, params={"page": 0, "size": 2})
    assert response.status_code == 200
    assert response.headers["x-total-count"] == "3"
    assert [a["id"] for a in response.json()] == [ids[2], ids[1]]

    response = client.get(BASE, params={"page": 1, "size": 2})
    assert response.headers["x-total-count"] == "3"
    assert [a["id"] for a in response.json()] == [ids[0]]

    assert len(client.get(BASE).json()) == 3


@pytest.mark.parametrize("params", [{"page": -1}, {"size": 0}, {"size": 101}])
def test_history_rejects_invalid_pagination(client, params):
    response = client.get(BASE, params=params)
    assert response.status_code == 422
    assert response.headers["content-type"].startswith("application/problem+json")


def test_cancel_returns_updated_analysis_and_second_cancel_conflicts(client):
    analysis_id = _upload(client).json()["id"]

    response = client.patch(f"{BASE}/{analysis_id}", json={"status": "cancelled"})
    assert response.status_code == 200
    assert response.json()["id"] == analysis_id
    assert response.json()["status"] == "cancelled"

    _assert_problem(
        client.patch(f"{BASE}/{analysis_id}", json={"status": "cancelled"}),
        409,
        "ANALYSIS_NOT_CANCELLABLE",
    )


def test_patch_not_found_and_invalid_status(client):
    _assert_problem(client.patch(f"{BASE}/9999", json={"status": "cancelled"}), 404, "ANALYSIS_NOT_FOUND")
    analysis_id = _upload(client).json()["id"]
    assert client.patch(f"{BASE}/{analysis_id}", json={"status": "completed"}).status_code == 422
    assert client.patch(f"{BASE}/{analysis_id}", json={}).status_code == 422


def test_delete_single_returns_204_without_body_and_removes_file(client, tmp_path):
    analysis_id = _upload(client).json()["id"]
    assert any((tmp_path / "uploads" / "test-user").iterdir())

    response = client.delete(f"{BASE}/{analysis_id}")
    assert response.status_code == 204
    assert response.content == b""
    assert not any((tmp_path / "uploads" / "test-user").iterdir())

    _assert_problem(client.delete(f"{BASE}/{analysis_id}"), 404, "ANALYSIS_NOT_FOUND")
    assert client.get(BASE).json() == []


def test_delete_all_returns_204_without_body(client, tmp_path):
    _upload(client)
    _upload(client)

    response = client.delete(BASE)
    assert response.status_code == 204
    assert response.content == b""
    assert client.get(BASE).json() == []
    assert not any((tmp_path / "uploads" / "test-user").iterdir())


def test_upload_validation_errors(client):
    _assert_problem(client.post(BASE, files={"file": ("empty.jpg", b"", "image/jpeg")}), 422, "IMAGE_EMPTY")
    _assert_problem(
        client.post(BASE, files={"file": ("a.txt", b"hello", "text/plain")}),
        415,
        "INVALID_IMAGE_FORMAT_JPG_ONLY",
    )
    big = b"\xff\xd8\xff" + b"0" * (5 * 1024 * 1024)
    _assert_problem(
        client.post(BASE, files={"file": ("big.jpg", big, "image/jpeg")}), 413, "IMAGE_TOO_LARGE_MAX_5MB"
    )
    assert client.post(BASE, data={"location": "x"}).status_code == 422


def test_framework_answers_405_with_allow_header(client):
    response = client.put(BASE)
    assert response.status_code == 405
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.headers["allow"] == "DELETE, GET, POST"

    response = client.post(f"{BASE}/1")
    assert response.status_code == 405
    assert response.headers["allow"] == "DELETE, GET, PATCH"

    # old hand-written 405 paths no longer exist
    assert client.get(f"{BASE}/1/cancel").status_code == 404


def test_missing_credentials_return_401_with_www_authenticate(tmp_path, monkeypatch):
    client = TestClient(_build_app(tmp_path, monkeypatch, override_auth=False))

    for response in (client.get(BASE), client.delete(BASE), client.post(BASE, files={"file": JPG})):
        body = _assert_problem(response, 401, "NOT_AUTHENTICATED")
        assert body["title"] == "Unauthorized"
        assert response.headers["www-authenticate"] == "Bearer"


def test_invalid_token_returns_401_invalid_token(tmp_path, monkeypatch):
    from app.presentation.dependencies import auth_dependency

    def reject(_token):
        raise auth_dependency.InvalidTokenError("bad")

    monkeypatch.setattr(auth_dependency, "authenticate_user", reject)
    client = TestClient(_build_app(tmp_path, monkeypatch, override_auth=False))

    response = client.get(BASE, headers={"Authorization": "Bearer nope"})
    _assert_problem(response, 401, "INVALID_TOKEN")
    assert response.headers["www-authenticate"] == "Bearer"


def test_real_app_serves_versioned_routes_only():
    from app.main import app

    client = TestClient(app)
    assert client.get("/api/v1/ping").json() == {"ping": "pong"}
    for root in ("/api/v1", "/api/v1/"):
        assert client.get(root).json() == {"service": "ClimaNuvem API", "status": "ok"}
    assert client.get("/ping").status_code == 404
    assert client.get("/").status_code == 404
    assert client.get("/uploads/x/y.jpg").status_code == 404
    assert client.get("/api/v1/analyses").status_code == 401
    assert client.get("/analysis/history").status_code == 404
    assert client.get("/nope").headers["content-type"].startswith("application/problem+json")


def _stored_path(tmp_path, analysis_id):
    engine = create_engine(f"sqlite:///{tmp_path / 'integration.db'}")
    with engine.connect() as conn:
        from sqlalchemy import text
        return conn.execute(text("SELECT image_path FROM analysis WHERE id = :i"), {"i": analysis_id}).scalar()


def test_image_url_format_and_authenticated_image_download(client, tmp_path):
    analysis_id = _upload(client).json()["id"]
    expected = f"/api/v1/analyses/{analysis_id}/image"
    assert client.get(f"{BASE}/{analysis_id}").json()["imageUrl"] == expected
    assert client.get(BASE).json()[0]["imageUrl"] == expected

    response = client.get(expected)
    assert response.status_code == 200
    assert response.headers["content-type"] == "image/jpeg"
    assert response.content == JPG[1]


def test_image_requires_authentication(tmp_path, monkeypatch):
    client = TestClient(_build_app(tmp_path, monkeypatch, override_auth=False))
    _assert_problem(client.get(f"{BASE}/1/image"), 401, "NOT_AUTHENTICATED")


def test_image_not_owned_or_unknown_returns_404(client, tmp_path):
    analysis_id = _upload(client).json()["id"]
    app = client.app
    app.dependency_overrides[get_current_user] = lambda: {"uid": "other", "firebase": {}}
    _assert_problem(client.get(f"{BASE}/{analysis_id}/image"), 404, "ANALYSIS_NOT_FOUND")
    _assert_problem(client.get(f"{BASE}/9999/image"), 404, "ANALYSIS_NOT_FOUND")


def test_image_missing_file_returns_404_image_not_found(client, tmp_path):
    analysis_id = _upload(client).json()["id"]
    for f in (tmp_path / "uploads" / "test-user").iterdir():
        f.unlink()
    _assert_problem(client.get(f"{BASE}/{analysis_id}/image"), 404, "IMAGE_NOT_FOUND")


def test_image_path_traversal_is_rejected(client, tmp_path):
    from sqlalchemy import text

    analysis_id = _upload(client).json()["id"]
    secret = tmp_path / "secret.jpg"
    secret.write_bytes(b"secret")
    engine = create_engine(f"sqlite:///{tmp_path / 'integration.db'}")
    with engine.begin() as conn:
        conn.execute(
            text("UPDATE analysis SET image_path = :p WHERE id = :i"),
            {"p": "/uploads/../secret.jpg", "i": analysis_id},
        )
    _assert_problem(client.get(f"{BASE}/{analysis_id}/image"), 404, "IMAGE_NOT_FOUND")
