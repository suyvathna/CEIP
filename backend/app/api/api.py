from fastapi import APIRouter

from app.api.daily_logs import router as daily_log_router
from app.api.events import router as event_router
from app.api.projects import router as project_router
from app.api.storage import router as storage_router
from app.api.evidences import router as evidence_router
from app.api.dashboard import router as dashboard_router
from app.api.users import router as user_router
from app.api.auth import router as auth_router
from app.api.intelligence import router as intelligence_router
from app.api.claims import router as claim_router
from app.api.claim_facts import router as claim_fact_router
from app.api.correspondence import router as correspondence_router
from app.api.claim_access import router as claim_access_router
from app.api.claim_access import public_router as public_claim_access_router

# Engine A - the "ALWAYS DO" compliance scheduler, plus the unified
# deadline feed both engines publish into.
from app.api.compliance import router as compliance_router

# Engine B - the "DO-IN-CASE" contractual state machine.
from app.api.determinations import router as determination_router
from app.api.variations import router as variation_router

# The alert stream both engines write to.
from app.api.notifications import router as notification_router

api_router = APIRouter()

api_router.include_router(project_router)
api_router.include_router(event_router)
api_router.include_router(daily_log_router)
api_router.include_router(storage_router)
api_router.include_router(evidence_router)
api_router.include_router(dashboard_router)
api_router.include_router(user_router)
api_router.include_router(auth_router)
api_router.include_router(intelligence_router)
api_router.include_router(claim_router)
api_router.include_router(claim_fact_router)
api_router.include_router(correspondence_router)
api_router.include_router(claim_access_router)
api_router.include_router(public_claim_access_router)
api_router.include_router(compliance_router)
api_router.include_router(determination_router)
api_router.include_router(variation_router)
api_router.include_router(notification_router)
