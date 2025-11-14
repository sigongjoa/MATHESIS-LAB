import uuid
from sqlalchemy import Column, String, Text, INT, TIMESTAMP
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
from backend.app.models.base import Base

class LiteratureItem(Base):
    __tablename__ = "literature_items"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    title = Column(String(512), nullable=False)
    authors = Column(Text, nullable=True)
    publication_year = Column(INT, nullable=True)
    tags = Column(Text, nullable=True)
    item_type = Column(String(50), nullable=True)
    abstract = Column(Text, nullable=True)
    url = Column(Text, nullable=True)
    created_at = Column(TIMESTAMP, server_default=func.now(), nullable=False)
    updated_at = Column(TIMESTAMP, server_default=func.now(), onupdate=func.now(), nullable=False)
