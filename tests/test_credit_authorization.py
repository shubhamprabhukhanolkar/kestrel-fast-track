import json
from backend.database import db, init_db
from backend.services.passwords import hash_password
from tests.conftest import login

BASE = "/api/v1/cases/KF-2026-0892"
PASSWORD = "TestAuthorizer2026!"
DRAFT = {
    "recipient": "rm@example.invalid",
    "subject": "Outstanding documents",
    "body": "Dear RM, please provide the outstanding native PDF documents.",
}


def set_authorizer_password():
    with db() as conn:
        conn.execute(
            "UPDATE users SET password_hash=? WHERE persona='arjun'",
            (hash_password(PASSWORD),),
        )


def test_cibil_sample_manual_validation_and_idempotence(client):
    login(client, "meena")
    assert client.get(BASE).json()["cibil_score"] == 742
    for score in [299, 901, 750.5]:
        assert (
            client.put(
                BASE + "/cibil",
                json={"score": score, "note": "Supplied report reviewed"},
            ).status_code
            == 422
        )
    assert (
        client.put(
            BASE + "/cibil",
            json={"score": 756, "note": "Report supplied by borrower on 16 November"},
        ).status_code
        == 200
    )
    init_db()
    case = client.get(BASE).json()
    assert case["cibil_score"] == 756 and case["cibil_source"] == "manual"
    assert case["cibil_updated_by"] == "Meena Pillai"
    login(client, "arjun")
    assert (
        client.put(
            BASE + "/cibil", json={"score": 700, "note": "Test another score"}
        ).status_code
        == 403
    )


def test_email_requires_authorizer_and_fresh_password_and_records_no_delivery(client):
    set_authorizer_password()
    login(client, "meena")
    draft = client.post(BASE + "/email-drafts", json=DRAFT).json()
    path = BASE + f"/email-drafts/{draft['id']}/authorize"
    assert client.post(path, json={"password": PASSWORD}).status_code == 403
    login(client, "arjun")
    assert client.get(BASE + "/email-drafts/latest").json()["body"] == DRAFT["body"]
    assert client.post(path, json={"password": "wrong-password"}).status_code == 401
    assert (
        client.get(BASE + "/email-drafts/latest").json()["status"]
        == "pending_authorization"
    )
    result = client.post(path, json={"password": PASSWORD})
    assert result.status_code == 200 and result.json()["delivered"] is False
    assert (
        client.get(BASE + "/email-drafts/latest").json()["status"]
        == "approved_for_sending"
    )
    assert client.post(path, json={"password": PASSWORD}).status_code == 409
    with db() as conn:
        payload = conn.execute(
            "SELECT payload FROM audit_events WHERE action='email_approval_recorded'"
        ).fetchone()[0]
        assert PASSWORD not in payload
        assert json.loads(payload)["delivered"] is False


def test_email_rejects_stale_version_and_locks_repeated_password_failures(client):
    set_authorizer_password()
    login(client, "meena")
    first = client.post(BASE + "/email-drafts", json=DRAFT).json()
    second = client.post(
        BASE + "/email-drafts",
        json={**DRAFT, "body": "New and revised request for the current documents."},
    ).json()
    login(client, "arjun")
    assert (
        client.post(
            BASE + f"/email-drafts/{first['id']}/authorize", json={"password": PASSWORD}
        ).status_code
        == 409
    )
    path = BASE + f"/email-drafts/{second['id']}/authorize"
    for _ in range(5):
        assert client.post(path, json={"password": "wrong"}).status_code == 401
    assert client.post(path, json={"password": PASSWORD}).status_code == 429
    assert (
        client.get(BASE + "/email-drafts/latest").json()["status"]
        == "pending_authorization"
    )
