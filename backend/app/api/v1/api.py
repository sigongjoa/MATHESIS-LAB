from fastapi import APIRouter

from backend.app.api.v1.endpoints import curriculums, nodes, literature, youtube # Added youtube

api_router = APIRouter()
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(literature.router, prefix="/literature", tags=["literature"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"]) # Added youtube router