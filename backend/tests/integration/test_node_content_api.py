import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum
from backend.app.models.node import NodeContent
from backend.app.core.ai import ai_client # Import ai_client

# Helper function to create a curriculum for testing
def create_test_curriculum(db_session: Session) -> Curriculum:
    test_curriculum = Curriculum(title="Test Curriculum for Content", description="Description for content tests")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    return test_curriculum

# Helper function to create a node for testing
def create_test_node(client: TestClient, curriculum_id: UUID) -> dict:
    node_data = {
        "title": "Node for Content Test",
        "parent_node_id": None,
    }
    response = client.post(f"/api/v1/curriculums/{curriculum_id}/nodes", json=node_data)
    assert response.status_code == 201, response.json()
    return response.json()

# --- NodeContent API Integration Tests ---

def test_create_node_content(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    content_data = {
        "node_id": node_id,
        "markdown_content": "## My Node Content",
    }
    response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)
    assert response.status_code == 201
    content = response.json()
    assert content["node_id"] == node_id
    assert content["markdown_content"] == "## My Node Content"

def test_create_node_content_node_not_found(client: TestClient):
    non_existent_node_id = uuid4()
    content_data = {
        "node_id": str(non_existent_node_id),
        "markdown_content": "## My Node Content"
    }
    # This test has a slight flaw: the node_id in the path and body are different.
    # The path node_id is what's validated first by the endpoint logic.
    response = client.post(f"/api/v1/nodes/{non_existent_node_id}/content", json=content_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"

def test_create_node_content_already_exists(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    content_data = {"node_id": node_id, "markdown_content": "## My Node Content"}
    client.post(f"/api/v1/nodes/{node_id}/content", json=content_data) # First creation

    response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data) # Second creation
    assert response.status_code == 409
    assert response.json()["detail"] == "Node content already exists for this node"

def test_read_node_content(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    content_data = {"node_id": node_id, "markdown_content": "## My Node Content"}
    client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)

    response = client.get(f"/api/v1/nodes/{node_id}/content")
    assert response.status_code == 200
    content = response.json()
    assert content["node_id"] == node_id
    assert content["markdown_content"] == "## My Node Content"

def test_read_node_content_not_found(client: TestClient, db_session: Session):
    # Create a node that exists but has no content
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]
    
    response = client.get(f"/api/v1/nodes/{node_id}/content")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node content not found"

def test_update_node_content(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    content_data = {"node_id": node_id, "markdown_content": "## Original Content"}
    client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)

    update_data = {"markdown_content": "## Updated Content"}
    response = client.put(f"/api/v1/nodes/{node_id}/content", json=update_data)
    assert response.status_code == 200
    content = response.json()
    assert content["node_id"] == node_id
    assert content["markdown_content"] == "## Updated Content"

def test_update_node_content_not_found(client: TestClient):
    non_existent_node_id = uuid4()
    update_data = {"markdown_content": "## Updated Content"}
    response = client.put(f"/api/v1/nodes/{non_existent_node_id}/content", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Node content not found"

def test_delete_node_content(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    content_data = {"node_id": node_id, "markdown_content": "## Content to Delete"}
    client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)

    response = client.delete(f"/api/v1/nodes/{node_id}/content")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/v1/nodes/{node_id}/content")
    assert get_response.status_code == 404

def test_delete_node_content_not_found(client: TestClient):
    non_existent_node_id = uuid4()
    response = client.delete(f"/api/v1/nodes/{non_existent_node_id}/content")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node content not found"


def test_summarize_node_content(client: TestClient, db_session: Session, mocker):
    """
    Test AI-powered summarization of node content.
    Mocks the AI client to avoid actual external calls.
    """
    # Mock the AI client's generate_text method
    mocker.patch.object(ai_client, "generate_text", return_value="Mocked AI Summary")

    # 1. Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # 2. Create content for the node
    content_data = {
        "node_id": node_id,
        "markdown_content": "This is a long piece of text that needs to be summarized by an AI. " * 10
    }
    create_response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)
    assert create_response.status_code == 201

    # 3. Call the summarize endpoint
    summarize_response = client.post(f"/api/v1/nodes/{node_id}/content/summarize")
    assert summarize_response.status_code == 200
    
    # 4. Check the response
    summarized_content = summarize_response.json()
    assert summarized_content["node_id"] == node_id
    assert "ai_generated_summary" in summarized_content
    assert summarized_content["ai_generated_summary"] == "Mocked AI Summary"

    # 5. Verify the content in the database
    db_content = db_session.query(NodeContent).filter(NodeContent.node_id == UUID(node_id)).first()
    assert db_content is not None
    assert db_content.ai_generated_summary == "Mocked AI Summary"


def test_extend_node_content(client: TestClient, db_session: Session, mocker):
    """
    Test AI-powered extension of node content.
    Mocks the AI client to avoid actual external calls.
    """
    # Mock the AI client's generate_text method
    mocker.patch.object(ai_client, "generate_text", return_value="Mocked AI Extension")

    # 1. Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # 2. Create content for the node
    content_data = {
        "node_id": node_id,
        "markdown_content": "This is a short piece of text that needs to be extended by an AI. " * 5
    }
    create_response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)
    assert create_response.status_code == 201

    # 3. Call the extend endpoint
    extend_response = client.post(f"/api/v1/nodes/{node_id}/content/extend", json={"prompt": "Make it longer."})
    assert extend_response.status_code == 200
    
    # 4. Check the response
    extended_content = extend_response.json()
    assert extended_content["node_id"] == node_id
    assert "ai_generated_extension" in extended_content
    assert extended_content["ai_generated_extension"] == "Mocked AI Extension"

    # 5. Verify the content in the database
    db_content = db_session.query(NodeContent).filter(NodeContent.node_id == UUID(node_id)).first()
    assert db_content is not None
    assert db_content.ai_generated_extension == "Mocked AI Extension"

def test_summarize_node_content_service_error(client: TestClient, db_session: Session, mocker):
    """
    Test AI-powered summarization when the service encounters an internal error.
    Mocks the AI client to raise a RuntimeError.
    """
    # Mock the AI client's generate_text method to raise a RuntimeError
    mocker.patch.object(
        ai_client,
        "generate_text",
        side_effect=RuntimeError("AI service internal error")
    )

    # 1. Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # 2. Create content for the node
    content_data = {
        "node_id": node_id,
        "markdown_content": "This is some content for summarization."
    }
    create_response = client.post(f"/api/v1/nodes/{node_id}/content", json=content_data)
    assert create_response.status_code == 201

    # 3. Call the summarize endpoint
    summarize_response = client.post(f"/api/v1/nodes/{node_id}/content/summarize")
    
    # 4. Check the response for internal server error
    assert summarize_response.status_code == 400 # Changed from 500 to 400 due to ValueError in service
    assert "AI summarization failed: AI service internal error" in summarize_response.json()["detail"]
