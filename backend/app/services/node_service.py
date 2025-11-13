from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload, joinedload
from sqlalchemy import func
import re

from backend.app.models.curriculum import Curriculum
from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.zotero_item import ZoteroItem
from backend.app.models.youtube_video import YouTubeVideo
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeContentCreate, NodeContentUpdate
from backend.app.core.ai import ai_client # Import the ai_client

def _extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extracts the YouTube video ID from a URL.
    Handles youtu.be, youtube.com/watch, and youtube.com/embed formats.
    """
    if url is None:
        return None
    
    patterns = [
        r"^(?:https?:\/\/)?(?:www\.)?youtu\.be\/([a-zA-Z0-9_-]{11})(?:[\?&].*)?$",
        r"^(?:https?:\/\/)?(?:www\.)?youtube\.com\/watch\?v=([a-zA-Z0-9_-]{11})(?:&.*)?$",
        r"^(?:https?:\/\/)?(?:www\.)?youtube\.com\/embed\/([a-zA-Z0-9_-]{11})(?:[\?&].*)?$",
    ]
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

class NodeService:
    def __init__(self, db: Session):
        self.db = db

    def create_node(self, node_in: NodeCreate, curriculum_id: UUID) -> Node:
        curriculum = self.db.query(Curriculum).filter(Curriculum.curriculum_id == curriculum_id).first()
        if not curriculum:
            raise ValueError(f"Curriculum with ID {curriculum_id} not found.")

        if node_in.parent_node_id:
            parent_node = self.db.query(Node).filter(Node.node_id == node_in.parent_node_id).first()
            if not parent_node:
                raise ValueError(f"Parent node with ID {node_in.parent_node_id} not found.")
            if parent_node.curriculum_id != curriculum_id:
                raise ValueError("Parent node does not belong to the specified curriculum.")
            max_order_index = self.db.query(func.max(Node.order_index)).filter(
                Node.curriculum_id == curriculum_id,
                Node.parent_node_id == node_in.parent_node_id
            ).scalar()
        else:
            max_order_index = self.db.query(func.max(Node.order_index)).filter(
                Node.curriculum_id == curriculum_id,
                Node.parent_node_id.is_(None)
            ).scalar()
        
        new_order_index = (max_order_index if max_order_index is not None else -1) + 1

        db_node = Node(
            curriculum_id=curriculum_id,
            parent_node_id=node_in.parent_node_id,
            title=node_in.title,
            order_index=new_order_index
        )
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def get_node(self, node_id: UUID) -> Optional[Node]:
        return self.db.query(Node)\
            .filter(Node.node_id == node_id)\
            .options(joinedload(Node.content), joinedload(Node.links))\
            .first()

    def get_nodes_by_curriculum(self, curriculum_id: UUID) -> List[Node]:
        return self.db.query(Node).filter(Node.curriculum_id == curriculum_id).order_by(Node.order_index).all()

    def update_node(self, node_id: UUID, node_in: NodeUpdate) -> Optional[Node]:
        db_node = self.get_node(node_id)
        if not db_node:
            return None
        update_data = node_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_node, key, value)
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def delete_node(self, node_id: UUID) -> bool:
        db_node = self.get_node(node_id)
        if not db_node:
            return False
        self.db.delete(db_node)
        self.db.commit()
        return True
    
    def create_node_content(self, content_in: NodeContentCreate) -> NodeContent:
        db_content = NodeContent(**content_in.model_dump())
        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)
        return db_content

    def get_node_content(self, node_id: UUID) -> Optional[NodeContent]:
        return self.db.query(NodeContent).filter(NodeContent.node_id == node_id).first()

    def update_node_content(self, node_id: UUID, content_in: NodeContentUpdate) -> Optional[NodeContent]:
        db_content = self.get_node_content(node_id)
        if not db_content:
            return None
        update_data = content_in.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_content, key, value)
        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)
        return db_content

    def delete_node_content(self, node_id: UUID) -> bool:
        db_content = self.get_node_content(node_id)
        if not db_content:
            return False
        self.db.delete(db_content)
        self.db.commit()
        return True

    def summarize_node_content(self, node_id: UUID) -> Optional[NodeContent]:
        db_content = self.get_node_content(node_id)
        if not db_content or not db_content.markdown_content:
            raise ValueError("Node content not found or is empty.")

        # Call the AI client for summarization
        try:
            summary = ai_client.generate_text(
                f"Summarize the following content concisely: {db_content.markdown_content}"
            )
            db_content.ai_generated_summary = summary
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except RuntimeError as e:
            raise ValueError(f"AI service error: {e}")


    def extend_node_content(self, node_id: UUID, prompt: Optional[str] = None) -> Optional[NodeContent]:
        db_content = self.get_node_content(node_id)
        if not db_content or not db_content.markdown_content:
            raise ValueError("Node content not found or is empty.")

        # Call the AI client for extension
        try:
            extension_prompt = f"Extend the following content with more details: {db_content.markdown_content}"
            if prompt:
                extension_prompt = f"{extension_prompt}\nSpecific instructions: {prompt}"

            extension = ai_client.generate_text(extension_prompt)
            db_content.ai_generated_extension = extension
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except RuntimeError as e:
            raise ValueError(f"AI service error: {e}")

    def create_zotero_link(self, node_id: UUID, zotero_item_id: UUID) -> NodeLink:
        if not self.get_node(node_id):
            raise ValueError("Node not found.")
        zotero_item = self.db.query(ZoteroItem).filter(ZoteroItem.zotero_item_id == zotero_item_id).first()
        if not zotero_item:
            raise ValueError("Zotero item not found.")
        db_link = NodeLink(node_id=node_id, link_type="ZOTERO", zotero_item_id=zotero_item_id)
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def create_youtube_link(self, node_id: UUID, youtube_url: str) -> NodeLink:
        if not self.get_node(node_id):
            raise ValueError("Node not found.")
        video_id = _extract_youtube_video_id(youtube_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL.")
        db_video = self.db.query(YouTubeVideo).filter(YouTubeVideo.video_id == video_id).first()
        if not db_video:
            db_video = YouTubeVideo(video_id=video_id, title="Placeholder Title", channel_title="Placeholder Channel")
            self.db.add(db_video)
            self.db.flush()
        db_link = NodeLink(node_id=node_id, link_type="YOUTUBE", youtube_video_id=db_video.youtube_video_id)
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def get_node_links(self, node_id: UUID) -> List[NodeLink]:
        return self.db.query(NodeLink).filter(NodeLink.node_id == node_id).all()

    def delete_node_link(self, link_id: UUID) -> bool:
        db_link = self.db.query(NodeLink).filter(NodeLink.link_id == link_id).first()
        if not db_link:
            return False
        self.db.delete(db_link)
        self.db.commit()
        return True

    def delete_node_link(self, link_id: UUID) -> bool:
        db_link = self.db.query(NodeLink).filter(NodeLink.link_id == link_id).first()
        if not db_link:
            return False
        self.db.delete(db_link)
        self.db.commit()
        return True
    
    def reorder_nodes(self, curriculum_id: UUID, node_id: UUID, new_parent_id: Optional[UUID], new_order_index: int) -> List[Node]:
        target_node = self.db.query(Node).filter(Node.node_id == node_id, Node.curriculum_id == curriculum_id).first()
        if not target_node:
            raise ValueError("Node not found in the specified curriculum.")
        if new_parent_id:
            ancestor = self.db.query(Node).filter(Node.node_id == new_parent_id).first()
            while ancestor:
                if ancestor.node_id == target_node.node_id:
                    raise ValueError("Cannot move a node to be a child of its own descendant.")
                ancestor = ancestor.parent_node if ancestor.parent_node_id else None
        old_parent_id = target_node.parent_node_id
        old_siblings = self.db.query(Node).filter(
            Node.curriculum_id == curriculum_id,
            Node.parent_node_id == old_parent_id,
            Node.node_id != node_id
        ).order_by(Node.order_index).all()
        if old_parent_id == new_parent_id:
            new_siblings = old_siblings
        else:
            new_siblings = self.db.query(Node).filter(
                Node.curriculum_id == curriculum_id,
                Node.parent_node_id == new_parent_id
            ).order_by(Node.order_index).all()
        if new_order_index < 0 or new_order_index > len(new_siblings):
            new_order_index = len(new_siblings)
        new_siblings.insert(new_order_index, target_node)
        target_node.parent_node_id = new_parent_id
        if old_parent_id != new_parent_id:
            for i, node in enumerate(old_siblings):
                node.order_index = i
        for i, node in enumerate(new_siblings):
            node.order_index = i
        self.db.commit()
        return self.get_nodes_by_curriculum(curriculum_id)

    async def generate_manim_guidelines_from_image(self, node_id: UUID, image_bytes: bytes, prompt: Optional[str] = None) -> Optional[NodeContent]:
        db_content = self.get_node_content(node_id)
        if not db_content:
            raise ValueError("Node content not found.")

        try:
            full_prompt = "Generate Manim code guidelines based on the provided image."
            if prompt:
                full_prompt = f"{full_prompt}\nAdditional instructions: {prompt}"

            guidelines = await ai_client.generate_manim_guidelines_from_image(image_bytes, full_prompt)
            
            db_content.manim_guidelines = guidelines
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except RuntimeError as e:
            raise ValueError(f"AI service error: {e}")