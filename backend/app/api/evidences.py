from uuid import UUID

from fastapi import (
    APIRouter,
    Depends,
    File,
    Form,
    HTTPException,
    UploadFile,
)
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.evidence import Evidence
from app.schemas.evidence import EvidenceResponse
from app.services.evidence_service import (
    create_evidence,
    delete_evidence,
    get_access_log,
    get_evidence,
    get_evidences,
    log_access,
    search_evidence,
)
from app.services.storage_service import (
    delete_file,
    download_file,
    upload_file,
)

from app.services.auth_service import (get_current_user)

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
    #dependencies=[Depends(get_current_user)]    # this line ensures that all endpoints in this router require authentication
)


@router.post("/upload", response_model=EvidenceResponse)
def upload_evidence(
    event_id: UUID | None = Form(None),
    daily_log_id: UUID | None = Form(None),
    correspondence_id: UUID | None = Form(None),
    obligation_id: UUID | None = Form(None),
    category: str | None = Form(None),
    caption: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    # An attachment needs exactly one owner. Most Daily Log photos (a
    # delivery, an HSE finding, general progress) have no corresponding
    # Event at all, which is exactly why event_id can no longer be
    # required here - but the upload still has to land somewhere.
    if not event_id and not daily_log_id and not correspondence_id and not obligation_id:
        raise HTTPException(
            status_code=422,
            detail="Provide one of event_id, daily_log_id, correspondence_id or obligation_id.",
        )

    uploaded = upload_file(file)

    evidence = Evidence(
        event_id=event_id,
        daily_log_id=daily_log_id,
        correspondence_id=correspondence_id,
        obligation_id=obligation_id,
        category=category,
        caption=caption,
        filename=uploaded["filename"],
        object_name=uploaded["object_name"],
        content_type=uploaded["content_type"],
        sha256_hash=uploaded["sha256_hash"],
    )

    created = create_evidence(db, evidence)
    log_access(db, created.id, "UPLOAD")
    return created


@router.get("/", response_model=list[EvidenceResponse])
def read_evidences(
    db: Session = Depends(get_db),
):
    return get_evidences(db)


@router.get("/search", response_model=list[EvidenceResponse])
def search_evidences(
    filename: str | None = None,
    event_id: UUID | None = None,
    daily_log_id: UUID | None = None,
    correspondence_id: UUID | None = None,
    obligation_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return search_evidence(
        db=db,
        filename=filename,
        event_id=event_id,
        daily_log_id=daily_log_id,
        correspondence_id=correspondence_id,
        obligation_id=obligation_id,
    )


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def read_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    log_access(db, evidence.id, "VIEW")
    return evidence


@router.get("/{evidence_id}/access-log")
def read_evidence_access_log(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    return get_access_log(db, evidence_id)


@router.delete("/{evidence_id}")
def remove_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    # Check the lock BEFORE touching storage - deleting the object first
    # and only then discovering it's locked would destroy the file while
    # the DB record survives, which is worse than either failure alone.
    if evidence.is_locked:
        raise HTTPException(
            status_code=409,
            detail=(
                "This evidence is locked because it's attached to a "
                "submitted claim and can no longer be deleted."
            ),
        )

    delete_file(evidence.object_name)
    delete_evidence(db, evidence)

    return {
        "message": "Evidence deleted successfully"
    }


@router.get("/download/{evidence_id}")
def download_evidence(
    evidence_id: UUID,
    db: Session = Depends(get_db),
):
    evidence = get_evidence(db, evidence_id)

    if evidence is None:
        raise HTTPException(
            status_code=404,
            detail="Evidence not found",
        )

    file = download_file(evidence.object_name)
    log_access(db, evidence.id, "DOWNLOAD")

    return StreamingResponse(
        file,
        media_type=evidence.content_type,
        headers={
            "Content-Disposition":
                f'attachment; filename="{evidence.filename}"'
        },
    )
