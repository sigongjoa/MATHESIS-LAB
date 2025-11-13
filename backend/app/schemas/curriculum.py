from typing import Optional, List
from uuid import UUID
from datetime import datetime

from pydantic import BaseModel, Field, ConfigDict # 1. ConfigDict 임포트

from backend.app.schemas.node import NodeResponse





class CurriculumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="커리큘럼 맵 제목")
    description: Optional[str] = Field(None, description="커리큘럼 맵에 대한 설명")
    is_public: Optional[bool] = Field(False, description="공개 여부")

class CurriculumCreate(CurriculumBase):
    pass

class CurriculumUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="커리큘럼 맵 제목")
    description: Optional[str] = Field(None, description="커리큘럼 맵에 대한 설명")
    is_public: Optional[bool] = Field(None, description="공개 여부")

class CurriculumResponse(CurriculumBase):
    curriculum_id: UUID = Field(..., description="커리큘럼 맵 고유 식별자")
    is_public: bool = Field(..., description="공개 여부")
    created_at: datetime = Field(..., description="생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")
    nodes: List['NodeResponse'] = [] # 2. class Config 대신 model_config 사용
