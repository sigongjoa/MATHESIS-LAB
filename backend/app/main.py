from fastapi import FastAPI
from backend.app.core.config import settings
from backend.app.api.v1.api import api_router
from backend.app.db.session import engine
from backend.app.models.base import Base

def create_tables(engine_override=None):
    target_engine = engine_override if engine_override else engine
    Base.metadata.create_all(bind=target_engine)

def get_application():
    app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
    )
    app.include_router(api_router, prefix=settings.API_V1_STR)
    return app

app = get_application()

@app.on_event("startup")
async def startup_event():
    create_tables()
    print("Database tables created/checked.")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)