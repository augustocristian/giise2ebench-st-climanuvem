import os

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.infrastructure.database.bootstrap import bootstrap_database
from app.infrastructure.database.database import get_db
from app.infrastructure.queue import analysis_queue
from app.presentation.dependencies.auth_dependency import get_current_user
from app.presentation.routes import analysis_routes


def _drain_analysis_queue():
    while not analysis_queue.empty():
        analysis_queue.get_nowait()
        analysis_queue.task_done()


def _build_test_client(tmp_path, monkeypatch):
    db_path = tmp_path / "integration.db"
    engine = create_engine(
        f"sqlite:///{db_path}",
        connect_args={"check_same_thread": False},
    )
    bootstrap_database(engine)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    uploads_dir = tmp_path / "uploads"
    monkeypatch.setattr(analysis_routes, "UPLOADS_BASE_DIR", str(uploads_dir))

    app = FastAPI()
    app.include_router(analysis_routes.router, prefix="/analysis")

    def override_user():
        return {
            "uid": "test-user",
            "firebase": {"sign_in_provider": "custom"},
        }

    def override_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_current_user] = override_user
    app.dependency_overrides[get_db] = override_db

    return TestClient(app)


def test_upload_history_cancel_and_delete_flow(tmp_path, monkeypatch):
    _drain_analysis_queue()
    client = _build_test_client(tmp_path, monkeypatch)

    upload_response = client.post(
        "/analysis/upload",
        files={"file": ("cloud.jpg", b"\xff\xd8\xff\xe0image-bytes", "image/jpeg")},
        data={"location": "Gijon", "latitude": "43.5", "longitude": "-5.6"},
    )

    assert upload_response.status_code == 200
    analysis_id = upload_response.json()["analysis_id"]

    history_response = client.get("/analysis/history")
    assert history_response.status_code == 200
    history = history_response.json()
    assert len(history) == 1
    assert history[0]["id"] == str(analysis_id)
    assert history[0]["status"] == "analyzing"
    assert history[0]["location"] == "Gijon"

    cancel_response = client.patch(f"/analysis/{analysis_id}/cancel")
    assert cancel_response.status_code == 200

    delete_response = client.delete(f"/analysis/{analysis_id}")
    assert delete_response.status_code == 200

    final_history_response = client.get("/analysis/history")
    assert final_history_response.status_code == 200
    assert final_history_response.json() == []

    user_uploads_dir = tmp_path / "uploads" / "test-user"
    assert not user_uploads_dir.exists() or not any(user_uploads_dir.iterdir())
