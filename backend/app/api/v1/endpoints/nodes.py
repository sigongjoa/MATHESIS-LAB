from typing import List, Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File, Form, Query
from sqlalchemy.orm import Session

from backend.app.db.session import get_db
from backend.app.core.dependencies import get_current_user
from backend.app.schemas.node import (
    NodeCreate, NodeUpdate, NodeResponse, NodeReorder,
    NodeContentCreate, NodeContentUpdate, NodeContentResponse, NodeContentExtendRequest,
    NodeLinkZoteroCreate, NodeLinkYouTubeCreate, NodeLinkResponse,
    NodeLinkPDFCreate, NodeLinkNodeCreate
)
from backend.app.services.node_service import NodeService

router = APIRouter()

# Dependency to get NodeService
def get_node_service(db: Session = Depends(get_db)) -> NodeService:
    return NodeService(db)

# Node Endpoints
@router.post("/", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node(node_in: NodeCreate, curriculum_id: str = Query(...), node_service: NodeService = Depends(get_node_service)):
    """
    새로운 노드를 생성합니다.
    """
    db_node = node_service.create_node(node_in, curriculum_id=curriculum_id)
    if db_node is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Failed to create node")
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
    특정 노드를 삭제합니다。
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
    db_content = node_service.create_node_content(node_id, content_in)
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

@router.post("/{node_id}/content/summarize", response_model=NodeContentResponse)
def summarize_node_content(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    AI를 사용하여 특정 노드의 내용을 요약합니다.
    """
    try:
        updated_content = node_service.summarize_node_content(node_id)
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"AI summarization failed: {str(e)}")

    if updated_content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return updated_content

@router.post("/{node_id}/content/extend", response_model=NodeContentResponse)
def extend_node_content(node_id: UUID, extend_request: NodeContentExtendRequest, node_service: NodeService = Depends(get_node_service)):
    """
    AI를 사용하여 특정 노드의 내용을 확장합니다.
    """
    updated_content = node_service.extend_node_content(node_id, prompt=extend_request.prompt)
    if updated_content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return updated_content

@router.post("/{node_id}/content/manim-guidelines", response_model=NodeContentResponse)
async def generate_manim_guidelines(
    node_id: UUID,
    image_file: UploadFile = File(..., description="Manim 코드 가이드라인을 생성할 이미지 파일"),
    prompt: Optional[str] = Form(None, description="Manim 코드 가이드라인 생성을 위한 추가 지시사항"), # Changed to Form
    node_service: NodeService = Depends(get_node_service)
):
    """
    AI를 사용하여 이미지로부터 Manim 코드 가이드라인을 생성하고 노드 콘텐츠에 저장합니다.
    """
    image_bytes = await image_file.read()
    updated_content = await node_service.generate_manim_guidelines_from_image(
        node_id=node_id,
        image_bytes=image_bytes,
        prompt=prompt
    )
    if updated_content is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node content not found")
    return updated_content

# NodeLink Endpoints
@router.post("/{node_id}/links/zotero", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_zotero_node_link(
    node_id: UUID,
    link_in: NodeLinkZoteroCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    Zotero 문헌을 특정 노드에 연결합니다.
    """
    try:
        db_link = await node_service.create_zotero_link(node_id=node_id, zotero_key=link_in.zotero_key)
        if db_link is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except RuntimeError as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))

@router.post("/{node_id}/links/youtube", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
def create_youtube_node_link(
    node_id: UUID,
    link_in: NodeLinkYouTubeCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    YouTube 영상을 특정 노드에 연결합니다.
    """
    db_link = node_service.create_youtube_link(node_id=node_id, youtube_url=link_in.youtube_url)
    if db_link is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Invalid YouTube URL")
    return db_link

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
    # First, check if the node exists (optional, but good practice for clearer error messages)
    # This also ensures the link belongs to the specified node if we were to add that check in the service
    db_node = node_service.get_node(node_id)
    if not db_node:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node not found")

    if not node_service.delete_node_link(link_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Node link not found")
    return

# [NEW] PDF File Link Endpoints
@router.post("/{node_id}/links/pdf", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
async def create_pdf_node_link(
    node_id: str,
    file: UploadFile = File(..., description="PDF file to upload"),
    node_service: NodeService = Depends(get_node_service),
    current_user=Depends(get_current_user)
):
    """
    PDF 파일을 업로드하고 특정 노드에 연결합니다.
    [UPDATED] 이제 파일을 직접 업로드하여 Google Drive에 저장합니다.
    """
    # Read file content
    file_content = await file.read()
    file_size = len(file_content)
    
    # Create a file-like object from bytes
    from io import BytesIO
    file_obj = BytesIO(file_content)
    
    try:
        db_link = node_service.create_pdf_link(
            node_id=node_id,
            file_obj=file_obj,
            file_name=file.filename or "uploaded.pdf",
            file_size_bytes=file_size,
            file_mime_type=file.content_type,
            owner_user=current_user
        )
        return db_link
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Failed to upload PDF: {str(e)}")

@router.get("/{node_id}/links/pdf", response_model=List[NodeLinkResponse])
def read_pdf_node_links(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 연결된 모든 PDF 링크를 조회합니다.
    """
    db_links = node_service.get_pdf_links(node_id)
    return db_links

# [NEW] Node-to-Node Link Endpoints
@router.post("/{node_id}/links/node", response_model=NodeLinkResponse, status_code=status.HTTP_201_CREATED)
def create_node_to_node_link(
    node_id: str,
    link_in: NodeLinkNodeCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    다른 노드를 현재 노드에 연결합니다.
    """
    db_link = node_service.create_node_link(
        source_node_id=node_id,
        target_node_id=link_in.linked_node_id,
        link_relationship=link_in.link_relationship
    )
    return db_link

@router.get("/{node_id}/links/node", response_model=List[NodeLinkResponse])
def read_node_to_node_links(node_id: UUID, node_service: NodeService = Depends(get_node_service)):
    """
    특정 노드에 연결된 모든 Node-to-Node 링크를 조회합니다.
    """
    db_links = node_service.get_node_to_node_links(node_id)
    return db_links
