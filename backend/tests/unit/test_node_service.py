import pytest
from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeContentCreate, NodeContentUpdate, NodeLinkCreate
from backend.app.services.node_service import NodeService

# Mock data for testing
@pytest.fixture
def mock_node_data():
    return {
        "curriculum_id": uuid4(),
        "title": "Test Node",
        "parent_node_id": None,
        "order_index": 0
    }

@pytest.fixture
def mock_node_content_data():
    return {
        "node_id": uuid4(),
        "markdown_content": "## Test Content",
        "ai_generated_summary": "Summary",
        "ai_generated_extension": "Extension"
    }

@pytest.fixture
def mock_node_link_data():
    return {
        "node_id": uuid4(),
        "link_type": "YOUTUBE",
        "youtube_video_id": uuid4(),
        "zotero_item_id": None
    }

@pytest.fixture
def node_service(db_session: Session):
    return NodeService(db_session)

# --- Node CRUD Tests ---

def test_create_node(node_service: NodeService, mock_node_data):
    node_in = NodeCreate(**mock_node_data)
    node = node_service.create_node(node_in)

    assert node.node_id is not None
    assert node.title == mock_node_data["title"]
    assert node.curriculum_id == mock_node_data["curriculum_id"]
    assert node.order_index == 0 # First node created should have order_index 0

def test_get_node(node_service: NodeService, mock_node_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)

    fetched_node = node_service.get_node(created_node.node_id)
    assert fetched_node is not None
    assert fetched_node.node_id == created_node.node_id

def test_get_node_not_found(node_service: NodeService):
    non_existent_id = uuid4()
    fetched_node = node_service.get_node(non_existent_id)
    assert fetched_node is None

def test_get_nodes_by_curriculum(node_service: NodeService, mock_node_data):
    curriculum_id = uuid4()
    node_in1 = NodeCreate(curriculum_id=curriculum_id, title="Node 1", parent_node_id=None, order_index=0)
    node_in2 = NodeCreate(curriculum_id=curriculum_id, title="Node 2", parent_node_id=None, order_index=0)
    node_service.create_node(node_in1)
    node_service.create_node(node_in2)

    nodes = node_service.get_nodes_by_curriculum(curriculum_id)
    assert len(nodes) == 2
    assert nodes[0].title == "Node 1" # order_index is handled by service
    assert nodes[1].title == "Node 2"

def test_update_node(node_service: NodeService, mock_node_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)

    update_data = NodeUpdate(title="Updated Node Title")
    updated_node = node_service.update_node(created_node.node_id, update_data)

    assert updated_node is not None
    assert updated_node.title == "Updated Node Title"
    assert updated_node.node_id == created_node.node_id

def test_update_node_not_found(node_service: NodeService):
    non_existent_id = uuid4()
    update_data = NodeUpdate(title="Non Existent")
    updated_node = node_service.update_node(non_existent_id, update_data)
    assert updated_node is None

def test_delete_node(node_service: NodeService, mock_node_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)

    deleted = node_service.delete_node(created_node.node_id)
    assert deleted is True
    assert node_service.get_node(created_node.node_id) is None

def test_delete_node_not_found(node_service: NodeService):
    non_existent_id = uuid4()
    deleted = node_service.delete_node(non_existent_id)
    assert deleted is False

# --- NodeContent CRUD Tests ---

def test_create_node_content(node_service: NodeService, mock_node_data, mock_node_content_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_content_data["node_id"] = created_node.node_id

    content_in = NodeContentCreate(**mock_node_content_data)
    content = node_service.create_node_content(content_in)

    assert content.content_id is not None
    assert content.node_id == created_node.node_id
    assert content.markdown_content == mock_node_content_data["markdown_content"]

def test_get_node_content(node_service: NodeService, mock_node_data, mock_node_content_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_content_data["node_id"] = created_node.node_id
    content_in = NodeContentCreate(**mock_node_content_data)
    created_content = node_service.create_node_content(content_in)

    fetched_content = node_service.get_node_content(created_node.node_id)
    assert fetched_content is not None
    assert fetched_content.content_id == created_content.content_id

def test_update_node_content(node_service: NodeService, mock_node_data, mock_node_content_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_content_data["node_id"] = created_node.node_id
    content_in = NodeContentCreate(**mock_node_content_data)
    node_service.create_node_content(content_in)

    update_data = NodeContentUpdate(markdown_content="Updated Content")
    updated_content = node_service.update_node_content(created_node.node_id, update_data)

    assert updated_content is not None
    assert updated_content.markdown_content == "Updated Content"

def test_delete_node_content(node_service: NodeService, mock_node_data, mock_node_content_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_content_data["node_id"] = created_node.node_id
    content_in = NodeContentCreate(**mock_node_content_data)
    node_service.create_node_content(content_in)

    deleted = node_service.delete_node_content(created_node.node_id)
    assert deleted is True
    assert node_service.get_node_content(created_node.node_id) is None

# --- NodeLink CRUD Tests ---

def test_create_node_link(node_service: NodeService, mock_node_data, mock_node_link_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_link_data["node_id"] = created_node.node_id

    link_in = NodeLinkCreate(**mock_node_link_data)
    link = node_service.create_node_link(link_in)

    assert link.link_id is not None
    assert link.node_id == created_node.node_id
    assert link.link_type == mock_node_link_data["link_type"]

def test_get_node_links(node_service: NodeService, mock_node_data, mock_node_link_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_link_data["node_id"] = created_node.node_id
    link_in = NodeLinkCreate(**mock_node_link_data)
    node_service.create_node_link(link_in)

    links = node_service.get_node_links(created_node.node_id)
    assert len(links) == 1
    assert links[0].link_type == mock_node_link_data["link_type"]

def test_delete_node_link(node_service: NodeService, mock_node_data, mock_node_link_data):
    node_in = NodeCreate(**mock_node_data)
    created_node = node_service.create_node(node_in)
    mock_node_link_data["node_id"] = created_node.node_id
    link_in = NodeLinkCreate(**mock_node_link_data)
    created_link = node_service.create_node_link(link_in)

    deleted = node_service.delete_node_link(created_link.link_id)
    assert deleted is True
    assert len(node_service.get_node_links(created_node.node_id)) == 0

def test_reorder_nodes_same_parent_move_forward(node_service: NodeService, mock_node_data):
    curriculum_id = mock_node_data["curriculum_id"]
    node1 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 1", parent_node_id=None, order_index=0))
    node2 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 2", parent_node_id=None, order_index=0))
    node3 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 3", parent_node_id=None, order_index=0))
    
    # Initial order: Node 1 (0), Node 2 (1), Node 3 (2)
    # Move Node 3 (order_index 2) to position 0
    updated_nodes = node_service.reorder_nodes(curriculum_id, node3.node_id, None, 0)
    
    # Expected order: Node 3 (0), Node 1 (1), Node 2 (2)
    assert updated_nodes[0].node_id == node3.node_id
    assert updated_nodes[0].order_index == 0
    assert updated_nodes[1].node_id == node1.node_id
    assert updated_nodes[1].order_index == 1
    assert updated_nodes[2].node_id == node2.node_id
    assert updated_nodes[2].order_index == 2

def test_reorder_nodes_same_parent_move_backward(node_service: NodeService, mock_node_data):
    curriculum_id = mock_node_data["curriculum_id"]
    node1 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 1", parent_node_id=None, order_index=0))
    node2 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 2", parent_node_id=None, order_index=0))
    node3 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 3", parent_node_id=None, order_index=0))
    
    # Initial order: Node 1 (0), Node 2 (1), Node 3 (2)
    # Move Node 1 (order_index 0) to position 2
    updated_nodes = node_service.reorder_nodes(curriculum_id, node1.node_id, None, 2)
    
    # Expected order: Node 2 (0), Node 3 (1), Node 1 (2)
    assert updated_nodes[0].node_id == node2.node_id
    assert updated_nodes[0].order_index == 0
    assert updated_nodes[1].node_id == node3.node_id
    assert updated_nodes[1].order_index == 1
    assert updated_nodes[2].node_id == node1.node_id
    assert updated_nodes[2].order_index == 2

def test_reorder_nodes_change_parent(node_service: NodeService, mock_node_data):
    curriculum_id = mock_node_data["curriculum_id"]
    parent_node = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Parent", parent_node_id=None, order_index=0))
    node1 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 1", parent_node_id=None, order_index=0))
    node2 = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Node 2", parent_node_id=None, order_index=0))
    child_node = node_service.create_node(NodeCreate(curriculum_id=curriculum_id, title="Child", parent_node_id=parent_node.node_id, order_index=0))

    # Initial state:
    # Root: Parent (0), Node 1 (1), Node 2 (2)
    # Children of Parent: Child (0)

    # Move Node 1 (root) to be a child of Parent at order_index 0
    updated_nodes = node_service.reorder_nodes(curriculum_id, node1.node_id, parent_node.node_id, 0)

    # Expected state:
    # Root: Parent (0), Node 2 (1)
    # Children of Parent: Node 1 (0), Child (1)

    root_nodes = [n for n in updated_nodes if n.parent_node_id is None]
    parent_children = [n for n in updated_nodes if n.parent_node_id == parent_node.node_id]

    assert len(root_nodes) == 2
    assert root_nodes[0].node_id == parent_node.node_id
    assert root_nodes[0].order_index == 0
    assert root_nodes[1].node_id == node2.node_id
    assert root_nodes[1].order_index == 1

    assert len(parent_children) == 2
    assert parent_children[0].node_id == node1.node_id
    assert parent_children[0].order_index == 0
    assert parent_children[1].node_id == child_node.node_id
    assert parent_children[1].order_index == 1
