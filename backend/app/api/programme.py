from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.programme import (
    ActivityCreate,
    ClaimDelayAnalysisOut,
    EventActivityImpactCreate,
    EventActivityImpactOut,
    PredecessorLinkRequest,
    ProgrammeActivityOut,
    ProjectCPMOut,
)
from app.services.programme_service import (
    add_predecessor,
    analyze_claim_delay,
    compute_baseline_cpm,
    create_activity,
    create_impact,
    delete_activity,
    get_project_activities,
    remove_predecessor,
    update_activity,
)

router = APIRouter(prefix="/programme", tags=["Programme"])


@router.post("/project/{project_id}/activities", response_model=ProgrammeActivityOut)
def create_activity_endpoint(
    project_id: UUID, payload: ActivityCreate, db: Session = Depends(get_db)
):
    return create_activity(db, project_id, payload)


@router.get(
    "/project/{project_id}/activities", response_model=list[ProgrammeActivityOut]
)
def list_activities_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    return get_project_activities(db, project_id)


@router.put("/activities/{activity_id}", response_model=ProgrammeActivityOut)
def update_activity_endpoint(
    activity_id: UUID, payload: ActivityCreate, db: Session = Depends(get_db)
):
    activity = update_activity(db, activity_id, payload)
    if activity is None:
        raise HTTPException(status_code=404, detail="Activity not found")
    return activity


@router.delete("/activities/{activity_id}")
def delete_activity_endpoint(activity_id: UUID, db: Session = Depends(get_db)):
    deleted = delete_activity(db, activity_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Activity not found")
    return {"message": "Activity deleted successfully"}


@router.post("/activities/{activity_id}/predecessors")
def add_predecessor_endpoint(
    activity_id: UUID, payload: PredecessorLinkRequest, db: Session = Depends(get_db)
):
    add_predecessor(db, activity_id, payload.predecessor_id)
    return {"message": "Predecessor linked"}


@router.delete("/activities/{activity_id}/predecessors/{predecessor_id}")
def remove_predecessor_endpoint(
    activity_id: UUID, predecessor_id: UUID, db: Session = Depends(get_db)
):
    removed = remove_predecessor(db, activity_id, predecessor_id)
    if not removed:
        raise HTTPException(status_code=404, detail="Predecessor link not found")
    return {"message": "Predecessor unlinked"}


@router.post(
    "/events/{event_id}/impacts", response_model=EventActivityImpactOut
)
def create_impact_endpoint(
    event_id: UUID, payload: EventActivityImpactCreate, db: Session = Depends(get_db)
):
    return create_impact(db, event_id, payload)


@router.get("/project/{project_id}/cpm", response_model=ProjectCPMOut)
def project_cpm_endpoint(project_id: UUID, db: Session = Depends(get_db)):
    result = compute_baseline_cpm(db, project_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail="No activities recorded for this project's programme yet.",
        )

    activities = get_project_activities(db, project_id)
    codes_by_id = {str(a.id): a.activity_code for a in activities}

    return {
        "project_id": project_id,
        "project_start": result.project_start,
        "project_finish": result.project_finish,
        "activities": [
            {
                "id": a.id,
                "activity_code": codes_by_id.get(a.id, a.id),
                "name": a.name,
                "duration_days": a.duration_days,
                "early_start": a.early_start,
                "early_finish": a.early_finish,
                "late_start": a.late_start,
                "late_finish": a.late_finish,
                "total_float": a.total_float,
                "is_critical": a.is_critical,
            }
            for a in result.activities.values()
        ],
    }


@router.get(
    "/claims/{claim_id}/delay-analysis", response_model=ClaimDelayAnalysisOut
)
def claim_delay_analysis_endpoint(
    claim_id: UUID, project_id: UUID, db: Session = Depends(get_db)
):
    analysis = analyze_claim_delay(db, claim_id, project_id)
    if analysis is None:
        raise HTTPException(
            status_code=404,
            detail="No activities recorded for this project's programme yet.",
        )
    return analysis
