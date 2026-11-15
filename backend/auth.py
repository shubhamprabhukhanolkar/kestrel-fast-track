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
