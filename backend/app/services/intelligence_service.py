from sqlalchemy.orm import Session

from app.repositories.intelligence_repository import (
    search_daily_diaries,
    search_evidence,
    search_events,
)


def intelligence_search(
    db: Session,
    keyword: str,
):
    results = []

    events = search_events(
        db,
        keyword,
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

    diaries = search_daily_diaries(
        db,
        keyword,
    )

    for diary in diaries:
        results.append(
            {
                "id": diary.id,
                "item_type": "Daily Diary",
                "title": diary.work_completed or "Daily Diary",
                "created_at": diary.created_at,
            }
        )

    evidences = search_evidence(
        db,
        keyword,
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