from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.schemas.curriculum import CurriculumCreate, CurriculumResponse
from backend.app.models.curriculum import Curriculum
from backend.app.db.session import get_db

router = APIRouter()

@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
def create_simple_curriculum(
    curriculum_in: CurriculumCreate,
    db: Session = Depends(get_db)
):
    """
    A simple endpoint to create a curriculum directly using the provided DB session.
    """
    db_curriculum = Curriculum(
        title=curriculum_in.title,
        description=curriculum_in.description,
        is_public=curriculum_in.is_public
    )
    db.add(db_curriculum)
    db.commit()
    db.refresh(db_curriculum)
    return db_curriculum
