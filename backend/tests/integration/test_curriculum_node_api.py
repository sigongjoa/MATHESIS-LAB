import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate, CurriculumUpdate

def test_create_node_for_curriculum(client: TestClient, db_session: Session):
    """
    POST /api/v1/curriculums/{curriculum_id}/nodes 엔드포인트가 노드를 올바르게 생성하는지 테스트합니다.
    """
    # 1. 테스트용 커리큘럼 생성
    test_curriculum = Curriculum(title="Curriculum for Node Test", description="Desc")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)

    # 2. 노드 생성 요청
    node_data = {"title": "New Node", "parent_node_id": None}
    response = client.post(f"/api/v1/curriculums/{test_curriculum.curriculum_id}/nodes", json=node_data)

    # 3. 검증
    assert response.status_code == 201
    created_node = response.json()
    assert created_node["title"] == node_data["title"]
    assert created_node["curriculum_id"] == str(test_curriculum.curriculum_id)
    assert "node_id" in created_node
    assert created_node["order_index"] == 0 # 첫 번째 노드이므로 0

def test_read_curriculum_with_nodes(client: TestClient, db_session: Session):
    """
    GET /api/v1/curriculums/{curriculum_id}가 노드를 포함하여 올바르게 반환하는지 테스트합니다.
    """
    # 1. 커리큘럼 및 노드 생성
    test_curriculum = Curriculum(title="Curriculum with Nodes", description="Desc")
    db_session.add(test_curriculum)
    db_session.commit()
    db_session.refresh(test_curriculum)
    
    node_data = {"title": "Node in Curriculum", "parent_node_id": None}
    client.post(f"/api/v1/curriculums/{test_curriculum.curriculum_id}/nodes", json=node_data)

    # 2. 커리큘럼 조회
    response = client.get(f"/api/v1/curriculums/{test_curriculum.curriculum_id}")

    # 3. 검증
    assert response.status_code == 200
    retrieved_curriculum = response.json()
    assert retrieved_curriculum["title"] == test_curriculum.title
    assert len(retrieved_curriculum["nodes"]) == 1
    assert retrieved_curriculum["nodes"][0]["title"] == node_data["title"]
    assert retrieved_curriculum["nodes"][0]["curriculum_id"] == str(test_curriculum.curriculum_id)