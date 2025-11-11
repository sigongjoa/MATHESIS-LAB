import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from unittest.mock import MagicMock

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.curriculum import Curriculum
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

@pytest.fixture
def db_session():
    """A mocked database session."""
    return MagicMock(spec=Session)

@pytest.fixture
def node_service(db_session: Session):
    return NodeService(db_session)

@pytest.fixture
def test_curriculum():
    """A mock curriculum object."""
    return Curriculum(curriculum_id=uuid4(), title="Test Curriculum")

# --- Node CRUD Tests ---

def test_create_node(node_service: NodeService, mock_node_data, test_curriculum):
    node_in = NodeCreate(**mock_node_data)
    
    # Mock the return value for the curriculum query
    node_service.db.query.return_value.filter.return_value.first.return_value = test_curriculum
    # Mock the return value for the max order index query
    node_service.db.query.return_value.filter.return_value.scalar.return_value = None
    
    node = node_service.create_node(node_in, test_curriculum.curriculum_id)

    assert node is not None
    assert node.title == mock_node_data["title"]
    assert node.curriculum_id == test_curriculum.curriculum_id
    assert node.order_index == 0  # First node should have order_index 0

def test_create_node_curriculum_not_found(node_service: NodeService, mock_node_data):
    node_in = NodeCreate(**mock_node_data)
    non_existent_curriculum_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None # Mock curriculum not found
    with pytest.raises(ValueError, match=f"Curriculum with ID {non_existent_curriculum_id} not found."):
        node_service.create_node(node_in, non_existent_curriculum_id)

def test_create_node_parent_node_not_found(node_service: NodeService, mock_node_data, test_curriculum):
    non_existent_parent_id = uuid4()
    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = non_existent_parent_id
    node_in = NodeCreate(**node_in_data)
    
    # Mock curriculum found
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        test_curriculum, # For curriculum query
        None             # For parent_node query
    ]
    with pytest.raises(ValueError, match=f"Parent node with ID {non_existent_parent_id} not found."):
        node_service.create_node(node_in, test_curriculum.curriculum_id)

def test_create_node_parent_node_wrong_curriculum(node_service: NodeService, mock_node_data, test_curriculum):
    wrong_curriculum_id = uuid4()
    parent_node_id = uuid4()
    mock_parent_node = Node(node_id=parent_node_id, curriculum_id=wrong_curriculum_id, title="Wrong Parent")
    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = parent_node_id
    node_in = NodeCreate(**node_in_data)

    # Mock curriculum found
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        test_curriculum, # For curriculum query
        mock_parent_node # For parent_node query
    ]
    with pytest.raises(ValueError, match="Parent node does not belong to the specified curriculum."):
        node_service.create_node(node_in, test_curriculum.curriculum_id)

def test_get_node(node_service: NodeService):
    test_node_id = uuid4()
    mock_node = Node(node_id=test_node_id, title="Fetched Node")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node

    fetched_node = node_service.get_node(test_node_id)
    
    assert fetched_node is not None
    assert fetched_node.node_id == test_node_id

def test_get_node_not_found(node_service: NodeService):
    non_existent_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None
    
    fetched_node = node_service.get_node(non_existent_id)
    
    assert fetched_node is None

def test_get_nodes_by_curriculum(node_service: NodeService, test_curriculum):
    mock_nodes = [
        Node(curriculum_id=test_curriculum.curriculum_id, title="Node 1", order_index=0),
        Node(curriculum_id=test_curriculum.curriculum_id, title="Node 2", order_index=1)
    ]
    node_service.db.query.return_value.filter.return_value.order_by.return_value.all.return_value = mock_nodes

    nodes = node_service.get_nodes_by_curriculum(test_curriculum.curriculum_id)
    
    assert len(nodes) == 2
    assert nodes[0].title == "Node 1"

def test_update_node(node_service: NodeService):
    test_node_id = uuid4()
    existing_node = Node(node_id=test_node_id, title="Old Title")
    node_service.db.query.return_value.filter.return_value.first.return_value = existing_node
    
    update_data = NodeUpdate(title="Updated Node Title")
    updated_node = node_service.update_node(test_node_id, update_data)

    assert updated_node is not None
    assert updated_node.title == "Updated Node Title"
    node_service.db.commit.assert_called_once()

def test_delete_node(node_service: NodeService):
    test_node_id = uuid4()
    existing_node = Node(node_id=test_node_id)
    node_service.db.query.return_value.filter.return_value.first.return_value = existing_node

    deleted = node_service.delete_node(test_node_id)

    assert deleted is True
    node_service.db.delete.assert_called_once_with(existing_node)
    node_service.db.commit.assert_called_once()

# --- NodeContent CRUD Tests ---

def test_create_node_content(node_service: NodeService, mock_node_content_data):
    test_node_id = uuid4()
    content_in = NodeContentCreate(node_id=test_node_id, **mock_node_content_data)
    
    content = node_service.create_node_content(content_in)

    assert content is not None
    assert content.node_id == test_node_id
    assert content.markdown_content == mock_node_content_data["markdown_content"]

def test_create_zotero_link_node_not_found(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_item_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        None, # Node not found
        None  # Zotero item not found (won't be reached)
    ]
    with pytest.raises(ValueError, match="Node not found."):
        node_service.create_zotero_link(node_id, zotero_item_id)

def test_create_zotero_link_zotero_item_not_found(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_item_id = uuid4()
    mock_node = Node(node_id=node_id, title="Test Node")
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # Node found
        None       # Zotero item not found
    ]
    with pytest.raises(ValueError, match="Zotero item not found."):
        node_service.create_zotero_link(node_id, zotero_item_id)

def test_create_youtube_link_node_not_found(node_service: NodeService, mocker):
    node_id = uuid4()
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    node_service.db.query.return_value.filter.return_value.first.return_value = None # Node not found
    with pytest.raises(ValueError, match="Node not found."):
        node_service.create_youtube_link(node_id, youtube_url)

def test_create_youtube_link_invalid_url(node_service: NodeService, mocker):
    node_id = uuid4()
    invalid_youtube_url = "https://notyoutube.com/watch?v=dQw4w9WgXcQ"
    mock_node = Node(node_id=node_id, title="Test Node")
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # For self.get_node(node_id)
        None       # For self.db.query(YouTubeVideo)... (no existing video for invalid URL)
    ]
    mocker.patch("backend.app.services.node_service._extract_youtube_video_id", return_value=None)
    with pytest.raises(ValueError, match="Invalid YouTube URL."):
        node_service.create_youtube_link(node_id, invalid_youtube_url)

# --- _extract_youtube_video_id Tests ---
def test_extract_youtube_video_id_valid_urls():
    from backend.app.services.node_service import _extract_youtube_video_id

    # Standard watch URL
    assert _extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("http://www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("https://youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("www.youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("youtube.com/watch?v=dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Shortened youtu.be URL
    assert _extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("http://youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("youtu.be/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # Embed URL
    assert _extract_youtube_video_id("https://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("http://www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("https://youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("www.youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("youtube.com/embed/dQw4w9WgXcQ") == "dQw4w9WgXcQ"

    # URL with extra parameters
    assert _extract_youtube_video_id("https://www.youtube.com/watch?v=dQw4w9WgXcQ&t=10s") == "dQw4w9WgXcQ"
    assert _extract_youtube_video_id("https://youtu.be/dQw4w9WgXcQ?feature=shared") == "dQw4w9WgXcQ"

def test_extract_youtube_video_id_invalid_urls():
    from backend.app.services.node_service import _extract_youtube_video_id

    assert _extract_youtube_video_id("https://www.google.com") is None
    assert _extract_youtube_video_id("https://notyoutube.com/watch?v=dQw4w9WgXcQ") is None
    assert _extract_youtube_video_id("invalid-url") is None
    assert _extract_youtube_video_id("") is None
    assert _extract_youtube_video_id(None) is None # type: ignore

def test_summarize_node_content_no_content(node_service: NodeService, mocker):
    node_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None # No NodeContent found
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        node_service.summarize_node_content(node_id)

def test_summarize_node_content_empty_markdown(node_service: NodeService, mocker):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        node_service.summarize_node_content(node_id)

def test_extend_node_content_no_content(node_service: NodeService, mocker):
    node_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None # No NodeContent found
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        node_service.extend_node_content(node_id)

def test_extend_node_content_empty_markdown(node_service: NodeService, mocker):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        node_service.extend_node_content(node_id)



# Note: The reorder_nodes tests are complex to unit test with mocks. 
# They are better suited for integration tests where a real DB session can be used.
# I will rely on the integration tests for reordering logic.
