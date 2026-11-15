import json
import copy
from concurrent.futures import ThreadPoolExecutor
from pydantic import BaseModel
from backend.database import db, now
from backend.services.agent_graph import demo_extract, graph
from backend.services.intake_rules import citation_issues, reconcile
from backend.services.llm_router import LLMRouter, ProviderUnavailable
from backend.config import settings
from conftest import login

BASE = "/api/v1"
PRIMARY = "KF-2026-0892"
CLEAN = "KF-2026-0911"
BLOCKED = "KF-2026-0904"


def test_sessions_roles_and_csrf(client):
    assert client.get(f"{BASE}/cases").status_code == 401
    login(client, "vikram")
    assert client.get(f"{BASE}/cases").status_code == 200
    assert (
        client.put(
            f"{BASE}/admin/failover-config", json={"simulate_503": True}
        ).status_code
        == 403
    )
    assert (
        client.post(
            f"{BASE}/auth/login",
            json={"persona": "arjun"},
            headers={"Origin": "https://untrusted.example"},
        ).status_code
        == 403
    )
    assert client.post(f"{BASE}/auth/logout").status_code == 200
    assert client.get(f"{BASE}/cases").status_code == 401


def test_seed_intake_pdf_and_finops(client):
    login(client, "meena")
    assert len(client.get(f"{BASE}/cases").json()) == 7
    blocked = client.get(f"{BASE}/cases/{BLOCKED}").json()
    assert not blocked["intake"]["passed"]
    assert any("2025-10, 2025-11" in c["detail"] for c in blocked["intake"]["checks"])
    assert client.post(f"{BASE}/cases/{BLOCKED}/pipeline", json={}).status_code == 422
    primary = client.get(f"{BASE}/cases/{PRIMARY}").json()
    assert primary["intake"]["passed"]
    november = next(r for r in primary["reconciliation"] if r["month"] == "2025-11")
    assert november["gstr3b_variance_pct"] == 12.3
    assert november["flagged"]
    assert client.get(
        f"{BASE}/cases/{PRIMARY}/documents/{primary['documents'][0]['id']}/pdf"
    ).content.startswith(b"%PDF")
    summary = client.get(f"{BASE}/finops/summary").json()
    assert len(summary["logs"]) == 15
    assert round(summary["avg_cost_per_application_inr"], 2) == 4.81
    assert len(summary["providers"]) == 2


def test_citation_validation_binds_value_month_field_page_line(client):
    with db() as conn:
        docs = [
            dict(d)
            for d in conn.execute("SELECT * FROM documents WHERE case_id=?", (PRIMARY,))
        ]
    cells = demo_extract(docs)["cells"]
    assert not citation_issues(cells, docs)
    for mutation in [
        "value",
        "month",
        "field",
        "source_doc",
        "page_number",
        "line_ref",
        "raw_text_quote",
    ]:
        bad = copy.deepcopy(cells)
        if mutation == "value":
            bad[0]["value"] += 1
        elif mutation == "month":
            bad[0]["month"] = "2025-02"
        elif mutation == "field":
            bad[0]["field"] = "debits"
        elif mutation == "source_doc":
            bad[0]["citation"]["source_doc"] = "invented.pdf"
        elif mutation == "page_number":
            bad[0]["citation"]["page_number"] = 99
        elif mutation == "line_ref":
            bad[0]["citation"]["line_ref"] = "L02"
        else:
            bad[0]["citation"]["raw_text_quote"] = "fabricated text"
        assert citation_issues(bad, docs), mutation
    assert citation_issues(cells[:-1] + [cells[0]], docs)


def test_reconciliation_math_and_zero_denominator():
    cells = [
        {"month": "2025-01", "field": f, "value": v}
        for f, v in [("credits", 100), ("gstr1", 90), ("gstr3b", 89.9)]
    ]
    result = reconcile(cells, 10)[0]
    assert result["gstr1_variance_pct"] == 10 and not result["gstr1_flagged"]
    assert result["gstr3b_flagged"]
    cells[0]["value"] = 0
    assert reconcile(cells, 10)[0]["flagged"]
    assert reconcile(cells, 10)[0]["gstr1_variance_pct"] is None


def test_pipeline_pins_prompts_and_has_real_node_events(client):
    login(client, "meena")
    response = client.post(f"{BASE}/cases/{PRIMARY}/pipeline", json={})
    assert response.status_code == 202
    run = client.get(f"{BASE}/cases/{PRIMARY}/runs/latest").json()
    assert run["status"] == "completed", run
    assert [e["node"] for e in run["events"]] == [
        "Orchestrator",
        "Extractor",
        "Critique",
        "Toner",
    ]
    assert run["prompt_versions"] == {
        "extractor_prompt": 1,
        "critique_prompt": 1,
        "toner_prompt": 1,
    }
    detail = client.get(f"{BASE}/cases/{PRIMARY}").json()
    assert len(detail["cells"]) == 60 and detail["verified_count"] == 0
    assert "NO MODEL APPROVES CREDIT" in detail["dossier"]


def test_critique_corrects_once_then_blocks(client, monkeypatch):
    from backend.services.agent_graph import llm

    real_call = llm.call
    calls = []

    def broken_call(case_id, agent, system, payload, schema, demo_factory):
        result = real_call(case_id, agent, system, payload, schema, demo_factory)
        calls.append(agent)
        if agent == "Extractor":
            result["cells"][0]["value"] += 100
        return result

    monkeypatch.setattr(llm, "call", broken_call)
    login(client, "meena")
    client.post(f"{BASE}/cases/{PRIMARY}/pipeline", json={})
    run = client.get(f"{BASE}/cases/{PRIMARY}/runs/latest").json()
    assert run["status"] == "failed"
    assert calls == ["Extractor", "Critique", "Extractor", "Critique"]
    assert "one correction retry" in run["error"]
    # Failed candidates never replace the existing cells.
    assert client.get(f"{BASE}/cases/{PRIMARY}").json()["cells"][0]["value"] == 330000


def test_critique_retry_can_recover(client, monkeypatch):
    from backend.services.agent_graph import llm

    real = llm.call
    attempts = 0

    def once(case_id, agent, system, payload, schema, demo_factory):
        nonlocal attempts
        result = real(case_id, agent, system, payload, schema, demo_factory)
        if agent == "Extractor":
            attempts += 1
            if attempts == 1:
                result["cells"][0]["citation"]["line_ref"] = "L99"
        return result

    monkeypatch.setattr(llm, "call", once)
    login(client, "meena")
    client.post(f"{BASE}/cases/{PRIMARY}/pipeline", json={})
    assert (
        client.get(f"{BASE}/cases/{PRIMARY}/runs/latest").json()["status"]
        == "completed"
    )
    assert attempts == 2


def test_failover_switch_logs_failed_primary_and_successful_backup(client):
    login(client, "farhan")
    assert (
        client.post(
            f"{BASE}/admin/failover-config", json={"simulate_503": True}
        ).status_code
        == 200
    )
    response = client.post(f"{BASE}/toner/preview", json={"case_id": CLEAN})
    assert response.status_code == 200, response.text
    logs = client.get(f"{BASE}/finops/summary").json()["logs"]
    assert logs[0]["provider"] == "groq_backup" and logs[0]["failover_triggered"] == 1
    assert logs[1]["provider"] == "vertex_gemini" and logs[1]["status"] == "error_503"
    assert logs[1]["failover_triggered"] == 1


def test_live_router_retryable_errors_and_nonretryable_errors(client, monkeypatch):
    class Output(BaseModel):
        text: str

    router = LLMRouter()
    monkeypatch.setattr(settings, "demo_mode", False)
    for code in (429, 500, 503):

        def unavailable(*args):
            raise ProviderUnavailable(code)

        monkeypatch.setattr(router, "_vertex", unavailable)
        monkeypatch.setattr(
            router, "_groq", lambda *args: ({"text": "backup"}, (10, 5))
        )
        assert (
            router.call(PRIMARY, "Toner", "prompt", {}, Output, lambda: {})["text"]
            == "backup"
        )

    def timeout(*args):
        raise TimeoutError()

    monkeypatch.setattr(router, "_vertex", timeout)
    assert (
        router.call(PRIMARY, "Toner", "prompt", {}, Output, lambda: {})["text"]
        == "backup"
    )

    def forbidden(*args):
        raise ProviderUnavailable(403)

    monkeypatch.setattr(router, "_vertex", forbidden)
    import pytest

    with pytest.raises(ProviderUnavailable):
        router.call(PRIMARY, "Toner", "prompt", {}, Output, lambda: {})


def test_prompt_version_history_policy_and_reset(client):
    login(client, "meena")
    content = "Always preserve exact citations. Use concise paragraphs. Do not approve credit."
    assert (
        client.put(f"{BASE}/prompts/toner_prompt", json={"content": content}).json()[
            "version"
        ]
        == 2
    )
    assert client.post(f"{BASE}/prompts/reset", json={}).status_code == 200
    data = client.get(f"{BASE}/prompts").json()
    assert data["active"]["toner_prompt"]["version"] == 3
    assert any(p["content"] == content for p in data["history"])
    assert (
        client.put(
            f"{BASE}/policy", json={"gst_variance_threshold_pct": 15}
        ).status_code
        == 403
    )
    login(client, "farhan")
    assert (
        client.put(
            f"{BASE}/policy", json={"gst_variance_threshold_pct": 15}
        ).status_code
        == 200
    )
    assert len(client.get(f"{BASE}/prompts").json()["policy_history"]) == 2
    case = client.get(f"{BASE}/cases/{PRIMARY}").json()
    assert not next(r for r in case["reconciliation"] if r["month"] == "2025-11")[
        "flagged"
    ]


def test_verification_logs_edits_and_correction_rate(client):
    login(client, "meena")
    case = client.get(f"{BASE}/cases/{PRIMARY}").json()
    cell = case["cells"][0]
    body = {
        "cell_id": cell["id"],
        "value": cell["value"] + 10,
        "reason": "Confirmed against original source; manual adjustment recorded",
    }
    assert client.put(f"{BASE}/cases/{PRIMARY}/verify", json=body).status_code == 200
    case = client.get(f"{BASE}/cases/{PRIMARY}").json()
    assert case["correction_rate_pct"] == 1.67
    assert case["verified_count"] == 1
    assert case["audit"][0]["action"] == "cell_verified"
    login(client, "arjun")
    assert client.put(f"{BASE}/cases/{PRIMARY}/verify", json=body).status_code == 403


def test_human_decision_preconditions_identity_immutability(client):
    body = {
        "outcome": "approve",
        "signature": "Arjun Iyer",
        "rationale": "Reviewed complete evidence and all monthly reconciliations; no unresolved policy exceptions.",
    }
    login(client, "meena")
    assert client.post(f"{BASE}/cases/{CLEAN}/decision", json=body).status_code == 403
    login(client, "arjun")
    assert (
        client.post(
            f"{BASE}/cases/{CLEAN}/decision", json={**body, "rationale": " " * 40}
        ).status_code
        == 422
    )
    assert client.post(f"{BASE}/cases/{PRIMARY}/decision", json=body).status_code == 422
    assert (
        client.post(
            f"{BASE}/cases/{CLEAN}/decision", json={**body, "signature": "Model"}
        ).status_code
        == 422
    )
    assert client.post(f"{BASE}/cases/{CLEAN}/decision", json=body).status_code == 200
    assert client.post(f"{BASE}/cases/{CLEAN}/decision", json=body).status_code == 409
    login(client, "meena")
    assert client.post(f"{BASE}/cases/{CLEAN}/pipeline", json={}).status_code == 409
    case = client.get(f"{BASE}/cases/{CLEAN}").json()
    assert case["decision"]["signature"] == "Arjun Iyer"
    pdf = client.get(f"{BASE}/cases/{CLEAN}/dossier.pdf")
    import fitz

    with fitz.open(stream=pdf.content, filetype="pdf") as doc:
        assert len(doc) == 1
        assert "Arjun Iyer" in doc[0].get_text()


def test_scanned_upload_invalidates_extractions_and_signed_docs_locked(client):
    login(client, "vikram")
    case = client.get(f"{BASE}/cases/{BLOCKED}").json()
    scan = next(d for d in case["documents"] if d["kind"] == "bank")
    pdf = client.get(f"{BASE}/cases/{BLOCKED}/documents/{scan['id']}/pdf").content
    result = client.post(
        f"{BASE}/cases/{PRIMARY}/documents",
        data={"kind": "bank"},
        files={"file": ("scan.pdf", pdf, "application/pdf")},
    )
    assert result.status_code == 200
    assert not result.json()["native_text"]
    updated = client.get(f"{BASE}/cases/{PRIMARY}").json()
    assert len(updated["cells"]) == 0 and not updated["intake"]["passed"]


def test_live_mode_disables_persona_switch_and_fails_closed(client, monkeypatch):
    monkeypatch.setattr(settings, "demo_mode", False)
    monkeypatch.setattr(settings, "auth_mode", "iap")
    monkeypatch.setattr(settings, "iap_audience", "")
    assert (
        client.post(f"{BASE}/auth/login", json={"persona": "arjun"}).status_code == 403
    )
    assert client.get(f"{BASE}/cases").status_code == 503


def test_missing_citation_schema_enters_single_correction_loop(client, monkeypatch):
    from backend.services.agent_graph import llm
    from backend.models import Extraction

    real = llm.call
    attempts = 0

    def missing_citation(case_id, agent, system, payload, schema, demo_factory):
        nonlocal attempts
        if agent == "Extractor":
            attempts += 1
            result = demo_factory()
            if attempts == 1:
                del result["cells"][0]["citation"]
                # Same Pydantic validation used by both production providers.
                return Extraction.model_validate(result).model_dump()
        return real(case_id, agent, system, payload, schema, demo_factory)

    monkeypatch.setattr(llm, "call", missing_citation)
    login(client, "meena")
    client.post(f"{BASE}/cases/{PRIMARY}/pipeline", json={})
    run = client.get(f"{BASE}/cases/{PRIMARY}/runs/latest").json()
    assert run["status"] == "completed", run
    assert attempts == 2
    assert len([e for e in run["events"] if e["node"] == "Critique"]) == 2


def test_signed_dossier_snapshots_policy_and_analyst_corrections(client):
    login(client, "meena")
    case = client.get(f"{BASE}/cases/{CLEAN}").json()
    cell = next(
        c for c in case["cells"] if c["month"] == "2025-11" and c["field"] == "credits"
    )
    assert (
        client.put(
            f"{BASE}/cases/{CLEAN}/verify",
            json={
                "cell_id": cell["id"],
                "value": 2000000,
                "reason": "Human source correction with recorded rationale",
            },
        ).status_code
        == 200
    )
    login(client, "arjun")
    assert (
        client.post(
            f"{BASE}/cases/{CLEAN}/decision",
            json={
                "outcome": "return_to_rm",
                "signature": "Arjun Iyer",
                "rationale": "Human correction increases November variance; return to RM for documented clarification.",
            },
        ).status_code
        == 200
    )
    before = client.get(f"{BASE}/cases/{CLEAN}").json()
    assert "bank INR 2,000,000.00" in before["dossier"]
    assert "Policy tolerance: 10.0%" in before["dossier"]
    assert (
        client.put(
            f"{BASE}/policy", json={"gst_variance_threshold_pct": 50}
        ).status_code
        == 200
    )
    after = client.get(f"{BASE}/cases/{CLEAN}").json()
    assert before["dossier"] == after["dossier"]
    audit_payload = json.loads(
        next(e for e in after["audit"] if e["action"] == "human_credit_decision")[
            "payload"
        ]
    )
    assert audit_payload["policy"]["gst_variance_threshold_pct"] == 10
    assert all(c["citation"] for c in audit_payload["cells"])
