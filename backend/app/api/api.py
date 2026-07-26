from fastapi import APIRouter

from app.api.projects import router as project_router

api_router = APIRouter()

api_router.include_router(project_router)