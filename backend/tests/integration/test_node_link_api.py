import pytest
from uuid import UUID, uuid4
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum
from backend.app.models.youtube_video import YouTubeVideo
from backend.app.models.zotero_item import ZoteroItem

def create_test_curriculum(db_session: Session) -> Curriculum:
    test_curriculum = Curriculum(title="Test Curriculum for Links", description="Desc for link tests")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    return test_curriculum

def create_test_node(client: TestClient, curriculum_id: UUID) -> dict:
    node_data = {"title": "Node for Link Test"}
    response = client.post(f"/api/v1/curriculums/{curriculum_id}/nodes", json=node_data)
    assert response.status_code == 201
    return response.json()

# --- NodeLink API Integration Tests ---

def test_create_youtube_link(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    link_data = {"youtube_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}
    response = client.post(f"/api/v1/nodes/{node_id}/links/youtube", json=link_data)
    
    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == node_id
    assert link["link_type"] == "YOUTUBE"
    assert link["youtube_video_id"] is not None

    # Verify the video was added to the DB
    video = db_session.query(YouTubeVideo).filter(YouTubeVideo.youtube_video_id == UUID(link["youtube_video_id"])).first()
    assert video is not None
    assert video.video_id == "dQw4w9WgXcQ"

def test_create_youtube_link_invalid_url(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    
    link_data = {"youtube_url": "https://www.not-youtube.com/watch?v=12345"}
    response = client.post(f"/api/v1/nodes/{node['node_id']}/links/youtube", json=link_data)
    assert response.status_code == 404 # Service raises ValueError which becomes 404 in endpoint
    assert "Invalid YouTube URL" in response.json()["detail"]

def test_create_zotero_link(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a dummy ZoteroItem to link to
    zotero_item = ZoteroItem(zotero_key="test_key", title="Test Zotero Item")
    db_session.add(zotero_item)
    db_session.commit()
    db_session.refresh(zotero_item)

    link_data = {"zotero_item_id": str(zotero_item.zotero_item_id)}
    response = client.post(f"/api/v1/nodes/{node_id}/links/zotero", json=link_data)
    
    assert response.status_code == 201
    link = response.json()
    assert link["node_id"] == node_id
    assert link["link_type"] == "ZOTERO"
    assert link["zotero_item_id"] == str(zotero_item.zotero_item_id)

def test_create_zotero_link_item_not_found(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)

    link_data = {"zotero_item_id": str(uuid4())} # Non-existent ID
    response = client.post(f"/api/v1/nodes/{node['node_id']}/links/zotero", json=link_data)
    assert response.status_code == 404
    assert "Zotero item not found" in response.json()["detail"]

def test_read_node_links(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a Zotero link
    zotero_item = ZoteroItem(zotero_key="test_key_read", title="Test Zotero Item")
    db_session.add(zotero_item)
    db_session.commit()
    db_session.refresh(zotero_item)
    client.post(f"/api/v1/nodes/{node_id}/links/zotero", json={"zotero_item_id": str(zotero_item.zotero_item_id)})

    # Create a YouTube link
    client.post(f"/api/v1/nodes/{node_id}/links/youtube", json={"youtube_url": "https://youtu.be/abcdef12345"})

    response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert response.status_code == 200
    links = response.json()
    assert len(links) == 2
    assert any(link["link_type"] == "YOUTUBE" for link in links)
    assert any(link["link_type"] == "ZOTERO" for link in links)

def test_delete_node_link_success_youtube(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a YouTube link to delete
    link_response = client.post(f"/api/v1/nodes/{node_id}/links/youtube", json={"youtube_url": "https://youtu.be/dQw4w9WgXcQ"})
    assert link_response.status_code == 201, link_response.json()
    link_id = link_response.json()["link_id"]

    # Delete the link
    delete_response = client.delete(f"/api/v1/nodes/{node_id}/links/{link_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_delete_node_link_success_zotero(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    node_id = node["node_id"]

    # Create a dummy ZoteroItem to link to
    zotero_item = ZoteroItem(zotero_key="test_key_delete", title="Test Zotero Item for Delete")
    db_session.add(zotero_item)
    db_session.commit()
    db_session.refresh(zotero_item)

    # Create a Zotero link to delete
    link_response = client.post(f"/api/v1/nodes/{node_id}/links/zotero", json={"zotero_item_id": str(zotero_item.zotero_item_id)})
    assert link_response.status_code == 201, link_response.json()
    link_id = link_response.json()["link_id"]

    # Delete the link
    delete_response = client.delete(f"/api/v1/nodes/{node_id}/links/{link_id}")
    assert delete_response.status_code == 204

    # Verify it's gone
    get_response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert get_response.status_code == 200
    assert len(get_response.json()) == 0

def test_delete_node_link_node_not_found(client: TestClient):
    non_existent_node_id = uuid4()
    some_link_id = uuid4() # This link_id doesn't matter as the node won't be found
    response = client.delete(f"/api/v1/nodes/{non_existent_node_id}/links/{some_link_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node not found"

def test_delete_node_link_link_not_found(client: TestClient, db_session: Session):
    curriculum = create_test_curriculum(db_session)
    node = create_test_node(client, curriculum.curriculum_id)
    
    non_existent_link_id = uuid4()
    response = client.delete(f"/api/v1/nodes/{node['node_id']}/links/{non_existent_link_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Node link not found"
