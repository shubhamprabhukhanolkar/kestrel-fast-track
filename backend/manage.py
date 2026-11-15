"""Operator provisioning from a trusted console; no public registration endpoint."""

import argparse
import getpass
import warnings
from backend.config import settings
from backend.database import db, init_db, PERSONAS, now
from backend.services.passwords import hash_password


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["set-password", "store-groq-key"])
    parser.add_argument("--persona", choices=PERSONAS)
    args = parser.parse_args()
    if args.command == "store-groq-key":
        from google.cloud import secretmanager
        from google.api_core.exceptions import AlreadyExists

        with warnings.catch_warnings():
            warnings.simplefilter("error", getpass.GetPassWarning)
            key = getpass.getpass("Groq API key (hidden): ")
        if not key.startswith("gsk_") or len(key) < 20:
            raise SystemExit("Invalid Groq key format")
        client = secretmanager.SecretManagerServiceClient()
        parent = f"projects/{settings.gcp_project}"
        secret = f"{parent}/secrets/kestrel-groq-api-key"
        try:
            client.create_secret(
                request={
                    "parent": parent,
                    "secret_id": "kestrel-groq-api-key",
                    "secret": {
                        "replication": {
                            "user_managed": {"replicas": [{"location": "asia-south1"}]}
                        }
                    },
                }
            )
        except AlreadyExists:
            pass
        client.add_secret_version(
            request={"parent": secret, "payload": {"data": key.encode()}}
        )
        print(f"Groq key stored securely: {secret}/versions/latest")
        return
    if not args.persona:
        parser.error("--persona is required for set-password")
    password = getpass.getpass(
        f"New password for {PERSONAS[args.persona]['name']} (12+ characters): "
    )
    if password != getpass.getpass("Repeat password: "):
        raise SystemExit("Passwords do not match")
    digest = hash_password(password)
    init_db()
    with db() as conn:
        conn.execute(
            "INSERT INTO users(persona,password_hash,updated_at) VALUES(?,?,?) ON CONFLICT(persona) DO UPDATE SET password_hash=excluded.password_hash,updated_at=excluded.updated_at",
            (args.persona, digest, now()),
        )
        conn.execute("DELETE FROM sessions WHERE persona=?", (args.persona,))
        conn.execute("DELETE FROM login_attempts WHERE identity=?", (args.persona,))
    print(
        f"Password updated for {PERSONAS[args.persona]['name']}; prior sessions revoked."
    )


if __name__ == "__main__":
    main()
