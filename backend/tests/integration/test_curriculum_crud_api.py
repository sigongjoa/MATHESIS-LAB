import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate, CurriculumUpdate

def test_create_curriculum(client: TestClient, db_session: Session):
    """
    POST /api/v1/curriculums 엔드포인트가 새 커리큘럼을 올바르게 생성하는지 테스트합니다.
    """
    curriculum_data = {"title": "New Test Curriculum", "description": "Description for new curriculum", "is_public": False}
    response = client.post("/api/v1/curriculums/", json=curriculum_data)

    assert response.status_code == 201
    created_curriculum = response.json()
    assert created_curriculum["title"] == curriculum_data["title"]
    assert created_curriculum["description"] == curriculum_data["description"]
    assert "curriculum_id" in created_curriculum
    assert "created_at" in created_curriculum
    assert "updated_at" in created_curriculum

    # 데이터베이스에 실제로 생성되었는지 확인
    db_session.expire_all()
    db_curriculum = db_session.query(Curriculum).filter(Curriculum.curriculum_id == created_curriculum["curriculum_id"]).first()
    assert db_curriculum is not None
    assert db_curriculum.title == curriculum_data["title"]

def test_create_curriculum_invalid_data(client: TestClient):
    """
    POST /api/v1/curriculums 엔드포인트가 유효하지 않은 데이터에 대해 422 에러를 반환하는지 테스트합니다.
    """
    curriculum_data = {"title": "", "description": "Invalid title"} # 빈 제목
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 422

def test_read_curriculum(client: TestClient, db_session: Session):
    """
    GET /api/v1/curriculums/{curriculum_id} 엔드포인트가 특정 커리큘럼을 올바르게 조회하는지 테스트합니다.
    """
    # 1. API를 통해 테스트용 커리큘럼 생성
    curriculum_data = {"title": "Read Test", "description": "Test for reading"}
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 201
    created_curriculum = response.json()
    curriculum_id = created_curriculum["curriculum_id"]

    # 2. 생성된 커리큘럼을 API를 통해 조회
    db_session.expire_all()
    response = client.get(f"/api/v1/curriculums/{curriculum_id}")

    assert response.status_code == 200
    retrieved_curriculum = response.json()
    assert retrieved_curriculum["title"] == curriculum_data["title"]
    assert retrieved_curriculum["description"] == curriculum_data["description"]
    assert retrieved_curriculum["curriculum_id"] == curriculum_id
    assert "nodes" in retrieved_curriculum
    assert retrieved_curriculum["nodes"] == []

def test_read_curriculum_not_found(client: TestClient):
    """
    GET /api/v1/curriculums/{curriculum_id} 엔드포인트가 존재하지 않는 ID에 대해 404 에러를 반환하는지 테스트합니다.
    """
    non_existent_uuid = UUID("12345678-1234-5678-1234-567812345678")
    response = client.get(f"/api/v1/curriculums/{non_existent_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Curriculum not found"

def test_update_curriculum(client: TestClient, db_session: Session):
    """
    PUT /api/v1/curriculums/{curriculum_id} 엔드포인트가 커리큘럼을 올바르게 업데이트하는지 테스트합니다.
    """
    # 1. API를 통해 테스트용 커리큘럼 생성
    initial_data = {"title": "Update Test", "description": "Original description"}
    response = client.post("/api/v1/curriculums/", json=initial_data)
    assert response.status_code == 201
    created_curriculum = response.json()
    curriculum_id = created_curriculum["curriculum_id"]

    # 2. 생성된 커리큘럼을 API를 통해 업데이트
    db_session.expire_all()
    update_data = {"title": "Updated Title", "description": "Updated description"}
    response = client.put(f"/api/v1/curriculums/{curriculum_id}", json=update_data)

    assert response.status_code == 200
    updated_curriculum = response.json()
    assert updated_curriculum["title"] == update_data["title"]
    assert updated_curriculum["description"] == update_data["description"]

    # 3. 데이터베이스에 실제로 업데이트되었는지 확인 (API를 통해 다시 조회)
    db_session.expire_all()
    response = client.get(f"/api/v1/curriculums/{curriculum_id}")
    assert response.status_code == 200
    db_curriculum = response.json()
    assert db_curriculum["title"] == update_data["title"]
    assert db_curriculum["description"] == update_data["description"]

def test_update_curriculum_not_found(client: TestClient):
    """
    PUT /api/v1/curriculums/{curriculum_id} 엔드포인트가 존재하지 않는 ID 업데이트 시 404 에러를 반환하는지 테스트합니다.
    """
    non_existent_uuid = UUID("12345678-1234-5678-1234-567812345678")
    update_data = {"title": "Non Existent"}
    response = client.put(f"/api/v1/curriculums/{non_existent_uuid}", json=update_data)
    assert response.status_code == 404
    assert response.json()["detail"] == "Curriculum not found"

def test_delete_curriculum(client: TestClient, db_session: Session):
    """
    DELETE /api/v1/curriculums/{curriculum_id} 엔드포인트가 커리큘럼을 올바르게 삭제하는지 테스트합니다.
    """
    # 1. API를 통해 테스트용 커리큘럼 생성
    initial_data = {"title": "Delete Test", "description": "To be deleted"}
    response = client.post("/api/v1/curriculums/", json=initial_data)
    assert response.status_code == 201
    created_curriculum = response.json()
    curriculum_id = created_curriculum["curriculum_id"]

    # 2. 생성된 커리큘럼을 API를 통해 삭제
    db_session.expire_all()
    response = client.delete(f"/api/v1/curriculums/{curriculum_id}")
    assert response.status_code == 204

    # 3. 데이터베이스에서 실제로 삭제되었는지 확인 (API를 통해 다시 조회)
    db_session.expire_all()
    response = client.get(f"/api/v1/curriculums/{curriculum_id}")
    assert response.status_code == 404

def test_delete_curriculum_not_found(client: TestClient):
    """
    DELETE /api/v1/curriculums/{curriculum_id} 엔드포인트가 존재하지 않는 ID 삭제 시 404 에러를 반환하는지 테스트합니다.
    """
    non_existent_uuid = UUID("12345678-1234-5678-1234-567812345678")
    response = client.delete(f"/api/v1/curriculums/{non_existent_uuid}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Curriculum not found"
