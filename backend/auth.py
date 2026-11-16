import hashlib
from datetime import datetime, timezone
from fastapi import HTTPException, Request
from backend.config import settings
from backend.database import db, PERSONAS


def current_user(request: Request):
    if settings.auth_mode == "iap":
        if not settings.iap_audience:
            raise HTTPException(503, "Live mode requires IAP_AUDIENCE and IAP_ROLE_MAP")
        from google.oauth2 import id_token
        from google.auth.transport import requests

        assertion = request.headers.get("x-goog-iap-jwt-assertion", "")
        try:
            claims = id_token.verify_token(
                assertion,
                requests.Request(),
                audience=settings.iap_audience,
                certs_url="https://www.gstatic.com/iap/verify/public_key",
            )
            if claims.get("iss") != "https://cloud.google.com/iap":
                raise ValueError("Invalid issuer")
            persona = settings.iap_role_map[claims["email"]]
            return {"persona": persona, **PERSONAS[persona]}
        except Exception:
            raise HTTPException(401, "Verified IAP identity required")
    if settings.auth_mode == "demo" and not settings.demo_mode:
        raise HTTPException(
            503, "Unauthenticated persona switching is disabled for live execution"
        )
    token = request.cookies.get("kestrel_session", "")
    with db() as conn:
        session = conn.execute(
            "SELECT * FROM sessions WHERE token_hash=?",
            (hashlib.sha256(token.encode()).hexdigest(),),
        ).fetchone()
    if (
        not session
        or session["auth_mode"] != settings.auth_mode
        or datetime.fromisoformat(session["expires_at"]) < datetime.now(timezone.utc)
    ):
        raise HTTPException(401, "Authenticated operator session required")
    return {"persona": session["persona"], **PERSONAS[session["persona"]]}


def require_role(user, *roles):
    if user["persona"] not in roles:
        raise HTTPException(
            403, "This action requires " + ", ".join(PERSONAS[r]["name"] for r in roles)
        )


def confirm_operator_password(user, password, purpose):
    """Verify a fresh password without replacing the session or logging the secret."""
    from datetime import timedelta
    from backend.database import now
    from backend.services.passwords import verify_password

    identity = f"{purpose}:{user['persona']}"
    failed = False
    with db() as conn:
        conn.execute("BEGIN IMMEDIATE")
        attempt = conn.execute(
            "SELECT * FROM login_attempts WHERE identity=?", (identity,)
        ).fetchone()
        if attempt and attempt["locked_until"] and attempt["locked_until"] > now():
            raise HTTPException(
                429, "Too many password attempts; retry after 15 minutes"
            )
        row = conn.execute(
            "SELECT password_hash FROM users WHERE persona=?", (user["persona"],)
        ).fetchone()
        if not row or not verify_password(password, row[0]):
            failures = (attempt["failures"] if attempt else 0) + 1
            locked = (
                (datetime.now(timezone.utc) + timedelta(minutes=15)).isoformat()
                if failures >= 5
                else None
            )
            conn.execute(
                "INSERT INTO login_attempts(identity,failures,locked_until) VALUES(?,?,?) ON CONFLICT(identity) DO UPDATE SET failures=excluded.failures,locked_until=excluded.locked_until",
                (identity, failures, locked),
            )
            failed = True
        else:
            conn.execute("DELETE FROM login_attempts WHERE identity=?", (identity,))
    if failed:
        raise HTTPException(401, "Authorizer password was not accepted")
