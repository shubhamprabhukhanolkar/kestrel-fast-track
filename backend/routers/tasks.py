from pydantic import BaseModel
from fastapi import APIRouter, HTTPException, Request
from backend.config import settings
from backend.database import db
from backend.services.jobs import execute

router = APIRouter(prefix="/api/v1/internal/tasks")


class TaskPayload(BaseModel):
    run_id: str


@router.post("/pipeline")
def pipeline_task(body: TaskPayload, request: Request):
    from google.oauth2 import id_token
    from google.auth.transport.requests import Request as GoogleRequest

    if (
        settings.task_backend != "cloud_tasks"
        or not settings.service_url
        or not settings.task_service_account
    ):
        raise HTTPException(403, "Cloud Tasks dispatch is not configured")
    authorization = request.headers.get("Authorization", "")
    try:
        if not authorization.startswith("Bearer "):
            raise ValueError()
        claims = id_token.verify_oauth2_token(
            authorization[7:],
            GoogleRequest(),
            audience=settings.service_url.rstrip("/"),
        )
        if claims.get("email") != settings.task_service_account or not claims.get(
            "email_verified"
        ):
            raise ValueError()
    except Exception:
        raise HTTPException(401, "Verified task service identity required")
    execute(body.run_id)
    with db() as conn:
        row = conn.execute(
            "SELECT status FROM runs WHERE id=?", (body.run_id,)
        ).fetchone()
    if not row:
        raise HTTPException(404, "Run not found")
    if row["status"] in ("queued", "running"):
        raise HTTPException(503, "Run is pending or executing; retry delivery")
    return {"status": row["status"]}
