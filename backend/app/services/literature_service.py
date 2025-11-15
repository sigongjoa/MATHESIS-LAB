from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import or_, and_
from backend.app.models.literature_item import LiteratureItem
from backend.app.schemas.literature_item import LiteratureItemCreate, LiteratureItemUpdate
import uuid

class LiteratureService:
    def __init__(self, db: Session):
        self.db = db

    def get(self, item_id: uuid.UUID) -> Optional[LiteratureItem]:
        return self.db.query(LiteratureItem).filter(LiteratureItem.id == str(item_id)).first()

    def get_multi(self, skip: int = 0, limit: int = 100) -> List[LiteratureItem]:
        return self.db.query(LiteratureItem).offset(skip).limit(limit).all()

    def get_multi_by_tags(
        self, tags: List[str], match: str = "all", skip: int = 0, limit: int = 100
    ) -> List[LiteratureItem]:
        if not tags:
            return self.get_multi(skip=skip, limit=limit)

        query = self.db.query(LiteratureItem)

        if match == "any":
            # OR logic: find items containing any of the tags
            conditions = [LiteratureItem.tags.contains(tag) for tag in tags]
            query = query.filter(or_(*conditions))
        else:
            # AND logic (default): find items containing all of the tags
            conditions = [LiteratureItem.tags.contains(tag) for tag in tags]
            query = query.filter(and_(*conditions))

        return query.offset(skip).limit(limit).all()

    def create(self, item_in: LiteratureItemCreate) -> LiteratureItem:
        db_item = LiteratureItem(**item_in.model_dump())
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def update(
        self, item_id: uuid.UUID, item_in: LiteratureItemUpdate
    ) -> Optional[LiteratureItem]:
        db_item = self.get(item_id)
        if not db_item:
            return None
        update_data = item_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_item, field, value)
        self.db.add(db_item)
        self.db.commit()
        self.db.refresh(db_item)
        return db_item

    def delete(self, item_id: uuid.UUID) -> Optional[LiteratureItem]:
        db_item = self.get(item_id)
        if not db_item:
            return None
        self.db.delete(db_item)
        self.db.commit()
        return db_item

literature_service: LiteratureService
