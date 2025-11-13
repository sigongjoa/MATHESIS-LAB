import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from unittest.mock import AsyncMock

from backend.app.models.curriculum import Curriculum
from backend.app.models.node import NodeContent
from backend.app.core.ai import ai_client

# Helper function to create a curriculum for testing
def create_test_curriculum(db_session: Session) -> Curriculum:
    test_curriculum = Curriculum(title="Test Curriculum for Manim", description="Description for Manim tests")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    return test_curriculum

# Helper function to create a node for testing
def create_test_node(client: TestClient, curriculum_id: UUID) -> dict:
    node_data = {
        "title": "Node for Manim Test",
        "parent_node_id": None,
    }
    response = client.post(f"/api/v1/curriculums/{curriculum_id}/nodes", json=node_data)
    assert response.status_code == 201, response.json()
    return response.json()

# Helper function to create node content for testing
def create_test_node_content(client: TestClient, node_id: UUID, markdown_content: str = "Initial content") -> dict:
    content_data = {
        "node_id": node_id,
        "markdown_content": markdown_content,
    }
    response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)
    assert response.status_code == 201, response.json()
    return response.json()

def test_generate_manim_guidelines_success(client: TestClient, db_session: Session, mocker):
    """
    Test successful generation of Manim guidelines from an image.
    """
    # Mock the AI client's generate_manim_guidelines_from_image method
    mock_guidelines = "Mocked Manim guidelines: Use circles and squares."
    mocker.patch.object(ai_client, "generate_manim_guidelines_from_image", new_callable=AsyncMock, return_value=mock_guidelines)

    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]
    create_test_node_content(client, node_id) # Ensure content exists

    # Create a dummy image file
    image_content = b"fake_image_bytes"
    files = {"image_file": ("test_image.jpg", image_content, "image/jpeg")}
    
    response = client.post(
        f"/api/v1/nodes/{node_id}/content/manim-guidelines",
        files=files,
        data={"prompt": "Focus on shapes."}
    )
    
    assert response.status_code == 200
    content = response.json()
    assert content["node_id"] == node_id
    assert content["manim_guidelines"] == mock_guidelines
    
    # Verify the AI client was called correctly
    ai_client.generate_manim_guidelines_from_image.assert_called_once_with(
        image_content,
        "Generate Manim code guidelines based on the provided image.\nAdditional instructions: Focus on shapes."
    )

    # Verify content in DB
    db_content = db_session.query(NodeContent).filter(NodeContent.node_id == UUID(node_id)).first()
    assert db_content is not None
    assert db_content.manim_guidelines == mock_guidelines

def test_generate_manim_guidelines_no_node_content(client: TestClient, db_session: Session, mocker):
    """
    Test generation when node content does not exist.
    """
    mocker.patch.object(ai_client, "generate_manim_guidelines_from_image", new_callable=AsyncMock, return_value="Mocked guidelines")

    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    image_content = b"fake_image_bytes"
    files = {"image_file": ("test_image.jpg", image_content, "image/jpeg")}

    response = client.post(
        f"/api/v1/nodes/{node_id}/content/manim-guidelines",
        files=files
    )
    assert response.status_code == 400
    assert "Node content not found" in response.json()["detail"]

def test_generate_manim_guidelines_ai_service_error(client: TestClient, db_session: Session, mocker):
    """
    Test generation when AI service encounters an error.
    """
    mocker.patch.object(
        ai_client,
        "generate_manim_guidelines_from_image",
        new_callable=AsyncMock,
        side_effect=RuntimeError("AI vision service failed")
    )

    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]
    create_test_node_content(client, node_id)

    image_content = b"fake_image_bytes"
    files = {"image_file": ("test_image.jpg", image_content, "image/jpeg")}

    response = client.post(
        f"/api/v1/nodes/{node_id}/content/manim-guidelines",
        files=files
    )
    assert response.status_code == 400
    assert "AI service error: AI vision service failed" in response.json()["detail"]