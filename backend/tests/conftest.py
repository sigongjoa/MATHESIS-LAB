import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Connection
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Generator

from backend.app.main import app
from backend.app.db.session import get_db, SessionLocal
from backend.app.models.base import Base
from backend.app.api.v1.api import api_router

# SQLite 인메모리 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(name="db_session")
def db_session_fixture() -> Generator[Session, None, None]:
    """
    테스트용 데이터베이스 세션을 제공하는 픽스처.
    각 테스트마다 트랜잭션을 시작하고, 테스트 종료 시 롤백합니다.
    테이블은 세션 시작 전에 생성하고, 세션 종료 후에 삭제합니다.
    """
    # 모든 테이블 생성
    Base.metadata.create_all(bind=engine)
    
    db = TestingSessionLocal()
    try:
        yield db  # 테스트 함수에 세션 제공
        db.commit() # Commit changes to the file-based DB
    finally:
        db.rollback() # Rollback to clean up for the next test
        db.close()
        # 모든 테이블 삭제
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