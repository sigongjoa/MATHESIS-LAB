from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.curriculum import CurriculumCreate, CurriculumResponse, CurriculumUpdate
from backend.app.services.curriculum_service import CurriculumService # Import the class
from backend.app.db.session import get_db

router = APIRouter()

# Dependency to get CurriculumService
def get_curriculum_service(db: Session = Depends(get_db)) -> CurriculumService:
    return CurriculumService(db)

@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
def create_curriculum(
    curriculum_in: CurriculumCreate, # Renamed parameter for clarity
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    새로운 커리큘럼 맵을 생성합니다.
    """
    db_curriculum = curriculum_service.create_curriculum(curriculum_in)
    return db_curriculum

@router.get("/{curriculum_id}", response_model=CurriculumResponse)
def read_curriculum(
    curriculum_id: UUID,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    특정 커리큘럼 맵의 상세 정보를 조회합니다.
    """
    db_curriculum = curriculum_service.get_curriculum(curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return db_curriculum

@router.put("/{curriculum_id}", response_model=CurriculumResponse)
def update_curriculum(
    curriculum_id: UUID,
    curriculum_in: CurriculumUpdate, # Renamed parameter for clarity
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    특정 커리큘럼 맵의 정보를 업데이트합니다.
    """
    db_curriculum = curriculum_service.update_curriculum(curriculum_id, curriculum_in)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return db_curriculum

@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum(
    curriculum_id: UUID,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    특정 커리큘럼 맵을 삭제합니다.
    """
    db_curriculum = curriculum_service.delete_curriculum(curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return