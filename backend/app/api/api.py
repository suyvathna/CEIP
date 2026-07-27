from fastapi import APIRouter

from app.api.daily_diaries import router as daily_diary_router
from app.api.events import router as event_router
from app.api.projects import router as project_router

api_router = APIRouter()

api_router.include_router(project_router)
api_router.include_router(event_router)
api_router.include_router(daily_diary_router)