from sqlalchemy.orm import Session
from uuid import UUID

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate, CurriculumUpdate

def create_curriculum(db: Session, curriculum: CurriculumCreate) -> Curriculum:
    db_curriculum = Curriculum(title=curriculum.title, description=curriculum.description)
    db.add(db_curriculum)
    db.commit()
    db.refresh(db_curriculum)
    return db_curriculum

def get_curriculum(db: Session, curriculum_id: UUID) -> Curriculum | None:
    return db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()

def update_curriculum(db: Session, curriculum_id: UUID, curriculum: CurriculumUpdate) -> Curriculum | None:
    db_curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if db_curriculum:
        update_data = curriculum.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_curriculum, key, value)
        db.add(db_curriculum)
        db.commit()
        db.refresh(db_curriculum)
    return db_curriculum

def delete_curriculum(db: Session, curriculum_id: UUID) -> Curriculum | None:
    db_curriculum = db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
    if db_curriculum:
        db.delete(db_curriculum)
        db.commit()
    return db_curriculum