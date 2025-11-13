import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum

# --- Public Curriculum API Integration Tests ---

def test_create_public_curriculum(client: TestClient):
    """
    Test creating a curriculum and setting it to public.
    """
    curriculum_data = {
        "title": "Public Curriculum",
        "description": "This curriculum is for everyone.",
        "is_public": True
    }
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 201
    curriculum = response.json()
    assert curriculum["title"] == "Public Curriculum"
    assert curriculum["is_public"] is True

def test_create_private_curriculum_by_default(client: TestClient):
    """
    Test that a curriculum is private by default.
    """
    curriculum_data = {
        "title": "Private Curriculum",
        "description": "This is a private curriculum."
    }
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 201
    curriculum = response.json()
    assert curriculum["title"] == "Private Curriculum"
    assert curriculum["is_public"] is False

def test_update_curriculum_to_public(client: TestClient, db_session: Session):
    """
    Test updating a curriculum to make it public.
    """
    # 1. Create a private curriculum
    private_curriculum = Curriculum(title="Soon to be Public", description="Initial description", is_public=False)
    db_session.add(private_curriculum)
    db_session.commit()
    db_session.refresh(private_curriculum)
    curriculum_id = private_curriculum.curriculum_id

    # 2. Update it to be public
    update_data = {"is_public": True}
    response = client.put(f"/api/v1/curriculums/{curriculum_id}", json=update_data)
    assert response.status_code == 200
    updated_curriculum = response.json()
    assert updated_curriculum["is_public"] is True

def test_read_public_curriculums(client: TestClient, db_session: Session):
    """
    Test that the /public endpoint returns only public curriculums.
    """
    # 1. Create a mix of public and private curriculums
    db_session.add(Curriculum(title="Public One", is_public=True))
    db_session.add(Curriculum(title="Private One", is_public=False))
    db_session.add(Curriculum(title="Public Two", is_public=True))
    db_session.commit()

    # 2. Call the public endpoint
    response = client.get("/api/v1/curriculums/public")
    assert response.status_code == 200
    public_curriculums = response.json()

    # 3. Check the results
    assert len(public_curriculums) == 2
    titles = {c["title"] for c in public_curriculums}
    assert "Public One" in titles
    assert "Public Two" in titles
    assert "Private One" not in titles

def test_read_all_curriculums_for_completeness(client: TestClient, db_session: Session):
    """
    Test the standard /curriculums endpoint to ensure it returns everything (for comparison).
    This test assumes the standard endpoint is not filtered for public/private.
    """
    # 1. Clear and create a mix of public and private curriculums
    db_session.query(Curriculum).delete()
    db_session.add(Curriculum(title="Public One", is_public=True))
    db_session.add(Curriculum(title="Private One", is_public=False))
    db_session.commit()

    # 2. Call the main endpoint
    response = client.get("/api/v1/curriculums/")
    assert response.status_code == 200
    all_curriculums = response.json()

    # 3. Check the results
    assert len(all_curriculums) == 2
