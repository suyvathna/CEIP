"""
Regression test for the Evidence delete FK-violation bug.

delete_evidence() used to call db.delete(evidence) / db.commit() without
first removing the EvidenceAccessLog rows that log_access() writes on
every upload/view/download. Since every upload immediately logs an
"UPLOAD" access row, evidence_access_log.evidence_id (a plain FK with no
ON DELETE clause) blocked the delete for literally every piece of
evidence, every time - surfaced to the caller as an unhandled 500 on
DELETE /evidence/{id}. Because the storage object was already removed
(delete_file runs before the DB delete in the API route) before that
500, the frontend was left showing a "phantom" evidence row whose file
no longer existed, so clicking it 500'd too.

This test drives evidence_service.delete_evidence() directly rather than
the HTTP route, since the route also calls out to MinIO (delete_file),
which isn't available in this environment - the bug and its fix live
entirely in the DB layer.

The rest of this test suite is pure logic and deliberately never opens a
database connection (see tests/conftest.py). Reproducing the FK
violation needs a real Postgres, since evidence/evidence_access_log use
Postgres-only column types (UUID), so this module builds its own
connection from backend/.env (or TEST_DATABASE_* overrides) and skips
itself entirely if neither is available.
"""

import os
from pathlib import Path
from uuid import uuid4

import pytest
from dotenv import dotenv_values
from sqlalchemy import create_engine, select
from sqlalchemy.orm import sessionmaker

BASE_DIR = Path(__file__).resolve().parent.parent
_dotenv_values = dotenv_values(BASE_DIR / ".env")


def _database_url() -> str | None:
    def _get(key: str) -> str | None:
        return os.environ.get(f"TEST_{key}") or os.environ.get(key) or _dotenv_values.get(key)

    host = _get("DATABASE_HOST")
    port = _get("DATABASE_PORT")
    name = _get("DATABASE_NAME")
    user = _get("DATABASE_USER")
    password = _get("DATABASE_PASSWORD")

    if not all([host, port, name, user, password]):
        return None

    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


_url = _database_url()
if _url is None:
    pytest.skip(
        "No database configured (add backend/.env or set TEST_DATABASE_* "
        "env vars) - skipping Evidence delete regression test",
        allow_module_level=True,
    )

_engine = create_engine(_url)
try:
    with _engine.connect():
        pass
except Exception as exc:  # noqa: BLE001 - any connection failure just skips this module
    pytest.skip(
        f"Could not connect to the configured database ({exc}) - skipping "
        "Evidence delete regression test",
        allow_module_level=True,
    )

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

from app.models.evidence import Evidence  # noqa: E402
from app.models.evidence_access_log import EvidenceAccessLog  # noqa: E402
from app.services.evidence_service import delete_evidence, log_access  # noqa: E402


def test_delete_evidence_with_access_log_succeeds():
    db = TestSessionLocal()
    try:
        evidence = Evidence(
            filename="test-photo.jpg",
            object_name=f"{uuid4()}.jpg",
            content_type="image/jpeg",
        )
        db.add(evidence)
        db.commit()
        db.refresh(evidence)

        # Every real upload does this immediately (see api/evidences.py
        # upload_evidence) - without it the bug wouldn't reproduce.
        log_access(db, evidence.id, "UPLOAD")

        access_row_exists = db.scalar(
            select(EvidenceAccessLog).where(EvidenceAccessLog.evidence_id == evidence.id)
        )
        assert access_row_exists is not None

        delete_evidence(db, evidence)

        assert db.get(Evidence, evidence.id) is None
        remaining_log = db.scalar(
            select(EvidenceAccessLog).where(EvidenceAccessLog.evidence_id == evidence.id)
        )
        assert remaining_log is None
    finally:
        db.rollback()
        db.close()
