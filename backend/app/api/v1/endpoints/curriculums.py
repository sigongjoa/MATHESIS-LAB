from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.curriculum import CurriculumCreate, CurriculumResponse, CurriculumUpdate
from backend.app.services import curriculum_service
from backend.app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
def create_curriculum(
    curriculum: CurriculumCreate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    새로운 커리큘럼 맵을 생성합니다.
    """
    db_curriculum = curriculum_service.create_curriculum(db, curriculum)
    return db_curriculum

@router.get("/{curriculum_id}", response_model=CurriculumResponse)
def read_curriculum(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 커리큘럼 맵의 상세 정보를 조회합니다.
    """
    db_curriculum = curriculum_service.get_curriculum(db, curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return db_curriculum

@router.put("/{curriculum_id}", response_model=CurriculumResponse)
def update_curriculum(
    curriculum_id: UUID,
    curriculum: CurriculumUpdate,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 커리큘럼 맵의 정보를 업데이트합니다.
    """
    db_curriculum = curriculum_service.update_curriculum(db, curriculum_id, curriculum)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return db_curriculum

@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum(
    curriculum_id: UUID,
    db: Annotated[Session, Depends(get_db)]
):
    """
    특정 커리큘럼 맵을 삭제합니다.
    """
    db_curriculum = curriculum_service.delete_curriculum(db, curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return {"ok": True}