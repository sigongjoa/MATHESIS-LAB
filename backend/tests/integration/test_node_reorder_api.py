import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum

def create_test_curriculum(db_session: Session) -> Curriculum:
    test_curriculum = Curriculum(title="Test Curriculum for Reorder", description="Desc for reorder tests")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    return test_curriculum

def create_test_node(client: TestClient, curriculum_id: UUID, title: str, parent_node_id: UUID = None) -> dict:
    node_data = {"title": title, "parent_node_id": str(parent_node_id) if parent_node_id else None}
    response = client.post(f"/api/v1/curriculums/{curriculum_id}/nodes", json=node_data)
    assert response.status_code == 201, response.json()
    return response.json()

def get_node_map(client: TestClient, curriculum_id: UUID) -> dict:
    response = client.get(f"/api/v1/curriculums/{curriculum_id}")
    return {node['node_id']: node for node in response.json()['nodes']}

# --- Reorder Nodes API Integration Tests ---

def test_reorder_nodes_move_forward_same_parent(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node1 = create_test_node(client, curriculum.curriculum_id, "Node 1")
    node2 = create_test_node(client, curriculum.curriculum_id, "Node 2")
    node3 = create_test_node(client, curriculum.curriculum_id, "Node 3")

    # Initial order: Node 1 (0), Node 2 (1), Node 3 (2)
    # Move Node 3 to index 0
    reorder_data = {"node_id": node3["node_id"], "new_parent_id": None, "new_order_index": 0}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200

    # Expected order: Node 3 (0), Node 1 (1), Node 2 (2)
    node_map = get_node_map(client, curriculum.curriculum_id)
    assert node_map[node3["node_id"]]["order_index"] == 0
    assert node_map[node1["node_id"]]["order_index"] == 1
    assert node_map[node2["node_id"]]["order_index"] == 2

def test_reorder_nodes_move_backward_same_parent(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node1 = create_test_node(client, curriculum.curriculum_id, "Node 1")
    node2 = create_test_node(client, curriculum.curriculum_id, "Node 2")
    node3 = create_test_node(client, curriculum.curriculum_id, "Node 3")

    # Initial order: Node 1 (0), Node 2 (1), Node 3 (2)
    # Move Node 1 to index 2
    reorder_data = {"node_id": node1["node_id"], "new_parent_id": None, "new_order_index": 2}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200

    # Expected order: Node 2 (0), Node 3 (1), Node 1 (2)
    node_map = get_node_map(client, curriculum.curriculum_id)
    assert node_map[node2["node_id"]]["order_index"] == 0
    assert node_map[node3["node_id"]]["order_index"] == 1
    assert node_map[node1["node_id"]]["order_index"] == 2

def test_reorder_nodes_change_parent(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    parent_node = create_test_node(client, curriculum.curriculum_id, "Parent")
    child_node = create_test_node(client, curriculum.curriculum_id, "Child", parent_node_id=parent_node["node_id"])
    node_to_move = create_test_node(client, curriculum.curriculum_id, "Node to Move")

    # Move "Node to Move" to be a child of "Parent" at index 0
    reorder_data = {"node_id": node_to_move["node_id"], "new_parent_id": parent_node["node_id"], "new_order_index": 0}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200

    node_map = get_node_map(client, curriculum.curriculum_id)
    # "Node to Move" is now a child of "Parent"
    assert node_map[node_to_move["node_id"]]["parent_node_id"] == parent_node["node_id"]
    assert node_map[node_to_move["node_id"]]["order_index"] == 0
    # "Child" is pushed to index 1
    assert node_map[child_node["node_id"]]["order_index"] == 1

def test_reorder_nodes_circular_dependency(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    parent = create_test_node(client, curriculum.curriculum_id, "Parent")
    child = create_test_node(client, curriculum.curriculum_id, "Child", parent_node_id=parent["node_id"])

    # Try to move "Parent" to be a child of "Child"
    reorder_data = {"node_id": parent["node_id"], "new_parent_id": child["node_id"], "new_order_index": 0}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    
    assert response.status_code == 400
    assert "Cannot move a node to be a child of its own descendant" in response.json()["detail"]

def test_reorder_nodes_no_change(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node1 = create_test_node(client, curriculum.curriculum_id, "Node 1")
    node2 = create_test_node(client, curriculum.curriculum_id, "Node 2")

    # "Move" Node 2 to its current position (index 1)
    reorder_data = {"node_id": node2["node_id"], "new_parent_id": None, "new_order_index": 1}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200

    node_map = get_node_map(client, curriculum.curriculum_id)
    assert node_map[node1["node_id"]]["order_index"] == 0
    assert node_map[node2["node_id"]]["order_index"] == 1

def test_reorder_nodes_out_of_bounds_index(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node1 = create_test_node(client, curriculum.curriculum_id, "Node 1")
    node2 = create_test_node(client, curriculum.curriculum_id, "Node 2")

    # Move Node 1 to an index that is out of bounds (e.g., 99)
    reorder_data = {"node_id": node1["node_id"], "new_parent_id": None, "new_order_index": 99}
    response = client.put(f"/api/v1/nodes/reorder/{curriculum.curriculum_id}", json=reorder_data)
    assert response.status_code == 200

    # It should be placed at the end of the list
    # Expected order: Node 2 (0), Node 1 (1)
    node_map = get_node_map(client, curriculum.curriculum_id)
    assert node_map[node2["node_id"]]["order_index"] == 0
    assert node_map[node1["node_id"]]["order_index"] == 1
