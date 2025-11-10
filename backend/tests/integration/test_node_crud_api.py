import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate
from backend.app.services.curriculum_service import CurriculumService

# Helper function to create a curriculum for testing nodes
def create_test_curriculum(db_session: Session) -> Curriculum:
    curriculum_service = CurriculumService(db_session)
    curriculum_in = CurriculumCreate(title="Test Curriculum for Nodes", description="Description for node tests")
    return curriculum_service.create_curriculum(curriculum_in)

# --- Node CRUD API Integration Tests ---

def test_create_node(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node_data = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "First Node",
        "parent_node_id": None,
        "order_index": 0
    }
    response = client.post("/api/v1/nodes/", json=node_data)
    assert response.status_code == 201
    node = response.json()
    assert node["title"] == "First Node"
    assert node["curriculum_id"] == str(curriculum.curriculum_id)
    assert "node_id" in node

def test_create_node_invalid_curriculum_id(client: TestClient, db_session: Session):
    node_data = {
        "curriculum_id": str(uuid4()), # Non-existent curriculum ID
        "title": "Invalid Node",
        "parent_node_id": None,
        "order_index": 0
    }
    response = client.post("/api/v1/nodes/", json=node_data)
    assert response.status_code == 404
    assert response.json()["detail"] == f"Curriculum with ID {node_data['curriculum_id']} not found."

def test_read_node(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node_data = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "Node to Read",
        "parent_node_id": None,
        "order_index": 0
    }
    create_response = client.post("/api/v1/nodes/", json=node_data)
    created_node_id = create_response.json()["node_id"]

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

def test_read_nodes_by_curriculum(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node_data1 = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "Node 1",
        "parent_node_id": None,
        "order_index": 0
    }
    node_data2 = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "Node 2",
        "parent_node_id": None,
        "order_index": 0
    }
    client.post("/api/v1/nodes/", json=node_data1)
    client.post("/api/v1/nodes/", json=node_data2)

    response = client.get(f"/api/v1/nodes/curriculum/{curriculum.curriculum_id}")
    assert response.status_code == 200
    nodes = response.json()
    assert len(nodes) == 2
    assert nodes[0]["title"] == "Node 1" # Order is handled by service
    assert nodes[1]["title"] == "Node 2"

def test_update_node(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node_data = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "Original Node",
        "parent_node_id": None,
        "order_index": 0
    }
    create_response = client.post("/api/v1/nodes/", json=node_data)
    created_node_id = create_response.json()["node_id"]

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
    curriculum = create_test_curriculum(db_session)
    node_data = {
        "curriculum_id": str(curriculum.curriculum_id),
        "title": "Node to Delete",
        "parent_node_id": None,
        "order_index": 0
    }
    create_response = client.post("/api/v1/nodes/", json=node_data)
    created_node_id = create_response.json()["node_id"]

    response = client.delete(f"/api/v1/nodes/{created_node_id}")
    assert response.status_code == 204
    
    get_response = client.get(f"/api/v1/nodes/{created_node_id}")
    assert get_response.status_code == 404

def test_delete_node_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/nodes/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"
