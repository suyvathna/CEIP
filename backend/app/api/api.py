from fastapi import APIRouter

from app.api.daily_diaries import router as daily_diary_router
from app.api.events import router as event_router
from app.api.projects import router as project_router
from app.api.storage import router as storage_router
from app.api.evidences import router as evidence_router
from app.api.dashboard import router as dashboard_router
from app.api.timeline import router as timeline_router
from app.api.users import router as user_router
from app.api.auth import router as auth_router
from app.api.intelligence import router as intelligence_router

api_router = APIRouter()

api_router.include_router(project_router)
api_router.include_router(event_router)
api_router.include_router(daily_diary_router)
api_router.include_router(storage_router)
api_router.include_router(evidence_router)
api_router.include_router(dashboard_router)
api_router.include_router(timeline_router)
api_router.include_router(user_router)
api_router.include_router(auth_router)
api_router.include_router(intelligence_router)