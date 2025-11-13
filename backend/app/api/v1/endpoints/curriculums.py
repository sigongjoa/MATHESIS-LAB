from typing import Annotated, List
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.schemas.curriculum import CurriculumCreate, CurriculumResponse, CurriculumUpdate
from backend.app.schemas.node import NodeCreate, NodeResponse
from backend.app.services.curriculum_service import CurriculumService
from backend.app.services.node_service import NodeService
from backend.app.db.session import get_db

router = APIRouter()

# Dependency to get CurriculumService
def get_curriculum_service(db: Session = Depends(get_db)) -> CurriculumService:
    return CurriculumService(db)

# Dependency to get NodeService
def get_node_service(db: Session = Depends(get_db)) -> NodeService:
    return NodeService(db)

@router.get("/", response_model=list[CurriculumResponse])
def read_all_curriculums(
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    모든 커리큘럼 맵의 목록을 조회합니다.
    """
    return curriculum_service.get_all_curriculums()

@router.post("/", response_model=CurriculumResponse, status_code=status.HTTP_201_CREATED)
def create_curriculum(
    curriculum_in: CurriculumCreate,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    새로운 커리큘럼 맵을 생성합니다.
    """
    db_curriculum = curriculum_service.create_curriculum(curriculum_in)
    return db_curriculum

@router.get("/public", response_model=List[CurriculumResponse])
def read_public_curriculums(
    skip: int = 0,
    limit: int = 100,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    공개된 모든 커리큘럼 맵 목록을 조회합니다.
    """
    public_curriculums = curriculum_service.get_public_curriculums(skip=skip, limit=limit)
    return public_curriculums

@router.get("/{curriculum_id}", response_model=CurriculumResponse)
def read_curriculum(
    curriculum_id: UUID,
    curriculum_service: CurriculumService = Depends(get_curriculum_service),
    node_service: NodeService = Depends(get_node_service)
):
    """
    특정 커리큘럼 맵의 상세 정보를 노드와 함께 조회합니다.
    """
    db_curriculum = curriculum_service.get_curriculum(curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    
    # Fetch and attach nodes
    nodes = node_service.get_nodes_by_curriculum(curriculum_id)
    db_curriculum.nodes = nodes
    
    return db_curriculum

@router.put("/{curriculum_id}", response_model=CurriculumResponse)
def update_curriculum(
    curriculum_id: UUID,
    curriculum_in: CurriculumUpdate,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    특정 커리큘럼 맵의 정보를 업데이트합니다.
    """
    db_curriculum = curriculum_service.update_curriculum(curriculum_id, curriculum_in)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return db_curriculum

@router.delete("/{curriculum_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_curriculum(
    curriculum_id: UUID,
    curriculum_service: CurriculumService = Depends(get_curriculum_service)
):
    """
    특정 커리큘럼 맵을 삭제합니다.
    """
    db_curriculum = curriculum_service.delete_curriculum(curriculum_id)
    if db_curriculum is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Curriculum not found")
    return

@router.post("/{curriculum_id}/nodes", response_model=NodeResponse, status_code=status.HTTP_201_CREATED)
def create_node_for_curriculum(
    curriculum_id: UUID,
    node_in: NodeCreate,
    node_service: NodeService = Depends(get_node_service)
):
    """
    특정 커리큘럼에 새로운 노드를 생성합니다.
    """
    try:
        db_node = node_service.create_node(node_in, curriculum_id)
        return db_node
    except ValueError as e:
        if "Curriculum with ID" in str(e) or "Parent node with ID" in str(e):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
        elif "Parent node does not belong to the specified curriculum" in str(e):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
        else:
            raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=str(e))