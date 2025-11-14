import pytest
from uuid import UUID, uuid4
from sqlalchemy.orm import Session
from unittest.mock import MagicMock, AsyncMock # Added AsyncMock

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.curriculum import Curriculum
from backend.app.models.zotero_item import ZoteroItem # Added ZoteroItem
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
    """A mocked database session that supports chained calls."""
    mock_session = MagicMock(spec=Session)
    
    # Create a mock for the query object
    mock_query = MagicMock()
    
    # Configure the mock_session.query to return the mock_query
    mock_session.query.return_value = mock_query
    
    # Configure the mock_query to return itself for chained calls like filter, options, order_by
    mock_query.filter.return_value = mock_query
    mock_query.options.return_value = mock_query
    mock_query.order_by.return_value = mock_query
    
    # Set default return values for terminal methods
    mock_query.all.return_value = []
    mock_query.first.return_value = None
    mock_query.scalar.return_value = None
    
    return mock_session

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
    
    # Configure mocks for db_session calls
    node_service.db.query.return_value.filter.return_value.first.return_value = test_curriculum
    node_service.db.query.return_value.filter.return_value.scalar.return_value = None # No existing nodes

    node = node_service.create_node(node_in, test_curriculum.curriculum_id)

    assert node is not None
    assert node.title == mock_node_data["title"]
    assert node.curriculum_id == str(test_curriculum.curriculum_id)
    assert node.order_index == 0  # First node should have order_index 0
    node_service.db.add.assert_called_once()
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(node)



def test_create_node_parent_node_not_found(node_service: NodeService, mock_node_data, test_curriculum):
    non_existent_parent_id = uuid4()
    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = str(non_existent_parent_id)
    node_in = NodeCreate(**node_in_data)
    
    # Mock curriculum found, but parent node not found
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        test_curriculum, # For curriculum query
        None             # For parent_node query
    ]
    
    with pytest.raises(ValueError, match=f"Parent node with ID {non_existent_parent_id} not found."):
        node_service.create_node(node_in, test_curriculum.curriculum_id)
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()

def test_create_node_parent_node_wrong_curriculum(node_service: NodeService, mock_node_data, test_curriculum):
    wrong_curriculum_id = uuid4()
    parent_node_id = uuid4()
    mock_parent_node = Node(node_id=parent_node_id, curriculum_id=wrong_curriculum_id, title="Wrong Parent")
    node_in_data = mock_node_data.copy()
    node_in_data["parent_node_id"] = str(parent_node_id)
    node_in = NodeCreate(**node_in_data)

    # Mock curriculum found, and parent node found but belongs to wrong curriculum
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        test_curriculum, # For curriculum query
        mock_parent_node # For parent_node query
    ]
    
    with pytest.raises(ValueError, match="Parent node does not belong to the specified curriculum."):
        node_service.create_node(node_in, test_curriculum.curriculum_id)
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()

def test_get_node(node_service: NodeService):
    test_node_id = uuid4()
    mock_node = Node(node_id=test_node_id, title="Fetched Node")
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_node

    fetched_node = node_service.get_node(test_node_id)
    
    assert fetched_node is not None
    assert fetched_node.node_id == test_node_id

def test_get_node_not_found(node_service: NodeService):
    non_existent_id = uuid4()
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = None
    
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
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = existing_node
    
    update_data = NodeUpdate(title="Updated Node Title")
    updated_node = node_service.update_node(test_node_id, update_data)

    assert updated_node is not None
    assert updated_node.title == "Updated Node Title"
    node_service.db.add.assert_called_once_with(existing_node)
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(existing_node)

def test_delete_node(node_service: NodeService):
    test_node_id = uuid4()
    existing_node = Node(node_id=test_node_id)
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = existing_node

    deleted = node_service.delete_node(test_node_id)

    assert deleted is True
    node_service.db.delete.assert_called_once_with(existing_node)
    node_service.db.commit.assert_called_once()

# --- NodeContent CRUD Tests ---

def test_create_node_content(node_service: NodeService, mock_node_content_data):
    test_node_id = uuid4()
    content_in = NodeContentCreate(node_id=str(test_node_id), **mock_node_content_data)
    
    content = node_service.create_node_content(test_node_id, content_in)

    assert content is not None
    assert content.node_id == str(test_node_id)
    assert content.markdown_content == mock_node_content_data["markdown_content"]
    node_service.db.add.assert_called_once()
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(content)

@pytest.mark.asyncio
async def test_create_zotero_link_node_not_found(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_key = "some_zotero_key"
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = None # Mock node not found

    with pytest.raises(ValueError, match="Node not found."):
        await node_service.create_zotero_link(node_id, zotero_key)
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()

@pytest.mark.asyncio
async def test_create_zotero_link_zotero_item_new_and_fetched(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_key = "new_zotero_key"
    mock_node = Node(node_id=node_id, title="Test Node")
    mock_zotero_data = {
        "zotero_key": zotero_key,
        "title": "Fetched Zotero Item",
        "authors": ["Author A"],
        "publication_year": 2023,
        "tags": ["tag1"],
        "item_type": "journalArticle",
        "abstract": "Abstract text",
        "url": "http://example.com"
    }

    # Mock node found
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_node
    # Mock ZoteroItem not found in our DB
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # For get_node
        None       # For ZoteroItem query
    ]

    # Mock external zotero_service call
    mock_get_item_by_key = mocker.patch("backend.app.services.zotero_service.zotero_service.get_item_by_key", new_callable=AsyncMock, return_value=mock_zotero_data)

    db_link = await node_service.create_zotero_link(node_id, zotero_key)

    assert db_link is not None
    assert db_link.node_id == str(node_id)
    assert db_link.link_type == "ZOTERO"
    assert db_link.zotero_item_id is not None

    # Verify ZoteroItem was added to our DB
    assert node_service.db.add.call_count == 2 # One for ZoteroItem, one for NodeLink
    assert isinstance(node_service.db.add.call_args_list[0].args[0], ZoteroItem)
    assert node_service.db.add.call_args_list[0].args[0].zotero_key == zotero_key
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(db_link)
    mock_get_item_by_key.assert_called_once_with(zotero_key)

@pytest.mark.asyncio
async def test_create_zotero_link_zotero_item_exists(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_key = "existing_zotero_key"
    mock_node = Node(node_id=node_id, title="Test Node")
    existing_zotero_item = ZoteroItem(zotero_item_id=uuid4(), zotero_key=zotero_key, title="Existing Item")

    # Mock node found
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_node
    # Mock ZoteroItem found in our DB
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # For get_node
        existing_zotero_item # For ZoteroItem query
    ]

    # Ensure external zotero_service call is NOT made
    mock_get_item_by_key = mocker.patch("backend.app.services.zotero_service.zotero_service.get_item_by_key", new_callable=AsyncMock)

    db_link = await node_service.create_zotero_link(node_id, zotero_key)

    assert db_link is not None
    assert db_link.node_id == str(node_id)
    assert db_link.link_type == "ZOTERO"
    assert db_link.zotero_item_id == str(existing_zotero_item.zotero_item_id)

    node_service.db.add.assert_called_once() # Only for NodeLink
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(db_link)
    mock_get_item_by_key.assert_not_called()

@pytest.mark.asyncio
async def test_create_zotero_link_fetch_failed(node_service: NodeService, mocker):
    node_id = uuid4()
    zotero_key = "failing_zotero_key"
    mock_node = Node(node_id=node_id, title="Test Node")

    # Mock node found
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_node
    # Mock ZoteroItem not found in our DB
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # For get_node
        None       # For ZoteroItem query
    ]

    # Mock external zotero_service call to raise an error
    mock_get_item_by_key = mocker.patch("backend.app.services.zotero_service.zotero_service.get_item_by_key", new_callable=AsyncMock, side_effect=ValueError("External Zotero API error"))

    with pytest.raises(ValueError, match="Failed to fetch Zotero item details: External Zotero API error"):
        await node_service.create_zotero_link(node_id, zotero_key)
    
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()
    mock_get_item_by_key.assert_called_once_with(zotero_key)

def test_create_youtube_link_node_not_found(node_service: NodeService):
    node_id = uuid4()
    youtube_url = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = None # Mock node not found

    with pytest.raises(ValueError, match="Node not found."):
        node_service.create_youtube_link(node_id, youtube_url)
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()

def test_create_youtube_link_invalid_url(node_service: NodeService, mocker):
    node_id = uuid4()
    invalid_youtube_url = "https://notyoutube.com/watch?v=dQw4w9WgXcQ"
    mock_node = Node(node_id=node_id, title="Test Node")
    
    node_service.db.query.return_value.filter.return_value.options.return_value.first.return_value = mock_node # For get_node
    node_service.db.query.return_value.filter.return_value.first.side_effect = [
        mock_node, # For get_node
        None       # For YouTubeVideo query (no existing video for invalid URL)
    ]

    mocker.patch("backend.app.services.node_service._extract_youtube_video_id", return_value=None)
    with pytest.raises(ValueError, match="Invalid YouTube URL."):
        node_service.create_youtube_link(node_id, invalid_youtube_url)
    node_service.db.add.assert_not_called()
    node_service.db.commit.assert_not_called()

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

# --- NodeLink CRUD Tests ---

def test_get_node_links(node_service: NodeService):
    node_id = uuid4()
    mock_links = [
        NodeLink(link_id=uuid4(), node_id=node_id, link_type="YOUTUBE"),
        NodeLink(link_id=uuid4(), node_id=node_id, link_type="ZOTERO")
    ]
    node_service.db.query.return_value.filter.return_value.all.return_value = mock_links

    links = node_service.get_node_links(node_id)
    assert len(links) == 2
    assert links[0].node_id == node_id

def test_get_node_links_no_links(node_service: NodeService):
    node_id = uuid4()
    node_service.db.query.return_value.filter.return_value.all.return_value = []

    links = node_service.get_node_links(node_id)
    assert len(links) == 0

def test_delete_node_link_success(node_service: NodeService):
    link_id = uuid4()
    mock_link = NodeLink(link_id=link_id, node_id=uuid4(), link_type="YOUTUBE")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_link

    result = node_service.delete_node_link(link_id)
    assert result is True
    node_service.db.delete.assert_called_once_with(mock_link)
    node_service.db.commit.assert_called_once()

def test_delete_node_link_not_found(node_service: NodeService):
    link_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None

    result = node_service.delete_node_link(link_id)
    assert result is False
    node_service.db.delete.assert_not_called()
    node_service.db.commit.assert_not_called()

@pytest.mark.asyncio
async def test_summarize_node_content_success(node_service: NodeService, mocker):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="Some content to summarize.")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content

    mock_generate_text = mocker.patch("backend.app.core.ai.ai_client.generate_text", return_value="Summarized content.")

    updated_content = await node_service.summarize_node_content(node_id)

    assert updated_content is not None
    assert updated_content.ai_generated_summary == "Summarized content."
    node_service.db.add.assert_called_once_with(mock_node_content)
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(mock_node_content)
    mock_generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_summarize_node_content_no_content(node_service: NodeService):
    node_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None # No NodeContent found
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        await node_service.summarize_node_content(node_id)

@pytest.mark.asyncio
async def test_summarize_node_content_empty_markdown(node_service: NodeService):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        await node_service.summarize_node_content(node_id)

@pytest.mark.asyncio
async def test_extend_node_content_success(node_service: NodeService, mocker):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="Some content to extend.")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content

    mock_generate_text = mocker.patch("backend.app.core.ai.ai_client.generate_text", return_value="Extended content.")

    updated_content = await node_service.extend_node_content(node_id, prompt="Add more details.")

    assert updated_content is not None
    assert updated_content.ai_generated_extension == "Extended content."
    node_service.db.add.assert_called_once_with(mock_node_content)
    node_service.db.commit.assert_called_once()
    node_service.db.refresh.assert_called_once_with(mock_node_content)
    mock_generate_text.assert_called_once()

@pytest.mark.asyncio
async def test_extend_node_content_no_content(node_service: NodeService):
    node_id = uuid4()
    node_service.db.query.return_value.filter.return_value.first.return_value = None # No NodeContent found
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        await node_service.extend_node_content(node_id)

@pytest.mark.asyncio
async def test_extend_node_content_empty_markdown(node_service: NodeService):
    node_id = uuid4()
    mock_node_content = NodeContent(node_id=node_id, markdown_content="")
    node_service.db.query.return_value.filter.return_value.first.return_value = mock_node_content
    with pytest.raises(ValueError, match="Node content not found or is empty."):
        await node_service.extend_node_content(node_id)

# Note: The reorder_nodes tests are complex to unit test with mocks. 
# They are better suited for integration tests where a real DB session can be used.
# I will rely on the integration tests for reordering logic.
