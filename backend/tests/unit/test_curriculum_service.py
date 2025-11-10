import pytest
from unittest.mock import MagicMock
from uuid import UUID, uuid4

from backend.app.services.curriculum_service import CurriculumService # Import the class
from backend.app.schemas.curriculum import CurriculumCreate, CurriculumUpdate
from backend.app.models.curriculum import Curriculum

@pytest.fixture
def mock_db_session():
    """
    데이터베이스 세션을 모킹하는 픽스처.
    """
    return MagicMock()

@pytest.fixture
def curriculum_service(mock_db_session):
    """
    CurriculumService 인스턴스를 제공하는 픽스처.
    """
    return CurriculumService(mock_db_session)

def test_create_curriculum(curriculum_service: CurriculumService, mock_db_session):
    """
    create_curriculum 함수가 새 커리큘럼을 올바르게 생성하는지 테스트합니다.
    """
    curriculum_data = CurriculumCreate(title="Test Curriculum", description="A test description")
    
    # create_curriculum 함수는 db.add, db.commit, db.refresh를 호출합니다.
    # db.refresh가 호출될 때 db_curriculum 객체가 업데이트되도록 모킹합니다.
    mock_db_session.refresh.side_effect = lambda obj: setattr(obj, "curriculum_id", uuid4())

    created_curriculum = curriculum_service.create_curriculum(curriculum_data)

    mock_db_session.add.assert_called_once()
    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(created_curriculum)

    assert created_curriculum.title == curriculum_data.title
    assert created_curriculum.description == curriculum_data.description
    assert isinstance(created_curriculum.curriculum_id, UUID)

def test_get_curriculum(curriculum_service: CurriculumService, mock_db_session):
    """
    get_curriculum 함수가 ID로 커리큘럼을 올바르게 조회하는지 테스트합니다.
    """
    test_uuid = uuid4()
    mock_curriculum = Curriculum(curriculum_id=test_uuid, title="Existing Curriculum")
    
    # filter().first() 호출 시 mock_curriculum을 반환하도록 모킹합니다.
    mock_db_session.query.return_value.filter.return_value.first.return_value = mock_curriculum

    retrieved_curriculum = curriculum_service.get_curriculum(test_uuid)

    mock_db_session.query.assert_called_once_with(Curriculum)
    mock_db_session.query.return_value.filter.assert_called_once()
    assert retrieved_curriculum == mock_curriculum

def test_get_curriculum_not_found(curriculum_service: CurriculumService, mock_db_session):
    """
    get_curriculum 함수가 존재하지 않는 ID에 대해 None을 반환하는지 테스트합니다.
    """
    test_uuid = uuid4()
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    retrieved_curriculum = curriculum_service.get_curriculum(test_uuid)

    assert retrieved_curriculum is None

def test_update_curriculum(curriculum_service: CurriculumService, mock_db_session):
    """
    update_curriculum 함수가 커리큘럼을 올바르게 업데이트하는지 테스트합니다.
    """
    test_uuid = uuid4()
    existing_curriculum = Curriculum(curriculum_id=test_uuid, title="Old Title", description="Old Description")
    update_data = CurriculumUpdate(title="New Title", description="New Description")

    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_curriculum
    
    updated_curriculum = curriculum_service.update_curriculum(test_uuid, update_data)

    mock_db_session.commit.assert_called_once()
    mock_db_session.refresh.assert_called_once_with(updated_curriculum)
    assert updated_curriculum.title == "New Title"
    assert updated_curriculum.description == "New Description"

def test_update_curriculum_not_found(curriculum_service: CurriculumService, mock_db_session):
    """
    update_curriculum 함수가 존재하지 않는 커리큘럼 업데이트 시 None을 반환하는지 테스트합니다.
    """
    test_uuid = uuid4()
    update_data = CurriculumUpdate(title="New Title")
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    updated_curriculum = curriculum_service.update_curriculum(test_uuid, update_data)

    mock_db_session.commit.assert_not_called()
    assert updated_curriculum is None

def test_delete_curriculum(curriculum_service: CurriculumService, mock_db_session):
    """
    delete_curriculum 함수가 커리큘럼을 올바르게 삭제하는지 테스트합니다.
    """
    test_uuid = uuid4()
    existing_curriculum = Curriculum(curriculum_id=test_uuid, title="To Be Deleted")
    mock_db_session.query.return_value.filter.return_value.first.return_value = existing_curriculum

    deleted_curriculum = curriculum_service.delete_curriculum(test_uuid)

    mock_db_session.delete.assert_called_once_with(existing_curriculum)
    mock_db_session.commit.assert_called_once()
    assert deleted_curriculum == existing_curriculum

def test_delete_curriculum_not_found(curriculum_service: CurriculumService, mock_db_session):
    """
    delete_curriculum 함수가 존재하지 않는 커리큘럼 삭제 시 None을 반환하는지 테스트합니다.
    """
    test_uuid = uuid4()
    mock_db_session.query.return_value.filter.return_value.first.return_value = None

    deleted_curriculum = curriculum_service.delete_curriculum(test_uuid)

    mock_db_session.delete.assert_not_called()
    mock_db_session.commit.assert_not_called()
    assert deleted_curriculum is None