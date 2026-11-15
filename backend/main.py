import hashlib
import secrets
from datetime import datetime, timezone, timedelta
from pathlib import Path
from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.config import settings
from backend.database import init_db, db, PERSONAS, now
from backend.models import Login
from backend.auth import current_user
from backend.routers import cases, prompts, finops, tasks
from backend.services.passwords import verify_password, hash_password
from backend.services.readiness import readiness, validate_production
from backend.services.llm_router import llm

DUMMY_PASSWORD_HASH = hash_password(secrets.token_urlsafe(32))


@asynccontextmanager
async def lifespan(app):
    validate_production()
    init_db()
    from backend.services.jobs import JobWorker

    worker = JobWorker()
    if settings.enable_job_worker and not settings.demo_mode:
        worker.start()
    try:
        yield
    finally:
        worker.stop()


app = FastAPI(title="Kestrel Finance Fast-Track", version="0.1.0", lifespan=lifespan)


@app.middleware("http")
async def headers_and_csrf(request: Request, call_next):
    if request.method not in ("GET", "HEAD", "OPTIONS"):
        origin = request.headers.get("origin")
        if origin:
            from urllib.parse import urlparse

            origin_clean = origin.rstrip("/")
            base_clean = str(request.base_url).rstrip("/")
            origin_parsed = urlparse(origin_clean)
            base_parsed = urlparse(base_clean)
            host_header = request.headers.get("x-forwarded-host") or request.headers.get("host")
            is_same_origin = (
                origin_clean == base_clean
                or origin_parsed.netloc == base_parsed.netloc
                or (host_header and origin_parsed.netloc == host_header)
                or (
                    settings.demo_mode
                    and origin in ("http://localhost:5173", "http://127.0.0.1:5173")
                )
            )
            if not is_same_origin:
                return Response("Cross-origin mutation denied", status_code=403)
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["Referrer-Policy"] = "same-origin"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob:; font-src 'self'; connect-src 'self'; frame-src 'self' blob:; object-src 'self'; base-uri 'self'; frame-ancestors 'self'"
    )
    if request.url.path.startswith("/api/"):
        response.headers["Cache-Control"] = "no-store"
    return response


@app.get("/api/v1/health")
def health():
    return {
        "status": "ok",
        "demo_mode": settings.demo_mode,
        "model": llm.primary_model,
        "primary_provider": llm.primary_provider,
        "backup_model": settings.groq_model,
        "project": settings.gcp_project,
        "region": settings.gcp_region,
        "vertex_location": settings.vertex_location
        if llm.primary_provider == "vertex_gemini"
        else None,
        "inference_location": settings.vertex_location
        if llm.primary_provider == "vertex_gemini"
        else "provider-managed",
        "auth_mode": settings.auth_mode,
        "execution_mode": "offline" if settings.demo_mode else "live",
        "sample_cases": settings.seed_sample_cases,
        "app_env": settings.app_env,
    }


@app.get("/api/v1/ready")
def ready(response: Response):
    result = readiness()
    response.status_code = 200 if result["ready"] else 503
    return result


@app.post("/api/v1/auth/login")
def login(body: Login, response: Response, request: Request):
    if settings.auth_mode == "iap":
        raise HTTPException(403, "Sign in through the configured Google IAP gateway")
    if settings.auth_mode == "demo" and not settings.demo_mode:
        raise HTTPException(
            403, "Unauthenticated persona switching is disabled for live AI"
        )
    if settings.auth_mode == "password":
        failed = False
        with db() as conn:
            conn.execute("BEGIN IMMEDIATE")
            attempt = conn.execute(
                "SELECT * FROM login_attempts WHERE identity=?", (body.persona,)
            ).fetchone()
            if attempt and attempt["locked_until"] and attempt["locked_until"] > now():
                raise HTTPException(
                    429, "Too many sign-in attempts; retry after 15 minutes"
                )
            row = conn.execute(
                "SELECT password_hash FROM users WHERE persona=?", (body.persona,)
            ).fetchone()
            if (
                not verify_password(
                    body.password, row[0] if row else DUMMY_PASSWORD_HASH
                )
                or not row
            ):
                failures = (attempt["failures"] if attempt else 0) + 1
                lock = (
                    (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                    if failures >= 5
                    else None
                )
                conn.execute(
                    "INSERT INTO login_attempts(identity,failures,locked_until) VALUES(?,?,?) ON CONFLICT(identity) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until",
                    (body.persona, failures, lock),
                )
                failed = True
            else:
                conn.execute(
                    "DELETE FROM login_attempts WHERE identity=?", (body.persona,)
                )
        if failed:
            raise HTTPException(401, "Invalid operator credentials")
    token = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute("DELETE FROM sessions WHERE expires_at<?", (now(),))
        conn.execute(
            "INSERT INTO sessions(token_hash,persona,expires_at,auth_mode) VALUES(?,?,?,?)",
            (
                hashlib.sha256(token.encode()).hexdigest(),
                body.persona,
                (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
                settings.auth_mode,
            ),
        )
    response.set_cookie(
        "kestrel_session",
        token,
        httponly=True,
        samesite="strict",
        secure=settings.secure_cookies or request.url.scheme == "https",
        max_age=28800,
    )
    return {"persona": body.persona, **PERSONAS[body.persona]}


@app.get("/api/v1/auth/me")
def me(user=Depends(current_user)):
    return user


@app.post("/api/v1/auth/logout")
def logout(request: Request, response: Response):
    token = request.cookies.get("kestrel_session", "")
    with db() as conn:
        conn.execute(
            "DELETE FROM sessions WHERE token_hash=?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        )
    response.delete_cookie("kestrel_session")
    return {"logged_out": True}


for router in (cases.router, prompts.router, finops.router, tasks.router):
    app.include_router(router)

static = Path(settings.static_dir)
if (static / "assets").exists():
    app.mount("/assets", StaticFiles(directory=static / "assets"), name="assets")


@app.get("/{path:path}")
def spa(path: str):
    if path.startswith("api/"):
        raise HTTPException(404, "API route not found")
    index = static / "index.html"
    if not index.exists():
        raise HTTPException(
            503, "Build frontend first: cd frontend && npm ci && npm run build"
        )
    return FileResponse(index)
