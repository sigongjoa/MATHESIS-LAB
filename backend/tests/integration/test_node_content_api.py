import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum

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
