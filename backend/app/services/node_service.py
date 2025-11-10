from typing import List, Optional
from uuid import UUID
from sqlalchemy.orm import Session
from sqlalchemy import func

from backend.app.models.node import Node, NodeContent, NodeLink
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeContentCreate, NodeContentUpdate, NodeLinkCreate

class NodeService:
    def __init__(self, db: Session):
        self.db = db

    def create_node(self, node_in: NodeCreate) -> Node:
        # Determine order_index: if parent_node_id is provided, get max order_index for children of that parent
        # If no parent_node_id, get max order_index for root nodes in the curriculum
        if node_in.parent_node_id:
            max_order_index = self.db.query(func.max(Node.order_index)).filter(
                Node.curriculum_id == node_in.curriculum_id,
                Node.parent_node_id == node_in.parent_node_id
            ).scalar()
        else:
            max_order_index = self.db.query(func.max(Node.order_index)).filter(
                Node.curriculum_id == node_in.curriculum_id,
                Node.parent_node_id.is_(None)
            ).scalar()
        
        new_order_index = (max_order_index if max_order_index is not None else -1) + 1

        db_node = Node(
            curriculum_id=node_in.curriculum_id,
            parent_node_id=node_in.parent_node_id,
            title=node_in.title,
            order_index=new_order_index
        )
        self.db.add(db_node)
        self.db.commit()
        self.db.refresh(db_node)
        return db_node

    def get_node(self, node_id: UUID) -> Optional[Node]:
        return self.db.query(Node).filter(Node.node_id == node_id).first()

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

    def create_node_link(self, link_in: NodeLinkCreate) -> NodeLink:
        db_link = NodeLink(**link_in.model_dump())
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
    
    def reorder_nodes(self, curriculum_id: UUID, node_id: UUID, new_parent_id: Optional[UUID], new_order_index: int) -> List[Node]:
        """
        노드의 순서를 변경하고, 필요한 경우 부모 노드를 변경합니다.
        동일한 부모 내에서 순서 변경 시, 기존 노드들의 order_index를 조정합니다.
        다른 부모로 이동 시, 기존 부모의 노드들과 새 부모의 노드들을 모두 조정합니다.
        """
        target_node = self.get_node(node_id)
        if not target_node:
            raise ValueError("Target node not found.")

        old_parent_id = target_node.parent_node_id
        old_order_index = target_node.order_index

        # 1. 타겟 노드의 부모 및 순서 업데이트
        target_node.parent_node_id = new_parent_id
        target_node.order_index = new_order_index
        self.db.add(target_node)
        self.db.flush() # 변경사항을 DB에 반영하지만 커밋은 하지 않음

        # 2. 기존 부모 노드들의 순서 조정 (타겟 노드가 제거되었으므로)
        if old_parent_id == new_parent_id: # 동일한 부모 내에서 순서 변경
            # 타겟 노드가 이동한 위치에 따라 기존 노드들의 순서 조정
            if new_order_index < old_order_index: # 앞으로 이동
                self.db.query(Node).filter(
                    Node.curriculum_id == curriculum_id,
                    Node.parent_node_id == old_parent_id,
                    Node.node_id != node_id,
                    Node.order_index >= new_order_index,
                    Node.order_index < old_order_index
                ).update({Node.order_index: Node.order_index + 1}, synchronize_session=False)
            else: # 뒤로 이동
                self.db.query(Node).filter(
                    Node.curriculum_id == curriculum_id,
                    Node.parent_node_id == old_parent_id,
                    Node.node_id != node_id,
                    Node.order_index > old_order_index,
                    Node.order_index <= new_order_index
                ).update({Node.order_index: Node.order_index - 1}, synchronize_session=False)
        else: # 다른 부모로 이동
            # 기존 부모의 노드들 순서 조정
            self.db.query(Node).filter(
                Node.curriculum_id == curriculum_id,
                Node.parent_node_id == old_parent_id,
                Node.node_id != node_id,
                Node.order_index > old_order_index
            ).update({Node.order_index: Node.order_index - 1}, synchronize_session=False)

            # 새 부모의 노드들 순서 조정 (타겟 노드가 삽입되었으므로)
            self.db.query(Node).filter(
                Node.curriculum_id == curriculum_id,
                Node.parent_node_id == new_parent_id,
                Node.node_id != node_id,
                Node.order_index >= new_order_index
            ).update({Node.order_index: Node.order_index + 1}, synchronize_session=False)
        
        self.db.commit()
        self.db.refresh(target_node)
        return self.get_nodes_by_curriculum(curriculum_id)
