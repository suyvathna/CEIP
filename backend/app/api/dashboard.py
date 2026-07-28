from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.dashboard import DashboardResponse
from app.services.dashboard_service import (
    get_dashboard_service,
    get_project_report_service,
)
from app.schemas.project_report import ProjectReportResponse

from fastapi.responses import JSONResponse
import json

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


@router.get(
    "/{project_id}",
    response_model=DashboardResponse,
)
def read_dashboard(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    dashboard = get_dashboard_service(
        db,
        project_id,
    )

    if dashboard is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return dashboard

@router.get(
    "/{project_id}/report",
    response_model=ProjectReportResponse,
)
def project_report(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    report = get_project_report_service(
        db,
        project_id,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return report

@router.get("/{project_id}/report/export")
def export_project_report(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    report = get_project_report_service(
        db,
        project_id,
    )

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Project not found",
        )

    return JSONResponse(
        content=json.loads(
            json.dumps(
                report,
                default=str,
            )
        ),
        headers={
            "Content-Disposition":
            f'attachment; filename="project_report_{project_id}.json"'
        },
    )