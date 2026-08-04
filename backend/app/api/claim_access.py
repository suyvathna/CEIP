from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.claim_access import ClaimAccessTokenCreate, ClaimAccessTokenOut
from app.services.claim_access_service import create_access_token, resolve_access_token
from app.services.claim_service import get_claim, get_claim_report_data
from app.services.pdf_service import generate_claim_report_pdf

router = APIRouter(prefix="/claims", tags=["Claim Access Links"])
# Deliberately outside the authenticated app entirely, and with no JSON
# endpoint of any kind - CEIP is Contractor-only, and this router is the
# ENTIRE surface an Engineer (or anyone else without a CEIP account) ever
# touches. Resolving a valid token serves a PDF directly; there is
# nothing here to log into, browse, or write back through.
public_router = APIRouter(prefix="/public/claims", tags=["Public Claim Access"])


@router.post("/{claim_id}/access-links", response_model=ClaimAccessTokenOut)
def create_claim_access_link(
    claim_id: UUID, payload: ClaimAccessTokenCreate, db: Session = Depends(get_db)
):
    """
    Generates a link the Contractor can send directly (email, Telegram,
    whatever) to anyone who needs to see this claim - typically the
    Engineer. There's no email-sending service wired up in this platform,
    so the link itself is returned here rather than dispatched
    automatically. Opening it serves a read-only PDF straight from the
    API (see the public_router below); it is never a page of this app.
    """
    claim = get_claim(db, claim_id)
    if claim is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    return create_access_token(
        db, claim_id, payload.recipient_email, payload.ttl_days
    )


@public_router.get("/{token}/pdf")
def public_claim_report_pdf(token: str, db: Session = Depends(get_db)):
    """
    The only thing anyone without a CEIP account can ever reach: resolve
    a valid, unexpired token straight to the same read-only PDF the
    Contractor can download themselves (see
    claim_service.get_claim_report_data / pdf_service.generate_claim_report_pdf).
    inline disposition so it opens straight in the browser rather than
    forcing a download - view-only by default, save is still up to them.
    """
    access = resolve_access_token(db, token)
    if access is None:
        raise HTTPException(
            status_code=404,
            detail="This link is invalid or has expired. Ask the Contractor "
            "for a new one.",
        )

    data = get_claim_report_data(db, access.claim_id)
    if data is None:
        raise HTTPException(status_code=404, detail="Claim not found")

    pdf = generate_claim_report_pdf(data)

    return StreamingResponse(
        pdf,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f'inline; filename="claim_report_{access.claim_id}.pdf"'
        },
    )
