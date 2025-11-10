from fastapi import FastAPI, Request
from contextlib import asynccontextmanager
import logging

from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.db.session import engine
from backend.app.models.base import Base
from backend.app.models import curriculum, node, zotero_item, youtube_video

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_tables(engine_override=None):
    target_engine = engine_override if engine_override else engine
    Base.metadata.create_all(bind=target_engine)

@asynccontextmanager
async def lifespan(app: FastAPI):
    create_tables()
    logger.info("Database tables created/checked.")
    yield

def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        lifespan=lifespan
    )

    @app.middleware("http")
    async def log_requests(request: Request, call_next):
        logger.info(f"Incoming request: {request.method} {request.url.path}")
        response = await call_next(request)
        return response

    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)