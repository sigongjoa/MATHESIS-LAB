from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.node import NodeCreate, NodeUpdate, NodeResponse, NodeContentCreate, NodeContentUpdate, NodeContentResponse, NodeLinkCreate, NodeLinkResponse
from backend.app.services.node_service import NodeService

router = APIRouter()

# Dependency to get NodeService
def get_node_service(db: Session = Depends(get_db)) -> NodeService:
    return NodeService(db)

# Node Endpoints
@router.post("/", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(node_in: NodeCreate, node_service: NodeService = Depends(get_node_service)):
    """
    새로운 노드를 생성합니다.
    """
    db_node = node_service.create_node(node_in)
    return db_node

@router.get("/{node_id}", response_model=NodeResponse)
def read_node(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드 정보를 조회합니다.
    """
    db_node = node_service.get_node(node_id)
    if db_node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return db_node

@router.get("/curriculum/{curriculum_id}", response_model=List[NodeResponse])
def read_nodes_by_curriculum(curriculum_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 커리큘럼에 속한 모든 노드를 조회합니다.
    """
    db_nodes = node_service.get_nodes_by_curriculum(curriculum_id)
    return db_nodes

@router.put("/{node_id}", response_model=NodeResponse)
def update_node(node_id: UUID, node_in: NodeUpdate, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드 정보를 업데이트합니다.
    """
    db_node = node_service.update_node(node_id, node_in)
    if db_node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return db_node

@router.delete("/{node_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드를 삭제합니다.
    """
    if not node_service.delete_node(node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return

@router.put("/reorder/{curriculum_id}", response_model=List[NodeResponse])
def reorder_nodes(
    curriculum_id: UUID,
    node_id: UUID,
    new_parent_id: Optional[UUID],
    new_order_index: int,
    node_service: NodeService = Depends(get_node_service)
):
    """
    커리큘럼 내 노드의 순서를 변경하거나 부모 노드를 변경합니다.
    """
    try:
        updated_nodes = node_service.reorder_nodes(curriculum_id, node_id, new_parent_id, new_order_index)
        return updated_nodes
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# NodeContent Endpoints
@router.post("/{node_id}/content", response_model=NodeContentResponse, status_code=status.HTTP_201_CREATED)
def create_node_content(node_id: UUID, content_in: NodeContentCreate, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 내용을 생성합니다.
    """
    # Ensure the node exists
    if not node_service.get_node(node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    # Ensure content doesn't already exist for this node
    if node_service.get_node_content(node_id):
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Node content already exists for this node")

    db_content = node_service.create_node_content(content_in)
    return db_content

@router.get("/{node_id}/content", response_model=NodeContentResponse)
def read_node_content(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 내용을 조회합니다.
    """
    db_content = node_service.get_node_content(node_id)
    if db_content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return db_content

@router.put("/{node_id}/content", response_model=NodeContentResponse)
def update_node_content(node_id: UUID, content_in: NodeContentUpdate, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 내용을 업데이트합니다.
    """
    db_content = node_service.update_node_content(node_id, content_in)
    if db_content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return db_content

@router.delete("/{node_id}/content", status_code=status.HTTP_204_NO_CONTENT)
def delete_node_content(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 내용을 삭제합니다.
    """
    if not node_service.delete_node_content(node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return

# NodeLink Endpoints
@router.post("/{node_id}/link", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
def create_node_link(node_id: UUID, link_in: NodeLinkCreate, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 링크를 생성합니다.
    """
    # Ensure the node exists
    if not node_service.get_node(node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    
    # Validate link_type and corresponding ID
    if link_in.link_type == "ZOTERO" and not link_in.zotero_item_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="zotero_item_id is required for ZOTERO link_type")
    if link_in.link_type == "YOUTUBE" and not link_in.youtube_video_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="youtube_video_id is required for YOUTUBE link_type")
    if link_in.link_type not in ["ZOTERO", "YOUTUBE"]:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid link_type. Must be ZOTERO or YOUTUBE.")

    db_link = node_service.create_node_link(link_in)
    return db_link

@router.get("/{node_id}/links", response_model=List[NodeLinkResponse])
def read_node_links(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 연결된 모든 링크를 조회합니다.
    """
    db_links = node_service.get_node_links(node_id)
    return db_links

@router.delete("/link/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node_link(link_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드 링크를 삭제합니다.
    """
    if not node_service.delete_node_link(link_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node link not found")
    return