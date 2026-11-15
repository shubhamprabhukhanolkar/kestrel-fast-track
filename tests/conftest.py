import pytest
import os
import uuid
from fastapi.testclient import TestClient
from backend.config import settings
from backend.main import app


@pytest.fixture(
    params=["sqlite", "postgresql"]
    if os.environ.get("TEST_DATABASE_URL")
    else ["sqlite"]
)
def client(tmp_path, monkeypatch, request):
    monkeypatch.setattr(settings, "database_path", str(tmp_path / "test.db"))
    monkeypatch.setattr(settings, "document_dir", str(tmp_path / "documents"))
    monkeypatch.setattr(settings, "demo_mode", True)
    monkeypatch.setattr(settings, "auth_mode", "demo")
    monkeypatch.setattr(settings, "seed_telemetry", True)
    monkeypatch.setattr(settings, "database_url", "")
    monkeypatch.setattr(settings, "documents_bucket", "")
    monkeypatch.setattr(settings, "enable_job_worker", False)
    monkeypatch.setattr(settings, "primary_provider", "vertex_gemini")
    schema = None
    admin_engine = None
    if request.param == "postgresql":
        from sqlalchemy import create_engine, text
        from sqlalchemy.engine import make_url

        schema = "test_" + uuid.uuid4().hex
        admin_engine = create_engine(os.environ["TEST_DATABASE_URL"])
        with admin_engine.begin() as conn:
            conn.execute(text(f"CREATE SCHEMA {schema}"))
        url = (
            make_url(os.environ["TEST_DATABASE_URL"])
            .update_query_dict({"options": "-csearch_path=" + schema})
            .render_as_string(hide_password=False)
        )
        monkeypatch.setattr(settings, "database_url", url)
    try:
        with TestClient(app) as client:
            yield client
    finally:
        if schema:
            from backend.persistence import engine

            engine(settings.database_url).dispose()
            with admin_engine.begin() as conn:
                conn.execute(text(f"DROP SCHEMA {schema} CASCADE"))
            admin_engine.dispose()


def login(client, persona):
    response = client.post("/api/v1/auth/login", json={"persona": persona})
    assert response.status_code == 200
    return response.json()
