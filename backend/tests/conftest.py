import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Generator

from backend.app.main import app # This is the main app
from backend.app.db.session import get_db as get_main_db # Original get_db
from backend.app.models.base import Base
from backend.app.api.v1.api import api_router
from backend.app.core.config import settings

# Use the DATABASE_URL from settings, which will now point to PostgreSQL
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

# Create a test engine
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
)

# Create a session local for testing
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """
    Set up and tear down the database for the entire test session.
    """
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def db_session() -> Generator[Session, None, None]:
    """
    Provides a clean database session for each test function.
    """
    db = TestingSessionLocal()
    print(f"--- conftest: db_session fixture created: {id(db)}")
    try:
        yield db
    finally:
        print(f"--- conftest: db_session fixture closed: {id(db)}")
        db.close()

@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    """
    Provides a FastAPI TestClient with overridden database dependency.
    The client uses the transactional db_session provided by the fixture.
    """
    # Override the get_db dependency on the main app instance
    app.dependency_overrides[get_main_db] = lambda: db_session

    with TestClient(app) as c: # Use the main app instance
        yield c
    app.dependency_overrides.clear()