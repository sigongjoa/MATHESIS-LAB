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

# --- Reorder Nodes API Integration Tests ---

def test_reorder_nodes_same_parent(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node1_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Node 1", "parent_node_id": None, "order_index": 0}
    node2_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Node 2", "parent_node_id": None, "order_index": 0}
    node3_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Node 3", "parent_node_id": None, "order_index": 0}

    node1 = client.post("/api/v1/nodes/", json=node1_data).json()
    node2 = client.post("/api/v1/nodes/", json=node2_data).json()
    node3 = client.post("/api/v1/nodes/", json=node3_data).json()

    # Initial order: Node 1 (0), Node 2 (1), Node 3 (2)
    # Move Node 3 (order_index 2) to position 0
    reorder_data = {
        "node_id": node3["node_id"],
        "new_parent_id": None,
        "new_order_index": 0
    }
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200
    updated_nodes = response.json()

    # Expected order: Node 3 (0), Node 1 (1), Node 2 (2)
    assert updated_nodes[0]["node_id"] == node3["node_id"]
    assert updated_nodes[0]["order_index"] == 0
    assert updated_nodes[1]["node_id"] == node1["node_id"]
    assert updated_nodes[1]["order_index"] == 1
    assert updated_nodes[2]["node_id"] == node2["node_id"]
    assert updated_nodes[2]["order_index"] == 2

def test_reorder_nodes_change_parent(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    parent_node_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Parent Node", "parent_node_id": None, "order_index": 0}
    node_to_move_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Node to Move", "parent_node_id": None, "order_index": 0}
    other_node_data = {"curriculum_id": str(curriculum.curriculum_id), "title": "Other Node", "parent_node_id": None, "order_index": 0}

    parent_node = client.post("/api/v1/nodes/", json=parent_node_data).json()
    node_to_move = client.post("/api/v1/nodes/", json=node_to_move_data).json()
    other_node = client.post("/api/v1/nodes/", json=other_node_data).json()

    # Initial root nodes: Parent Node (0), Node to Move (1), Other Node (2)
    # Move Node to Move to be a child of Parent Node at order_index 0
    reorder_data = {
        "node_id": node_to_move["node_id"],
        "new_parent_id": parent_node["node_id"],
        "new_order_index": 0
    }
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200
    updated_nodes = response.json()

    # Verify root nodes
    root_nodes = [n for n in updated_nodes if n["parent_node_id"] is None]
    assert len(root_nodes) == 2
    assert root_nodes[0]["node_id"] == parent_node["node_id"]
    assert root_nodes[0]["order_index"] == 0
    assert root_nodes[1]["node_id"] == other_node["node_id"]
    assert root_nodes[1]["order_index"] == 1

    # Verify children of parent_node
    parent_children = [n for n in updated_nodes if n["parent_node_id"] == parent_node["node_id"]]
    assert len(parent_children) == 1
    assert parent_children[0]["node_id"] == node_to_move["node_id"]
    assert parent_children[0]["order_index"] == 0
