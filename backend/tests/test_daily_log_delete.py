"""
Regression test for the Daily Log delete FK-violation bug.

delete_daily_log() used to call db.delete(db_daily_log) / db.commit()
without first removing the DailyLogEventLink rows created by
_auto_link_same_day_events (or additional_event_ids) when a Daily Log has
been auto-linked to same-day Events. Postgres then rejected the delete
with a ForeignKeyViolation on daily_log_event_links, surfaced to the API
caller as an unhandled 500 on DELETE /daily-logs/{id}.

The rest of this test suite is pure logic and deliberately never opens a
database connection (see tests/conftest.py). Reproducing the FK
violation needs a real Postgres, since daily_logs/events/daily_log_event_links
use Postgres-only column types (UUID, JSONB), so this module builds its
own connection from backend/.env (or TEST_DATABASE_* overrides) and skips
itself entirely if neither is available.
"""

import os
from datetime import date, time
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
        "env vars) - skipping Daily Log delete regression test",
        allow_module_level=True,
    )

_engine = create_engine(_url)
try:
    with _engine.connect():
        pass
except Exception as exc:  # noqa: BLE001 - any connection failure just skips this module
    pytest.skip(
        f"Could not connect to the configured database ({exc}) - skipping "
        "Daily Log delete regression test",
        allow_module_level=True,
    )

TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=_engine)

from fastapi.testclient import TestClient  # noqa: E402

from app.db.session import get_db  # noqa: E402
from app.main import app  # noqa: E402
from app.models.daily_log import DailyLog, DailyLogEventLink  # noqa: E402
from app.models.event import Event  # noqa: E402
from app.models.project import Project  # noqa: E402


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = _override_get_db


@pytest.fixture
def project_and_event():
    db = TestSessionLocal()
    project = Project(
        project_code=f"TEST-{uuid4().hex[:10]}",
        project_name="Daily Log Delete Regression Project",
        client_name="Test Client",
        contract_type="Design-Build",
        country="Cambodia",
        city="Phnom Penh",
        planned_start=date(2026, 1, 1),
        planned_finish=date(2026, 12, 31),
    )
    db.add(project)
    db.flush()

    diary_date = date(2026, 3, 15)

    event = Event(
        project_id=project.id,
        title="Same-day event",
        event_date=diary_date,
        event_time=time(9, 0),
        event_type="Instruction",
    )
    db.add(event)
    db.commit()

    yield project.id, event.id, diary_date

    db.query(DailyLogEventLink).filter(
        DailyLogEventLink.event_id == event.id
    ).delete()
    db.query(DailyLog).filter(DailyLog.project_id == project.id).delete()
    db.query(Event).filter(Event.id == event.id).delete()
    db.query(Project).filter(Project.id == project.id).delete()
    db.commit()
    db.close()


def test_delete_daily_log_auto_linked_to_event_returns_200(project_and_event):
    project_id, event_id, diary_date = project_and_event

    with TestClient(app) as client:
        create_response = client.post(
            "/daily-logs/",
            json={
                "project_id": str(project_id),
                "diary_date": diary_date.isoformat(),
            },
        )
        assert create_response.status_code == 200, create_response.text
        daily_log_id = create_response.json()["id"]

        # Sanity-check the auto-link actually fired, otherwise this test
        # would pass even without the fix.
        assert str(event_id) in create_response.json()["linked_event_ids"]

        db = TestSessionLocal()
        try:
            link_exists = db.scalar(
                select(DailyLogEventLink).where(
                    DailyLogEventLink.daily_log_id == daily_log_id,
                    DailyLogEventLink.event_id == event_id,
                )
            )
            assert link_exists is not None
        finally:
            db.close()

        delete_response = client.delete(f"/daily-logs/{daily_log_id}")
        assert delete_response.status_code == 200, delete_response.text

        get_response = client.get(f"/daily-logs/{daily_log_id}")
        assert get_response.status_code == 404
