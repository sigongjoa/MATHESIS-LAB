import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate

def test_create_simple_curriculum(client: TestClient, db_session: Session):
    """
    Test the simple_crud endpoint for creating a curriculum via API.
    Verifies API response correctness (integration test).
    """
    curriculum_data = {"title": "Simple Test Curriculum", "description": "Description for simple test", "is_public": True}
    response = client.post("/api/v1/simple-curriculums/", json=curriculum_data)

    # Verify API response
    assert response.status_code == 201
    created_curriculum = response.json()

    # Verify response structure and data
    assert "curriculum_id" in created_curriculum
    assert isinstance(created_curriculum["curriculum_id"], str)
    # UUID format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx (36 chars with hyphens)
    assert len(created_curriculum["curriculum_id"]) in [32, 36]  # 32 without hyphens, 36 with hyphens

    assert created_curriculum["title"] == curriculum_data["title"]
    assert created_curriculum["description"] == curriculum_data["description"]
    assert created_curriculum["is_public"] == curriculum_data["is_public"]
    assert "created_at" in created_curriculum
    assert "updated_at" in created_curriculum
