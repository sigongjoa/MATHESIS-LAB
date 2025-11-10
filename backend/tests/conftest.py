import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.db.session import get_db
from backend.app.models.base import Base

# SQLite 인메모리 데이터베이스 설정
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db" # Use a file-based SQLite for easier debugging if needed, or :memory: for pure in-memory

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(name="db_session")
def db_session_fixture():
    """
    테스트용 데이터베이스 세션을 제공하는 픽스처.
    각 테스트 시작 전에 테이블을 생성하고, 테스트 종료 후에 삭제합니다.
    """
    Base.metadata.create_all(bind=engine)  # 모든 테이블 생성
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)  # 모든 테이블 삭제

@pytest.fixture(name="client")
def client_fixture(db_session: Session, mocker):
    """
    테스트용 FastAPI 클라이언트를 제공하는 픽스처.
    get_db 의존성을 오버라이드하고, backend.app.db.session의 engine과 SessionLocal을 테스트용으로 패치합니다.
    """
    # backend.app.db.session 모듈이 임포트될 때 프로덕션 엔진이 초기화되므로,
    # 테스트용 엔진으로 패치하여 TestClient가 시작될 때 사용하도록 합니다.
    mocker.patch('backend.app.db.session.engine', engine) # conftest.py의 SQLite engine
    mocker.patch('backend.app.db.session.SessionLocal', TestingSessionLocal)

    def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear() # 의존성 오버라이드 초기화
    Base.metadata.drop_all(bind=engine) # 테스트 종료 후 테이블 삭제