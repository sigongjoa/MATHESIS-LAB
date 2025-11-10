from typing import Optional
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict # 1. ConfigDict 임포트

class CurriculumBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="커리큘럼 맵의 제목")
    description: Optional[str] = Field(None, description="커리큘럼 맵에 대한 설명")

class CurriculumCreate(CurriculumBase):
    pass

class CurriculumUpdate(CurriculumBase):
    title: Optional[str] = Field(None, min_length=1, max_length=255, description="커리큘럼 맵의 제목")

class CurriculumResponse(CurriculumBase):
    curriculum_id: UUID = Field(..., description="커리큘럼 맵의 고유 식별자")
    created_at: datetime = Field(..., description="커리큘럼 맵 생성 시각")
    updated_at: datetime = Field(..., description="마지막 정보 수정 시각")

    model_config = ConfigDict(from_attributes=True) # 2. class Config 대신 model_config 사용