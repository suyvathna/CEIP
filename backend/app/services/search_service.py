from sqlalchemy.orm import Session

from app.models.evidence import Evidence
from app.models.event import Event


def search_evidence_service(
    db: Session,
    project_id=None,
    filename=None,
    event_type=None,
    content_type=None,
):
    query = (
        db.query(Evidence)
        .join(Event)
    )

    if project_id:
        query = query.filter(
            Event.project_id == project_id
        )

    if filename:
        query = query.filter(
            Evidence.filename.ilike(f"%{filename}%")
        )

    if event_type:
        query = query.filter(
            Event.event_type == event_type
        )

    if content_type:
        query = query.filter(
            Evidence.content_type.ilike(f"%{content_type}%")
        )

    results = query.order_by(
        Evidence.created_at.desc()
    ).all()

    return {
        "total_results": len(results),
        "evidence": results,
    }