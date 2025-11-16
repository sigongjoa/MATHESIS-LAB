from fastapi import FastAPI
from contextlib import asynccontextmanager
from fastapi.middleware.cors import CORSMiddleware

from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.db.session import engine
from backend.app.models.base import Base
from backend.app.models import curriculum, node, zotero_item, youtube_video, user, user_session

def create_tables(engine_override=None):
    target_engine = engine_override if engine_override else engine
    Base.metadata.create_all(bind=target_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    print("Database tables created/checked.")
    yield

def get_application(db_engine=None, run_lifespan: bool = True):
    # Use the provided db_engine for create_tables if available, otherwise use the default
    current_engine = db_engine if db_engine else engine

    lifespan_context = None
    if run_lifespan:
        @asynccontextmanager
        async def _lifespan(app: FastAPI):
            create_tables(current_engine) # Pass the current_engine to create_tables
            print("Database tables created/checked.")
            yield
        lifespan_context = _lifespan

    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan_context
    )

    # CORS Middleware 추가
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://localhost:3002"],  # Frontend ports
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)