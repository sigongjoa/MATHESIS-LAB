from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
import pytest

from backend.app.schemas.literature_item import LiteratureItemCreate, LiteratureItemUpdate

def test_create_literature_item(client: TestClient, db_session: Session):
    data = {
        "title": "Test Driven Development",
        "authors": "Kent Beck",
        "publication_year": 2002,
        "tags": "tdd, testing, software engineering",
        "item_type": "Book",
        "abstract": "An introduction to TDD.",
        "url": "http://example.com/tdd"
    }
    response = client.post("/api/v1/literature", json=data)
    assert response.status_code == 201
    content = response.json()
    assert content["title"] == data["title"]
    assert content["authors"] == data["authors"]
    assert "id" in content

def test_read_literature_item(client: TestClient, db_session: Session):
    data = {
        "title": "Clean Code",
        "authors": "Robert C. Martin",
        "publication_year": 2008,
        "tags": "software craftsmanship, best practices",
        "item_type": "Book"
    }
    response = client.post("/api/v1/literature", json=data)
    assert response.status_code == 201
    item_id = response.json()["id"]

    response = client.get(f"/api/v1/literature/{item_id}")
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == data["title"]
    assert content["id"] == item_id

def test_read_nonexistent_literature_item(client: TestClient, db_session: Session):
    import uuid
    non_existent_id = uuid.uuid4()
    response = client.get(f"/api/v1/literature/{non_existent_id}")
    assert response.status_code == 404

def test_update_literature_item(client: TestClient, db_session: Session):
    data = {"title": "Initial Title", "tags": "initial"}
    response = client.post("/api/v1/literature", json=data)
    assert response.status_code == 201
    item_id = response.json()["id"]

    update_data = {"title": "Updated Title", "tags": "updated, revised"}
    response = client.put(f"/api/v1/literature/{item_id}", json=update_data)
    assert response.status_code == 200
    content = response.json()
    assert content["title"] == update_data["title"]
    assert content["tags"] == update_data["tags"]

def test_delete_literature_item(client: TestClient, db_session: Session):
    data = {"title": "To Be Deleted"}
    response = client.post("/api/v1/literature", json=data)
    assert response.status_code == 201
    item_id = response.json()["id"]

    response = client.delete(f"/api/v1/literature/{item_id}")
    assert response.status_code == 200
    
    # Verify it's gone
    response = client.get(f"/api/v1/literature/{item_id}")
    assert response.status_code == 404

def test_read_literature_items_with_tags(client: TestClient, db_session: Session):
    # Create items
    client.post("/api/v1/literature", json={"title": "Item 1", "tags": "python, fastapi"})
    client.post("/api/v1/literature", json={"title": "Item 2", "tags": "python, testing"})
    client.post("/api/v1/literature", json={"title": "Item 3", "tags": "fastapi, testing"})
    client.post("/api/v1/literature", json={"title": "Item 4", "tags": "javascript"})

    # Test AND search (default)
    response = client.get("/api/v1/literature?tags=python,fastapi")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == "Item 1"

    # Test AND search (explicit)
    response = client.get("/api/v1/literature?tags=python,testing&match=all")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 1
    assert items[0]["title"] == "Item 2"

    # Test OR search
    response = client.get("/api/v1/literature?tags=python,javascript&match=any")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 3
    titles = {item["title"] for item in items}
    assert {"Item 1", "Item 2", "Item 4"} == titles

    # Test single tag search
    response = client.get("/api/v1/literature?tags=fastapi")
    assert response.status_code == 200
    items = response.json()
    assert len(items) == 2
    titles = {item["title"] for item in items}
    assert {"Item 1", "Item 3"} == titles
    
    # Test no tags
    response = client.get("/api/v1/literature")
    assert response.status_code == 200
    assert len(response.json()) >= 4