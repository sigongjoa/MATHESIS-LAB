import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Text, Integer, DateTime
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Import as PG_UUID to avoid name collision

from backend.app.models.base import Base

class ZoteroItem(Base):
    __tablename__ = "zotero_items"

    zotero_item_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    zotero_key = Column(String(255), unique=True, nullable=False)
    title = Column(String(512), nullable=False)
    authors = Column(Text, nullable=True)
    publication_year = Column(Integer, nullable=True)
    tags = Column(Text, nullable=True)
    item_type = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    def __repr__(self):
        return f"<ZoteroItem(zotero_item_id='{self.zotero_item_id}', title='{self.title}')>"
