from backend.database import init_db, db
from backend.config import settings
from backend.services.llm_router import llm
from tests.conftest import login

BASE = "/api/v1"


def test_pending_cases_cover_threshold_and_seeding_preserves_existing_work(client):
    login(client, "meena")
    cases = client.get(f"{BASE}/cases").json()
    assert len(cases) == 7 and all(c["is_pending"] for c in cases)
    assert sum(c["loan_amount"] < 2500000 for c in cases) == 4
    assert sum(c["loan_amount"] >= 2500000 for c in cases) == 3
    for case in cases:
        if case["loan_amount"] >= 2500000:
            detail = client.get(f"{BASE}/cases/{case['id']}").json()
            assert not detail["intake"]["passed"]
            assert (
                client.post(f"{BASE}/cases/{case['id']}/pipeline", json={}).status_code
                == 422
            )
    with db() as conn:
        conn.execute(
            "UPDATE cases SET gap_notes='Existing analyst work preserved' WHERE id='KF-2026-0892'"
        )
        # Simulate upgrading an existing three-case workspace.
        conn.execute("DELETE FROM documents WHERE case_id >= 'KF-2026-0920'")
        conn.execute("DELETE FROM cases WHERE id >= 'KF-2026-0920'")
    init_db()
    init_db()
    with db() as conn:
        assert conn.execute("SELECT COUNT(*) FROM cases").fetchone()[0] == 7
        assert conn.execute("SELECT COUNT(*) FROM documents").fetchone()[0] == 21
        assert (
            conn.execute("SELECT COUNT(*) FROM agent_telemetry_logs").fetchone()[0]
            == 15
        )
        assert (
            conn.execute(
                "SELECT gap_notes FROM cases WHERE id='KF-2026-0892'"
            ).fetchone()[0]
            == "Existing analyst work preserved"
        )


def test_rm_revision_passes_edited_draft_instructions_and_real_gaps(
    client, monkeypatch
):
    login(client, "vikram")
    captured = {}

    def generate(case_id, agent, system, payload, schema, demo):
        captured.update(payload)
        return {
            "text": "Dear RM, please send the missing October and November GSTR-3B by Friday."
        }

    monkeypatch.setattr(llm, "call", generate)
    response = client.post(
        f"{BASE}/toner/preview",
        json={
            "case_id": "KF-2026-0904",
            "tone": "Polite RM Document Chaser",
            "current_draft": "My manually edited draft",
            "instructions": "Use bullets and request the returns by Friday.",
        },
    )
    assert response.status_code == 200
    assert captured["current_draft"] == "My manually edited draft"
    assert captured["revision_instructions"].endswith("by Friday.")
    assert not captured["intake_checks"]["passed"]
    assert any(
        "2025-10, 2025-11" in c["detail"] for c in captured["intake_checks"]["checks"]
    )
    assert "NO MODEL APPROVES CREDIT" in response.json()["text"]
    assert (
        client.post(
            f"{BASE}/toner/preview", json={"instructions": "x" * 2001}
        ).status_code
        == 422
    )


def test_model_cost_explanation_uses_configured_rates_and_requires_login(
    client, monkeypatch
):
    assert client.get(f"{BASE}/finops/pricing").status_code == 401
    login(client, "farhan")
    monkeypatch.setattr(settings, "gemini_input_inr", 27)
    monkeypatch.setattr(settings, "gemini_output_inr", 225)
    monkeypatch.setattr(settings, "groq_input_inr", 13.5)
    monkeypatch.setattr(settings, "groq_output_inr", 54)
    pricing = client.get(f"{BASE}/finops/pricing").json()
    gemini, groq = pricing["models"]
    assert (10000 * gemini["input_rate"] + 1000 * gemini["output_rate"]) / 1e6 == 0.495
    assert (10000 * groq["input_rate"] + 1000 * groq["output_rate"]) / 1e6 == 0.189
    assert gemini["model"] == settings.gemini_model_name
    assert groq["model"] == settings.groq_model
