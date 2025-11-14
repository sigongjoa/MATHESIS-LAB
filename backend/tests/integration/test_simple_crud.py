import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate

def test_create_simple_curriculum(client: TestClient, db_session: Session):
    """
    Test the simple_crud endpoint for creating a curriculum.
    """
    curriculum_data = {"title": "Simple Test Curriculum", "description": "Description for simple test", "is_public": True}
    response = client.post("/api/v1/simple-curriculums/", json=curriculum_data)

    assert response.status_code == 201
    created_curriculum = response.json()
    assert created_curriculum["title"] == curriculum_data["title"]
    assert created_curriculum["description"] == curriculum_data["description"]
    assert created_curriculum["is_public"] == curriculum_data["is_public"]
    assert "curriculum_id" in created_curriculum

    # Verify the curriculum exists in the database using the test session
    db_session.expire_all() # Clear session cache to ensure fresh data
    db_curriculum = db_session.query(Curriculum).filter(Curriculum.curriculum_id == UUID(created_curriculum["curriculum_id"])).first()
    assert db_curriculum is not None
    assert db_curriculum.title == curriculum_data["title"]
    assert db_curriculum.description == curriculum_data["description"]
    assert db_curriculum.is_public == curriculum_data["is_public"]
