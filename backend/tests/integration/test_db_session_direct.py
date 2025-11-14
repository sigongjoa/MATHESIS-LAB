from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum

def test_direct_curriculum_creation(db_session: Session):
    """
    db_session 픽스처를 직접 사용하여 커리큘럼을 생성하고 조회하는 테스트.
    """
    # 1. 커리큘럼 객체 생성
    curriculum_data = {
        "title": "Direct Test Curriculum",
        "description": "Description for direct test curriculum",
        "is_public": False
    }
    new_curriculum = Curriculum(**curriculum_data)

    # 2. 세션에 추가하고 플러시
    db_session.add(new_curriculum)
    db_session.flush()
    db_session.refresh(new_curriculum) # ID를 얻기 위해 새로고침

    print(f"Directly created curriculum ID: {new_curriculum.curriculum_id}")

    # 3. 동일한 세션에서 조회
    retrieved_curriculum = db_session.query(Curriculum).filter(
        Curriculum.curriculum_id == new_curriculum.curriculum_id
    ).first()

    # 4. 어설션
    assert retrieved_curriculum is not None
    assert retrieved_curriculum.title == curriculum_data["title"]
    assert retrieved_curriculum.description == curriculum_data["description"]
    assert retrieved_curriculum.is_public == curriculum_data["is_public"]
    assert retrieved_curriculum.curriculum_id == new_curriculum.curriculum_id
