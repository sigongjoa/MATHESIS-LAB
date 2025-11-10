import uuid
from pydantic import BaseModel, ConfigDict
from datetime import datetime
from typing import Optional

class LiteratureItemBase(BaseModel):
    title: str
    authors: Optional[str] = None
    publication_year: Optional[int] = None
    tags: Optional[str] = None
    item_type: Optional[str] = None
    abstract: Optional[str] = None
    url: Optional[str] = None

class LiteratureItemCreate(LiteratureItemBase):
    pass

class LiteratureItemUpdate(LiteratureItemBase):
    title: Optional[str] = None

class LiteratureItemInDB(LiteratureItemBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)

class LiteratureItemSchema(LiteratureItemInDB):
    pass
