import hashlib
from pathlib import Path
from backend.config import settings


def persist_document(case_id, name, content):
    digest = hashlib.sha256(content).hexdigest()
    if settings.documents_bucket:
        from google.cloud import storage

        blob = (
            storage.Client(project=settings.gcp_project)
            .bucket(settings.documents_bucket)
            .blob(f"documents/{case_id}/{digest}/{name}")
        )
        # Immutable content-addressed object; metadata is only committed after upload succeeds.
        from google.api_core.exceptions import PreconditionFailed

        try:
            blob.upload_from_string(
                content,
                content_type="application/pdf",
                if_generation_match=0,
                timeout=30,
            )
        except PreconditionFailed:
            # The key includes the SHA-256 of the complete bytes, so reuse is idempotent.
            pass
        return f"gs://{settings.documents_bucket}/{blob.name}"
    path = Path(settings.document_dir) / case_id / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content)
    return str(path)


def read_document(location):
    if location.startswith("gs://"):
        from google.cloud import storage

        bucket, key = location[5:].split("/", 1)
        if bucket != settings.documents_bucket:
            raise ValueError("Document is outside the configured tenancy bucket")
        return (
            storage.Client(project=settings.gcp_project)
            .bucket(bucket)
            .blob(key)
            .download_as_bytes(timeout=30)
        )
    resolved = Path(location).resolve()
    if not resolved.is_relative_to(Path(settings.document_dir).resolve()):
        raise ValueError("Document path is outside the configured document root")
    return resolved.read_bytes()
