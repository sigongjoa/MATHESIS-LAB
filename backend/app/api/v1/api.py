from fastapi import APIRouter

from backend.app.api.v1.endpoints import curriculums, nodes # Import nodes router

api_router = APIRouter()
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"]) # Include nodes router