from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.dashboard_service import get_project_report_service
from app.schemas.project_report import ProjectReportResponse

from fastapi.responses import JSONResponse
import json
from fastapi.responses import StreamingResponse
from app.services.pdf_service import (
    generate_project_report_pdf,
)
from app.services.excel_service import (
    generate_project_report_excel,
)

router = APIRouter(
    prefix="/dashboard",
    tags=["Dashboard"],
)


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

@router.get("/{project_id}/report/pdf")
def export_project_report_pdf(
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

    pdf = generate_project_report_pdf(report)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition":
            f'attachment; filename="project_report_{project_id}.pdf"'
        },
    )

@router.get("/{project_id}/report/excel")
def export_project_report_excel(
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

    excel = generate_project_report_excel(report)

    return StreamingResponse(
        excel,
        media_type=(
            "application/vnd.openxmlformats-officedocument."
            "spreadsheetml.sheet"
        ),
        headers={
            "Content-Disposition": (
                f'attachment; filename="project_report_{project_id}.xlsx"'
            )
        },
    )