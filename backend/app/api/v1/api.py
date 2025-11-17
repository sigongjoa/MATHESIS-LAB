from fastapi import APIRouter

from backend.app.api.v1.endpoints import auth, curriculums, nodes, literature, youtube, simple_crud, gcp, google_drive # 모든 라우터 임포트

api_router = APIRouter()
api_router.include_router(auth.router)  # Auth endpoints at /auth
api_router.include_router(curriculums.router, prefix="/curriculums", tags=["curriculums"])
api_router.include_router(nodes.router, prefix="/nodes", tags=["nodes"])
api_router.include_router(literature.router, prefix="/literature", tags=["literature"])
api_router.include_router(youtube.router, prefix="/youtube", tags=["youtube"])
api_router.include_router(simple_crud.router, prefix="/simple-curriculums", tags=["simple-curriculums"])
api_router.include_router(gcp.router)  # GCP endpoints at /gcp
api_router.include_router(google_drive.router)  # Google Drive endpoints at /google-drive