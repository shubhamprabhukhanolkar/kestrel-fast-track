import json
from fastapi import APIRouter, Depends, HTTPException
from backend.auth import current_user, require_role
from backend.config import settings
from backend.database import db, audit
from backend.models import FailoverConfig

router = APIRouter(prefix="/api/v1", dependencies=[Depends(current_user)])


@router.get("/finops/summary")
def summary():
    where = "" if settings.demo_mode else " WHERE mode='live_estimate'"
    with db() as conn:
        totals = dict(
            conn.execute(
                "SELECT COALESCE(SUM(cost_inr),0) total_spend_inr,COUNT(DISTINCT case_id) application_count,COALESCE(SUM(input_tokens),0) input_tokens,COALESCE(SUM(output_tokens),0) output_tokens,COALESCE(AVG(latency_ms),0) avg_latency_ms,COUNT(*) attempts,COALESCE(SUM(CASE WHEN failover_triggered=1 AND provider='groq_backup' THEN 1 ELSE 0 END),0) failover_calls FROM agent_telemetry_logs"
                + where
            ).fetchone()
        )
        totals["avg_cost_per_application_inr"] = totals["total_spend_inr"] / max(
            1, totals["application_count"]
        )
        app_where = where + (" AND" if where else " WHERE") + " case_id IS NOT NULL"
        totals["application_spend_inr"] = conn.execute(
            "SELECT COALESCE(SUM(cost_inr),0) FROM agent_telemetry_logs" + app_where
        ).fetchone()[0]
        totals["avg_cost_per_application_inr"] = (
            totals["application_spend_inr"] / totals["application_count"]
            if totals["application_count"]
            else 0
        )
        agents = [
            dict(r)
            for r in conn.execute(
                "SELECT agent_name,SUM(input_tokens) input_tokens,SUM(output_tokens) output_tokens,SUM(cost_inr) cost_inr,AVG(latency_ms) avg_latency_ms,COUNT(*) calls FROM agent_telemetry_logs"
                + where
                + " GROUP BY agent_name"
            )
        ]
        providers = [
            dict(r)
            for r in conn.execute(
                "SELECT provider,COUNT(*) calls,SUM(cost_inr) cost_inr FROM agent_telemetry_logs"
                + where
                + " GROUP BY provider"
            )
        ]
        modes = [
            dict(r)
            for r in conn.execute(
                "SELECT mode,COUNT(*) calls,SUM(cost_inr) cost_inr FROM agent_telemetry_logs"
                + where
                + " GROUP BY mode"
            )
        ]
        logs = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM agent_telemetry_logs"
                + where
                + " ORDER BY id DESC LIMIT 100"
            )
        ]
        return {
            **totals,
            "agents": agents,
            "providers": providers,
            "modes": modes,
            "logs": logs,
            "demo_mode": settings.demo_mode,
            "cost_basis": "SDK token counts with configured estimated INR rates. Unknown failed-request usage is not confirmed zero billing. "
            + (
                "Offline synthetic metrics included."
                if settings.demo_mode
                else "Only actual live provider attempts are included; sample metrics are excluded."
            ),
        }


@router.post("/admin/provider-check")
def provider_check(user=Depends(current_user)):
    require_role(user, "farhan")
    if settings.demo_mode:
        raise HTTPException(409, "Provider connectivity checks require live execution")
    from backend.services.llm_router import llm

    return {"providers": llm.probe()}


@router.get("/admin/readiness")
def admin_readiness(user=Depends(current_user)):
    require_role(user, "farhan")
    from backend.services.readiness import readiness

    return readiness()


@router.get("/admin/failover-config")
def get_failover():
    with db() as conn:
        return json.loads(
            conn.execute("SELECT value FROM settings WHERE key='failover'").fetchone()[
                0
            ]
        )


@router.put("/admin/failover-config")
@router.post("/admin/failover-config")
def update_failover(body: FailoverConfig, user=Depends(current_user)):
    require_role(user, "farhan")
    with db() as conn:
        conn.execute(
            "UPDATE settings SET value=? WHERE key='failover'",
            (body.model_dump_json(),),
        )
        audit(conn, None, user["name"], "failover_config_changed", body.model_dump())
    return body
