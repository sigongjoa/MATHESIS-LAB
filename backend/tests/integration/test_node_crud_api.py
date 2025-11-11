import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum

# Helper function to create a curriculum for testing nodes
def create_test_curriculum(db_session: Session) -> Curriculum:
    """
    Creates a simple curriculum object in the DB for testing purposes.
    """
    test_curriculum = Curriculum(title="Test Curriculum for Nodes", description="Description for node tests")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    return test_curriculum

# --- Node Read, Update, Delete API Integration Tests ---

def test_read_node(client: TestClient, db_session: Session):
    # Setup: Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node_data = {"title": "Node to Read", "parent_node_id": None}
    create_response = client.post(f"/api/v1/curriculums/{curriculum.curriculum_id}/nodes", json=node_data)
    assert create_response.status_code == 201
    created_node_id = create_response.json()["node_id"]

    # Test: Read the node
    response = client.get(f"/api/v1/nodes/{created_node_id}")
    assert response.status_code == 200
    node = response.json()
    assert node["node_id"] == created_node_id
    assert node["title"] == "Node to Read"

def test_read_node_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.get(f"/api/v1/nodes/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"

def test_update_node(client: TestClient, db_session: Session):
    # Setup: Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node_data = {"title": "Original Node", "parent_node_id": None}
    create_response = client.post(f"/api/v1/curriculums/{curriculum.curriculum_id}/nodes", json=node_data)
    assert create_response.status_code == 201
    created_node_id = create_response.json()["node_id"]

    # Test: Update the node
    update_data = {"title": "Updated Node Title"}
    response = client.put(f"/api/v1/nodes/{created_node_id}", json=update_data)
    assert response.status_code == 200
    node = response.json()
    assert node["node_id"] == created_node_id
    assert node["title"] == "Updated Node Title"

def test_update_node_not_found(client: TestClient):
    non_existent_id = uuid4()
    update_data = {"title": "Non Existent"}
    response = client.put(f"/api/v1/nodes/{non_existent_id}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"

def test_delete_node(client: TestClient, db_session: Session):
    # Setup: Create a curriculum and a node
    curriculum = create_test_curriculum(db_session)
    node_data = {"title": "Node to Delete", "parent_node_id": None}
    create_response = client.post(f"/api/v1/curriculums/{curriculum.curriculum_id}/nodes", json=node_data)
    assert create_response.status_code == 201
    created_node_id = create_response.json()["node_id"]

    # Test: Delete the node
    response = client.delete(f"/api/v1/nodes/{created_node_id}")
    assert response.status_code == 204
    
    # Verify deletion
    get_response = client.get(f"/api/v1/nodes/{created_node_id}")
    assert get_response.status_code == 404

def test_delete_node_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/nodes/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"
