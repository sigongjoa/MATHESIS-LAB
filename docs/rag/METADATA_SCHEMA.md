# 메타데이터 스키마 정의

RAG 시스템에서 사용하는 청크(Chunk) 메타데이터의 표준 스키마를 정의합니다.

## 📋 목차
1. [개요](#개요)
2. [필수 메타데이터](#필수-메타데이터)
3. [선택 메타데이터](#선택-메타데이터)
4. [데이터 타입 및 제약 조건](#데이터-타입-및-제약-조건)
5. [예시](#예시)
6. [검증 규칙](#검증-규칙)

---

## 개요

메타데이터는 RAG 시스템의 검색 정확도와 효율성을 결정하는 핵심 요소입니다. 모든 청크는 다음 메타데이터를 포함해야 합니다.

### 메타데이터의 역할
- **검색 필터링**: 질문에 맞는 청크만 선별
- **버전 관리**: 교육과정 개정 간 분리
- **출처 추적**: 근거 인용 시 정확한 출처 제공
- **품질 관리**: 데이터 무결성 검증

---

## 필수 메타데이터

모든 청크에 반드시 포함되어야 하는 필드입니다.

### 1. `policy_version`
- **타입**: `String`
- **설명**: 교육과정 개정 연도
- **형식**: `YYYY개정`
- **예시**: `"2022개정"`, `"2015개정"`, `"2009개정"`
- **목적**: 시간적 확장성 - 과거/미래 교육과정 버전 분리

### 2. `scope_type`
- **타입**: `Enum`
- **설명**: 문서의 범위 유형
- **가능한 값**:
  - `NATIONAL`: 국가 교육과정
  - `SCHOOL`: 개별 학교 운영 계획
- **예시**: `"NATIONAL"`
- **목적**: 공간적 확장성 - 정책과 실행 문서 구분

### 3. `document_type`
- **타입**: `Enum`
- **설명**: 청크가 속한 문서의 유형
- **가능한 값**:
  - `성취기준`: 성취기준 본문 + 해설 + 고려사항
  - `내용체계`: 핵심 아이디어, 내용 요소, 지식/이해 등
  - `교수학습방법`: 교수·학습 방향 및 방법
  - `평가계획`: 평가 원칙 및 방법
  - `수업운영`: 학교별 수업 운영 계획
- **예시**: `"성취기준"`
- **목적**: 질문 의도에 맞는 청크 유형 우선 검색

### 4. `chunk_id`
- **타입**: `String (UUID)`
- **설명**: 청크의 고유 식별자
- **형식**: UUID v4
- **예시**: `"550e8400-e29b-41d4-a716-446655440000"`
- **목적**: 청크 추적 및 인용

### 5. `source_file`
- **타입**: `String`
- **설명**: 원본 파일 경로
- **예시**: `"assets/curriculum/2022/[별책 8] 수학과 교육과정.pdf"`
- **목적**: 원본 문서 추적

### 6. `indexed_at`
- **타입**: `DateTime (ISO 8601)`
- **설명**: 인덱싱 시간
- **예시**: `"2025-11-20T21:48:19+09:00"`
- **목적**: 데이터 신선도 추적

---

## 선택 메타데이터

문서 유형에 따라 추가로 포함될 수 있는 필드입니다.

### 국가 교육과정 전용

#### 1. `curriculum_code`
- **타입**: `String`
- **설명**: 성취기준 코드
- **형식**: `[학년+과목+영역+번호]`
- **정규식**: `^\[\d+[가-힣]+\d+-\d+\]$`
- **예시**: `"[9수01-01]"`, `"[12대수01]"`
- **목적**: 성취기준 고유 식별 및 개정 간 추적

#### 2. `subject`
- **타입**: `String`
- **설명**: 과목명
- **예시**: `"수학"`, `"공통수학1"`, `"대수"`
- **목적**: 과목별 필터링

#### 3. `grade_level`
- **타입**: `String`
- **설명**: 학년(군)
- **예시**: `"초1~2"`, `"중1~3"`, `"고등학교"`
- **목적**: 학년별 필터링

#### 4. `domain`
- **타입**: `String`
- **설명**: 영역
- **예시**: `"수와 연산"`, `"변화와 관계"`, `"도형과 측정"`
- **목적**: 영역별 필터링

#### 5. `page_number`
- **타입**: `Integer`
- **설명**: 원본 문서 페이지 번호
- **예시**: `115`
- **목적**: 근거 인용 시 페이지 명시

### 학교 운영 계획 전용

#### 1. `institution_id`
- **타입**: `String`
- **설명**: 학교 고유 식별자
- **형식**: `[학교명]_[년도]`
- **예시**: `"협성고_2025"`
- **목적**: 다중 학교 데이터 관리

#### 2. `school_name`
- **타입**: `String`
- **설명**: 학교명
- **예시**: `"협성고등학교"`
- **목적**: 사용자 친화적 표시

#### 3. `academic_year`
- **타입**: `String`
- **설명**: 학년도
- **예시**: `"2025"`
- **목적**: 연도별 필터링

#### 4. `semester`
- **타입**: `Integer`
- **설명**: 학기
- **가능한 값**: `1`, `2`
- **예시**: `1`
- **목적**: 학기별 필터링

#### 5. `teacher_name`
- **타입**: `String`
- **설명**: 담당 교사명
- **예시**: `"김철수"`
- **목적**: 담당자 추적 (선택적)

---

## 데이터 타입 및 제약 조건

### 타입 정의

```python
from enum import Enum
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field, validator
import re

class ScopeType(str, Enum):
    NATIONAL = "NATIONAL"
    SCHOOL = "SCHOOL"

class DocumentType(str, Enum):
    ACHIEVEMENT_STANDARD = "성취기준"
    CONTENT_SYSTEM = "내용체계"
    TEACHING_METHOD = "교수학습방법"
    EVALUATION_PLAN = "평가계획"
    CLASS_OPERATION = "수업운영"

class ChunkMetadata(BaseModel):
    # 필수 필드
    policy_version: str = Field(..., regex=r"^\d{4}개정$")
    scope_type: ScopeType
    document_type: DocumentType
    chunk_id: str = Field(..., regex=r"^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$")
    source_file: str
    indexed_at: datetime
    
    # 선택 필드 - 국가 교육과정
    curriculum_code: Optional[str] = Field(None, regex=r"^\[\d+[가-힣]+\d+-\d+\]$")
    subject: Optional[str] = None
    grade_level: Optional[str] = None
    domain: Optional[str] = None
    page_number: Optional[int] = Field(None, ge=1)
    
    # 선택 필드 - 학교 운영 계획
    institution_id: Optional[str] = None
    school_name: Optional[str] = None
    academic_year: Optional[str] = Field(None, regex=r"^\d{4}$")
    semester: Optional[int] = Field(None, ge=1, le=2)
    teacher_name: Optional[str] = None
    
    @validator('institution_id')
    def validate_institution_id(cls, v, values):
        if values.get('scope_type') == ScopeType.SCHOOL and not v:
            raise ValueError('institution_id is required for SCHOOL scope')
        return v
    
    @validator('curriculum_code')
    def validate_curriculum_code(cls, v, values):
        if values.get('document_type') == DocumentType.ACHIEVEMENT_STANDARD and not v:
            raise ValueError('curriculum_code is required for 성취기준 document type')
        return v
```

---

## 예시

### 예시 1: 국가 교육과정 - 성취기준

```json
{
  "policy_version": "2022개정",
  "scope_type": "NATIONAL",
  "document_type": "성취기준",
  "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
  "source_file": "assets/curriculum/2022/[별책 8] 수학과 교육과정.pdf",
  "indexed_at": "2025-11-20T21:48:19+09:00",
  "curriculum_code": "[9수01-01]",
  "subject": "수학",
  "grade_level": "중1~3",
  "domain": "수와 연산",
  "page_number": 115
}
```

### 예시 2: 국가 교육과정 - 내용 체계

```json
{
  "policy_version": "2022개정",
  "scope_type": "NATIONAL",
  "document_type": "내용체계",
  "chunk_id": "660e8400-e29b-41d4-a716-446655440001",
  "source_file": "assets/curriculum/2022/[별책 8] 수학과 교육과정.pdf",
  "indexed_at": "2025-11-20T21:48:19+09:00",
  "subject": "수학",
  "grade_level": "초1~2",
  "domain": "수와 연산",
  "page_number": 23
}
```

### 예시 3: 학교 운영 계획 - 평가 계획

```json
{
  "policy_version": "2022개정",
  "scope_type": "SCHOOL",
  "document_type": "평가계획",
  "chunk_id": "770e8400-e29b-41d4-a716-446655440002",
  "source_file": "assets/schools/협성고/2025/교수학습_및_평가_운영_계획.hwp",
  "indexed_at": "2025-11-20T21:48:19+09:00",
  "institution_id": "협성고_2025",
  "school_name": "협성고등학교",
  "academic_year": "2025",
  "semester": 2,
  "subject": "스포츠 생활",
  "grade_level": "고3"
}
```

---

## 검증 규칙

### 자동 검증 스크립트

```python
# tools/validate_metadata.py

from typing import Dict, Any
import re

def validate_chunk_metadata(metadata: Dict[str, Any]) -> tuple[bool, list[str]]:
    """
    청크 메타데이터 유효성 검사
    
    Returns:
        (is_valid, error_messages)
    """
    errors = []
    
    # 필수 필드 검증
    required_fields = ['policy_version', 'scope_type', 'document_type', 
                      'chunk_id', 'source_file', 'indexed_at']
    for field in required_fields:
        if field not in metadata:
            errors.append(f"Missing required field: {field}")
    
    # policy_version 형식 검증
    if 'policy_version' in metadata:
        if not re.match(r'^\d{4}개정$', metadata['policy_version']):
            errors.append(f"Invalid policy_version format: {metadata['policy_version']}")
    
    # scope_type 검증
    if 'scope_type' in metadata:
        if metadata['scope_type'] not in ['NATIONAL', 'SCHOOL']:
            errors.append(f"Invalid scope_type: {metadata['scope_type']}")
    
    # curriculum_code 검증 (성취기준인 경우)
    if metadata.get('document_type') == '성취기준':
        if 'curriculum_code' not in metadata:
            errors.append("curriculum_code is required for 성취기준")
        elif not re.match(r'^\[\d+[가-힣]+\d+-\d+\]$', metadata['curriculum_code']):
            errors.append(f"Invalid curriculum_code format: {metadata['curriculum_code']}")
    
    # institution_id 검증 (학교 문서인 경우)
    if metadata.get('scope_type') == 'SCHOOL':
        if 'institution_id' not in metadata:
            errors.append("institution_id is required for SCHOOL scope")
    
    return (len(errors) == 0, errors)

# 사용 예시
if __name__ == "__main__":
    test_metadata = {
        "policy_version": "2022개정",
        "scope_type": "NATIONAL",
        "document_type": "성취기준",
        "chunk_id": "550e8400-e29b-41d4-a716-446655440000",
        "source_file": "assets/curriculum/2022/[별책 8] 수학과 교육과정.pdf",
        "indexed_at": "2025-11-20T21:48:19+09:00",
        "curriculum_code": "[9수01-01]"
    }
    
    is_valid, errors = validate_chunk_metadata(test_metadata)
    if is_valid:
        print("✓ Metadata is valid")
    else:
        print("✗ Validation errors:")
        for error in errors:
            print(f"  - {error}")
```

---

## 버전 관리

메타데이터 스키마 변경 시:
1. 버전 번호 업데이트
2. 변경 이력 기록
3. 기존 청크 마이그레이션 스크립트 작성

### 변경 이력

| 버전 | 날짜 | 변경 내용 |
|------|------|----------|
| 1.0 | 2025-11-20 | 초기 스키마 정의 |

---

**문서 버전**: 1.0  
**작성일**: 2025-11-20  
**작성자**: MATHESIS LAB 개발팀
