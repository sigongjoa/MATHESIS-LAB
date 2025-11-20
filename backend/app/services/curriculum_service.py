from sqlalchemy.orm import Session
from uuid import UUID
from typing import Optional

from backend.app.models.curriculum import Curriculum
from backend.app.schemas.curriculum import CurriculumCreate, CurriculumUpdate

class CurriculumService:
    def __init__(self, db: Session):
        self.db = db

    def get_all_curriculums(self) -> list[Curriculum]:
        return self.db.query(Curriculum).all()

    def create_curriculum(self, curriculum_in: CurriculumCreate, owner_user=None) -> Curriculum:
        db_curriculum = Curriculum(
            title=curriculum_in.title, 
            description=curriculum_in.description,
            is_public=curriculum_in.is_public
        )
        self.db.add(db_curriculum)
        self.db.commit()
        self.db.refresh(db_curriculum)

        # [NEW] Sync to Google Drive using user's credentials
        if owner_user:
            try:
                from backend.app.services.gdrive_service import get_user_gdrive_service
                user_gdrive = get_user_gdrive_service(owner_user)
                folder_id = user_gdrive.create_folder(db_curriculum.title)
                db_curriculum.gdrive_folder_id = folder_id
                self.db.add(db_curriculum)
                self.db.commit()
                self.db.refresh(db_curriculum)
            except Exception as e:
                # In a real app, we might want to queue this for retry
                print(f"Failed to create GDrive folder: {e}")

        return db_curriculum

    def get_curriculum(self, curriculum_id: UUID) -> Optional[Curriculum]:
        return self.db.query(Curriculum).filter(Curriculum.curriculum_id == str(curriculum_id)).first()

    def get_public_curriculums(self, skip: int = 0, limit: int = 100) -> list[Curriculum]:
        return self.db.query(Curriculum).filter(Curriculum.is_public == True).offset(skip).limit(limit).all()

    def update_curriculum(self, curriculum_id: UUID, curriculum_in: CurriculumUpdate) -> Optional[Curriculum]:
        db_curriculum = self.get_curriculum(curriculum_id)
        if db_curriculum:
            update_data = curriculum_in.model_dump(exclude_unset=True)
            for key, value in update_data.items():
                setattr(db_curriculum, key, value)
            self.db.add(db_curriculum)
            self.db.commit()
            self.db.refresh(db_curriculum)
        return db_curriculum

    def delete_curriculum(self, curriculum_id: UUID) -> Optional[Curriculum]:
        db_curriculum = self.get_curriculum(curriculum_id)
        if db_curriculum:
            self.db.delete(db_curriculum)
            self.db.commit()
        return db_curriculum