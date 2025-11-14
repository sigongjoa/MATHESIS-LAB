import pytest
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Connection
from sqlalchemy.pool import StaticPool
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Generator

from backend.app.main import app
from backend.app.db.session import get_db, SessionLocal
from backend.app.models.base import Base
from backend.app.api.v1.api import api_router

# Import all models so that Base.metadata.create_all() works
from backend.app.models import curriculum, node, zotero_item, youtube_video

# SQLite 인메모리 데이터베이스 설정 (connection 공유 방식)
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

# 테스트용 엔진 생성 (StaticPool로 모든 세션이 같은 인메모리 DB 공유)
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,  # 모든 connection이 같은 인메모리 DB를 공유
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    테스트용 데이터베이스 세션을 제공하는 픽스처.
    인메모리 DB를 사용하여 세션 격리 문제를 해결합니다.
    각 테스트마다 테이블을 생성하고 종료 시 삭제합니다.
    """
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)

    # 세션 생성
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # 모든 테이블 삭제 (다음 테스트를 위해)
        Base.metadata.drop_all(bind=engine)

@pytest.fixture(name="client")
def client_fixture(db_session: Session): # Changed type hint to Session
    """
    테스트용 FastAPI 클라이언트를 제공하는 픽스처.
    각 테스트마다 새로운 FastAPI 앱 인스턴스를 생성하고, 의존성을 오버라이드합니다.
    """
    from backend.app.core.config import settings # Import settings
    from backend.app.db.session import get_db as get_main_db # 원본 get_db를 가져옴

    test_app = FastAPI(
        title=settings.PROJECT_NAME,
        openapi_url="/api/v1/openapi.json",
    )
    test_app.include_router(api_router, prefix="/api/v1")

    def override_get_db():
        yield db_session

    test_app.dependency_overrides[get_main_db] = override_get_db
    with TestClient(test_app) as c:
        yield c
    test_app.dependency_overrides.clear() # 의존성 오버라이드 초기화