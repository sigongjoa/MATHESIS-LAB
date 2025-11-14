# 데이터베이스 설계 문서 (Database Design Document)

## 1. 개요
이 문서는 'MATHESIS LAB' 프로젝트의 데이터베이스 스키마를 정의합니다. 플랫폼의 핵심 데이터(커리큘럼 맵, 노드, 사용자 등)와 자체 호스팅 Zotero 서버의 데이터 구조를 포함하여, 데이터의 일관성과 무결성을 보장하고 효율적인 데이터 관리를 위한 청사진을 제공합니다.

## 2. 엔티티-관계 다이어그램 (ERD)

### 2.1. 플랫폼 DB 스키마 (PostgreSQL)
'MATHESIS LAB'의 주요 엔티티와 이들 간의 관계를 시각화합니다.

```mermaid
erDiagram
    CURRICULUMS {
        UUID curriculum_id PK
        VARCHAR title
        TEXT description
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    NODES {
        UUID node_id PK
        UUID curriculum_id FK
        UUID parent_node_id FK "NULLable for root nodes"
        VARCHAR title
        INT order_index
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    NODE_CONTENTS {
        UUID content_id PK
        UUID node_id FK UNIQUE
        TEXT markdown_content
        TEXT ai_generated_summary "NULLable"
        TEXT ai_generated_extension "NULLable"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    NODE_LINKS {
        UUID link_id PK
        UUID node_id FK
        UUID zotero_item_id FK "NULLable"
        UUID youtube_video_id FK "NULLable"
        VARCHAR link_type "ZOTERO or YOUTUBE"
        TIMESTAMP created_at
    }

    ZOTERO_ITEMS {
        UUID zotero_item_id PK
        VARCHAR zotero_key UNIQUE "Zotero internal key"
        VARCHAR title
        TEXT authors
        INT publication_year
        TEXT tags
        TEXT item_type
        TEXT abstract "NULLable"
        TEXT url "NULLable"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    YOUTUBE_VIDEOS {
        UUID youtube_video_id PK
        VARCHAR video_id UNIQUE "YouTube video ID"
        VARCHAR title
        VARCHAR channel_title
        TEXT description "NULLable"
        VARCHAR thumbnail_url "NULLable"
        INT duration_seconds "NULLable"
        TIMESTAMP published_at "NULLable"
        TIMESTAMP created_at
    }
```

### 2.2. Zotero DB 스키마 분석 (PostgreSQL on GKE)
자체 호스팅 Zotero 서버는 자체적인 PostgreSQL 데이터베이스를 사용합니다. 'MATHESIS LAB' 플랫폼은 이 Zotero DB에 직접 접근하기보다는 Zotero API를 통해 상호작용합니다. 따라서 여기서는 Zotero의 핵심 테이블 구조를 이해하고, 필요한 경우 플랫폼과의 연동을 위한 고려사항을 명시합니다.

**주요 Zotero 테이블 (예시):**
*   `items`: 문헌의 기본 정보 (제목, 저자, 출판일 등)
*   `itemTags`: 문헌과 태그 간의 연결
*   `tags`: 태그 정보
*   `collections`: 컬렉션 정보
*   `itemAttachments`: 첨부 파일 정보

**연동 고려사항:**
*   'MATHESIS LAB' 플랫폼은 `ZOTERO_ITEMS` 테이블에 Zotero의 `item_id` (또는 `key`)를 저장하여 문헌을 참조합니다.
*   Zotero DB 스키마는 Zotero 버전 업데이트에 따라 변경될 수 있으므로, 직접적인 DB 접근보다는 Zotero API를 통한 연동을 우선합니다.

## 3. 데이터 사전 (Data Dictionary)

### 3.2. CURRICULUMS 테이블
| 컬럼명          | 데이터 타입   | 제약 조건       | 설명                               |
| :-------------- | :------------ | :-------------- | :--------------------------------- |
| `curriculum_id` | `VARCHAR(36)` | `PRIMARY KEY`   | 커리큘럼 맵 고유 식별자            |
| `title`         | `VARCHAR(255)`| `NOT NULL`      | 커리큘럼 맵 제목                   |
| `description`   | `TEXT`        | `NULLABLE`      | 커리큘럼 맵 설명                   |
| `created_at`    | `TIMESTAMP`   | `NOT NULL`      | 커리큘럼 맵 생성 시각              |
| `updated_at`    | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |

### 3.3. NODES 테이블
| 컬럼명          | 데이터 타입   | 제약 조건       | 설명                               |
| :-------------- | :------------ | :-------------- | :--------------------------------- |
| `node_id`       | `VARCHAR(36)` | `PRIMARY KEY`   | 노드 고유 식별자                   |
| `curriculum_id` | `VARCHAR(36)` | `FOREIGN KEY`   | 노드가 속한 커리큘럼 맵 ID         |
| `parent_node_id`| `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 부모 노드 ID (최상위 노드는 NULL)  |
| `title`         | `VARCHAR(255)`| `NOT NULL`      | 노드 제목                          |
| `order_index`   | `INT`         | `NOT NULL`      | 커리큘럼 맵 내 노드 순서           |
| `created_at`    | `TIMESTAMP`   | `NOT NULL`      | 노드 생성 시각                     |
| `updated_at`    | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |

### 3.4. NODE_CONTENTS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `content_id`      | `VARCHAR(36)` | `PRIMARY KEY`   | 노드 내용 고유 식별자              |
| `node_id`         | `VARCHAR(36)` | `FOREIGN KEY`, `UNIQUE` | 내용이 연결된 노드 ID              |
| `markdown_content`| `TEXT`        | `NULLABLE`      | 노드의 본문 내용 (마크다운 형식)   |
| `ai_generated_summary`| `TEXT`    | `NULLABLE`      | AI가 생성한 요약 내용              |
| `ai_generated_extension`| `TEXT`  | `NULLABLE`      | AI가 생성한 확장 내용              |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 내용 생성 시각                     |
| `updated_at`      | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |

### 3.5. NODE_LINKS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `link_id`         | `VARCHAR(36)` | `PRIMARY KEY`   | 링크 고유 식별자                   |
| `node_id`         | `VARCHAR(36)` | `FOREIGN KEY`   | 링크가 연결된 노드 ID              |
| `zotero_item_id`  | `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 연결된 Zotero 문헌 ID              |
| `youtube_video_id`| `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 연결된 YouTube 영상 ID             |
| `link_type`       | `VARCHAR(10)` | `NOT NULL`      | 링크 유형 (ZOTERO 또는 YOUTUBE)    |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 링크 생성 시각                     |
| **제약:** `zotero_item_id`와 `youtube_video_id` 중 하나만 `NOT NULL`이어야 함.

### 3.6. ZOTERO_ITEMS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `zotero_item_id`  | `VARCHAR(36)` | `PRIMARY KEY`   | Zotero 문헌 고유 식별자 (플랫폼 내부) |
| `zotero_key`      | `VARCHAR(255)`| `NOT NULL`, `UNIQUE` | Zotero 시스템 내 문헌 고유 키      |
| `title`           | `VARCHAR(512)`| `NOT NULL`      | 문헌 제목                          |
| `authors`         | `TEXT`        | `NULLABLE`      | 저자 목록 (JSON 또는 콤마 구분)    |
| `publication_year`| `INT`         | `NULLABLE`      | 출판 연도                          |
| `tags`            | `TEXT`        | `NULLABLE`      | 태그 목록 (JSON 또는 콤마 구분)    |
| `item_type`       | `VARCHAR(50)` | `NULLABLE`      | 문헌 유형 (예: article, book)      |
| `abstract`        | `TEXT`        | `NULLABLE`      | 초록                               |
| `url`             | `TEXT`        | `NULLABLE`      | 원본 자료 URL                      |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 플랫폼에 기록된 시각               |
| `updated_at`      | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |

### 3.7. YOUTUBE_VIDEOS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `youtube_video_id`| `VARCHAR(36)` | `PRIMARY KEY`   | YouTube 영상 고유 식별자 (플랫폼 내부) |
| `video_id`        | `VARCHAR(20)` | `NOT NULL`, `UNIQUE` | YouTube 영상의 고유 ID (예: dQw4w9WgXcQ) |
| `title`           | `VARCHAR(512)`| `NOT NULL`      | 영상 제목                          |
| `channel_title`   | `VARCHAR(255)`| `NULLABLE`      | 채널 제목                          |
| `description`     | `TEXT`        | `NULLABLE`      | 영상 설명                          |
| `thumbnail_url`   | `TEXT`        | `NULLABLE`      | 썸네일 이미지 URL                  |
| `duration_seconds`| `INT`         | `NULLABLE`      | 영상 길이 (초)                     |
| `published_at`    | `TIMESTAMP`   | `NULLABLE`      | 영상 게시일                        |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 플랫폼에 기록된 시각               |

## 4. UUID 처리 정책 (UUID Handling Policy)

UUID는 시스템 내에서 고유한 식별자로 사용되지만, 데이터베이스 및 애플리케이션 계층 간의 일관된 처리를 위해 다음과 같은 정책을 따릅니다.

### 4.1. 데이터베이스 (Database)
- **저장 방식**: 모든 UUID는 데이터베이스에 `VARCHAR(36)` 타입으로 저장됩니다. 이는 `UUID` 객체의 표준 문자열 표현(예: `xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx`)을 저장하기 위함입니다.
- **호환성**: PostgreSQL의 네이티브 `UUID` 타입 대신 `VARCHAR(36)`을 사용함으로써 SQLite와 같은 다른 데이터베이스 시스템과의 호환성을 높입니다.

### 4.2. SQLAlchemy 모델 (SQLAlchemy Models)
- **컬럼 정의**: SQLAlchemy 모델에서 UUID 필드는 `Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))`와 같이 `String` 타입으로 정의됩니다.
- **자동 생성**: `default=lambda: str(uuid.uuid4())`를 사용하여 새 레코드 생성 시 자동으로 문자열 형태의 UUID가 할당되도록 합니다.

### 4.3. Pydantic 스키마 (Pydantic Schemas)
- **타입 힌트**: Pydantic 스키마에서 UUID를 나타내는 필드는 `str` 타입 힌트를 사용합니다 (예: `node_id: str`).
- **유효성 검사**: 필요한 경우, 입력 데이터의 UUID 형식을 검증하기 위해 `uuid.UUID` 타입을 사용할 수 있으나, 서비스 계층으로 전달하기 전에 반드시 `str`로 변환해야 합니다.

### 4.4. 서비스 계층 (Service Layer)
- **입력/출력**: 서비스 계층의 메서드는 UUID를 `str` 타입으로 받거나 반환하는 것을 기본으로 합니다.
- **변환**: API 엔드포인트 또는 테스트 코드에서 `uuid.UUID` 객체를 서비스 메서드로 전달하기 전에 `str()` 함수를 사용하여 명시적으로 문자열로 변환해야 합니다.
- **쿼리**: 데이터베이스 쿼리 시, `Node.node_id == some_uuid_string`과 같이 문자열 값을 사용하여 비교합니다.

### 4.5. API 엔드포인트 (API Endpoints)
- **타입 힌트**: FastAPI의 경로(path), 쿼리(query), 바디(body) 파라미터에서 `UUID` 타입 힌트를 사용할 수 있습니다. FastAPI는 자동으로 문자열을 `uuid.UUID` 객체로 변환해줍니다.
- **서비스 호출**: FastAPI가 변환한 `uuid.UUID` 객체를 서비스 계층으로 전달할 때는 `str()` 함수를 사용하여 문자열로 변환하여 전달합니다 (예: `node_service.get_node(str(node_id))`).

이 정책을 통해 UUID 처리의 일관성과 명확성을 확보하고, 잠재적인 타입 관련 오류를 방지합니다.
