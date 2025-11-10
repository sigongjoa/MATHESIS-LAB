from fastapi import APIRouter

from backend.app.api.v1.endpoints import curriculums

api_router = APIRouter()
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])