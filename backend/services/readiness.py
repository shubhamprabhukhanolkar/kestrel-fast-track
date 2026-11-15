from backend.config import settings
from backend.database import db
from datetime import datetime, timezone, timedelta


def readiness():
    checks = []

    def add(key, ok, detail):
        checks.append({"key": key, "passed": bool(ok), "detail": detail})

    with db() as conn:
        conn.execute("SELECT 1").fetchone()
        users = conn.execute("SELECT COUNT(*) FROM users").fetchone()[0]
        observations = [
            dict(r)
            for r in conn.execute(
                "SELECT * FROM agent_telemetry_logs WHERE agent_name='ProviderCheck' AND mode='live_estimate' ORDER BY id DESC LIMIT 20"
            )
        ]
    add(
        "database", True, "PostgreSQL" if settings.database_url else "SQLite local disk"
    )
    add(
        "authentication",
        (settings.auth_mode == "password" and users > 0)
        or (
            settings.auth_mode == "iap"
            and settings.iap_audience
            and settings.iap_role_map
        )
        or (settings.auth_mode == "demo" and settings.demo_mode),
        f"{settings.auth_mode}; {users} provisioned password operators",
    )
    if not settings.demo_mode:
        try:
            import google.auth

            google.auth.default(
                scopes=["https://www.googleapis.com/auth/cloud-platform"]
            )
            credentials_available = True
        except Exception:
            credentials_available = False
        add(
            "vertex_credentials",
            credentials_available,
            "Application Default Credentials or attached runtime identity required",
        )
        add(
            "backup_configured",
            settings.groq_api_key or settings.groq_secret_name,
            "Groq environment key or Secret Manager reference required",
        )
        cutoff = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
        for provider in ("vertex_gemini", "groq_backup"):
            observation = next(
                (row for row in observations if row["provider"] == provider), None
            )
            connected = (
                observation
                and observation["status"] == "success"
                and observation["timestamp"] >= cutoff
            )
            add(
                provider + "_connectivity",
                connected,
                provider
                + ": "
                + (observation["status"] if observation else "not checked")
                + "; successful check must be within 15 minutes",
            )
    if settings.app_env == "production":
        add(
            "live_execution",
            not settings.demo_mode,
            "Production profile rejects simulated AI",
        )
        add(
            "durable_database",
            bool(settings.database_url),
            "Cloud SQL/PostgreSQL required on Cloud Run",
        )
        add(
            "durable_documents",
            bool(settings.documents_bucket),
            "Private GCS bucket in asia-south1 required",
        )
        add(
            "durable_jobs",
            settings.task_backend == "cloud_tasks"
            and settings.service_url
            and settings.task_service_account,
            "Cloud Tasks, service URL and task identity required",
        )
        add(
            "secure_identity",
            settings.auth_mode != "demo" and settings.secure_cookies,
            "Authenticated operators and secure cookies required",
        )
    return {
        "ready": all(c["passed"] for c in checks),
        "checks": checks,
        "execution_mode": "offline" if settings.demo_mode else "live",
        "provider_connectivity": "Based on recorded live provider checks; configuration alone is insufficient",
    }


def validate_production():
    if settings.app_env != "production":
        return
    required = [
        not settings.demo_mode,
        settings.auth_mode != "demo",
        bool(settings.database_url),
        bool(settings.documents_bucket),
        settings.task_backend == "cloud_tasks",
        bool(settings.task_service_account),
        bool(settings.service_url),
        settings.secure_cookies,
        settings.gcp_region == "asia-south1",
        settings.vertex_location == "asia-south1",
    ]
    if not all(required):
        raise RuntimeError(
            "Production requires live AI, authenticated operators, PostgreSQL, a private asia-south1 document bucket, Cloud Tasks identity/service URL and secure cookies. All GCP locations must remain asia-south1."
        )
    from google.cloud import storage

    bucket = storage.Client(project=settings.gcp_project).get_bucket(
        settings.documents_bucket, timeout=20
    )
    if bucket.location.lower() != "asia-south1":
        raise RuntimeError("Document bucket must be in asia-south1")
