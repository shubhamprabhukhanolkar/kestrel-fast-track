import json
import pytest
from pydantic import BaseModel, ValidationError
from backend.config import settings, Settings
from backend.database import db, now, init_db
from backend.services.passwords import hash_password, verify_password
from backend.services.llm_router import llm, ProviderUnavailable
from backend.services.agent_graph import demo_extract, run_pipeline
from backend.services.jobs import execute, claim, after
from backend.services.document_index import extract_periods, cited_lines
from backend.services.intake_rules import citation_issues
from backend.services.readiness import validate_production
from backend.persistence import postgres_sql

CASE = "KF-2026-0892"
BASE = "/api/v1"
PASSWORD = "A-test-only-password-2026"


def live_login(client, monkeypatch, persona="meena"):
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "auth_mode", "password")
    with db() as conn:
        conn.execute(
            "INSERT INTO users(persona,password_hash,updated_at) VALUES(?,?,?) ON CONFLICT(persona) DO UPDATE SET password_hash=excluded.password_hash",
            (persona, hash_password(PASSWORD), now()),
        )
    response = client.post(
        f"{BASE}/auth/login", json={"persona": persona, "password": PASSWORD}
    )
    assert response.status_code == 200


def test_defaults_are_live_and_region_is_locked():
    config = Settings(_env_file=None)
    assert config.demo_mode is False
    assert config.auth_mode == "password"
    with pytest.raises(ValidationError):
        Settings(_env_file=None, vertex_location="global")


def test_password_auth_and_offline_session_cannot_cross_into_live(client, monkeypatch):
    client.post(f"{BASE}/auth/login", json={"persona": "arjun"})
    monkeypatch.setattr(settings, "auth_mode", "password")
    monkeypatch.setattr(settings, "demo_mode", False)
    assert client.get(f"{BASE}/cases").status_code == 401
    assert (
        client.post(f"{BASE}/auth/login", json={"persona": "arjun"}).status_code == 401
    )
    live_login(client, monkeypatch)
    assert client.get(f"{BASE}/auth/me").json()["persona"] == "meena"
    assert client.post(f"{BASE}/admin/provider-check", json={}).status_code == 403
    assert (
        client.post(
            f"{BASE}/cases/KF-2026-0911/decision",
            json={
                "outcome": "approve",
                "signature": "Arjun Iyer",
                "rationale": "Verified human credit assessment with sufficient rationale.",
            },
        ).status_code
        == 403
    )


def test_password_lockout_persists_failed_attempts(client, monkeypatch):
    live_login(client, monkeypatch)
    for _ in range(5):
        assert (
            client.post(
                f"{BASE}/auth/login", json={"persona": "meena", "password": "incorrect"}
            ).status_code
            == 401
        )
    assert (
        client.post(
            f"{BASE}/auth/login", json={"persona": "meena", "password": PASSWORD}
        ).status_code
        == 429
    )
    with db() as conn:
        assert (
            conn.execute(
                "SELECT failures FROM login_attempts WHERE identity=?", ("meena",)
            ).fetchone()[0]
            == 5
        )
    assert verify_password(PASSWORD, hash_password(PASSWORD))
    assert not verify_password("incorrect", hash_password(PASSWORD))


def mocked_vertex(monkeypatch):
    with db() as conn:
        docs = [
            dict(r)
            for r in conn.execute("SELECT * FROM documents WHERE case_id=?", (CASE,))
        ]

    def provider(system, payload, schema):
        if schema.__name__ == "Extraction":
            result = demo_extract(docs)
        elif schema.__name__ == "CritiqueResult":
            result = {"issues": []}
        elif schema.__name__ == "Probe":
            result = {"status": "ok"}
        else:
            result = {
                "text": "Grounded provider test response. NO MODEL APPROVES CREDIT."
            }
        return schema.model_validate(result).model_dump(), (100, 50)

    monkeypatch.setattr(llm, "_vertex", provider)
    return provider


def test_live_pipeline_uses_durable_queue_and_only_live_telemetry(client, monkeypatch):
    live_login(client, monkeypatch)
    mocked_vertex(monkeypatch)
    response = client.post(f"{BASE}/cases/{CASE}/pipeline", json={})
    assert response.status_code == 202
    run_id = response.json()["run_id"]
    assert client.get(f"{BASE}/cases/{CASE}/runs/latest").json()["status"] == "queued"
    assert client.post(f"{BASE}/cases/{CASE}/pipeline", json={}).status_code == 409
    execute(run_id)
    run = client.get(f"{BASE}/cases/{CASE}/runs/latest").json()
    assert run["status"] == "completed", run
    assert run["execution_mode"] == "live" and run["attempts"] == 1
    assert execute(run_id) is None
    summary = client.get(f"{BASE}/finops/summary").json()
    assert summary["attempts"] == 3
    assert all(r["mode"] == "live_estimate" for r in summary["logs"])
    assert len(client.get(f"{BASE}/cases/{CASE}").json()["cells"]) == 60


def test_missing_live_credentials_never_invoke_simulated_fallback(client, monkeypatch):
    live_login(client, monkeypatch)

    class Output(BaseModel):
        text: str

    def unavailable(*args):
        raise RuntimeError("Credentials unavailable")

    monkeypatch.setattr(llm, "_vertex", unavailable)

    def forbidden_factory():
        raise AssertionError("Simulation was invoked in live mode")

    with pytest.raises(RuntimeError, match="Credentials unavailable"):
        llm.call(CASE, "Toner", "system", {}, Output, forbidden_factory)


def test_live_queue_retries_transient_failure_and_recovers(client, monkeypatch):
    live_login(client, monkeypatch)
    healthy = mocked_vertex(monkeypatch)

    def down(*args):
        raise ProviderUnavailable(503)

    monkeypatch.setattr(llm, "_vertex", down)
    monkeypatch.setattr(llm, "_groq", down)
    run_id = client.post(f"{BASE}/cases/{CASE}/pipeline", json={}).json()["run_id"]
    execute(run_id)
    run = client.get(f"{BASE}/cases/{CASE}/runs/latest").json()
    assert run["status"] == "queued" and run["attempts"] == 1
    with db() as conn:
        conn.execute(
            "UPDATE runs SET next_attempt_at=? WHERE id=?", (after(-1), run_id)
        )
    monkeypatch.setattr(llm, "_vertex", healthy)
    execute(run_id)
    assert (
        client.get(f"{BASE}/cases/{CASE}/runs/latest").json()["status"] == "completed"
    )


def test_restart_recovery_preserves_live_leases_and_fences_stale_worker(
    client, monkeypatch
):
    live_login(client, monkeypatch)
    run_id = client.post(f"{BASE}/cases/{CASE}/pipeline", json={}).json()["run_id"]
    first = claim(run_id)
    init_db()
    assert claim(run_id) is None
    with db() as conn:
        conn.execute("UPDATE runs SET lease_until=? WHERE id=?", (after(-1), run_id))
    second = claim(run_id)
    assert first["owner"] != second["owner"]
    run_pipeline(CASE, run_id, "Meena Pillai", execution_token=first["owner"])
    with db() as conn:
        row = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
        assert row["owner"] == second["owner"] and row["status"] == "running"


def test_provider_checks_meter_real_paths_and_exclude_seed_metrics(client, monkeypatch):
    live_login(client, monkeypatch, "farhan")
    healthy = mocked_vertex(monkeypatch)
    monkeypatch.setattr(llm, "_groq", healthy)
    result = client.post(f"{BASE}/admin/provider-check", json={})
    assert result.status_code == 200
    assert all(r["connected"] for r in result.json()["providers"])
    summary = client.get(f"{BASE}/finops/summary").json()
    assert summary["attempts"] == 2 and summary["application_count"] == 0
    assert summary["avg_cost_per_application_inr"] == 0


def test_production_profile_refuses_ephemeral_or_simulated_configuration(
    client, monkeypatch
):
    monkeypatch.setattr(settings, "app_env", "production")
    with pytest.raises(RuntimeError, match="Production requires"):
        validate_production()


def test_real_pdf_periods_and_contiguous_multiline_citations(client):
    assert extract_periods("Period November 2025; 31/12/2025; 2025-10-05") == [
        "2025-10",
        "2025-11",
        "2025-12",
    ]
    assert (
        cited_lines(
            [["Return period: November 2025", "Total taxable value", "12,45,340.00"]],
            1,
            "L02-L03",
        )
        == "Total taxable value\n12,45,340.00"
    )
    with db() as conn:
        docs = [
            dict(r)
            for r in conn.execute("SELECT * FROM documents WHERE case_id=?", (CASE,))
        ]
    cells = demo_extract(docs)["cells"]
    doc = next(d for d in docs if d["kind"] == "gstr3b")
    pages = json.loads(doc["pages"])
    pages[10] = ["Return period: November 2025", "Total taxable value", "12,45,340.00"]
    doc["pages"] = json.dumps(pages)
    cell = next(c for c in cells if c["month"] == "2025-11" and c["field"] == "gstr3b")
    cell["citation"].update(
        line_ref="L02-L03", raw_text_quote="Total taxable value\n12,45,340.00"
    )
    assert citation_issues(cells, docs) == []
    cell["value"] += 0.1
    assert citation_issues(cells, docs)


def test_postgres_sql_compilation_uses_bound_parameters_and_portable_types():
    sql, values = postgres_sql(
        "SELECT * FROM cases WHERE id=? AND business=?", (CASE, "O'Reilly")
    )
    assert sql == "SELECT * FROM cases WHERE id=:p0 AND business=:p1"
    assert values["p1"] == "O'Reilly"
    assert postgres_sql("INSERT OR IGNORE INTO settings VALUES(?,?)", ("k", "v"))[
        0
    ].endswith("ON CONFLICT DO NOTHING")
    assert (
        "BIGSERIAL"
        in postgres_sql("CREATE TABLE t(id INTEGER PRIMARY KEY,value REAL)")[0]
    )


def test_internal_task_endpoint_rejects_unauthenticated_dispatch(client, monkeypatch):
    monkeypatch.setattr(settings, "task_backend", "cloud_tasks")
    monkeypatch.setattr(settings, "service_url", "https://workbench.example")
    monkeypatch.setattr(
        settings, "task_service_account", "tasks@example.iam.gserviceaccount.com"
    )
    assert (
        client.post(
            f"{BASE}/internal/tasks/pipeline", json={"run_id": "untrusted"}
        ).status_code
        == 401
    )
