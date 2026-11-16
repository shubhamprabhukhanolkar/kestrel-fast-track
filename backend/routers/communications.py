from fastapi import APIRouter, Depends, HTTPException
from backend.auth import current_user, require_role, confirm_operator_password
from backend.database import db, audit, now
from backend.models import CibilUpdate, EmailDraft, EmailAuthorization
from backend.routers.cases import get_case, unlocked

router = APIRouter(prefix="/api/v1/cases", dependencies=[Depends(current_user)])


@router.put("/{case_id}/cibil")
def update_cibil(case_id: str, body: CibilUpdate, user=Depends(current_user)):
    require_role(user, "meena")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        case = get_case(conn, case_id)
        unlocked(conn, case_id)
        conn.execute(
            "UPDATE cases SET cibil_score=?,cibil_source='manual',cibil_note=?,cibil_updated_by=?,cibil_updated_at=?,revision=revision+1 WHERE id=?",
            (body.score, body.note, user["name"], now(), case_id),
        )
        audit(
            conn,
            case_id,
            user["name"],
            "cibil_score_updated",
            {
                "previous_score": case["cibil_score"],
                "score": body.score,
                "source": "manual",
                "note": body.note,
            },
        )
    return {"saved": True, "source": "manual", "score": body.score}


@router.get("/{case_id}/email-drafts/latest")
def latest_email(case_id: str):
    with db() as conn:
        get_case(conn, case_id)
        row = conn.execute(
            "SELECT * FROM email_drafts WHERE case_id=? ORDER BY id DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        return dict(row) if row else None


@router.post("/{case_id}/email-drafts", status_code=201)
def submit_email(case_id: str, body: EmailDraft, user=Depends(current_user)):
    require_role(user, "meena", "arjun")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        get_case(conn, case_id)
        conn.execute(
            "INSERT INTO email_drafts(case_id,recipient,subject,body,created_at,created_by) VALUES(?,?,?,?,?,?)",
            (case_id, body.recipient, body.subject, body.body, now(), user["name"]),
        )
        draft = dict(
            conn.execute(
                "SELECT * FROM email_drafts WHERE case_id=? ORDER BY id DESC LIMIT 1",
                (case_id,),
            ).fetchone()
        )
        audit(
            conn,
            case_id,
            user["name"],
            "email_submitted_for_authorization",
            {
                "draft_id": draft["id"],
                "recipient": body.recipient,
                "subject": body.subject,
            },
        )
        return draft


@router.post("/{case_id}/email-drafts/{draft_id}/authorize")
def authorize_email(
    case_id: str, draft_id: int, body: EmailAuthorization, user=Depends(current_user)
):
    require_role(user, "arjun")
    confirm_operator_password(
        user, body.password.get_secret_value(), "email-authorization"
    )
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        get_case(conn, case_id)
        latest = conn.execute(
            "SELECT * FROM email_drafts WHERE case_id=? ORDER BY id DESC LIMIT 1",
            (case_id,),
        ).fetchone()
        if not latest or latest["id"] != draft_id:
            raise HTTPException(
                409, "A newer draft is available; review it before authorizing"
            )
        if latest["status"] != "pending_authorization":
            raise HTTPException(409, "This email approval has already been recorded")
        conn.execute(
            "UPDATE email_drafts SET status='approved_for_sending',authorized_at=?,authorized_by=? WHERE id=?",
            (now(), user["name"], draft_id),
        )
        audit(
            conn,
            case_id,
            user["name"],
            "email_approval_recorded",
            {"draft_id": draft_id, "delivery_mode": "simulation", "delivered": False},
        )
        return {
            "status": "approved_for_sending",
            "authorized_by": user["name"],
            "delivered": False,
        }
