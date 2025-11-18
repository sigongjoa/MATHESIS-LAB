from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func, and_
from datetime import datetime, UTC
import re

from backend.app.models.curriculum import Curriculum
from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.models.zotero_item import ZoteroItem
from backend.app.models.youtube_video import YouTubeVideo
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeContentCreate, NodeContentUpdate
from backend.app.core.ai import ai_client # Import the ai_client
from backend.app.services.zotero_service import zotero_service # Import zotero_service

def _extract_youtube_video_id(url: str) -> Optional[str]:
    """
    Extracts the YouTube video ID from a URL.

    Handles multiple YouTube URL formats:
    - youtu.be/VIDEO_ID
    - youtube.com/watch?v=VIDEO_ID
    - youtube.com/embed/VIDEO_ID
    - m.youtube.com/watch?v=VIDEO_ID
    - youtube.com/watch?v=VIDEO_ID&t=... (with timestamps)

    Args:
        url: YouTube URL to extract ID from

    Returns:
        11-character video ID if found, None otherwise

    Raises:
        ValueError: If URL is invalid or empty
    """
    if url is None:
        return None

    if not isinstance(url, str):
        return None

    url = url.strip()
    if not url:
        return None

    # YouTube video ID is always 11 characters (alphanumeric + dash + underscore)
    video_id_pattern = r"([a-zA-Z0-9_-]{11})"

    # Multiple URL patterns to handle different YouTube URL formats
    # Use word boundaries to ensure we match "youtube.com", not "notyoutube.com"
    patterns = [
        # youtu.be/VIDEO_ID or youtu.be/VIDEO_ID?t=...
        r"(?://|^)youtu\.be/" + video_id_pattern,
        # youtube.com/watch?v=VIDEO_ID (with or without additional params)
        r"(?://|^)(?:www\.)?youtube\.com/watch\?v=" + video_id_pattern,
        # youtube.com/embed/VIDEO_ID
        r"(?://|^)(?:www\.)?youtube\.com/embed/" + video_id_pattern,
        # m.youtube.com/watch?v=VIDEO_ID (mobile)
        r"(?://|^)m\.youtube\.com/watch\?v=" + video_id_pattern,
        # youtube-nocookie.com/embed/VIDEO_ID
        r"(?://|^)youtube-nocookie\.com/embed/" + video_id_pattern,
    ]

    for pattern in patterns:
        match = re.search(pattern, url, re.IGNORECASE)
        if match:
            video_id = match.group(1)
            if len(video_id) == 11:
                return video_id

    # If no pattern matched, return None (not found, not an error)
    return None

class NodeService:
    def __init__(self, db: Session):
        self.db = db

    def create_node(self, node_in: NodeCreate, curriculum_id: UUID) -> Node:
        """
        Create node with transaction-level lock to prevent race conditions.

        [REVISED] Implements transaction lock (SELECT ... FOR UPDATE) to ensure
        atomic calculation of order_index.
        """
        str_curriculum_id = str(curriculum_id)
        str_parent_node_id = str(node_in.parent_node_id) if node_in.parent_node_id else None

        try:
            # 1. Validate curriculum exists
            curriculum = self.db.query(Curriculum).filter(
                Curriculum.curriculum_id == str_curriculum_id
            ).first()
            if not curriculum:
                raise ValueError(f"Curriculum with ID {curriculum_id} not found.")

            # 2. Parent validation with lock [REVISED]
            if str_parent_node_id:
                parent_node = self.db.query(Node).filter(
                    and_(
                        Node.node_id == str_parent_node_id,
                        Node.deleted_at.is_(None)  # [REVISED] Active nodes only
                    )
                ).with_for_update().first()  # [REVISED] Transaction lock

                if not parent_node:
                    raise ValueError(f"Parent node with ID {node_in.parent_node_id} not found or deleted.")
                if parent_node.curriculum_id != str_curriculum_id:
                    raise ValueError("Parent node does not belong to the specified curriculum.")

            # 3. Calculate order_index atomically (lock ensures atomic execution)
            last_sibling = self.db.query(Node).filter(
                and_(
                    Node.parent_node_id == str_parent_node_id,
                    Node.curriculum_id == str_curriculum_id,
                    Node.deleted_at.is_(None)  # [REVISED] Active nodes only
                )
            ).order_by(Node.order_index.desc()).first()

            new_order_index = (last_sibling.order_index + 1) if last_sibling else 0

            # 4. Create node with explicit node_type [REVISED]
            db_node = Node(
                title=node_in.title,
                parent_node_id=str_parent_node_id,
                node_type=node_in.node_type or 'CONTENT',  # [REVISED] Explicit type
                curriculum_id=str_curriculum_id,
                order_index=new_order_index,
                deleted_at=None  # [REVISED]
            )
            self.db.add(db_node)
            self.db.commit()
            self.db.refresh(db_node)
            return db_node

        except Exception as e:
            self.db.rollback()
            raise e

    def get_node(self, node_id: UUID) -> Optional[Node]:
        """Get active node by ID [REVISED] with soft deletion filter"""
        return self.db.query(Node).filter(
            and_(
                Node.node_id == str(node_id),
                Node.deleted_at.is_(None)  # [REVISED] Active nodes only
            )
        ).first()

    def get_nodes_by_curriculum(self, curriculum_id: UUID) -> List[Node]:
        """Get active nodes by curriculum [REVISED] with soft deletion filter"""
        return self.db.query(Node).filter(
            and_(
                Node.curriculum_id == str(curriculum_id),
                Node.deleted_at.is_(None)  # [REVISED] Active nodes only
            )
        ).order_by(Node.order_index).all()

    def get_nodes_by_type(self, curriculum_id: UUID, node_type: str) -> List[Node]:
        """[REVISED] Query nodes by explicit type"""
        return self.db.query(Node).filter(
            and_(
                Node.curriculum_id == str(curriculum_id),
                Node.node_type == node_type,
                Node.deleted_at.is_(None)  # [REVISED] Active nodes only
            )
        ).all()

    # ... (other methods)

    async def create_zotero_link(self, node_id: UUID, zotero_key: str) -> NodeLink:
        str_node_id = str(node_id)
        if not self.get_node(str_node_id): # Pass string to get_node
            raise ValueError("Node not found.")

        # Check if Zotero item already exists in our database
        db_zotero_item = self.db.query(ZoteroItem).filter(ZoteroItem.zotero_key == zotero_key).first()

        if not db_zotero_item:
            # If not, fetch details from external Zotero API
            try:
                zotero_data = await zotero_service.get_item_by_key(zotero_key)
            except (ValueError, RuntimeError) as e:
                raise ValueError(f"Failed to fetch Zotero item details: {e}")

            # Create new ZoteroItem in our database
            db_zotero_item = ZoteroItem(
                zotero_key=zotero_data.get("zotero_key"),
                title=zotero_data.get("title", "No Title"),
                authors=", ".join(zotero_data.get("authors", [])),
                publication_year=zotero_data.get("publication_year"),
                tags=", ".join(zotero_data.get("tags", [])),
                item_type=zotero_data.get("item_type"),
                abstract=zotero_data.get("abstract"),
                url=zotero_data.get("url"),
            )
            self.db.add(db_zotero_item)
            self.db.flush() # Use flush to get zotero_item_id before commit

        # Create NodeLink
        db_link = NodeLink(node_id=str_node_id, link_type="ZOTERO", zotero_item_id=str(db_zotero_item.zotero_item_id))
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def create_node_content(self, node_id: UUID, content_in: NodeContentCreate) -> NodeContent:
        content_data = content_in.model_dump()
        content_data.pop("node_id", None) # Remove node_id if present, as it's passed separately
        db_content = NodeContent(**content_data, node_id=str(node_id))
        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)
        return db_content

    def get_node_content(self, node_id: UUID) -> Optional[NodeContent]:
        return self.db.query(NodeContent).filter(NodeContent.node_id == str(node_id)).first()

    def update_node_content(self, node_id: UUID, content_update: NodeContentUpdate) -> NodeContent:
        """
        Update node content with provided data.

        Args:
            node_id: UUID of the node
            content_update: Updated content data

        Returns:
            Updated NodeContent object

        Raises:
            ValueError: If node content not found
        """
        db_content = self.get_node_content(str(node_id))
        if not db_content:
            raise ValueError(f"Node content not found for node_id: {node_id}")

        update_data = content_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_content, key, value)
        self.db.add(db_content)
        self.db.commit()
        self.db.refresh(db_content)
        return db_content

    def delete_node_content(self, node_id: UUID) -> bool:
        """
        Delete node content.

        Args:
            node_id: UUID of the node

        Returns:
            True if content was deleted, raises ValueError if not found

        Raises:
            ValueError: If node content not found
        """
        db_content = self.get_node_content(str(node_id))
        if not db_content:
            raise ValueError(f"Node content not found for node_id: {node_id}")

        self.db.delete(db_content)
        self.db.commit()
        return True

    def update_node(self, node_id: UUID, node_update: NodeUpdate) -> Node:
        """
        Update node with provided data.

        Args:
            node_id: UUID of the node
            node_update: Updated node data

        Returns:
            Updated Node object

        Raises:
            ValueError: If node not found
        """
        db_node = self.get_node(str(node_id))
        if not db_node:
            raise ValueError(f"Node not found: {node_id}")

        update_data = node_update.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            setattr(db_node, key, value)
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def delete_node(self, node_id: UUID) -> bool:
        """
        [REVISED] Soft-delete node and all descendants.
        Sets deleted_at timestamp instead of hard delete.
        """
        db_node = self.get_node(str(node_id))
        if not db_node:
            return False

        try:
            # 1. Get all descendant IDs recursively
            def get_descendant_ids(nid: str, visited=None) -> set:
                if visited is None:
                    visited = set()
                if nid in visited:
                    return set()
                visited.add(nid)

                children = self.db.query(Node.node_id).filter(
                    and_(
                        Node.parent_node_id == nid,
                        Node.deleted_at.is_(None)
                    )
                ).all()

                result = {nid}
                for (child_id,) in children:
                    result.update(get_descendant_ids(child_id, visited))

                return result

            descendant_ids = get_descendant_ids(str(node_id))

            # 2. Soft-delete all nodes
            now = datetime.now(UTC)
            self.db.query(Node).filter(
                Node.node_id.in_(descendant_ids)
            ).update({Node.deleted_at: now})

            # 3. Soft-delete contents
            self.db.query(NodeContent).filter(
                NodeContent.node_id.in_(descendant_ids)
            ).update({NodeContent.deleted_at: now})

            # 4. Soft-delete links
            self.db.query(NodeLink).filter(
                NodeLink.node_id.in_(descendant_ids)
            ).update({NodeLink.deleted_at: now})

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise e

    def restore_node(self, node_id: UUID) -> Optional[Node]:
        """[REVISED] Restore soft-deleted node"""
        node = self.db.query(Node).filter(
            Node.node_id == str(node_id)
        ).first()

        if not node or node.deleted_at is None:
            raise ValueError(f"Node {node_id} not found or not deleted")

        node.deleted_at = None
        self.db.commit()
        return node

    def get_deleted_nodes(self, curriculum_id: UUID) -> List[Node]:
        """[REVISED] Get deleted nodes for trash/recovery"""
        return self.db.query(Node).filter(
            and_(
                Node.curriculum_id == str(curriculum_id),
                Node.deleted_at.is_not(None)
            )
        ).order_by(Node.deleted_at.desc()).all()

    def summarize_node_content(self, node_id: UUID) -> Optional[NodeContent]:
        db_content = self.get_node_content(str(node_id)) # Pass string to get_node_content
        if not db_content or not db_content.markdown_content:
            raise ValueError("Node content not found or is empty.")

        try:
            summary = ai_client.generate_text(f"Summarize the following content: {db_content.markdown_content}")
            db_content.ai_generated_summary = summary
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except Exception as e:
            raise ValueError(f"AI summarization failed: {e}")

    def extend_node_content(self, node_id: UUID, prompt: Optional[str] = None) -> Optional[NodeContent]:
        db_content = self.get_node_content(str(node_id)) # Pass string to get_node_content
        if not db_content or not db_content.markdown_content:
            raise ValueError("Node content not found or is empty.")

        full_prompt = f"Extend the following content: {db_content.markdown_content}"
        if prompt:
            full_prompt += f"\nAdditional instructions: {prompt}"

        try:
            extension = ai_client.generate_text(full_prompt)
            db_content.ai_generated_extension = extension
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except Exception as e:
            raise ValueError(f"AI extension failed: {e}")

    async def generate_manim_guidelines_from_image(self, node_id: UUID, image_bytes: bytes, prompt: Optional[str] = None) -> Optional[NodeContent]:
        db_content = self.get_node_content(str(node_id)) # Pass string to get_node_content
        if not db_content:
            raise ValueError("Node content not found.")

        try:
            guidelines = await ai_client.generate_manim_code_from_image(image_bytes, prompt)
            db_content.manim_guidelines = guidelines
            self.db.add(db_content)
            self.db.commit()
            self.db.refresh(db_content)
            return db_content
        except Exception as e:
            raise ValueError(f"AI Manim guideline generation failed: {e}")

    def create_youtube_link(self, node_id: UUID, youtube_url: str) -> NodeLink:
        str_node_id = str(node_id)
        if not self.get_node(str_node_id): # Pass string to get_node
            raise ValueError("Node not found.")

        video_id = _extract_youtube_video_id(youtube_url)
        if not video_id:
            raise ValueError("Invalid YouTube URL provided.")

        # In a real application, you might fetch YouTube video details here
        # For now, we'll just store the video_id
        db_youtube_video = YouTubeVideo(video_id=video_id, title=f"YouTube Video {video_id}")
        self.db.add(db_youtube_video)
        self.db.flush() # Use flush to get youtube_video_id before commit

        db_link = NodeLink(node_id=str_node_id, link_type="YOUTUBE", youtube_video_id=str(db_youtube_video.youtube_video_id))
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def get_node_links(self, node_id: UUID) -> List[NodeLink]:
        return self.db.query(NodeLink).filter(NodeLink.node_id == str(node_id)).all()

    def delete_node_link(self, link_id: UUID) -> bool:
        db_link = self.db.query(NodeLink).filter(NodeLink.link_id == str(link_id)).first()
        if not db_link:
            return False
        self.db.delete(db_link)
        self.db.commit()
        return True

    # [NEW] PDF File Link Methods
    def create_pdf_link(self, node_id: UUID, drive_file_id: str, file_name: str,
                       file_size_bytes: Optional[int] = None,
                       file_mime_type: Optional[str] = None) -> NodeLink:
        """
        Create a link to a PDF file in Google Drive.

        Args:
            node_id: UUID of the node
            drive_file_id: Google Drive file ID
            file_name: Original file name
            file_size_bytes: File size in bytes
            file_mime_type: MIME type (e.g., application/pdf)

        Returns:
            Created NodeLink object

        Raises:
            ValueError: If node not found
        """
        str_node_id = str(node_id)
        if not self.get_node(str_node_id):
            raise ValueError(f"Node not found: {node_id}")

        db_link = NodeLink(
            node_id=str_node_id,
            link_type="DRIVE_PDF",
            drive_file_id=drive_file_id,
            file_name=file_name,
            file_size_bytes=file_size_bytes,
            file_mime_type=file_mime_type or "application/pdf"
        )
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    # [NEW] Node-to-Node Link Methods
    def create_node_link(self, source_node_id: UUID, target_node_id: UUID,
                        link_relationship: str = "REFERENCE") -> NodeLink:
        """
        Create a link between two nodes.

        Args:
            source_node_id: UUID of the source node
            target_node_id: UUID of the target (linked) node
            link_relationship: Type of relationship (SOURCE, REFERENCE, EXTENDS, DEPENDS_ON, RELATED)

        Returns:
            Created NodeLink object

        Raises:
            ValueError: If nodes not found or if trying to link a node to itself
        """
        str_source_id = str(source_node_id)
        str_target_id = str(target_node_id)

        # Validate nodes exist
        if not self.get_node(str_source_id):
            raise ValueError(f"Source node not found: {source_node_id}")
        if not self.get_node(str_target_id):
            raise ValueError(f"Target node not found: {target_node_id}")

        # Prevent self-linking
        if str_source_id == str_target_id:
            raise ValueError("Cannot link a node to itself")

        db_link = NodeLink(
            node_id=str_source_id,
            link_type="NODE",
            linked_node_id=str_target_id,
            link_relationship=link_relationship
        )
        self.db.add(db_link)
        self.db.commit()
        self.db.refresh(db_link)
        return db_link

    def get_node_to_node_links(self, node_id: UUID) -> List[NodeLink]:
        """
        Get all node-to-node links for a given node.

        Args:
            node_id: UUID of the node

        Returns:
            List of NODE-type NodeLink objects
        """
        return self.db.query(NodeLink).filter(
            NodeLink.node_id == str(node_id),
            NodeLink.link_type == "NODE"
        ).all()

    def get_pdf_links(self, node_id: UUID) -> List[NodeLink]:
        """
        Get all PDF file links for a given node.

        Args:
            node_id: UUID of the node

        Returns:
            List of DRIVE_PDF-type NodeLink objects
        """
        return self.db.query(NodeLink).filter(
            NodeLink.node_id == str(node_id),
            NodeLink.link_type == "DRIVE_PDF"
        ).all()

    def reorder_nodes(self, curriculum_id: UUID, node_id: UUID, new_parent_id: Optional[UUID], new_order_index: int) -> List[Node]:
        str_curriculum_id = str(curriculum_id)
        str_node_id = str(node_id)
        str_new_parent_id = str(new_parent_id) if new_parent_id else None

        node_to_reorder = self.db.query(Node).filter(Node.node_id == str_node_id, Node.curriculum_id == str_curriculum_id).first()
        if not node_to_reorder:
            raise ValueError("Node not found in the specified curriculum.")

        # Prevent circular dependency: a node cannot be its own parent or a descendant of itself
        if str_new_parent_id == str_node_id:
            raise ValueError("A node cannot be its own parent.")
        
        # Check for circular dependency if new_parent_id is a descendant of node_to_reorder
        if str_new_parent_id:
            current_node = self.db.query(Node).filter(Node.node_id == str_new_parent_id).first()
            while current_node:
                if current_node.parent_node_id == str_node_id:
                    raise ValueError("Circular dependency detected: cannot move a node to be a child of its own descendant.")
                current_node = self.db.query(Node).filter(Node.node_id == current_node.parent_node_id).first()

        old_parent_id = node_to_reorder.parent_node_id
        old_order_index = node_to_reorder.order_index

        affected_nodes = []

        # Case 1: Parent is changing or staying the same but order is changing within the same parent
        if old_parent_id != str_new_parent_id:
            # Remove from old parent's list: decrement order_index for nodes after the old position
            if old_parent_id is None:
                # Top-level nodes
                self.db.query(Node).filter(
                    Node.curriculum_id == str_curriculum_id,
                    Node.parent_node_id.is_(None),
                    Node.order_index > old_order_index
                ).update({Node.order_index: Node.order_index - 1})
            else:
                # Children of a specific parent
                self.db.query(Node).filter(
                    Node.curriculum_id == str_curriculum_id,
                    Node.parent_node_id == old_parent_id,
                    Node.order_index > old_order_index
                ).update({Node.order_index: Node.order_index - 1})
            self.db.commit() # Commit changes to old list before calculating new list's max index

            node_to_reorder.parent_node_id = str_new_parent_id
            node_to_reorder.order_index = -1 # Temporarily set to -1 to exclude from next count

        # Get the list of siblings for the new parent
        if str_new_parent_id is None:
            # Top-level nodes
            siblings = self.db.query(Node).filter(
                Node.curriculum_id == str_curriculum_id,
                Node.parent_node_id.is_(None),
                Node.node_id != str_node_id # Exclude the node being reordered
            ).order_by(Node.order_index).all()
        else:
            # Children of a specific parent
            siblings = self.db.query(Node).filter(
                Node.curriculum_id == str_curriculum_id,
                Node.parent_node_id == str_new_parent_id,
                Node.node_id != str_node_id # Exclude the node being reordered
            ).order_by(Node.order_index).all()

        # Ensure new_order_index is within bounds
        if new_order_index < 0:
            new_order_index = 0
        if new_order_index > len(siblings):
            new_order_index = len(siblings)

        # Re-index siblings and insert the reordered node
        new_siblings_list = []
        inserted = False
        for i, sibling in enumerate(siblings):
            if i == new_order_index and not inserted:
                node_to_reorder.order_index = i
                new_siblings_list.append(node_to_reorder)
                affected_nodes.append(node_to_reorder)
                inserted = True
            sibling.order_index = len(new_siblings_list)
            new_siblings_list.append(sibling)
            affected_nodes.append(sibling)
        
        if not inserted: # If new_order_index was at the end
            node_to_reorder.order_index = len(new_siblings_list)
            new_siblings_list.append(node_to_reorder)
            affected_nodes.append(node_to_reorder)

        self.db.add_all(affected_nodes)
        self.db.commit()

        # Refresh all affected nodes to get their latest state
        for node in affected_nodes:
            self.db.refresh(node)

        return new_siblings_list