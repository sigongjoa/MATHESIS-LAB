import uuid
from datetime import datetime, UTC

from sqlalchemy import Column, String, Text, DateTime, ForeignKey, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PG_UUID # Import as PG_UUID to avoid name collision

from backend.app.models.base import Base
from backend.app.models.zotero_item import ZoteroItem # Import ZoteroItem
from backend.app.models.youtube_video import YouTubeVideo # Import YouTubeVideo

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    curriculum_id = Column(String, ForeignKey("curriculums.curriculum_id"), nullable=False)
    parent_node_id = Column(String, ForeignKey("nodes.node_id"), nullable=True)

    # [REVISED] Explicit node type for queryability
    node_type = Column(String(50), nullable=False, default='CONTENT')

    title = Column(String(255), nullable=False)
    order_index = Column(Integer, nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # [REVISED] Soft deletion timestamp
    deleted_at = Column(DateTime, nullable=True)

    curriculum = relationship("Curriculum", back_populates="nodes")
    parent_node = relationship("Node", remote_side=[node_id], back_populates="child_nodes")
    child_nodes = relationship("Node", back_populates="parent_node", cascade="all, delete-orphan")
    content = relationship("NodeContent", back_populates="node", uselist=False, cascade="all, delete-orphan")
    links = relationship("NodeLink", back_populates="node", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Node(node_id='{self.node_id}', title='{self.title}', curriculum_id='{self.curriculum_id}')>"

class NodeContent(Base):
    __tablename__ = "node_contents"

    content_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("nodes.node_id"), unique=True, nullable=False)
    markdown_content = Column(Text, nullable=True)
    ai_generated_summary = Column(Text, nullable=True)
    ai_generated_extension = Column(Text, nullable=True)
    manim_guidelines = Column(Text, nullable=True) # New field for Manim guidelines
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC), nullable=False)

    # [REVISED] Soft deletion timestamp
    deleted_at = Column(DateTime, nullable=True)

    node = relationship("Node", back_populates="content")

    def __repr__(self):
        return f"<NodeContent(content_id='{self.content_id}', node_id='{self.node_id}')>"

class NodeLink(Base):
    __tablename__ = "node_links"

    link_id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_id = Column(String, ForeignKey("nodes.node_id"), nullable=False)
    zotero_item_id = Column(String, ForeignKey("zotero_items.zotero_item_id"), nullable=True)
    youtube_video_id = Column(String, ForeignKey("youtube_videos.youtube_video_id"), nullable=True)
    link_type = Column(String(10), nullable=False) # "ZOTERO" or "YOUTUBE"
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    # [REVISED] Soft deletion timestamp
    deleted_at = Column(DateTime, nullable=True)

    node = relationship("Node", back_populates="links")
    zotero_item = relationship("ZoteroItem") # Assuming ZoteroItem model exists
    youtube_video = relationship("YouTubeVideo") # Assuming YouTubeVideo model exists

    def __repr__(self):
        return f"<NodeLink(link_id='{self.link_id}', node_id='{self.node_id}', type='{self.link_type}')>"
