from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.db.session import engine
from backend.app.models.base import Base
from backend.app.models import curriculum, node, zotero_item, youtube_video

def create_tables(engine_override=None):
    target_engine = engine_override if engine_override else engine
    Base.metadata.create_all(bind=target_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print("Database tables created/checked.")
    yield

def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    # CORS Middleware 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],  # 프론트엔드 주소
        allow_credentials=True,
        allow_methods=["*"],  # 모든 HTTP 메소드 허용
        allow_headers=["*"],  # 모든 HTTP 헤더 허용
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)