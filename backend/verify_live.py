"""Explicit, billable provider verification using isolated synthetic borrower data."""

import argparse
import json
import uuid
import time
from pathlib import Path
from backend.config import settings
from backend.database import init_db, db, now
from backend.services.llm_router import llm
from backend.services.jobs import execute


def main():
    parser = argparse.ArgumentParser()
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--primary-pipeline",
        action="store_true",
        help="Verify normal live routing without injected failures; configured backup may handle real primary outages",
    )
    mode.add_argument(
        "--backup-pipeline",
        action="store_true",
        help="Run real Groq extraction, critique and tone formatting under an explicit simulated primary 503",
    )
    args = parser.parse_args()
    if settings.demo_mode or settings.database_url or settings.app_env != "local":
        raise SystemExit(
            "Run in the local live profile; cloud database and offline simulation are intentionally unsupported for this isolated verification"
        )
    root = Path("artifacts") / f"live-verification-{uuid.uuid4().hex[:10]}"
    settings.database_path = str(root / "verification.db")
    settings.document_dir = str(root / "documents")
    settings.seed_sample_cases = True
    settings.seed_telemetry = False
    init_db()
    report = {
        "timestamp": now(),
        "project": settings.gcp_project,
        "deployment_region": settings.vertex_location,
        "inference_location": settings.vertex_location
        if llm.primary_provider == "vertex_gemini"
        else "provider-managed",
        "primary_provider": llm.primary_provider,
        "model": llm.primary_model,
        "providers": llm.probe(include_backup=not args.primary_pipeline),
    }
    if args.backup_pipeline or args.primary_pipeline:
        run_id = str(uuid.uuid4())
        with db() as conn:
            conn.execute(
                "UPDATE settings SET value=? WHERE key='failover'",
                (
                    json.dumps(
                        {"simulate_503": args.backup_pipeline, "simulate_429": False}
                    ),
                ),
            )
            conn.execute(
                "INSERT INTO runs(id,case_id,status,events,started_at,actor,execution_mode) VALUES(?,?,'queued','[]',?,?,'live')",
                (run_id, "KF-2026-0892", now(), "Live verification runner"),
            )
        for attempt in range(settings.job_max_attempts):
            execute(run_id)
            with db() as conn:
                state = conn.execute(
                    "SELECT status FROM runs WHERE id=?", (run_id,)
                ).fetchone()[0]
            if state != "queued":
                break
            if attempt + 1 < settings.job_max_attempts:
                time.sleep(settings.job_retry_delay_seconds + 1)
        with db() as conn:
            run = dict(
                conn.execute("SELECT * FROM runs WHERE id=?", (run_id,)).fetchone()
            )
            report[
                "backup_pipeline" if args.backup_pipeline else "primary_pipeline"
            ] = {
                "status": run["status"],
                "error": run["error"],
                "events": json.loads(run["events"]),
                "attempts": run["attempts"],
                "simulation": "Primary 503 is injected; all Groq model responses are LIVE"
                if args.backup_pipeline
                else "None. Normal live routing; provider_attempts records any real failover.",
            }
            report["provider_attempts"] = [
                dict(r)
                for r in conn.execute("SELECT * FROM agent_telemetry_logs ORDER BY id")
            ]
            report["extracted_cells"] = (
                conn.execute(
                    "SELECT COUNT(*) FROM cells WHERE case_id='KF-2026-0892'"
                ).fetchone()[0]
                if run["status"] == "completed"
                else None
            )
            conn.execute(
                "UPDATE settings SET value=? WHERE key='failover'",
                (json.dumps({"simulate_503": False, "simulate_429": False}),),
            )
    output = root / "report.json"
    output.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(
        json.dumps(
            {
                "providers": report["providers"],
                "backup_pipeline_status": report.get("backup_pipeline", {}).get(
                    "status"
                ),
                "primary_pipeline_status": report.get("primary_pipeline", {}).get(
                    "status"
                ),
                "report": str(output),
            }
        )
    )


if __name__ == "__main__":
    main()
