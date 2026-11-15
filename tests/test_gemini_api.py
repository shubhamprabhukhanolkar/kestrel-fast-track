from types import SimpleNamespace
import pytest
from pydantic import BaseModel, SecretStr, ValidationError
from backend.config import settings, Settings
from backend.database import db
from backend.services.llm_router import llm, ProviderUnavailable
from backend.services.readiness import readiness
from test_live_runtime import live_login, mocked_vertex, CASE, BASE
from backend.services.jobs import execute


class Output(BaseModel):
    text: str


def use_api(monkeypatch):
    monkeypatch.setattr(settings, "primary_provider", "gemini_api")
    monkeypatch.setattr(settings, "allow_nonregional_inference", True)
    monkeypatch.setattr(
        settings, "gemini_api_key", SecretStr("test-key-never-valid-for-inference")
    )


def test_api_selection_requires_explicit_boundary_acknowledgement():
    with pytest.raises(ValidationError):
        Settings(
            _env_file=None,
            primary_provider="gemini_api",
            allow_nonregional_inference=False,
        )
    config = Settings(
        _env_file=None, primary_provider="gemini_api", allow_nonregional_inference=True
    )
    assert config.gcp_region == "asia-south1"


def test_api_sdk_uses_key_without_vertex_identity_and_masks_key(client, monkeypatch):
    live_login(client, monkeypatch)
    use_api(monkeypatch)
    from google import genai

    captured = {}

    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)
            self.models = SimpleNamespace(
                generate_content=lambda **kwargs: SimpleNamespace(
                    text='{"text":"actual transport result"}',
                    usage_metadata=SimpleNamespace(
                        prompt_token_count=10,
                        candidates_token_count=5,
                        thoughts_token_count=3,
                    ),
                )
            )

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

    monkeypatch.setattr(genai, "Client", Client)

    def no_fixture():
        raise AssertionError("Offline fixture was used")

    result = llm.call(CASE, "Toner", "system", {}, Output, no_fixture)
    assert result["text"] == "actual transport result"
    assert captured["vertexai"] is False
    assert "project" not in captured and "location" not in captured
    assert "test-key-never-valid-for-inference" not in repr(settings)
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM agent_telemetry_logs ORDER BY id DESC LIMIT 1"
        ).fetchone()
        assert row["provider"] == "gemini_api"
        assert row["model_name"] == settings.gemini_model_name
        assert row["input_tokens"] == 10 and row["output_tokens"] == 8


def test_api_transient_failure_routes_to_backup_and_labels_telemetry(
    client, monkeypatch
):
    live_login(client, monkeypatch)
    use_api(monkeypatch)

    def down(*args):
        raise ProviderUnavailable(429)

    monkeypatch.setattr(llm, "_gemini_api", down)
    monkeypatch.setattr(
        llm, "_groq", lambda *args: ({"text": "backup response"}, (4, 2))
    )
    assert (
        llm.call(CASE, "Toner", "system", {}, Output, lambda: {})["text"]
        == "backup response"
    )
    with db() as conn:
        rows = list(
            conn.execute("SELECT * FROM agent_telemetry_logs ORDER BY id DESC LIMIT 2")
        )
        assert (
            rows[0]["provider"] == "groq_backup" and rows[0]["failover_triggered"] == 1
        )
        assert rows[1]["provider"] == "gemini_api" and rows[1]["status"] == "error_429"


def test_api_missing_key_fails_closed_without_vertex_or_mock_fallback(
    client, monkeypatch
):
    live_login(client, monkeypatch)
    use_api(monkeypatch)
    monkeypatch.setattr(settings, "gemini_api_key", SecretStr(""))
    monkeypatch.setattr(settings, "gemini_secret_name", "")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY"):
        llm.call(
            CASE,
            "Toner",
            "system",
            {},
            Output,
            lambda: (_ for _ in ()).throw(AssertionError("Simulated response")),
        )


def test_api_health_reports_hosting_separately_from_inference(client, monkeypatch):
    use_api(monkeypatch)
    health = client.get(BASE + "/health").json()
    assert health["region"] == "asia-south1"
    assert health["primary_provider"] == "gemini_api"
    assert health["model"] == settings.gemini_model_name
    assert health["vertex_location"] is None
    assert health["inference_location"] == "provider-managed"


def test_full_queue_uses_api_transport_for_all_agents(client, monkeypatch):
    live_login(client, monkeypatch)
    use_api(monkeypatch)
    healthy = mocked_vertex(monkeypatch)
    monkeypatch.setattr(llm, "_gemini_api", healthy)
    run_id = client.post(f"{BASE}/cases/{CASE}/pipeline", json={}).json()["run_id"]
    execute(run_id)
    run = client.get(f"{BASE}/cases/{CASE}/runs/latest").json()
    assert run["status"] == "completed", run
    with db() as conn:
        rows = list(
            conn.execute(
                "SELECT * FROM agent_telemetry_logs WHERE mode='live_estimate'"
            )
        )
        assert len(rows) == 3
        assert all(row["provider"] == "gemini_api" for row in rows)


def test_api_readiness_requires_current_model_not_vertex_adc(client, monkeypatch):
    live_login(client, monkeypatch, "farhan")
    use_api(monkeypatch)
    healthy = mocked_vertex(monkeypatch)
    monkeypatch.setattr(llm, "_gemini_api", healthy)
    monkeypatch.setattr(llm, "_groq", healthy)
    llm.probe()
    result = readiness()
    assert result["ready"]
    assert not any(c["key"] == "vertex_credentials" for c in result["checks"])
    monkeypatch.setattr(settings, "gemini_model_name", "gemini-other-model")
    assert not readiness()["ready"]
