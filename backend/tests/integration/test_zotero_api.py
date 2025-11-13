import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock

from backend.app.core.config import settings
from backend.app.services.zotero_service import zotero_service

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
