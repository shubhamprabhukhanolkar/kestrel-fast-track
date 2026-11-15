"""Durable run queue: local leased worker, or authenticated Cloud Tasks delivery."""

import json
import threading
import uuid
from datetime import datetime, timezone, timedelta
from backend.config import settings
from backend.database import db, now


def after(seconds):
    return (datetime.now(timezone.utc) + timedelta(seconds=seconds)).isoformat()


def recover_expired(conn):
    conn.execute(
        "UPDATE runs SET status='queued',owner=NULL,lease_until=NULL,error='Execution lease expired; safely queued for retry' WHERE status='running' AND (lease_until IS NULL OR lease_until<?) AND attempts<?",
        (now(), settings.job_max_attempts),
    )
    conn.execute(
        "UPDATE runs SET status='failed',finished_at=?,error='Execution lease expired after maximum attempts' WHERE status='running' AND (lease_until IS NULL OR lease_until<?) AND attempts>=?",
        (now(), now(), settings.job_max_attempts),
    )


def claim(run_id=None):
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        recover_expired(conn)
        if run_id:
            row = conn.execute(
                "SELECT * FROM runs WHERE id=? AND status='queued' AND (next_attempt_at IS NULL OR next_attempt_at<=?)",
                (run_id, now()),
            ).fetchone()
        else:
            row = conn.execute(
                "SELECT * FROM runs WHERE status='queued' AND (next_attempt_at IS NULL OR next_attempt_at<=?) ORDER BY started_at LIMIT 1",
                (now(),),
            ).fetchone()
        if not row:
            return None
        owner = uuid.uuid4().hex
        conn.execute(
            "UPDATE runs SET status='running',owner=?,lease_until=?,attempts=attempts+1,error=NULL WHERE id=?",
            (owner, after(settings.job_lease_seconds), row["id"]),
        )
        return {**dict(row), "owner": owner}


def execute(run_id=None):
    job = claim(run_id)
    if not job:
        return None
    stopped = threading.Event()

    def heartbeat():
        while not stopped.wait(max(1, settings.job_lease_seconds // 3)):
            try:
                with db() as conn:
                    conn.execute(
                        "UPDATE runs SET lease_until=? WHERE id=? AND owner=? AND status='running'",
                        (after(settings.job_lease_seconds), job["id"], job["owner"]),
                    )
            except Exception:
                # Completion is fenced by the owner and lease; a failed heartbeat cannot grant ownership.
                pass

    thread = threading.Thread(target=heartbeat, daemon=True)
    thread.start()
    try:
        from backend.services.agent_graph import run_pipeline

        run_pipeline(
            job["case_id"], job["id"], job["actor"], execution_token=job["owner"]
        )
    finally:
        stopped.set()
        thread.join(timeout=2)
    return job["id"]


def enqueue_cloud_task(job):
    from google.cloud import tasks_v2
    from google.api_core.exceptions import AlreadyExists

    client = tasks_v2.CloudTasksClient()
    parent = client.queue_path(
        settings.gcp_project, settings.gcp_region, settings.tasks_queue
    )
    task = {
        "name": f"{parent}/tasks/run-{job['id']}-{job['attempts'] or 0}",
        "http_request": {
            "http_method": tasks_v2.HttpMethod.POST,
            "url": settings.service_url.rstrip("/") + "/api/v1/internal/tasks/pipeline",
            "headers": {"Content-Type": "application/json"},
            "body": json.dumps({"run_id": job["id"]}).encode(),
            "oidc_token": {
                "service_account_email": settings.task_service_account,
                "audience": settings.service_url.rstrip("/"),
            },
        },
        "dispatch_deadline": {"seconds": 600},
    }
    try:
        client.create_task(request={"parent": parent, "task": task}, timeout=20)
    except AlreadyExists:
        pass


class JobWorker:
    def __init__(self):
        self.stopped = threading.Event()
        self.thread = None

    def start(self):
        self.thread = threading.Thread(
            target=self.loop, name="kestrel-durable-jobs", daemon=True
        )
        self.thread.start()

    def loop(self):
        while not self.stopped.is_set():
            try:
                if settings.task_backend == "worker":
                    if execute():
                        continue
                else:
                    with db() as conn:
                        conn.execute("BEGIN IMMEDIATE")
                        recover_expired(conn)
                        queued = [
                            dict(r)
                            for r in conn.execute(
                                "SELECT * FROM runs WHERE status='queued' AND (next_attempt_at IS NULL OR next_attempt_at<=?) LIMIT 20",
                                (now(),),
                            )
                        ]
                    for job in queued:
                        if not self.stopped.is_set():
                            enqueue_cloud_task(job)
            except Exception as exc:
                import logging

                logging.getLogger(__name__).warning(
                    "Queue worker unavailable: %s", type(exc).__name__
                )
            self.stopped.wait(2)

    def stop(self):
        self.stopped.set()
        if self.thread:
            self.thread.join(timeout=3)
