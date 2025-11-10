import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate
from backend.app.services.curriculum_service import CurriculumService
import backend.app.models.youtube_video # Import for YouTubeVideo model
import backend.app.models.zotero_item # Import for ZoteroItem model

# Helper function to create a curriculum for testing nodes
def create_test_curriculum(db_session: Session) -> Curriculum:
    curriculum_service = CurriculumService(db_session)
    curriculum_in = CurriculumCreate(title="Test Curriculum for Nodes", description="Description for node tests")
    return curriculum_service.create_curriculum(curriculum_in)

# Helper function to create a node for testing node links
def create_test_node(client: TestClient, db_session: Session, curriculum_id: UUID) -> dict:
    node_data = {
        "curriculum_id": str(curriculum_id),
        "title": "Node for Link Test",
        "parent_node_id": None,
        "order_index": 0
    }
    response = client.post("/api/v1/nodes/", json=node_data)
    assert response.status_code == 201
    return response.json()

# --- NodeLink API Integration Tests ---

def test_create_node_link_youtube(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, db_session, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a dummy YouTubeVideo entry for the foreign key
    db_session.add(backend.app.models.youtube_video.YouTubeVideo(video_id="test_video_id", title="Test Video"))
    db_session.commit()
    youtube_video = db_session.query(backend.app.models.youtube_video.YouTubeVideo).filter_by(video_id="test_video_id").first()

    link_data = {
        "node_id": node_id,
        "link_type": "YOUTUBE",
        "youtube_video_id": str(youtube_video.youtube_video_id),
        "zotero_item_id": None
    }
    response = client.post(f"/api/v1/nodes/{node_id}/link", json=link_data)
    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == node_id
    assert link["link_type"] == "YOUTUBE"
    assert link["youtube_video_id"] == str(youtube_video.youtube_video_id)

def test_create_node_link_zotero(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, db_session, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a dummy ZoteroItem entry for the foreign key
    db_session.add(backend.app.models.zotero_item.ZoteroItem(zotero_key="test_zotero_key", title="Test Zotero Item"))
    db_session.commit()
    zotero_item = db_session.query(backend.app.models.zotero_item.ZoteroItem).filter_by(zotero_key="test_zotero_key").first()

    link_data = {
        "node_id": node_id,
        "link_type": "ZOTERO",
        "zotero_item_id": str(zotero_item.zotero_item_id),
        "youtube_video_id": None
    }
    response = client.post(f"/api/v1/nodes/{node_id}/link", json=link_data)
    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == node_id
    assert link["link_type"] == "ZOTERO"
    assert link["zotero_item_id"] == str(zotero_item.zotero_item_id)

def test_create_node_link_node_not_found(client: TestClient):
    non_existent_node_id = uuid4()
    link_data = {
        "node_id": str(non_existent_node_id),
        "link_type": "YOUTUBE",
        "youtube_video_id": str(uuid4())
    }
    response = client.post(f"/api/v1/nodes/{non_existent_node_id}/link", json=link_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"

def test_create_node_link_invalid_link_type(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, db_session, curriculum.curriculum_id)
    node_id = node["node_id"]

    link_data = {
        "node_id": node_id,
        "link_type": "INVALID",
        "youtube_video_id": str(uuid4())
    }
    response = client.post(f"/api/v1/nodes/{node_id}/link", json=link_data)
    assert response.status_code == 422 # Pydantic validation error

def test_read_node_links(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, db_session, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create dummy YouTubeVideo and ZoteroItem
    db_session.add(backend.app.models.youtube_video.YouTubeVideo(video_id="video1", title="Video 1"))
    db_session.add(backend.app.models.zotero_item.ZoteroItem(zotero_key="zotero1", title="Zotero 1"))
    db_session.commit()
    youtube_video = db_session.query(backend.app.models.youtube_video.YouTubeVideo).filter_by(video_id="video1").first()
    zotero_item = db_session.query(backend.app.models.zotero_item.ZoteroItem).filter_by(zotero_key="zotero1").first()

    link_data1 = {
        "node_id": node_id,
        "link_type": "YOUTUBE",
        "youtube_video_id": str(youtube_video.youtube_video_id),
        "zotero_item_id": None
    }
    link_data2 = {
        "node_id": node_id,
        "link_type": "ZOTERO",
        "zotero_item_id": str(zotero_item.zotero_item_id),
        "youtube_video_id": None
    }
    client.post(f"/api/v1/nodes/{node_id}/link", json=link_data1)
    client.post(f"/api/v1/nodes/{node_id}/link", json=link_data2)

    response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert response.status_code == 200
    links = response.json()
    assert len(links) == 2
    assert any(link["link_type"] == "YOUTUBE" for link in links)
    assert any(link["link_type"] == "ZOTERO" for link in links)

def test_delete_node_link(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, db_session, curriculum.curriculum_id)
    node_id = node["node_id"]

    db_session.add(backend.app.models.youtube_video.YouTubeVideo(video_id="video_to_delete", title="Video to Delete"))
    db_session.commit()
    youtube_video = db_session.query(backend.app.models.youtube_video.YouTubeVideo).filter_by(video_id="video_to_delete").first()

    link_data = {
        "node_id": node_id,
        "link_type": "YOUTUBE",
        "youtube_video_id": str(youtube_video.youtube_video_id),
        "zotero_item_id": None
    }
    create_link_response = client.post(f"/api/v1/nodes/{node_id}/link", json=link_data)
    created_link_id = create_link_response.json()["link_id"]

    response = client.delete(f"/api/v1/nodes/link/{created_link_id}")
    assert response.status_code == 204

    get_response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_delete_node_link_not_found(client: TestClient):
    non_existent_id = uuid4()
    response = client.delete(f"/api/v1/nodes/link/{non_existent_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node link not found"
