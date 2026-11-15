import json
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import current_user, require_role
from backend.database import db, active_prompts, DEFAULT_PROMPTS, now, audit, policy
from backend.models import PromptUpdate, PolicyUpdate, TonePreview
from backend.routers.cases import get_case
from backend.services.agent_graph import format_memo
from backend.services.intake_rules import reconcile

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_user)])


@router.get("/prompts")
def prompts():
    with db() as conn:
        return {
            "active": active_prompts(conn),
            "history": [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM prompt_versions ORDER BY id DESC LIMIT 100"
                )
            ],
            "policy": policy(conn),
            "policy_history": [
                dict(r)
                for r in conn.execute(
                    "SELECT * FROM policy_versions ORDER BY id DESC LIMIT 50"
                )
            ],
        }


@router.put("/prompts/{agent_key}")
def update_prompt(agent_key: str, body: PromptUpdate, user=Depends(current_user)):
    require_role(user, "meena", "farhan")
    if agent_key not in DEFAULT_PROMPTS:
        raise HTTPException(404, "Unknown prompt key")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        version = active_prompts(conn)[agent_key]["version"] + 1
        conn.execute(
            "INSERT INTO prompt_versions(agent_key,version,content,timestamp,actor) VALUES(?,?,?,?,?)",
            (agent_key, version, body.content, now(), user["name"]),
        )
        audit(
            conn,
            None,
            user["name"],
            "prompt_version_saved",
            {"agent_key": agent_key, "version": version},
        )
    return {"version": version}


@router.post("/prompts/reset")
def reset(user=Depends(current_user)):
    require_role(user, "meena", "farhan")
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        current = active_prompts(conn)
        for key, content in DEFAULT_PROMPTS.items():
            conn.execute(
                "INSERT INTO prompt_versions(agent_key,version,content,timestamp,actor) VALUES(?,?,?,?,?)",
                (key, current[key]["version"] + 1, content, now(), user["name"]),
            )
        audit(conn, None, user["name"], "prompt_defaults_restored", {})
    return {"reset": True}


@router.put("/policy")
def update_policy(body: PolicyUpdate, user=Depends(current_user)):
    require_role(user, "arjun", "farhan")
    with db() as conn:
        conn.execute(
            "UPDATE settings SET value=? WHERE key='policy'", (body.model_dump_json(),)
        )
        conn.execute(
            "INSERT INTO policy_versions(value,timestamp,actor) VALUES(?,?,?)",
            (body.model_dump_json(), now(), user["name"]),
        )
        audit(conn, None, user["name"], "policy_changed", body.model_dump())
    return body


@router.post("/toner/preview")
def preview(body: TonePreview, user=Depends(current_user)):
    require_role(user, "vikram", "meena", "arjun", "farhan")
    with db() as conn:
        case = get_case(conn, body.case_id)
        cells = [
            dict(c)
            for c in conn.execute(
                "SELECT * FROM cells WHERE case_id=?", (body.case_id,)
            )
        ]
        for c in cells:
            c["citation"] = json.loads(c["citation"])
        prompts = active_prompts(conn)
        recon = reconcile(cells, policy(conn)["gst_variance_threshold_pct"])
    if body.tone != "Polite RM Document Chaser" and (
        len(cells) != 60 or any(not c["verified_by"] for c in cells)
    ):
        raise HTTPException(
            422,
            "Verify all 60 source fields before generating a final dossier; RM chaser remains available",
        )
    try:
        text = format_memo(case, cells, recon, prompts, body.tone)
    except Exception:
        raise HTTPException(
            502, "Toner provider unavailable; check backend provider configuration"
        )
    with db() as conn:
        audit(
            conn,
            body.case_id,
            user["name"],
            "toner_preview",
            {"tone": body.tone, "prompt_version": prompts["toner_prompt"]["version"]},
        )
    return {"text": text, "prompt_version": prompts["toner_prompt"]["version"]}
