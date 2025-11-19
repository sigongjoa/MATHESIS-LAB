# 데이터베이스 설계 문서 (Database Design Document)

## 1. 개요
이 문서는 'MATHESIS LAB' 프로젝트의 데이터베이스 스키마를 정의합니다. 플랫폼의 핵심 데이터(커리큘럼 맵, 노드, 사용자 등)와 자체 호스팅 Zotero 서버의 데이터 구조를 포함하여, 데이터의 일관성과 무결성을 보장하고 효율적인 데이터 관리를 위한 청사진을 제공합니다.

## 2. 엔티티-관계 다이어그램 (ERD)

### 2.1. 플랫폼 DB 스키마 (SQLite/PostgreSQL)
'MATHESIS LAB'의 주요 엔티티와 이들 간의 관계를 시각화합니다.

```mermaid
erDiagram
    USERS ||--o{ CURRICULUMS : "owns"
    USERS ||--o{ USER_SESSIONS : "creates"

    CURRICULUMS ||--o{ NODES : "contains"
    CURRICULUMS ||--o{ SYNC_METADATA : "has"
    CURRICULUMS ||--o{ CURRICULUM_DRIVE_FOLDERS : "maps_to"

    NODES ||--o{ NODES : "parent-child"
    NODES ||--o{ NODE_CONTENTS : "contains"
    NODES ||--o{ NODE_LINKS : "connected_by"

    NODE_CONTENTS ||--|| NODES : "belongs_to"

    NODE_LINKS ||--o{ NODES : "links_from"
    NODE_LINKS ||--o{ NODES : "links_to"
    NODE_LINKS ||--o{ ZOTERO_ITEMS : "references"
    NODE_LINKS ||--o{ YOUTUBE_VIDEOS : "references"

    SYNC_METADATA ||--|| NODES : "tracks"

    USERS {
        UUID user_id PK
        VARCHAR email UK
        VARCHAR name
        VARCHAR password_hash "NULLable - for OAuth users"
        TEXT profile_picture_url "NULLable"
        VARCHAR role "Default: user"
        BOOLEAN is_active
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP last_login "NULLable"
        TIMESTAMP deleted_at "NULLable - soft delete"
    }

    USER_SESSIONS {
        UUID session_id PK
        VARCHAR user_id FK
        VARCHAR refresh_token_hash UK
        TIMESTAMP created_at
        TIMESTAMP expires_at
        TIMESTAMP revoked_at "NULLable"
    }

    CURRICULUMS {
        UUID curriculum_id PK
        VARCHAR owner_id FK "User who owns this curriculum"
        VARCHAR title
        TEXT description
        BOOLEAN is_public "Default: FALSE"
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    NODES {
        UUID node_id PK
        UUID curriculum_id FK
        UUID parent_node_id FK "NULLable for root nodes"
        VARCHAR node_type "Default: CONTENT (for queryability)"
        VARCHAR title
        INT order_index
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP deleted_at "NULLable - soft delete"
    }

    NODE_CONTENTS {
        UUID content_id PK
        UUID node_id FK UNIQUE
        TEXT markdown_content
        TEXT ai_generated_summary "NULLable"
        TEXT ai_generated_extension "NULLable"
        TEXT manim_guidelines "NULLable for Manim animation guidelines"
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP deleted_at "NULLable - soft delete"
    }

    NODE_LINKS {
        UUID link_id PK
        UUID node_id FK "Source node"
        UUID zotero_item_id FK "NULLable - for Zotero links"
        UUID youtube_video_id FK "NULLable - for YouTube links"
        VARCHAR link_type "ZOTERO | YOUTUBE | DRIVE_PDF | NODE"
        VARCHAR drive_file_id "NULLable - Google Drive PDF file ID"
        VARCHAR file_name "NULLable - PDF filename"
        INT file_size_bytes "NULLable - PDF file size"
        VARCHAR file_mime_type "NULLable - MIME type (application/pdf)"
        UUID linked_node_id FK "NULLable - for node-to-node links"
        VARCHAR link_relationship "NULLable - EXTENDS | REFERENCES | DEPENDS_ON | SOURCE"
        TIMESTAMP created_at
        TIMESTAMP deleted_at "NULLable - soft delete"
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
        VARCHAR channel_title "NULLable"
        TEXT description "NULLable"
        VARCHAR thumbnail_url "NULLable"
        INT duration_seconds "NULLable"
        TIMESTAMP published_at "NULLable"
        TIMESTAMP created_at
    }

    SYNC_METADATA {
        UUID id PK
        UUID curriculum_id FK
        UUID node_id FK UK
        VARCHAR google_drive_file_id "NULLable"
        VARCHAR google_drive_folder_id "NULLable"
        TIMESTAMP last_local_modified
        TIMESTAMP last_drive_modified "NULLable"
        TIMESTAMP last_sync_time "NULLable"
        VARCHAR sync_status "pending | synced | conflict | failed"
        BOOLEAN is_synced
        TIMESTAMP created_at
        TIMESTAMP updated_at
    }

    CURRICULUM_DRIVE_FOLDERS {
        UUID id PK
        UUID curriculum_id FK UK
        VARCHAR google_drive_folder_id
        TIMESTAMP created_at
        TIMESTAMP updated_at
        TIMESTAMP last_sync_at "NULLable"
    }

    GOOGLE_DRIVE_TOKENS {
        UUID id PK
        VARCHAR user_id "NULLable - user association"
        VARCHAR access_token
        VARCHAR refresh_token "NULLable"
        TIMESTAMP token_expiry "NULLable"
        VARCHAR token_type "Default: Bearer"
        VARCHAR scope "NULLable - OAuth scopes"
        BOOLEAN is_valid
        TIMESTAMP created_at
        TIMESTAMP updated_at
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

### 3.1. USERS 테이블 (Authentication)
| 컬럼명              | 데이터 타입   | 제약 조건       | 설명                               |
| :----------------- | :------------ | :-------------- | :--------------------------------- |
| `user_id`          | `VARCHAR(36)` | `PRIMARY KEY`   | 사용자 고유 식별자                 |
| `email`            | `VARCHAR(255)`| `NOT NULL`, `UNIQUE` | 사용자 이메일 (로그인용)           |
| `name`             | `VARCHAR(255)`| `NOT NULL`      | 사용자 이름                        |
| `password_hash`    | `VARCHAR(255)`| `NULLABLE`      | 비밀번호 해시 (OAuth 사용자는 NULL) |
| `profile_picture_url`| `TEXT`      | `NULLABLE`      | 프로필 사진 URL                    |
| `role`             | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'user'` | 사용자 역할 (user, admin 등)     |
| `is_active`        | `BOOLEAN`     | `NOT NULL`, `DEFAULT TRUE` | 계정 활성 상태                  |
| `created_at`       | `TIMESTAMP`   | `NOT NULL`      | 사용자 생성 시각                   |
| `updated_at`       | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |
| `last_login`       | `TIMESTAMP`   | `NULLABLE`      | 마지막 로그인 시각                 |
| `deleted_at`       | `TIMESTAMP`   | `NULLABLE`      | 소프트 삭제 시각 (삭제되지 않으면 NULL) |

### 3.2. USER_SESSIONS 테이블 (Token Management)
| 컬럼명              | 데이터 타입   | 제약 조건       | 설명                               |
| :----------------- | :------------ | :-------------- | :--------------------------------- |
| `session_id`       | `VARCHAR(36)` | `PRIMARY KEY`   | 세션 고유 식별자                   |
| `user_id`          | `VARCHAR(36)` | `FOREIGN KEY`   | 세션의 사용자 ID                   |
| `refresh_token_hash`| `VARCHAR(255)`| `NOT NULL`, `UNIQUE` | Refresh 토큰 해시 (암호화 저장)   |
| `created_at`       | `TIMESTAMP`   | `NOT NULL`      | 세션 생성 시각                     |
| `expires_at`       | `TIMESTAMP`   | `NOT NULL`      | 세션 만료 시각                     |
| `revoked_at`       | `TIMESTAMP`   | `NULLABLE`      | 세션 폐기 시각 (폐기되지 않으면 NULL) |

### 3.3. CURRICULUMS 테이블
| 컬럼명          | 데이터 타입   | 제약 조건       | 설명                               |
| :-------------- | :------------ | :-------------- | :--------------------------------- |
| `curriculum_id` | `VARCHAR(36)` | `PRIMARY KEY`   | 커리큘럼 맵 고유 식별자            |
| `owner_id`      | `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 커리큘럼 소유자 사용자 ID          |
| `title`         | `VARCHAR(255)`| `NOT NULL`      | 커리큘럼 맵 제목                   |
| `description`   | `TEXT`        | `NULLABLE`      | 커리큘럼 맵 설명                   |
| `is_public`     | `BOOLEAN`     | `NOT NULL`, `DEFAULT FALSE` | 공개 여부 (공개/비공개)   |
| `created_at`    | `TIMESTAMP`   | `NOT NULL`      | 커리큘럼 맵 생성 시각              |
| `updated_at`    | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |

### 3.4. NODES 테이블
| 컬럼명          | 데이터 타입   | 제약 조건       | 설명                               |
| :-------------- | :------------ | :-------------- | :--------------------------------- |
| `node_id`       | `VARCHAR(36)` | `PRIMARY KEY`   | 노드 고유 식별자                   |
| `curriculum_id` | `VARCHAR(36)` | `FOREIGN KEY`   | 노드가 속한 커리큘럼 맵 ID         |
| `parent_node_id`| `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 부모 노드 ID (최상위 노드는 NULL)  |
| `node_type`     | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'CONTENT'` | 노드 유형 (쿼리를 위한 분류)        |
| `title`         | `VARCHAR(255)`| `NOT NULL`      | 노드 제목                          |
| `order_index`   | `INT`         | `NOT NULL`      | 커리큘럼 맵 내 노드 순서           |
| `created_at`    | `TIMESTAMP`   | `NOT NULL`      | 노드 생성 시각                     |
| `updated_at`    | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |
| `deleted_at`    | `TIMESTAMP`   | `NULLABLE`      | 소프트 삭제 시각 (삭제되지 않으면 NULL) |

### 3.5. NODE_CONTENTS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `content_id`      | `VARCHAR(36)` | `PRIMARY KEY`   | 노드 내용 고유 식별자              |
| `node_id`         | `VARCHAR(36)` | `FOREIGN KEY`, `UNIQUE` | 내용이 연결된 노드 ID              |
| `markdown_content`| `TEXT`        | `NULLABLE`      | 노드의 본문 내용 (마크다운 형식)   |
| `ai_generated_summary`| `TEXT`    | `NULLABLE`      | AI가 생성한 요약 내용              |
| `ai_generated_extension`| `TEXT`  | `NULLABLE`      | AI가 생성한 확장 내용              |
| `manim_guidelines`| `TEXT`        | `NULLABLE`      | Manim 애니메이션 가이드라인        |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 내용 생성 시각                     |
| `updated_at`      | `TIMESTAMP`   | `NOT NULL`      | 마지막 정보 수정 시각              |
| `deleted_at`      | `TIMESTAMP`   | `NULLABLE`      | 소프트 삭제 시각 (삭제되지 않으면 NULL) |

### 3.6. NODE_LINKS 테이블
| 컬럼명            | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------- | :------------ | :-------------- | :--------------------------------- |
| `link_id`         | `VARCHAR(36)` | `PRIMARY KEY`   | 링크 고유 식별자                   |
| `node_id`         | `VARCHAR(36)` | `FOREIGN KEY`   | 소스 노드 ID (링크 출발점)         |
| `zotero_item_id`  | `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 연결된 Zotero 문헌 ID              |
| `youtube_video_id`| `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 연결된 YouTube 영상 ID             |
| `drive_file_id`   | `VARCHAR(255)`| `NULLABLE`      | Google Drive 파일 ID (PDF)        |
| `file_name`       | `VARCHAR(255)`| `NULLABLE`      | 파일 이름 (PDF 파일)               |
| `file_size_bytes` | `INT`         | `NULLABLE`      | 파일 크기 (바이트)                 |
| `file_mime_type`  | `VARCHAR(100)`| `NULLABLE`      | MIME 타입 (예: application/pdf)    |
| `linked_node_id`  | `VARCHAR(36)` | `FOREIGN KEY`, `NULLABLE` | 대상 노드 ID (노드-노드 링크)      |
| `link_relationship`| `VARCHAR(50)`| `NULLABLE`      | 링크 관계 (EXTENDS, REFERENCES, DEPENDS_ON, SOURCE 등) |
| `link_type`       | `VARCHAR(20)` | `NOT NULL`      | 링크 유형 (ZOTERO\|YOUTUBE\|DRIVE_PDF\|NODE) |
| `created_at`      | `TIMESTAMP`   | `NOT NULL`      | 링크 생성 시각                     |
| `deleted_at`      | `TIMESTAMP`   | `NULLABLE`      | 소프트 삭제 시각 (삭제되지 않으면 NULL) |
| **제약:** link_type에 따라 해당 FK만 NOT NULL이어야 함 (예: ZOTERO이면 zotero_item_id만)

### 3.7. ZOTERO_ITEMS 테이블
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

### 3.8. YOUTUBE_VIDEOS 테이블
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

### 3.9. SYNC_METADATA 테이블 (Google Drive Synchronization Tracking)
| 컬럼명                   | 데이터 타입   | 제약 조건       | 설명                               |
| :----------------------- | :------------ | :-------------- | :--------------------------------- |
| `id`                     | `VARCHAR(36)` | `PRIMARY KEY`   | 동기화 메타데이터 고유 식별자      |
| `curriculum_id`          | `VARCHAR(36)` | `FOREIGN KEY`   | 커리큘럼 ID                        |
| `node_id`                | `VARCHAR(36)` | `FOREIGN KEY`, `UNIQUE` | 노드 ID (각 노드당 1개만 가능)  |
| `google_drive_file_id`   | `VARCHAR(255)`| `NULLABLE`      | Google Drive 파일 ID               |
| `google_drive_folder_id` | `VARCHAR(255)`| `NULLABLE`      | Google Drive 폴더 ID               |
| `last_local_modified`    | `TIMESTAMP`   | `NOT NULL`      | 로컬 DB에서 마지막 수정 시각       |
| `last_drive_modified`    | `TIMESTAMP`   | `NULLABLE`      | Google Drive에서 마지막 수정 시각  |
| `last_sync_time`         | `TIMESTAMP`   | `NULLABLE`      | 마지막 동기화 시각                 |
| `sync_status`            | `VARCHAR(20)` | `NOT NULL`, `DEFAULT 'pending'` | 동기화 상태 (pending\|synced\|conflict\|failed) |
| `is_synced`              | `BOOLEAN`     | `NOT NULL`, `DEFAULT FALSE` | 동기화 완료 여부                |
| `created_at`             | `TIMESTAMP`   | `NOT NULL`      | 레코드 생성 시각                   |
| `updated_at`             | `TIMESTAMP`   | `NOT NULL`      | 레코드 업데이트 시각               |

### 3.10. CURRICULUM_DRIVE_FOLDERS 테이블 (Curriculum-Drive Folder Mapping)
| 컬럼명                  | 데이터 타입   | 제약 조건       | 설명                               |
| :---------------------- | :------------ | :-------------- | :--------------------------------- |
| `id`                    | `VARCHAR(36)` | `PRIMARY KEY`   | 맵핑 고유 식별자                   |
| `curriculum_id`         | `VARCHAR(36)` | `FOREIGN KEY`, `UNIQUE` | 커리큘럼 ID (각 커리큘럼당 1개만)  |
| `google_drive_folder_id`| `VARCHAR(255)`| `NOT NULL`      | Google Drive 폴더 ID               |
| `created_at`            | `TIMESTAMP`   | `NOT NULL`      | 폴더 생성 시각                     |
| `updated_at`            | `TIMESTAMP`   | `NOT NULL`      | 폴더 정보 업데이트 시각            |
| `last_sync_at`          | `TIMESTAMP`   | `NULLABLE`      | 마지막 동기화 시각                 |

### 3.11. GOOGLE_DRIVE_TOKENS 테이블 (OAuth Token Storage)
| 컬럼명          | 데이터 타입   | 제약 조건       | 설명                               |
| :-------------- | :------------ | :-------------- | :--------------------------------- |
| `id`            | `VARCHAR(36)` | `PRIMARY KEY`   | 토큰 고유 식별자                   |
| `user_id`       | `VARCHAR(36)` | `NULLABLE`      | 사용자 ID (선택사항)               |
| `access_token`  | `VARCHAR(500)`| `NOT NULL`      | Google Drive API 액세스 토큰       |
| `refresh_token` | `VARCHAR(500)`| `NULLABLE`      | 갱신 토큰 (오프라인 액세스용)      |
| `token_expiry`  | `TIMESTAMP`   | `NULLABLE`      | 토큰 만료 시각                     |
| `token_type`    | `VARCHAR(50)` | `NOT NULL`, `DEFAULT 'Bearer'` | 토큰 유형                       |
| `scope`         | `VARCHAR(500)`| `NULLABLE`      | OAuth 스코프 (쉼표 구분)           |
| `is_valid`      | `BOOLEAN`     | `NOT NULL`, `DEFAULT TRUE` | 토큰 유효성 여부                 |
| `created_at`    | `TIMESTAMP`   | `NOT NULL`      | 토큰 생성 시각                     |
| `updated_at`    | `TIMESTAMP`   | `NOT NULL`      | 토큰 업데이트 시각                 |

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
