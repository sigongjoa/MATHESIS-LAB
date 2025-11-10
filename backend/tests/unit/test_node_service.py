import pytest
from uuid import UUID, uuid4
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, patch

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.curriculum import Curriculum # Import Curriculum model
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
def db_session():
    """
    A mocked database session that can be configured to return specific objects for queries.
    """
    mock_session = MagicMock(spec=Session)
    
    # Default mock curriculum
    mock_curriculum_obj = Curriculum(curriculum_id=uuid4(), title="Mock Curriculum", description="Mock Description")
    
    # Store mock objects that can be returned by queries
    mock_data = {
        Curriculum: {mock_curriculum_obj.curriculum_id: mock_curriculum_obj},
        Node: {},
        NodeContent: {},
        NodeLink: {}
    }

    def mock_query(model):
        mock_filter_result = MagicMock()
        
        def filter_side_effect(*args, **kwargs):
            mock_filter_result = MagicMock()
            mock_filter_result.first.return_value = None # Default
            mock_filter_result.all.return_value = [] # Default
            mock_filter_result.scalar.return_value = None # Default for scalar queries

            for filter_clause in args:
                # Handle BinaryExpression (e.g., Column == value)
                if hasattr(filter_clause, 'left') and hasattr(filter_clause, 'right'):
                    column_name = getattr(filter_clause.left, 'name', None)
                    value = getattr(filter_clause.right, 'value', None)
                    
                    # Handle .is_(None) or .is_(True/False)
                    if value is None and hasattr(filter_clause.right, 'effective_value'):
                        value = filter_clause.right.effective_value

                    if column_name and value is not None:
                        if model == Curriculum and column_name == "curriculum_id":
                            mock_filter_result.first.return_value = mock_data[Curriculum].get(value)
                        elif model == Node and column_name == "node_id":
                            mock_filter_result.first.return_value = mock_data[Node].get(value)
                        elif model == Node and column_name == "parent_node_id":
                            # This is for queries like .filter(Node.parent_node_id == parent_id).all()
                            nodes_for_parent = [n for n in mock_data[Node].values() if n.parent_node_id == value]
                            mock_filter_result.all.return_value = sorted(nodes_for_parent, key=lambda n: n.order_index)
                        elif model == NodeContent and column_name == "node_id":
                            mock_filter_result.first.return_value = mock_data[NodeContent].get(value)
                        elif model == NodeLink and column_name == "link_id":
                            mock_filter_result.first.return_value = mock_data[NodeLink].get(value)
                        elif model == NodeLink and column_name == "node_id":
                            # This is for queries like .filter(NodeLink.node_id == node_id).all()
                            links_for_node = [link for link in mock_data[model].values() if link.node_id == value]
                            mock_filter_result.all.return_value = links_for_node
                
                # Handle other types of filters if necessary, e.g., func.max
                elif hasattr(filter_clause, 'name') and filter_clause.name == 'max':
                    # This is a placeholder for func.max(Node.order_index)
                    # In a real scenario, you might need to inspect filter_clause.clauses[0].name
                    # and return the max order_index from mock_data[Node]
                    if model == Node:
                        parent_id_filter = next((arg for arg in args if hasattr(arg, 'left') and getattr(arg.left, 'name', None) == 'parent_node_id'), None)
                        if parent_id_filter:
                            parent_id_value = getattr(parent_id_filter.right, 'value', None)
                            relevant_nodes = [n for n in mock_data[Node].values() if n.parent_node_id == parent_id_value]
                            if relevant_nodes:
                                mock_filter_result.scalar.return_value = max(n.order_index for n in relevant_nodes)
                            else:
                                mock_filter_result.scalar.return_value = -1 # No nodes, so max is -1 for 0-based index
                        else:
                            # If no parent_node_id filter, consider all nodes
                            if mock_data[Node]:
                                mock_filter_result.scalar.return_value = max(n.order_index for n in mock_data[Node].values())
                            else:
                                mock_filter_result.scalar.return_value = -1
            
            return mock_filter_result

        mock_query_obj = MagicMock()
        mock_query_obj.filter.side_effect = filter_side_effect
        mock_query_obj.order_by.return_value = mock_filter_result # For get_nodes_by_curriculum
        mock_query_obj.scalar.side_effect = lambda: mock_filter_result.scalar.return_value # For func.max(Node.order_index)
        mock_query_obj.all.side_effect = lambda: mock_filter_result.all.return_value # For .all() calls
        mock_query_obj.first.side_effect = lambda: mock_filter_result.first.return_value # For .first() calls
        return mock_query_obj

    mock_session.query.side_effect = mock_query
    mock_session.add.side_effect = lambda obj: (
        mock_data[type(obj)].update({obj.curriculum_id: obj}) if isinstance(obj, Curriculum) else
        mock_data[type(obj)].update({obj.node_id: obj}) if isinstance(obj, Node) else
        mock_data[type(obj)].update({obj.content_id: obj}) if isinstance(obj, NodeContent) else
        mock_data[type(obj)].update({obj.link_id: obj}) if isinstance(obj, NodeLink) else
        None
    )
    mock_session.commit.return_value = None
    mock_session.refresh.side_effect = lambda obj: (
        setattr(obj, "curriculum_id", uuid4()) if isinstance(obj, Curriculum) and not obj.curriculum_id else
        setattr(obj, "node_id", uuid4()) if isinstance(obj, Node) and not obj.node_id else
        setattr(obj, "content_id", uuid4()) if isinstance(obj, NodeContent) and not obj.content_id else
        setattr(obj, "link_id", uuid4()) if isinstance(obj, NodeLink) and not obj.link_id else
        None
    )
    mock_session.delete.side_effect = lambda obj: (
        mock_data[type(obj)].pop(obj.curriculum_id, None) if isinstance(obj, Curriculum) else
        mock_data[type(obj)].pop(obj.node_id, None) if isinstance(obj, Node) else
        mock_data[type(obj)].pop(obj.content_id, None) if isinstance(obj, NodeContent) else
        mock_data[type(obj)].pop(obj.link_id, None) if isinstance(obj, NodeLink) else
        None
    )

    # Add the default mock curriculum to the mock_data
    mock_data[Curriculum][mock_curriculum_obj.curriculum_id] = mock_curriculum_obj
    mock_session.mock_data = mock_data # Attach for easier inspection in tests

    return mock_session

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
