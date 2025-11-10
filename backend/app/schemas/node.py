from typing import Optional, List
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict

# Node Schemas
class NodeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="노드 제목")
    parent_node_id: Optional[UUID] = Field(None, description="부모 노드 ID (최상위 노드는 NULL)")
    order_index: int = Field(..., ge=0, description="커리큘럼 맵 내 노드 순서")

class NodeCreate(NodeBase):
    curriculum_id: UUID = Field(..., description="노드가 속한 커리큘럼 맵 ID")

class NodeUpdate(NodeBase):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="노드 제목")
    parent_node_id: Optional[UUID] = Field(None, description="부모 노드 ID (최상위 노드는 NULL)")
    order_index: Optional[int] = Field(None, ge=0, description="커리큘럼 맵 내 노드 순서")

class NodeResponse(NodeBase):
    node_id: UUID = Field(..., description="노드 고유 식별자")
    curriculum_id: UUID = Field(..., description="노드가 속한 커리큘럼 맵 ID")
    created_at: datetime = Field(..., description="노드 생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")

    model_config = ConfigDict(from_attributes=True)

# NodeContent Schemas
class NodeContentBase(BaseModel):
    markdown_content: Optional[str] = Field(None, description="노드의 본문 내용 (마크다운 형식)")
    ai_generated_summary: Optional[str] = Field(None, description="AI가 생성한 요약 내용")
    ai_generated_extension: Optional[str] = Field(None, description="AI가 생성한 확장 내용")

class NodeContentCreate(NodeContentBase):
    node_id: UUID = Field(..., description="내용이 연결된 노드 ID")

class NodeContentUpdate(NodeContentBase):
    pass

class NodeContentResponse(NodeContentBase):
    content_id: UUID = Field(..., description="노드 내용 고유 식별자")
    node_id: UUID = Field(..., description="내용이 연결된 노드 ID")
    created_at: datetime = Field(..., description="내용 생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")

    model_config = ConfigDict(from_attributes=True)

# NodeLink Schemas
class NodeLinkBase(BaseModel):
    link_type: str = Field(..., pattern="^(ZOTERO|YOUTUBE)$", description="링크 유형 (ZOTERO 또는 YOUTUBE)")
    zotero_item_id: Optional[UUID] = Field(None, description="연결된 Zotero 문헌 ID")
    youtube_video_id: Optional[UUID] = Field(None, description="연결된 YouTube 영상 ID")

class NodeLinkCreate(NodeLinkBase):
    node_id: UUID = Field(..., description="링크가 연결된 노드 ID")

class NodeLinkResponse(NodeLinkBase):
    link_id: UUID = Field(..., description="링크 고유 식별자")
    node_id: UUID = Field(..., description="링크가 연결된 노드 ID")
    created_at: datetime = Field(..., description="링크 생성 시각")

    model_config = ConfigDict(from_attributes=True)
