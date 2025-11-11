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

def test_read_literature_items_pagination(client: TestClient, db_session: Session):
    """
    GET /api/v1/literature 엔드포인트가 페이지네이션(skip, limit)을 올바르게 처리하는지 테스트합니다.
    """
    # 테스트용 문헌 항목 여러 개 생성
    created_items = []
    for i in range(10):
        item = {"title": f"Literature Item {i}", "authors": "Test Author", "publication_year": 2023, "item_type": "Article"}
        response = client.post("/api/v1/literature", json=item)
        assert response.status_code == 201
        created_items.append(response.json())
    
    # API는 생성 시간(created_at) 기준으로 정렬될 것으로 예상되므로, 테스트 데이터도 그렇게 정렬
    # 실제 서비스 계층의 정렬 로직에 따라 이 부분은 조정될 수 있음
    created_items.sort(key=lambda x: x["created_at"])

    # 첫 번째 페이지 조회 (limit=5, skip=0)
    response = client.get("/api/v1/literature?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["id"] == created_items[0]["id"]
    assert data[4]["id"] == created_items[4]["id"]

    # 두 번째 페이지 조회 (limit=5, skip=5)
    response = client.get("/api/v1/literature?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert data[0]["id"] == created_items[5]["id"]
    assert data[4]["id"] == created_items[9]["id"]

    # limit 초과 조회 (남은 항목만 반환)
    response = client.get("/api/v1/literature?skip=8&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == created_items[8]["id"]
    assert data[1]["id"] == created_items[9]["id"]

    # skip이 전체 항목 수보다 큰 경우
    response = client.get("/api/v1/literature?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0