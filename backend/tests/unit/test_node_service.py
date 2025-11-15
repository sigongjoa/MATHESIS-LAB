import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, AsyncMock, patch

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.curriculum import Curriculum
from backend.app.models.zotero_item import ZoteroItem
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeContentCreate, NodeContentUpdate, NodeLinkCreate
from backend.app.services.node_service import NodeService

# Mock data for testing
@pytest.fixture
def mock_node_data():
    """Provides basic data for creating a node."""
    return {
        "title": "Test Node",
        "parent_node_id": None,
    }

@pytest.fixture
def mock_node_content_data():
    return {
        "markdown_content": "## Test Content",
    }

@pytest.fixture
def mock_node_link_data():
    return {
        "link_type": "YOUTUBE",
        "youtube_video_id": uuid4(),
        "zotero_item_id": None
    }

# Use the real database fixture from conftest.py
@pytest.fixture
def node_service(db_session: Session):
    """NodeService with real database session for unit tests."""
    return NodeService(db_session)

@pytest.fixture
def test_curriculum(db_session: Session):
    """Create a real curriculum object in the database."""
    curriculum = Curriculum(curriculum_id=str(uuid4()), title="Test Curriculum")
    db_session.add(curriculum)
    db_session.commit()
    db_session.refresh(curriculum)
    return curriculum

# --- Node CRUD Tests ---

def test_create_node(node_service: NodeService, mock_node_data, test_curriculum):
    """Test creating a new node."""
    node_in = NodeCreate(**mock_node_data)

    node = node_service.create_node(node_in, UUID(test_curriculum.curriculum_id))

    assert node is not None
    assert node.title == mock_node_data["title"]
    assert node.curriculum_id == test_curriculum.curriculum_id
    assert node.order_index == 0  # First node should have order_index 0
    assert node.node_type == "CONTENT"  # Default type
    assert node.deleted_at is None  # Not deleted

def test_create_node_parent_node_not_found(node_service: NodeService, mock_node_data, test_curriculum):
    """Test creating node with non-existent parent raises error."""
    non_existent_parent_id = uuid4()
    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = str(non_existent_parent_id)
    node_in = NodeCreate(**node_in_data)

    with pytest.raises(ValueError, match="Parent node with ID .* not found"):
        node_service.create_node(node_in, UUID(test_curriculum.curriculum_id))

def test_create_node_parent_node_wrong_curriculum(node_service: NodeService, mock_node_data, test_curriculum, db_session: Session):
    """Test creating node with parent from different curriculum raises error."""
    # Create another curriculum
    other_curriculum = Curriculum(curriculum_id=str(uuid4()), title="Other Curriculum")
    db_session.add(other_curriculum)
    db_session.commit()

    # Create a node in the other curriculum
    parent_node = Node(
        node_id=str(uuid4()),
        curriculum_id=other_curriculum.curriculum_id,
        parent_node_id=None,
        title="Parent in Other Curriculum",
        order_index=0,
        node_type="CONTENT"
    )
    db_session.add(parent_node)
    db_session.commit()

    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = parent_node.node_id
    node_in = NodeCreate(**node_in_data)

    with pytest.raises(ValueError, match="Parent node does not belong to the specified curriculum"):
        node_service.create_node(node_in, UUID(test_curriculum.curriculum_id))

def test_get_node(node_service: NodeService, test_curriculum):
    """Test retrieving a node by ID."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Fetched Node",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    fetched_node = node_service.get_node(UUID(node.node_id))

    assert fetched_node is not None
    assert fetched_node.node_id == node.node_id
    assert fetched_node.title == "Fetched Node"

def test_get_node_not_found(node_service: NodeService):
    """Test retrieving non-existent node returns None."""
    non_existent_id = uuid4()

    fetched_node = node_service.get_node(non_existent_id)

    assert fetched_node is None

def test_get_nodes_by_curriculum(node_service: NodeService, test_curriculum):
    """Test retrieving all nodes in a curriculum."""
    # Create multiple nodes
    nodes_to_create = [
        Node(node_id=str(uuid4()), curriculum_id=test_curriculum.curriculum_id, parent_node_id=None, title="Node 1", order_index=0, node_type="CONTENT"),
        Node(node_id=str(uuid4()), curriculum_id=test_curriculum.curriculum_id, parent_node_id=None, title="Node 2", order_index=1, node_type="SECTION")
    ]
    for n in nodes_to_create:
        node_service.db.add(n)
    node_service.db.commit()

    nodes = node_service.get_nodes_by_curriculum(UUID(test_curriculum.curriculum_id))

    assert len(nodes) == 2
    assert nodes[0].title == "Node 1"
    assert nodes[1].title == "Node 2"

def test_update_node(node_service: NodeService, test_curriculum):
    """Test updating a node."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Old Title",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    update_data = NodeUpdate(title="Updated Node Title")
    updated_node = node_service.update_node(UUID(node.node_id), update_data)

    assert updated_node is not None
    assert updated_node.title == "Updated Node Title"

def test_delete_node(node_service: NodeService, test_curriculum):
    """Test soft-deleting a node."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Node to Delete",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    deleted = node_service.delete_node(UUID(node.node_id))

    assert deleted is True

    # Verify soft deletion (deleted_at is set)
    fetched_node = node_service.db.query(Node).filter(Node.node_id == node.node_id).first()
    assert fetched_node is not None
    assert fetched_node.deleted_at is not None

    # Verify get_node returns None (filtered out by deleted_at)
    assert node_service.get_node(UUID(node.node_id)) is None

def test_delete_node_with_descendants(node_service: NodeService, test_curriculum):
    """Test soft-deleting a node and its descendants."""
    # Create parent node
    parent = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Parent",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(parent)
    node_service.db.commit()

    # Create child node
    child = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=parent.node_id,
        title="Child",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(child)
    node_service.db.commit()

    # Delete parent
    deleted = node_service.delete_node(UUID(parent.node_id))
    assert deleted is True

    # Verify both parent and child are soft deleted
    parent_in_db = node_service.db.query(Node).filter(Node.node_id == parent.node_id).first()
    child_in_db = node_service.db.query(Node).filter(Node.node_id == child.node_id).first()

    assert parent_in_db.deleted_at is not None
    assert child_in_db.deleted_at is not None

# --- NodeContent CRUD Tests ---

def test_create_node_content(node_service: NodeService, mock_node_content_data, test_curriculum):
    """Test creating node content."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Node",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    content_in = NodeContentCreate(node_id=node.node_id, **mock_node_content_data)

    content = node_service.create_node_content(UUID(node.node_id), content_in)

    assert content is not None
    assert content.node_id == node.node_id
    assert content.markdown_content == mock_node_content_data["markdown_content"]

# --- NodeLink CRUD Tests ---

def test_get_node_links(node_service: NodeService, test_curriculum):
    """Test retrieving node links."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Node",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    links = [
        NodeLink(link_id=str(uuid4()), node_id=node.node_id, link_type="YOUTUBE"),
        NodeLink(link_id=str(uuid4()), node_id=node.node_id, link_type="ZOTERO")
    ]
    for link in links:
        node_service.db.add(link)
    node_service.db.commit()

    fetched_links = node_service.get_node_links(UUID(node.node_id))
    assert len(fetched_links) == 2
    assert fetched_links[0].node_id == node.node_id

def test_get_node_links_no_links(node_service: NodeService, test_curriculum):
    """Test retrieving node with no links."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Node",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    links = node_service.get_node_links(UUID(node.node_id))
    assert len(links) == 0

def test_delete_node_link_success(node_service: NodeService, test_curriculum):
    """Test deleting a node link."""
    node = Node(
        node_id=str(uuid4()),
        curriculum_id=test_curriculum.curriculum_id,
        parent_node_id=None,
        title="Node",
        order_index=0,
        node_type="CONTENT"
    )
    node_service.db.add(node)
    node_service.db.commit()

    link = NodeLink(link_id=str(uuid4()), node_id=node.node_id, link_type="YOUTUBE")
    node_service.db.add(link)
    node_service.db.commit()

    result = node_service.delete_node_link(UUID(link.link_id))
    assert result is True

    # Verify link is actually deleted
    fetched_link = node_service.db.query(NodeLink).filter(NodeLink.link_id == link.link_id).first()
    assert fetched_link is None

def test_delete_node_link_not_found(node_service: NodeService):
    """Test deleting non-existent link returns False."""
    link_id = uuid4()

    result = node_service.delete_node_link(link_id)
    assert result is False

# --- Utility function tests ---

def test_extract_youtube_video_id_valid_urls():
    """Test extracting video ID from valid YouTube URLs."""
    from backend.app.services.node_service import _extract_youtube_video_id

    # Standard watch URL
    assert _extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("http://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Shortened youtu.be URL
    assert _extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # URL with extra parameters
    assert _extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") == "dQw4w9WgXcQ"

def test_extract_youtube_video_id_invalid_urls():
    """Test extracting video ID from invalid YouTube URLs."""
    from backend.app.services.node_service import _extract_youtube_video_id

    assert _extract_youtube_video_id("https://www.google.com") is None
    assert _extract_youtube_video_id("https://notyoutube.com/watch?v=dQw4w9WgXcQ") is None
    assert _extract_youtube_video_id("invalid-url") is None
    assert _extract_youtube_video_id("") is None
    assert _extract_youtube_video_id(None) is None  # type: ignore
