from uuid import UUID

from sqlalchemy.orm import Session

from app.repositories.intelligence_repository import (
    search_daily_logs,
    search_evidence,
    search_events,
)


def intelligence_search(
    db: Session,
    keyword: str,
    project_id: UUID | None = None,
):
    results = []

    events = search_events(
        db,
        keyword,
        project_id,
    )

    for event in events:
        results.append(
            {
                "id": event.id,
                "item_type": "Event",
                "title": event.title,
                "created_at": event.created_at,
            }
        )

    daily_logs = search_daily_logs(
        db,
        keyword,
        project_id,
    )

    for daily_log in daily_logs:
        results.append(
            {
                "id": daily_log.id,
                "item_type": "Daily Log",
                "title": daily_log.work_completed or "Daily Log",
                "created_at": daily_log.created_at,
            }
        )

    evidences = search_evidence(
        db,
        keyword,
        project_id,
    )

    for evidence in evidences:
        results.append(
            {
                "id": evidence.id,
                "item_type": "Evidence",
                "title": evidence.filename,
                "created_at": evidence.created_at,
            }
        )

    results.sort(
        key=lambda x: x["created_at"],
        reverse=True,
    )

    return results