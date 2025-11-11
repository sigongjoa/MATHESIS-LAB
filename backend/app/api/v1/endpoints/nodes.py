from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.schemas.node import (
    NodeCreate, NodeUpdate, NodeResponse, NodeReorder,
    NodeContentCreate, NodeContentUpdate, NodeContentResponse,
    NodeLinkZoteroCreate, NodeLinkYouTubeCreate, NodeLinkResponse
)
from backend.app.services.node_service import NodeService

router = APIRouter()

# Dependency to get NodeService
def get_node_service(db: Session = Depends(get_db)) -> NodeService:
    return NodeService(db)

# Node Endpoints
@router.get("/{node_id}", response_model=NodeResponse)
def read_node(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드 정보를 조회합니다.
    """
    db_node = node_service.get_node(node_id)
    if db_node is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
    return db_node

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
    reorder_in: NodeReorder,
    node_service: NodeService = Depends(get_node_service)
):
    """
    커리큘럼 내 노드의 순서를 변경하거나 부모 노드를 변경합니다.
    """
    try:
        updated_nodes = node_service.reorder_nodes(
            curriculum_id=curriculum_id,
            node_id=reorder_in.node_id,
            new_parent_id=reorder_in.new_parent_id,
            new_order_index=reorder_in.new_order_index
        )
        return updated_nodes
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))

# NodeContent Endpoints
@router.post("/{node_id}/content", response_model=NodeContentResponse, status_code=status.HTTP_201_CREATED)
def create_node_content(node_id: UUID, content_in: NodeContentCreate, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 대한 내용을 생성합니다.
    """
    if not node_service.get_node(node_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
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
@router.post("/{node_id}/links/zotero", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
def create_zotero_node_link(
    node_id: UUID,
    link_in: NodeLinkZoteroCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    Zotero 문헌을 특정 노드에 연결합니다.
    """
    try:
        db_link = node_service.create_zotero_link(node_id=node_id, zotero_item_id=link_in.zotero_item_id)
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))

@router.post("/{node_id}/links/youtube", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
def create_youtube_node_link(
    node_id: UUID,
    link_in: NodeLinkYouTubeCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    YouTube 영상을 특정 노드에 연결합니다.
    """
    try:
        db_link = node_service.create_youtube_link(node_id=node_id, youtube_url=link_in.youtube_url)
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"An external error occurred: {e}")

@router.get("/{node_id}/links", response_model=List[NodeLinkResponse])
def read_node_links(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 연결된 모든 링크를 조회합니다.
    """
    db_links = node_service.get_node_links(node_id)
    return db_links

@router.delete("/{node_id}/links/{link_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_node_link(node_id: UUID, link_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드 링크를 삭제합니다.
    """
    if not node_service.delete_node_link(link_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node link not found")
    return
