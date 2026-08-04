from datetime import date
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.db.session import get_db
from app.models.project import Project
from app.schemas.daily_log import (
    DailyLogCreate,
    DailyLogResponse,
)

from app.schemas.daily_report import DailyReportResponse
from app.services.daily_log_service import (
    create_daily_log,
    delete_daily_log,
    get_daily_logs,
    get_daily_log,
    get_daily_report,
    get_daily_reports_for_project,
    update_daily_log,
    get_logs_for_event,
    get_logs_for_project,
)
from app.services.excel_service import (
    generate_daily_log_excel,
    generate_project_daily_log_compilation_excel,
)
from app.services.pdf_service import (
    generate_daily_log_pdf,
    generate_project_daily_log_compilation_pdf,
)

router = APIRouter(
    prefix="/daily-logs",
    tags=["Daily Logs"],
)

@router.post("/", response_model=DailyLogResponse)
def create_daily_log_endpoint(
    daily_log: DailyLogCreate,
    db: Session = Depends(get_db),
):
    return create_daily_log(db, daily_log)


@router.get("/", response_model=list[DailyLogResponse])
def read_daily_logs_endpoint(
    db: Session = Depends(get_db),
):
    return get_daily_logs(db)

@router.get("/event/{event_id}", response_model=list[DailyLogResponse])
def read_logs_for_event_endpoint(
    event_id: UUID,
    db: Session = Depends(get_db),
):
    return get_logs_for_event(db, event_id)

@router.get("/project/{project_id}", response_model=list[DailyLogResponse])
def read_logs_for_project_endpoint(
    project_id: UUID,
    db: Session = Depends(get_db),
):
    return get_logs_for_project(db, project_id)


@router.get("/project/{project_id}/report/pdf")
def project_daily_log_report_pdf_endpoint(
    project_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    """
    The Report tab's compiled Daily Log export - every Daily Log for this
    project (optionally bounded to a date range), formatted to match the
    reference site-log template, one day per section. This is the
    day-by-day site record a Contractor would actually hand an Engineer
    or DAAB alongside a claim.
    """
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    reports = get_daily_reports_for_project(db, project_id, start_date, end_date)
    pdf = generate_project_daily_log_compilation_pdf(reports, project.project_name)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="daily_log_compilation_{project_id}.pdf"'
        },
    )


@router.get("/project/{project_id}/report/excel")
def project_daily_log_report_excel_endpoint(
    project_id: UUID,
    start_date: date | None = None,
    end_date: date | None = None,
    db: Session = Depends(get_db),
):
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    reports = get_daily_reports_for_project(db, project_id, start_date, end_date)
    excel = generate_project_daily_log_compilation_excel(reports, project.project_name)

    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="daily_log_compilation_{project_id}.xlsx"'
        },
    )


@router.get("/{daily_log_id}", response_model=DailyLogResponse)
def read_daily_log_endpoint(
    daily_log_id: UUID,
    db: Session = Depends(get_db),
):
    daily_log = get_daily_log(db, daily_log_id)

    if daily_log is None:
        raise HTTPException(
            status_code=404,
            detail="Daily log not found",
        )

    return daily_log


@router.put("/{daily_log_id}", response_model=DailyLogResponse)
def update_daily_log_endpoint(
    daily_log_id: UUID,
    daily_log: DailyLogCreate,
    db: Session = Depends(get_db),
):
    updated = update_daily_log(db, daily_log_id, daily_log)

    if updated is None:
        raise HTTPException(
            status_code=404,
            detail="Daily log not found",
        )

    return updated


@router.delete("/{daily_log_id}")
def delete_daily_log_endpoint(
    daily_log_id: UUID,
    db: Session = Depends(get_db),
):
    deleted = delete_daily_log(db, daily_log_id)

    if deleted is None:
        raise HTTPException(
            status_code=404,
            detail="Daily log not found",
        )

    return {"message": "Daily log deleted successfully"}


@router.get(
    "/{daily_log_id}/report",
    response_model=DailyReportResponse,
)
def daily_report_endpoint(
    daily_log_id: UUID,
    db: Session = Depends(get_db),
):
    report = get_daily_report(db, daily_log_id)

    if report is None:
        raise HTTPException(
            status_code=404,
            detail="Daily log not found",
        )

    return report


@router.get("/{daily_log_id}/report/pdf")
def daily_log_report_pdf_endpoint(
    daily_log_id: UUID,
    db: Session = Depends(get_db),
):
    """Single-day Daily Log PDF, matching the reference site-log
    template's section layout - see pdf_service.generate_daily_log_pdf."""
    report = get_daily_report(db, daily_log_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Daily log not found")

    project = db.get(Project, report["project_id"])
    pdf = generate_daily_log_pdf(report, project.project_name if project else None)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="daily_log_{daily_log_id}.pdf"'
        },
    )


@router.get("/{daily_log_id}/report/excel")
def daily_log_report_excel_endpoint(
    daily_log_id: UUID,
    db: Session = Depends(get_db),
):
    report = get_daily_report(db, daily_log_id)
    if report is None:
        raise HTTPException(status_code=404, detail="Daily log not found")

    excel = generate_daily_log_excel(report)

    return StreamingResponse(
        excel,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={
            "Content-Disposition": f'attachment; filename="daily_log_{daily_log_id}.xlsx"'
        },
    )
