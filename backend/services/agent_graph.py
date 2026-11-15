import json
from typing import TypedDict
from pydantic import BaseModel, Field, ValidationError
from langgraph.graph import StateGraph, START, END
from backend.database import db, active_prompts, policy, now, audit
from backend.models import Extraction, Memo
from backend.services.intake_rules import intake_check, reconcile, citation_issues
from backend.services.llm_router import llm
from backend.config import settings
from backend.services.evidence_payload import (
    critique_payload,
    compact_cells,
    compact_reconciliation,
)


class CritiqueResult(BaseModel):
    issues: list[str] = Field(default_factory=list)


class PipelineState(TypedDict, total=False):
    case_id: str
    run_id: str
    case: dict
    documents: list[dict]
    prompts: dict
    threshold: float
    cells: list[dict]
    issues: list[str]
    extraction_issues: list[str]
    reconciliation: list[dict]
    attempts: int
    dossier: str
    execution_token: str


def event(state, node, message):
    with db() as conn:
        row = conn.execute(
            "SELECT * FROM runs WHERE id=?", (state["run_id"],)
        ).fetchone()
        if state.get("execution_token") and (
            row["owner"] != state["execution_token"]
            or row["status"] != "running"
            or row["lease_until"] < now()
        ):
            raise RuntimeError("Execution lease lost")
        entries = json.loads(row["events"])
        entries.append({"node": node, "message": message, "timestamp": now()})
        conn.execute(
            "UPDATE runs SET events=? WHERE id=?",
            (json.dumps(entries), state["run_id"]),
        )


def source_payload(documents):
    return [
        {
            "source_doc": d["name"],
            "kind": d["kind"],
            "pages": [
                {
                    "page_number": p + 1,
                    "lines": [
                        {"line_ref": f"L{n + 1:02d}", "text": line}
                        for n, line in enumerate(lines)
                    ],
                }
                for p, lines in enumerate(json.loads(d["pages"]))
            ],
        }
        for d in documents
    ]


def demo_extract(documents):
    import re

    cells = []
    for doc in documents:
        for page_idx, lines in enumerate(json.loads(doc["pages"])):
            for line_idx, line in enumerate(lines):
                match = re.fullmatch(
                    r"(\d{4}-\d{2}) (credits|debits|average_balance|gstr1|gstr3b) INR ([\d.]+)",
                    line,
                )
                if match:
                    month, field, amount = match.groups()
                    cells.append(
                        {
                            "month": month,
                            "field": field,
                            "value": float(amount),
                            "citation": {
                                "source_doc": doc["name"],
                                "page_number": page_idx + 1,
                                "line_ref": f"L{line_idx + 1:02d}",
                                "raw_text_quote": line,
                                "confidence": 0.99,
                            },
                        }
                    )
    return {"cells": cells}


def OrchestratorNode(state):
    with db() as conn:
        case = dict(
            conn.execute(
                "SELECT * FROM cases WHERE id=?", (state["case_id"],)
            ).fetchone()
        )
        documents = [
            dict(d)
            for d in conn.execute(
                "SELECT * FROM documents WHERE case_id=?", (state["case_id"],)
            )
        ]
        if conn.execute(
            "SELECT 1 FROM decisions WHERE case_id=?", (state["case_id"],)
        ).fetchone():
            raise ValueError("Signed cases are locked")
        prompts = active_prompts(conn)
        threshold = policy(conn)["gst_variance_threshold_pct"]
        conn.execute(
            "UPDATE runs SET prompt_versions=? WHERE id=?",
            (
                json.dumps({k: p["version"] for k, p in prompts.items()}),
                state["run_id"],
            ),
        )
    if not intake_check(case, documents)["passed"]:
        raise ValueError(
            "Intake preconditions failed; request complete native PDFs before extraction"
        )
    event(
        state,
        "Orchestrator",
        "Step 1 passed. Prompt versions and threshold pinned; deterministic route selected.",
    )
    return {
        "case": case,
        "documents": documents,
        "prompts": prompts,
        "threshold": threshold,
        "attempts": 0,
    }


def ExtractorAgentNode(state):
    event(
        state,
        "Extractor",
        f"Step 2: extracting 60 cited fields; attempt {state['attempts'] + 1}",
    )
    try:
        payload = {"documents": source_payload(state["documents"])}
        if state.get("issues"):
            payload["correction_instructions"] = state["issues"]
        result = llm.call(
            state["case_id"],
            "Extractor",
            state["prompts"]["extractor_prompt"]["content"],
            payload,
            Extraction,
            lambda: demo_extract(state["documents"]),
        )
        return {
            "cells": result["cells"],
            "extraction_issues": [],
            "attempts": state["attempts"] + 1,
        }
    except ValidationError as exc:
        issues = [
            f"Missing or invalid structured extraction: {e['loc']} ({e['type']})"
            for e in exc.errors()[:10]
        ]
        return {
            "cells": [],
            "extraction_issues": issues,
            "attempts": state["attempts"] + 1,
        }


def CritiqueAgentNode(state):
    deterministic = state.get("extraction_issues", []) + citation_issues(
        state["cells"], state["documents"]
    )
    reconciliation = reconcile(state["cells"], state["threshold"])
    result = llm.call(
        state["case_id"],
        "Critique",
        state["prompts"]["critique_prompt"]["content"],
        critique_payload(
            state["cells"],
            state["documents"],
            reconciliation,
            state["threshold"],
            deterministic,
        ),
        CritiqueResult,
        lambda: {"issues": deterministic},
    )
    issues = list(dict.fromkeys(deterministic + result["issues"]))
    event(
        state,
        "Critique",
        f"Citation QA: {len(issues)} issues. Deterministic reconciliation: {sum(r['flagged'] for r in reconciliation)} exception month(s).",
    )
    return {"issues": issues, "reconciliation": reconciliation}


def critique_route(state):
    if state["issues"]:
        if state["attempts"] < 2:
            return "Extractor"
        raise ValueError(
            "Critique blocked output after one correction retry: "
            + "; ".join(state["issues"][:5])
        )
    return "Toner"


def demo_memo(case, reconciliation, tone):
    exceptions = [r for r in reconciliation if r["flagged"]]
    if tone == "Polite RM Document Chaser":
        return {
            "text": f"Dear Vikram,\nPlease obtain the outstanding native PDF documents or clarification for {case['business']} ({case['id']}).\n{case['gap_notes']}\nPlease link each clarification to its source before analyst verification. Thank you.\nNO MODEL APPROVES CREDIT. Named human credit manager judgement required."
        }
    heading = (
        "CREDIT RISK REVIEW — EVIDENCE DOSSIER"
        if tone == "Strict CRO Regulatory Memo"
        else "ANALYST EVIDENCE DOSSIER"
    )
    details = (
        "\n".join(
            f"{r['month']}: bank INR {r['bank_credits']:,.2f}; GSTR-1 variance {r['gstr1_variance_pct']}%; GSTR-3B variance {r['gstr3b_variance_pct']}%. Exception requires human assessment."
            for r in exceptions
        )
        or "All twelve months are within the configured reconciliation tolerance."
    )
    return {
        "text": f"{heading}\n{case['id']} | {case['business']} | {case['city']}\nRequested facility: INR {case['loan_amount']:,.0f}. Twelve months Jan–Dec 2025 reviewed.\n{details}\nRM notes (unverified explanation): {case['gap_notes']}\nEvidence anchors: HDFC_Bank_12M_Statement.pdf p.11 L01; GSTR1_12M_Returns.pdf p.11 L01; GSTR3B_12M_Returns.pdf p.11 L01.\nAnalyst verification and explicit exception rationale required.\nNO MODEL APPROVES CREDIT. Named human credit manager judgement required."
    }


def format_memo(
    case,
    cells,
    reconciliation,
    prompts,
    tone,
    *,
    instructions="",
    current_draft="",
    intake=None,
):
    result = llm.call(
        case["id"],
        "Toner",
        prompts["toner_prompt"]["content"],
        {
            "case": {
                k: case[k]
                for k in ("id", "business", "city", "loan_amount", "gap_notes")
            },
            "grounded_findings": compact_cells(cells, include_quotes=False),
            "analyst_verified_count": sum(bool(c.get("verified_by")) for c in cells),
            "reconciliation": compact_reconciliation(reconciliation),
            "instructions": "Expand source document aliases in any citation. Do not imply human verification unless analyst_verified_count equals the number of cells.",
            "tone": tone,
            "revision_instructions": instructions,
            "current_draft": current_draft,
            "intake_checks": intake,
            "drafting_rules": "Apply the operator's style and wording instructions to the current draft, if provided. Return the complete revised draft. Preserve actual document gaps, facility eligibility and unresolved exceptions. Do not invent facts, claim human verification or approve credit. A chaser is an unsent communication draft, not a completed credit review.",
        },
        Memo,
        lambda: demo_memo(case, reconciliation, tone),
    )
    text = result["text"]
    if "NO MODEL APPROVES CREDIT" not in text:
        text += "\nNO MODEL APPROVES CREDIT. Named human credit manager signature and rationale required."
    return text


def TonerAgentNode(state):
    event(
        state,
        "Toner",
        "Formatting evidence dossier. Analyst verification and human judgement remain pending.",
    )
    dossier = format_memo(
        state["case"],
        state["cells"],
        state["reconciliation"],
        state["prompts"],
        "Concise Analyst Dossier",
    )
    return {"dossier": dossier}


builder = StateGraph(PipelineState)
for name, node in [
    ("Orchestrator", OrchestratorNode),
    ("Extractor", ExtractorAgentNode),
    ("Critique", CritiqueAgentNode),
    ("Toner", TonerAgentNode),
]:
    builder.add_node(name, node)
builder.add_edge(START, "Orchestrator")
builder.add_edge("Orchestrator", "Extractor")
builder.add_edge("Extractor", "Critique")
builder.add_conditional_edges(
    "Critique", critique_route, {"Extractor": "Extractor", "Toner": "Toner"}
)
builder.add_edge("Toner", END)
graph = builder.compile()


def run_pipeline(case_id, run_id, actor, execution_token=None):
    try:
        result = graph.invoke(
            {"case_id": case_id, "run_id": run_id, "execution_token": execution_token},
            {"recursion_limit": 12},
        )
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if execution_token and (
                run["owner"] != execution_token
                or run["status"] != "running"
                or run["lease_until"] < now()
            ):
                return
            conn.execute("DELETE FROM cells WHERE case_id=?", (case_id,))
            for c in result["cells"]:
                conn.execute(
                    "INSERT INTO cells(case_id,month,field,value,original_value,citation) VALUES(?,?,?,?,?,?)",
                    (
                        case_id,
                        c["month"],
                        c["field"],
                        c["value"],
                        c["value"],
                        json.dumps(c["citation"]),
                    ),
                )
            conn.execute(
                "UPDATE cases SET status='awaiting_verification',dossier=?,revision=revision+1 WHERE id=?",
                (result["dossier"], case_id),
            )
            conn.execute(
                "UPDATE runs SET status='completed',finished_at=? WHERE id=?",
                (now(), run_id),
            )
            audit(
                conn,
                case_id,
                actor,
                "pipeline_completed",
                {
                    "run_id": run_id,
                    "prompt_versions": {
                        k: p["version"] for k, p in result["prompts"].items()
                    },
                    "threshold_pct": result["threshold"],
                },
            )
    except Exception as exc:
        # Keep raw provider errors out of API responses; they may contain request data.
        safe = (
            str(exc)[:500]
            if isinstance(exc, ValueError)
            else f"{type(exc).__name__}: pipeline failed; check provider credentials, quota and service health"
        )
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            run = conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            if execution_token and (
                run["owner"] != execution_token or run["status"] != "running"
            ):
                return
            retry = (
                bool(execution_token)
                and not isinstance(exc, ValueError)
                and run["attempts"] < settings.job_max_attempts
                and type(exc).__name__
                not in ("DefaultCredentialsError", "RefreshError")
                and (getattr(exc, "status_code", None) or getattr(exc, "code", None))
                not in (400, 401, 403, 404, 422)
            )
            from backend.services.jobs import after

            conn.execute(
                "UPDATE runs SET status=?,error=?,finished_at=?,next_attempt_at=?,owner=NULL,lease_until=NULL WHERE id=?",
                (
                    "queued" if retry else "failed",
                    safe,
                    None if retry else now(),
                    after(settings.job_retry_delay_seconds) if retry else None,
                    run_id,
                ),
            )
            audit(
                conn,
                case_id,
                actor,
                "pipeline_failed",
                {"run_id": run_id, "error": safe},
            )
