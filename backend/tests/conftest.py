import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from fastapi import FastAPI
from fastapi.testclient import TestClient
from typing import Generator
from unittest.mock import MagicMock

from backend.app.main import app # This is the main app
from backend.app.db.session import get_db
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
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)

    try:
        yield session
    finally:
        # Rollback the transaction to clean up changes
        transaction.rollback()
        session.close()
        connection.close()

@pytest.fixture(name="client")
def client_fixture(db_session: Session):
    def override_get_db():
        try:
            yield db_session
        finally:
            # Expunge all objects from the session after each request
            # This ensures that subsequent requests get fresh data
            db_session.expunge_all()

    app.dependency_overrides = {}
    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
