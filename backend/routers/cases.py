import json
import sqlite3
import uuid
from pathlib import Path
import re
from fastapi import (
    APIRouter,
    Depends,
    HTTPException,
    BackgroundTasks,
    UploadFile,
    File,
    Form,
)
from fastapi.responses import FileResponse, Response
import pymupdf as fitz
from backend.auth import current_user, require_role
from backend.config import settings
from backend.database import db, policy, audit, now, MONTHS
from backend.models import VerifyCell, Decision
from backend.services.intake_rules import intake_check, reconcile
from backend.services.agent_graph import run_pipeline
from backend.services.evidence import evidence_snapshot
from backend.services.document_index import extract_periods
from sqlalchemy.exc import IntegrityError

router = APIRouter(prefix="/api/v1/cases", dependencies=[Depends(current_user)])


def get_case(conn, case_id):
    row = conn.execute("SELECT * FROM cases WHERE id=?", (case_id,)).fetchone()
    if not row:
        raise HTTPException(404, "Case not found")
    return dict(row)


def unlocked(conn, case_id):
    if conn.execute("SELECT 1 FROM decisions WHERE case_id=?", (case_id,)).fetchone():
        raise HTTPException(409, "Signed case is locked")
    if conn.execute(
        "SELECT 1 FROM runs WHERE case_id=? AND status IN ('queued','running')",
        (case_id,),
    ).fetchone():
        raise HTTPException(409, "Extraction is running; wait for completion")


@router.get("")
def list_cases():
    with db() as conn:
        return [
            dict(r)
            for r in conn.execute(
                "SELECT cases.*, CASE WHEN EXISTS (SELECT 1 FROM decisions WHERE decisions.case_id=cases.id) THEN 0 ELSE 1 END AS is_pending FROM cases ORDER BY id"
            )
        ]


@router.get("/{case_id}")
def detail(case_id: str):
    with db() as conn:
        case = get_case(conn, case_id)
        documents = [
            dict(d)
            for d in conn.execute("SELECT * FROM documents WHERE case_id=?", (case_id,))
        ]
        cells = [
            dict(c)
            for c in conn.execute(
                "SELECT * FROM cells WHERE case_id=? ORDER BY month,field", (case_id,)
            )
        ]
        for c in cells:
            c["citation"] = json.loads(c["citation"])
        case["intake"] = intake_check(case, documents)
        case["documents"] = [
            {
                k: (json.loads(d[k]) if k in ("months", "pages") else v)
                for k, v in d.items()
                if k != "path"
            }
            for d in documents
        ]
        case["cells"] = cells
        case["reconciliation"] = reconcile(
            cells, policy(conn)["gst_variance_threshold_pct"]
        )
        case["correction_rate_pct"] = (
            round(
                sum(c["value"] != c["original_value"] for c in cells)
                / len(cells)
                * 100,
                2,
            )
            if cells
            else 0
        )
        case["verified_count"] = sum(bool(c["verified_by"]) for c in cells)
        case["audit"] = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM audit_events WHERE case_id=? ORDER BY id DESC LIMIT 100",
                (case_id,),
            )
        ]
        row = conn.execute(
            "SELECT * FROM decisions WHERE case_id=?", (case_id,)
        ).fetchone()
        case["decision"] = dict(row) if row else None
        return case


@router.post("/{case_id}/intake-check")
def check(case_id: str, user=Depends(current_user)):
    require_role(user, "vikram", "meena")
    with db() as conn:
        result = intake_check(
            get_case(conn, case_id),
            [
                dict(d)
                for d in conn.execute(
                    "SELECT * FROM documents WHERE case_id=?", (case_id,)
                )
            ],
        )
        audit(conn, case_id, user["name"], "intake_checked", result)
        return result


@router.post("/{case_id}/pipeline", status_code=202)
def start_pipeline(
    case_id: str, background: BackgroundTasks, user=Depends(current_user)
):
    require_role(user, "vikram", "meena")
    run_id = str(uuid.uuid4())
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        case = get_case(conn, case_id)
        unlocked(conn, case_id)
        docs = [
            dict(d)
            for d in conn.execute("SELECT * FROM documents WHERE case_id=?", (case_id,))
        ]
        if not intake_check(case, docs)["passed"]:
            raise HTTPException(
                422,
                "Intake blocked: complete native text PDFs and cash-share notes required",
            )
        try:
            conn.execute(
                "INSERT INTO runs(id,case_id,status,events,started_at,actor,execution_mode) VALUES(?,?,?,'[]',?,?,?)",
                (
                    run_id,
                    case_id,
                    "running" if settings.demo_mode else "queued",
                    now(),
                    user["name"],
                    "offline" if settings.demo_mode else "live",
                ),
            )
        except (sqlite3.IntegrityError, IntegrityError):
            raise HTTPException(409, "Extraction already running")
        audit(conn, case_id, user["name"], "pipeline_started", {"run_id": run_id})
    if settings.demo_mode:
        background.add_task(run_pipeline, case_id, run_id, user["name"])
    return {"run_id": run_id}


@router.get("/{case_id}/runs/latest")
def latest_run(case_id: str):
    with db() as conn:
        get_case(conn, case_id)
        row = conn.execute(
            "SELECT * FROM runs WHERE case_id=? ORDER BY started_at DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        return (
            {
                **dict(row),
                "events": json.loads(row["events"]),
                "prompt_versions": json.loads(row["prompt_versions"] or "{}"),
            }
            if row
            else None
        )


@router.put("/{case_id}/verify")
def verify(case_id: str, body: VerifyCell, user=Depends(current_user)):
    require_role(user, "meena")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        get_case(conn, case_id)
        unlocked(conn, case_id)
        row = conn.execute(
            "SELECT * FROM cells WHERE id=? AND case_id=?", (body.cell_id, case_id)
        ).fetchone()
        if not row:
            raise HTTPException(404, "Cell not found")
        conn.execute(
            "UPDATE cells SET value=?,verified_by=? WHERE id=?",
            (body.value, user["name"], body.cell_id),
        )
        conn.execute("UPDATE cases SET revision=revision+1 WHERE id=?", (case_id,))
        audit(
            conn,
            case_id,
            user["name"],
            "cell_verified",
            {
                "cell_id": body.cell_id,
                "old_value": row["value"],
                "new_value": body.value,
                "reason": body.reason,
                "original_citation": json.loads(row["citation"]),
            },
        )
        pending = conn.execute(
            "SELECT COUNT(*) FROM cells WHERE case_id=? AND verified_by IS NULL",
            (case_id,),
        ).fetchone()[0]
        conn.execute(
            "UPDATE cases SET status=? WHERE id=?",
            ("awaiting_signoff" if pending == 0 else "awaiting_verification", case_id),
        )
    return {"verified": True, "remaining": pending}


@router.post("/{case_id}/decision")
def decision(case_id: str, body: Decision, user=Depends(current_user)):
    require_role(user, "arjun")
    if body.signature.strip() != user["name"]:
        raise HTTPException(
            422, "Signature must match the authenticated credit manager: Arjun Iyer"
        )
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        case = get_case(conn, case_id)
        unlocked(conn, case_id)
        cells = [
            dict(c)
            for c in conn.execute("SELECT * FROM cells WHERE case_id=?", (case_id,))
        ]
        docs = [
            dict(d)
            for d in conn.execute("SELECT * FROM documents WHERE case_id=?", (case_id,))
        ]
        if (
            not settings.demo_mode
            and not conn.execute(
                "SELECT 1 FROM runs WHERE case_id=? AND status='completed' AND execution_mode='live'",
                (case_id,),
            ).fetchone()
        ):
            raise HTTPException(
                422,
                "A completed live extraction and critique run is required before sign-off",
            )
        if (
            not intake_check(case, docs)["passed"]
            or len(cells) != 60
            or any(not c["verified_by"] for c in cells)
        ):
            raise HTTPException(
                422,
                "Intake must pass and all 60 cells must be verified by Meena Pillai",
            )
        if not case["dossier"]:
            raise HTTPException(422, "Evidence dossier required")
        snapshot = evidence_snapshot(
            case, cells, policy(conn)["gst_variance_threshold_pct"]
        )
        conn.execute("UPDATE cases SET dossier=? WHERE id=?", (snapshot, case_id))
        conn.execute(
            "INSERT INTO decisions(case_id,timestamp,signature,rationale,outcome,revision) VALUES(?,?,?,?,?,?)",
            (
                case_id,
                now(),
                user["name"],
                body.rationale.strip(),
                body.outcome,
                case["revision"],
            ),
        )
        conn.execute("UPDATE cases SET status=? WHERE id=?", (body.outcome, case_id))
        audit(
            conn,
            case_id,
            user["name"],
            "human_credit_decision",
            {
                **body.model_dump(),
                "revision": case["revision"],
                "dossier": snapshot,
                "reconciliation": reconcile(
                    cells, policy(conn)["gst_variance_threshold_pct"]
                ),
                "policy": policy(conn),
                "cells": [
                    {
                        "id": c["id"],
                        "value": c["value"],
                        "verified_by": c["verified_by"],
                        "citation": json.loads(c["citation"]),
                    }
                    for c in cells
                ],
            },
        )
    return {"recorded": True, "signature": user["name"], "outcome": body.outcome}


@router.get("/{case_id}/documents/{doc_id}/pdf")
def pdf(case_id: str, doc_id: int):
    with db() as conn:
        doc = conn.execute(
            "SELECT * FROM documents WHERE id=? AND case_id=?", (doc_id, case_id)
        ).fetchone()
        if not doc:
            raise HTTPException(404, "Document not found")
        from backend.services.document_store import read_document

        return Response(
            read_document(doc["path"]),
            media_type="application/pdf",
            headers={"Content-Disposition": f'inline; filename="{doc["name"]}"'},
        )


@router.get("/{case_id}/dossier.pdf")
def dossier_pdf(case_id: str):
    with db() as conn:
        case = get_case(conn, case_id)
        decision_row = conn.execute(
            "SELECT * FROM decisions WHERE case_id=?", (case_id,)
        ).fetchone()
        cells = [
            dict(c)
            for c in conn.execute("SELECT * FROM cells WHERE case_id=?", (case_id,))
        ]
        threshold = policy(conn)["gst_variance_threshold_pct"]
    doc = fitz.open()
    page = doc.new_page()
    page.insert_text((40, 45), "KESTREL FINANCE | EVIDENCE DOSSIER", fontsize=15)
    decision_text = "\nHUMAN OUTCOME: PENDING"
    if decision_row:
        decision_text = f"\nHUMAN OUTCOME: {decision_row['outcome']}\nSigned: {decision_row['signature']} at {decision_row['timestamp']}\nRationale: {decision_row['rationale']}"
    narrative = (
        case["dossier"] if decision_row else evidence_snapshot(case, cells, threshold)
    )
    text = narrative + decision_text + "\nNO MODEL APPROVES CREDIT."
    # Fit a single page while preserving the complete decision/rationale within model limits.
    size = 10.0
    while size >= 5:
        shape = page.new_shape()
        remaining = shape.insert_textbox(
            fitz.Rect(40, 65, 555, 800), text, fontsize=size, fontname="helv"
        )
        if remaining >= 0:
            shape.commit()
            break
        size -= 0.5
    output = doc.tobytes()
    doc.close()
    return Response(
        output,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'attachment; filename="{case_id}-dossier.pdf"'
        },
    )


@router.post("/{case_id}/documents")
async def upload_document(
    case_id: str,
    kind: str = Form(...),
    file: UploadFile = File(...),
    user=Depends(current_user),
):
    require_role(user, "vikram", "meena")
    if kind not in ("bank", "gstr1", "gstr3b"):
        raise HTTPException(422, "Document kind must be bank, gstr1 or gstr3b")
    content = await file.read(15 * 1024 * 1024 + 1)
    if len(content) > 15 * 1024 * 1024 or not content.startswith(b"%PDF-"):
        raise HTTPException(422, "Upload a PDF no larger than 15 MB")
    try:
        with fitz.open(stream=content, filetype="pdf") as pdf_doc:
            if pdf_doc.is_encrypted or len(pdf_doc) > 200 or len(pdf_doc) == 0:
                raise ValueError()
            pages = [page.get_text().splitlines() for page in pdf_doc]
    except Exception:
        raise HTTPException(422, "Invalid, encrypted or oversized PDF")
    native = all(len(" ".join(lines).strip()) >= 30 for lines in pages)
    months = extract_periods("\n".join("\n".join(p) for p in pages))
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        get_case(conn, case_id)
        unlocked(conn, case_id)
        name = f"{kind}_{uuid.uuid4().hex[:8]}.pdf"
        from backend.services.document_store import persist_document

        location = persist_document(case_id, name, content)
        conn.execute(
            "DELETE FROM documents WHERE case_id=? AND kind=?", (case_id, kind)
        )
        conn.execute(
            "INSERT INTO documents(case_id,name,kind,native_text,months,pages,path) VALUES(?,?,?,?,?,?,?)",
            (
                case_id,
                name,
                kind,
                int(native),
                json.dumps(months),
                json.dumps(pages),
                location,
            ),
        )
        conn.execute("DELETE FROM cells WHERE case_id=?", (case_id,))
        conn.execute(
            "UPDATE cases SET status='ready_for_extraction',dossier='',revision=revision+1 WHERE id=?",
            (case_id,),
        )
        audit(
            conn,
            case_id,
            user["name"],
            "document_replaced",
            {"kind": kind, "name": name, "native_text": native, "coverage": months},
        )
    return {
        "name": name,
        "native_text": native,
        "months": months,
        "note": "Coverage recognizes ISO, numeric and named-month dates. Original source text is indexed without rewriting; analyst validates reporting periods.",
    }
