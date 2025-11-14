import pytest
from uuid import UUID
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.models.curriculum import Curriculum

# --- Public Curriculum API Integration Tests ---

def test_create_public_curriculum(client: TestClient):
    """
    Test creating a curriculum and setting it to public.
    """
    curriculum_data = {
        "title": "Public Curriculum",
        "description": "This curriculum is for everyone.",
        "is_public": True
    }
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 201
    curriculum = response.json()
    assert curriculum["title"] == "Public Curriculum"
    assert curriculum["is_public"] is True

def test_create_private_curriculum_by_default(client: TestClient):
    """
    Test that a curriculum is private by default.
    """
    curriculum_data = {
        "title": "Private Curriculum",
        "description": "This is a private curriculum."
    }
    response = client.post("/api/v1/curriculums/", json=curriculum_data)
    assert response.status_code == 201
    curriculum = response.json()
    assert curriculum["title"] == "Private Curriculum"
    assert curriculum["is_public"] is False

def test_update_curriculum_to_public(client: TestClient, db_session: Session):
    """
    Test updating a curriculum to make it public.
    """
    # 1. Create a private curriculum
    private_curriculum = Curriculum(title="Soon to be Public", description="Initial description", is_public=False)
    db_session.add(private_curriculum)
    db_session.commit()
    db_session.refresh(private_curriculum)
    curriculum_id = private_curriculum.curriculum_id

    # 2. Update it to be public
    update_data = {"is_public": True}
    response = client.put(f"/api/v1/curriculums/{curriculum_id}", json=update_data)
    assert response.status_code == 200
    updated_curriculum = response.json()
    assert updated_curriculum["is_public"] is True

def test_read_public_curriculums(client: TestClient, db_session: Session):
    """
    Test that the /public endpoint returns only public curriculums.
    """
    # 1. Create a mix of public and private curriculums
    db_session.add(Curriculum(title="Public One", is_public=True))
    db_session.add(Curriculum(title="Private One", is_public=False))
    db_session.add(Curriculum(title="Public Two", is_public=True))
    db_session.commit()

    # 2. Call the public endpoint
    response = client.get("/api/v1/curriculums/public")
    assert response.status_code == 200
    public_curriculums = response.json()

    # 3. Check the results
    assert len(public_curriculums) == 2
    titles = {c["title"] for c in public_curriculums}
    assert "Public One" in titles
    assert "Public Two" in titles
    assert "Private One" not in titles

def test_read_all_curriculums_for_completeness(client: TestClient, db_session: Session):
    """
    Test the standard /curriculums endpoint to ensure it returns everything (for comparison).
    This test assumes the standard endpoint is not filtered for public/private.
    """
    # 1. Clear and create a mix of public and private curriculums
    db_session.query(Curriculum).delete()
    db_session.add(Curriculum(title="Public One", is_public=True))
    db_session.add(Curriculum(title="Private One", is_public=False))
    db_session.commit()

    # 2. Call the main endpoint
    response = client.get("/api/v1/curriculums/")
    assert response.status_code == 200
    all_curriculums = response.json()

    # 3. Check the results
    assert len(all_curriculums) == 2
    
def test_read_public_curriculums_pagination(client: TestClient, db_session: Session):
    """
    GET /api/v1/curriculums/public 엔드포인트가 페이지네이션(skip, limit)을 올바르게 처리하는지 테스트합니다.
    """
    # 테스트용 공개 커리큘럼 여러 개 생성
    created_curriculums = []
    for i in range(10):
        curriculum = Curriculum(title=f"Public Curriculum {i}", description=f"Description {i}", is_public=True)
        db_session.add(curriculum)
        created_curriculums.append(curriculum)
    db_session.commit()
    
    # 생성된 커리큘럼을 created_at 기준으로 정렬 (API 응답 순서를 예측하기 위함)
    created_curriculums.sort(key=lambda c: c.created_at)

    # 첫 번째 페이지 조회 (limit=5, skip=0)
    response = client.get("/api/v1/curriculums/public?skip=0&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert UUID(data[0]["curriculum_id"]) == created_curriculums[0].curriculum_id
    assert UUID(data[4]["curriculum_id"]) == created_curriculums[4].curriculum_id

    # 두 번째 페이지 조회 (limit=5, skip=5)
    response = client.get("/api/v1/curriculums/public?skip=5&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 5
    assert UUID(data[0]["curriculum_id"]) == created_curriculums[5].curriculum_id
    assert UUID(data[4]["curriculum_id"]) == created_curriculums[9].curriculum_id

    # limit 초과 조회 (남은 항목만 반환)
    response = client.get("/api/v1/curriculums/public?skip=8&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert UUID(data[0]["curriculum_id"]) == created_curriculums[8].curriculum_id
    assert UUID(data[1]["curriculum_id"]) == created_curriculums[9].curriculum_id

    # skip이 전체 항목 수보다 큰 경우
    response = client.get("/api/v1/curriculums/public?skip=10&limit=5")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 0
