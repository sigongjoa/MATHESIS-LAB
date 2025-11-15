import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock
from uuid import UUID # Added this import

from backend.app.core.config import settings
from backend.app.services.zotero_service import zotero_service
from backend.app.models.curriculum import Curriculum # Added for test setup
from backend.app.models.node import Node # Added for test setup
from backend.app.models.zotero_item import ZoteroItem # Added for test setup

def test_search_zotero_items_success(client: TestClient, mocker):
    """
    Test successful search for Zotero items by tag.
    """
    # Configure Zotero API settings for the test
    settings.ZOTERO_API_BASE_URL = "http://mock-zotero-api.com"
    settings.ZOTERO_API_KEY = "mock_key"

    mock_response_data = [
        {
            "zotero_key": "item1",
            "title": "Mock Zotero Item 1",
            "authors": ["Author A"],
            "publication_year": 2023,
            "tags": ["tag1", "python"],
            "item_type": "journalArticle",
            "abstract": "Abstract 1",
            "url": "http://example.com/item1"
        },
        {
            "zotero_key": "item2",
            "title": "Mock Zotero Item 2",
            "authors": ["Author B"],
            "publication_year": 2022,
            "tags": ["tag1", "fastapi"],
            "item_type": "book",
            "abstract": "Abstract 2",
            "url": "http://example.com/item2"
        },
    ]

    # Mock the ZoteroService's get_items_by_tag method
    mocker.patch.object(
        zotero_service,
        "get_items_by_tag",
        new_callable=AsyncMock,
        return_value=mock_response_data
    )

    response = client.get("/api/v1/literature/zotero/items?tag=tag1")
    
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    assert items[0]["zotero_key"] == "item1"
    assert items[1]["title"] == "Mock Zotero Item 2"
    
    zotero_service.get_items_by_tag.assert_called_once_with(tag="tag1")

@pytest.fixture
def mock_zotero_item_data():
    return {
        "zotero_key": "new_item_key",
        "title": "Newly Linked Zotero Item",
        "authors": ["New Author"],
        "publication_year": 2024,
        "tags": ["new", "zotero"],
        "item_type": "report",
        "abstract": "Abstract for new item.",
        "url": "http://example.com/new_item"
    }

@pytest.mark.asyncio
async def test_create_zotero_node_link_success_new_item(client: TestClient, mocker, db_session, mock_zotero_item_data):
    """
    Test successful creation of a Zotero node link when the Zotero item is new to our DB.
    """
    # Create a dummy node to link to
    node_id = UUID("a0a0a0a0-a0a0-4a0a-8a0a-0a0a0a0a0a0a")
    curriculum_id = UUID("b0b0b0b0-b0b0-4b0b-8b0b-0b0b0b0b0b0b")
    db_session.add(Curriculum(curriculum_id=str(curriculum_id), title="Test Curriculum"))
    db_session.add(Node(node_id=str(node_id), curriculum_id=str(curriculum_id), title="Test Node", order_index=0))
    db_session.commit()

    # Mock zotero_service.get_item_by_key to return data for a new item
    mocker.patch.object(
        zotero_service,
        "get_item_by_key",
        new_callable=AsyncMock,
        return_value=mock_zotero_item_data
    )

    response = client.post(f"/api/v1/nodes/{node_id}/links/zotero", json={"zotero_key": "new_item_key"})
    
    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == str(node_id)
    assert link["link_type"] == "ZOTERO"
    assert "zotero_item_id" in link

    # Verify that ZoteroItem was created in our DB
    db_zotero_item = db_session.query(ZoteroItem).filter(ZoteroItem.zotero_key == "new_item_key").first()
    assert db_zotero_item is not None
    assert db_zotero_item.title == "Newly Linked Zotero Item"
    assert db_zotero_item.zotero_item_id == link["zotero_item_id"]
    
    zotero_service.get_item_by_key.assert_called_once_with("new_item_key")

@pytest.mark.asyncio
async def test_create_zotero_node_link_success_existing_item(client: TestClient, mocker, db_session):
    """
    Test successful creation of a Zotero node link when the Zotero item already exists in our DB.
    """
    # Create a dummy node and an existing ZoteroItem in our DB
    node_id = UUID("c0c0c0c0-c0c0-4c0c-8c0c-0c0c0c0c0c0c")
    curriculum_id = UUID("d0d0d0d0-d0d0-4d0d-8d0d-0d0d0d0d0d0d")
    db_session.add(Curriculum(curriculum_id=str(curriculum_id), title="Another Curriculum"))
    db_session.add(Node(node_id=str(node_id), curriculum_id=str(curriculum_id), title="Another Node", order_index=0))

    existing_zotero_item = ZoteroItem(
        zotero_key="existing_item_key",
        title="Existing Zotero Item",
        authors="Existing Author",
        publication_year=2020,
        item_type="book"
    )
    db_session.add(existing_zotero_item)
    db_session.commit()
    db_session.refresh(existing_zotero_item)
    zotero_item_id = existing_zotero_item.zotero_item_id  # Save before detaching

    # Ensure get_item_by_key is NOT called
    mocker.patch.object(zotero_service, "get_item_by_key", new_callable=AsyncMock)

    response = client.post(f"/api/v1/nodes/{node_id}/links/zotero", json={"zotero_key": "existing_item_key"})

    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == str(node_id)
    assert link["link_type"] == "ZOTERO"
    assert link["zotero_item_id"] == zotero_item_id

    zotero_service.get_item_by_key.assert_not_called()

@pytest.mark.asyncio
async def test_create_zotero_node_link_node_not_found(client: TestClient, mocker):
    """
    Test creation of a Zotero node link when the node does not exist.
    """
    non_existent_node_id = UUID("e0e0e0e0-e0e0-4e0e-8e0e-0e0e0e0e0e0e")
    mocker.patch.object(zotero_service, "get_item_by_key", new_callable=AsyncMock, return_value={}) # Mock to avoid error

    response = client.post(f"/api/v1/nodes/{non_existent_node_id}/links/zotero", json={"zotero_key": "some_key"})
    
    assert response.status_code == 404
    assert "Node not found" in response.json()["detail"]

@pytest.mark.asyncio
async def test_create_zotero_node_link_zotero_item_not_found_external(client: TestClient, mocker, db_session):
    """
    Test creation of a Zotero node link when the Zotero item is not found externally.
    """
    node_id = UUID("f0f0f0f0-f0f0-4f0f-8f0f-0f0f0f0f0f0f")
    curriculum_id = UUID("10101010-1010-4010-8010-010101010101")
    db_session.add(Curriculum(curriculum_id=str(curriculum_id), title="Temp Curriculum"))
    db_session.add(Node(node_id=str(node_id), curriculum_id=str(curriculum_id), title="Temp Node", order_index=0))
    db_session.commit()

    mocker.patch.object(
        zotero_service,
        "get_item_by_key",
        new_callable=AsyncMock,
        side_effect=ValueError("Failed to fetch Zotero item details: Zotero item with key 'non_existent_key' not found.")
    )

    response = client.post(f"/api/v1/nodes/{node_id}/links/zotero", json={"zotero_key": "non_existent_key"})
    
    assert response.status_code == 404
    assert "Failed to fetch Zotero item details" in response.json()["detail"]
    zotero_service.get_item_by_key.assert_called_once_with("non_existent_key")

def test_search_zotero_items_no_tag(client: TestClient):
    """
    Test search without providing a tag.
    """
    response = client.get("/api/v1/literature/zotero/items")
    assert response.status_code == 422 # Unprocessable Entity due to missing query parameter

def test_search_zotero_items_service_error(client: TestClient, mocker):
    """
    Test search when ZoteroService encounters an error.
    """
    settings.ZOTERO_API_BASE_URL = "http://mock-zotero-api.com"
    settings.ZOTERO_API_KEY = "mock_key"

    mocker.patch.object(
        zotero_service,
        "get_items_by_tag",
        new_callable=AsyncMock,
        side_effect=RuntimeError("Zotero API is down")
    )

    response = client.get("/api/v1/literature/zotero/items?tag=error_tag")
    assert response.status_code == 500
    assert "Zotero API is down" in response.json()["detail"]

def test_search_zotero_items_config_error(client: TestClient, mocker):
    """
    Test search when Zotero API base URL is not configured.
    """
    settings.ZOTERO_API_BASE_URL = None # Unset the base URL for this test

    mocker.patch.object(
        zotero_service,
        "get_items_by_tag",
        new_callable=AsyncMock,
        side_effect=ValueError("Zotero API base URL is not configured.")
    )

    response = client.get("/api/v1/literature/zotero/items?tag=any")
    assert response.status_code == 400
    assert "Zotero API base URL is not configured." in response.json()["detail"]
