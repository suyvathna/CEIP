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
    get_evidence,
    get_evidences,
    search_evidence,
)
from app.services.storage_service import (
    download_file,
    upload_file,
)

router = APIRouter(
    prefix="/evidence",
    tags=["Evidence"],
)


@router.post("/upload", response_model=EvidenceResponse)
def upload_evidence(
    event_id: UUID = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    uploaded = upload_file(file)

    evidence = Evidence(
        event_id=event_id,
        filename=uploaded["filename"],
        object_name=uploaded["object_name"],
        content_type=uploaded["content_type"],
    )

    return create_evidence(db, evidence)


@router.get("/", response_model=list[EvidenceResponse])
def read_evidences(
    db: Session = Depends(get_db),
):
    return get_evidences(db)


@router.get("/search", response_model=list[EvidenceResponse])
def search_evidences(
    filename: str | None = None,
    event_id: UUID | None = None,
    db: Session = Depends(get_db),
):
    return search_evidence(
        db=db,
        filename=filename,
        event_id=event_id,
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

    return evidence


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

    return StreamingResponse(
        file,
        media_type=evidence.content_type,
        headers={
            "Content-Disposition":
                f'attachment; filename="{evidence.filename}"'
        },
    )