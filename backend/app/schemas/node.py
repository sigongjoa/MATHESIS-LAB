from typing import Optional, List
from datetime import datetime
from uuid import UUID # Keep UUID for parsing input, but use str for fields that map to DB String
from pydantic import BaseModel, Field, ConfigDict

# Node Schemas
class NodeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="노드 제목")
    parent_node_id: Optional[str] = Field(None, description="부모 노드 ID (최상위 노드는 NULL)")

class NodeCreate(NodeBase):
    pass

class NodeUpdate(NodeBase):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="노드 제목")
    parent_node_id: Optional[str] = Field(None, description="부모 노드 ID (최상위 노드는 NULL)")

class NodeResponse(NodeBase):
    node_id: str = Field(..., description="노드 고유 식별자")
    curriculum_id: str = Field(..., description="노드가 속한 커리큘럼 맵 ID")
    order_index: int = Field(..., ge=0, description="커리큘럼 맵 내 노드 순서")
    created_at: datetime = Field(..., description="노드 생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")
    content: Optional['NodeContentResponse'] = None
    links: List['NodeLinkResponse'] = []

    model_config = ConfigDict(from_attributes=True)

class NodeReorder(BaseModel):
    node_id: str = Field(..., description="순서를 변경할 노드의 ID")
    new_parent_id: Optional[str] = Field(None, description="새로운 부모 노드의 ID (최상위 노드는 NULL)")
    new_order_index: int = Field(..., ge=0, description="새로운 순서 인덱스")

# NodeContent Schemas
class NodeContentBase(BaseModel):
    markdown_content: Optional[str] = Field(None, description="노드의 본문 내용 (마크다운 형식)")
    ai_generated_summary: Optional[str] = Field(None, description="AI가 생성한 요약 내용")
    ai_generated_extension: Optional[str] = Field(None, description="AI가 생성한 확장 내용")
    manim_guidelines: Optional[str] = Field(None, description="AI가 생성한 Manim 코드 가이드라인")

class NodeContentCreate(NodeContentBase):
    node_id: str = Field(..., description="내용이 연결된 노드 ID")

class NodeContentUpdate(NodeContentBase):
    pass

class NodeContentResponse(NodeContentBase):
    content_id: str = Field(..., description="노드 내용 고유 식별자")
    node_id: str = Field(..., description="내용이 연결된 노드 ID")
    created_at: datetime = Field(..., description="내용 생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")

    model_config = ConfigDict(from_attributes=True)

class NodeContentExtendRequest(BaseModel):
    prompt: Optional[str] = Field(None, description="AI 내용 확장을 위한 특정 지시사항")

# NodeLink Schemas
class NodeLinkBase(BaseModel):
    link_type: str = Field(..., description="링크 유형 (ZOTERO 또는 YOUTUBE)")
    zotero_item_id: Optional[str] = Field(None, description="연결된 Zotero 문헌 ID")
    youtube_video_id: Optional[str] = Field(None, description="연결된 YouTube 영상 ID")

class NodeLinkCreate(NodeLinkBase):
    pass

class NodeLinkZoteroCreate(BaseModel):
    zotero_key: str = Field(..., description="연결할 Zotero 문헌의 고유 키 (외부 ID)")

class NodeLinkYouTubeCreate(BaseModel):
    youtube_url: str = Field(..., description="연결할 YouTube 영상의 URL")

class NodeLinkResponse(NodeLinkBase):
    link_id: str = Field(..., description="링크 고유 식별자")
    node_id: str = Field(..., description="링크가 연결된 노드 ID")
    created_at: datetime = Field(..., description="링크 생성 시각")

    model_config = ConfigDict(from_attributes=True)

class YouTubeVideoResponse(BaseModel):
    video_id: str
    title: str
    channel_title: Optional[str] = None
    description: Optional[str] = None
    thumbnail_url: Optional[str] = None
    duration_seconds: Optional[int] = None
    published_at: Optional[datetime] = None
