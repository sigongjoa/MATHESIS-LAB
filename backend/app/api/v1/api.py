from fastapi import APIRouter

from backend.app.api.v1.endpoints import curriculums, nodes, literature, youtube, simple_crud # 모든 라우터 임포트

api_router = APIRouter()
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(literature.router, prefix="/literature", tags=["literature"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
api_router.include_router(simple_crud.router, prefix="/simple-curriculums", tags=["simple-curriculums"])