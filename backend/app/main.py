from fastapi import FastAPI
from contextlib import asynccontextmanager # 1. asynccontextmanager 임포트
from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.db.session import engine
from backend.app.models.base import Base

def create_tables(engine_override=None):
    target_engine = engine_override if engine_override else engine
    Base.metadata.create_all(bind=target_engine)

@asynccontextmanager # 2. lifespan 관리자 정의
async def lifespan(app: FastAPI):
    # 시작 시 실행
    create_tables()
    print("Database tables created/checked.")
    yield
    # 종료 시 실행 (필요한 경우)

def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan # 3. lifespan 적용
    )
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

# 4. 기존 @app.on_event("startup") 핸들러 제거

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)