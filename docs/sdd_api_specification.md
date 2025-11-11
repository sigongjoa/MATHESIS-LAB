# API 명세서 (API Specification)

## 1. 개요
이 문서는 'MATHESIS LAB' 프로젝트의 내부 컴포넌트 간 통신 규약을 정의하는 API 명세서입니다. 웹 프론트엔드와 백엔드, 백엔드와 외부 서비스(Vertex AI, Zotero) 간의 인터페이스를 명확히 하여 개발의 일관성과 효율성을 높입니다.

## 2. 내부 API (웹 프론트엔드 ↔ 백엔드)

### 2.2. 커리큘럼 맵 관리

*   **`POST /curriculums`**
    *   **설명:** 새 커리큘럼 맵을 생성합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "title": "string",
          "description": "string (optional)"
        }
        ```
    *   **응답 (201 Created):**
        ```json
        {
          "curriculum_id": "uuid",
          "title": "string",
          "description": "string",
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
*   **`GET /curriculums`**
    *   **설명:** 모든 커리큘럼 맵의 목록을 조회합니다.
    *   **쿼리 파라미터:**
        *   `skip`: `int` (optional, default: 0) - 건너뛸 항목 수
        *   `limit`: `int` (optional, default: 100) - 반환할 최대 항목 수
    *   **응답 (200 OK):**
        ```json
        [
          {
            "curriculum_id": "uuid",
            "title": "string",
            "description": "string",
            "is_public": "boolean",
            "created_at": "datetime",
            "updated_at": "datetime"
          },
          ...
        ]
        ```
*   **`GET /curriculums/public`**
    *   **설명:** 공개된 모든 커리큘럼 맵의 목록을 조회합니다.
    *   **쿼리 파라미터:**
        *   `skip`: `int` (optional, default: 0) - 건너뛸 항목 수
        *   `limit`: `int` (optional, default: 100) - 반환할 최대 항목 수
    *   **응답 (200 OK):**
        ```json
        [
          {
            "curriculum_id": "uuid",
            "title": "string",
            "description": "string",
            "is_public": "boolean",
            "created_at": "datetime",
            "updated_at": "datetime"
          },
          ...
        ]
        ```
*   **`GET /curriculums/{curriculum_id}`**
    *   **설명:** 특정 커리큘럼 맵의 상세 정보를 조회합니다 (노드 포함).
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (200 OK):**
        ```json
        {
          "curriculum_id": "uuid",
          "title": "string",
          "description": "string",
          "nodes": [
            {
              "node_id": "uuid",
              "title": "string",
              "parent_node_id": "uuid (nullable)",
              "order_index": 0,
              "content": { ... }, // NODE_CONTENTS 참조
              "links": [ ... ] // NODE_LINKS 참조
            }
          ],
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
*   **`PUT /curriculums/{curriculum_id}`**
    *   **설명:** 특정 커리큘럼 맵의 정보를 업데이트합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "title": "string (optional)",
          "description": "string (optional)",
          "is_public": "boolean (optional)"
        }
        ```
    *   **응답 (200 OK):** 업데이트된 커리큘럼 맵 정보
*   **`DELETE /curriculums/{curriculum_id}`**
    *   **설명:** 특정 커리큘럼 맵을 삭제합니다. (연결된 노드, 콘텐츠, 링크도 함께 삭제)
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (204 No Content)**

### 2.3. 문헌 관리

*   **`POST /literature`**
    *   **설명:** 새 문헌 항목을 생성합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "title": "string",
          "authors": "string (optional)",
          "publication_year": "integer (optional)",
          "tags": "string (comma-separated, optional)",
          "item_type": "string (optional)",
          "abstract": "string (optional)",
          "url": "string (optional)"
        }
        ```
    *   **응답 (201 Created):**
        ```json
        {
          "id": "uuid",
          "title": "string",
          "authors": "string",
          "publication_year": "integer",
          "tags": "string",
          "item_type": "string",
          "abstract": "string",
          "url": "string",
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
*   **`GET /literature`**
    *   **설명:** 문헌 항목 목록을 조회합니다. 태그로 필터링 및 페이지네이션이 가능합니다.
    *   **쿼리 파라미터:**
        *   `tags`: `string` (optional) - 쉼표로 구분된 태그 목록
        *   `match`: `string` (optional, default: "all", enum: ["all", "any"]) - 태그 일치 방식 (모든 태그 일치 또는 하나라도 일치)
        *   `skip`: `int` (optional, default: 0) - 건너뛸 항목 수
        *   `limit`: `int` (optional, default: 100) - 반환할 최대 항목 수
    *   **응답 (200 OK):**
        ```json
        [
          {
            "id": "uuid",
            "title": "string",
            "authors": "string",
            "publication_year": "integer",
            "tags": "string",
            "item_type": "string",
            "abstract": "string",
            "url": "string",
            "created_at": "datetime",
            "updated_at": "datetime"
          },
          ...
        ]
        ```
*   **`GET /literature/{item_id}`**
    *   **설명:** 특정 ID의 문헌 항목을 조회합니다.
    *   **응답 (200 OK):** 조회된 문헌 항목 정보
*   **`PUT /literature/{item_id}`**
    *   **설명:** 특정 문헌 항목의 정보를 업데이트합니다.
    *   **요청:** `LiteratureItemCreate`와 유사하지만 모든 필드가 optional
    *   **응답 (200 OK):** 업데이트된 문헌 항목 정보
*   **`DELETE /literature/{item_id}`**
    *   **설명:** 특정 문헌 항목을 삭제합니다.
    *   **응답 (200 OK):** 삭제된 문헌 항목 정보

### 2.4. 노드 콘텐츠 관리

*   **`POST /nodes/{node_id}/content/summarize`**
    *   **설명:** AI를 사용하여 특정 노드의 내용을 요약합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (200 OK):** 요약된 노드 콘텐츠 정보 (ai_generated_summary 필드 포함)
    *   **오류 처리:**
        *   `404 Not Found`: 노드 콘텐츠를 찾을 수 없거나 노드 ID가 유효하지 않은 경우.
        *   `400 Bad Request`: 노드 콘텐츠가 비어 있거나 AI 서비스에 전달할 수 없는 형식인 경우.
        *   `500 Internal Server Error`: AI 서비스 호출 중 외부 오류가 발생한 경우.
*   **`POST /nodes/{node_id}/content/extend`**
    *   **설명:** AI를 사용하여 특정 노드의 내용을 확장합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "prompt": "string (optional, for specific extension instructions)"
        }
        ```
    *   **응답 (200 OK):** 확장된 노드 콘텐츠 정보 (ai_generated_extension 필드 포함)
    *   **오류 처리:**
        *   `404 Not Found`: 노드 콘텐츠를 찾을 수 없거나 노드 ID가 유효하지 않은 경우.
        *   `400 Bad Request`: 노드 콘텐츠가 비어 있거나 AI 서비스에 전달할 수 없는 형식인 경우.
        *   `500 Internal Server Error`: AI 서비스 호출 중 외부 오류가 발생한 경우.

### 2.5. 노드 관리

*   **`POST /curriculums/{curriculum_id}/nodes`**
    *   **설명:** 특정 커리큘럼 맵에 새 노드를 추가합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "title": "string",
          "parent_node_id": "uuid (optional, for child nodes)"
        }
        ```
    *   **응답 (201 Created):**
        ```json
        {
          "node_id": "uuid",
          "title": "string",
          "parent_node_id": "uuid (nullable)",
          "order_index": 0,
          "content": { ... },
          "created_at": "datetime",
          "updated_at": "datetime"
        }
        ```
*   **`PUT /nodes/{node_id}`**
    *   **설명:** 특정 노드의 정보를 업데이트합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "title": "string (optional)"
        }
        ```
    *   **응답 (200 OK):** 업데이트된 노드 정보
*   **`DELETE /nodes/{node_id}`**
    *   **설명:** 특정 노드를 삭제합니다. (하위 노드 및 연결된 콘텐츠/링크도 함께 삭제)
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (204 No Content)**
*   **`PUT /curriculums/{curriculum_id}/nodes/reorder`**
    *   **설명:** 커리큘럼 맵 내 노드들의 순서를 변경하거나 부모 노드를 변경합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "node_id": "uuid",
          "new_parent_id": "uuid (nullable)",
          "new_order_index": "int"
        }
        ```
    *   **응답 (200 OK):** 업데이트된 노드 목록
    *   **오류 처리:**
        *   `400 Bad Request`: 순환 참조 발생 시 또는 유효하지 않은 이동 시.

### 2.6. 노드 링크 관리 (Zotero, YouTube)

*   **`POST /nodes/{node_id}/links/zotero`**
    *   **설명:** Zotero 문헌을 노드에 연결합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "zotero_item_id": "uuid"
        }
        ```
    *   **응답 (201 Created):** 연결된 링크 정보
    *   **오류 처리:**
        *   `404 Not Found`: 노드를 찾을 수 없거나 Zotero 항목을 찾을 수 없는 경우.
*   **`POST /nodes/{node_id}/links/youtube`**
    *   **설명:** YouTube 영상을 노드에 연결합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **요청:**
        ```json
        {
          "youtube_url": "string (e.g., https://www.youtube.com/watch?v=dQw4w9WgXcQ)"
        }
        ```
    *   **응답 (201 Created):** 연결된 링크 정보 (YouTube 영상 메타데이터 포함)
    *   **오류 처리:**
        *   `404 Not Found`: 노드를 찾을 수 없는 경우.
        *   `400 Bad Request`: 유효하지 않은 YouTube URL인 경우.
        *   `500 Internal Server Error`: YouTube API 호출 중 외부 오류가 발생한 경우.
*   **`GET /nodes/{node_id}/links`**
    *   **설명:** 특정 노드에 연결된 모든 링크를 조회합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (200 OK):** 연결된 링크 목록
*   **`DELETE /nodes/{node_id}/links/{link_id}`**
    *   **설명:** 노드에 연결된 특정 링크를 삭제합니다.
    *   **요청 헤더:** `Authorization: Bearer <access_token>`
    *   **응답 (204 No Content)**
    *   **오류 처리:**
        *   `404 Not Found`: 노드 링크를 찾을 수 없는 경우.

## 3. 핵심 AI API (백엔드 ↔ Vertex AI)

백엔드는 Google Cloud Vertex AI SDK를 사용하여 Gemini 모델을 호출합니다. 다음은 주요 사용 사례에 대한 추상적인 명세입니다.

### 3.1. 이미지 기반 Manim 코드 가이드라인 생성

*   **서비스:** Vertex AI Gemini Pro Vision
*   **백엔드 호출:**
    *   **입력:** 이미지 파일 (Base64 인코딩 또는 Cloud Storage URL), 프롬프트 텍스트 (예: "이 이미지에 대한 Manim 코드 생성 가이드라인을 제공해줘.")
    *   **출력:** 생성된 텍스트 (Manim 코드 가이드라인)
*   **오류 처리:** API 호출 실패, 응답 시간 초과 시 적절한 오류 메시지 반환.

### 3.2. 노드 내용 기반 요약/확장/질의응답

*   **서비스:** Vertex AI Gemini Pro
*   **백엔드 호출:**
    *   **입력:** 노드 내용 텍스트, AI 요청 유형 (요약, 확장, 질의응답), 추가 질의 (질의응답 시)
    *   **출력:** AI가 생성한 텍스트 (요약, 확장된 내용, 답변)
*   **오류 처리:** API 호출 실패, 응답 시간 초과 시 적절한 오류 메시지 반환.

## 4. Zotero API (백엔드 ↔ 자체 호스팅 Zotero 서버)

백엔드는 자체 호스팅 Zotero 서버의 API 엔드포인트를 호출하여 문헌 정보를 관리합니다.

### 4.1. Zotero 문헌 검색 (태그 기반)

*   **`GET /zotero/items`**
    *   **설명:** 특정 태그가 붙은 Zotero 문헌 목록을 조회합니다.
    *   **쿼리 파라미터:** `tag={tag_name}` (필수)
    *   **응답 (200 OK):**
        ```json
        [
          {
            "zotero_key": "string",
            "title": "string",
            "authors": ["string"],
            "publication_year": 2023,
            "tags": ["string"],
            "item_type": "string",
            "abstract": "string (nullable)",
            "url": "string (nullable)"
          },
          ...
        ]
        ```
    *   **오류 처리:** 태그가 없거나 검색 결과가 없을 시 빈 배열 반환.

## 5. YouTube Data API (백엔드 ↔ YouTube)

백엔드는 YouTube Data API를 사용하여 영상 정보를 조회합니다.

### 5.1. YouTube 영상 정보 조회

*   **서비스:** YouTube Data API v3
*   **백엔드 호출:**
    *   **입력:** YouTube 영상 ID (URL에서 추출)
    *   **출력:** 영상 제목, 채널 제목, 설명, 썸네일 URL, 길이, 게시일 등 메타데이터
*   **오류 처리:** 유효하지 않은 영상 ID, API 호출 실패 시 오류 메시지 반환.

## 6. API 문서화 도구
*   **추천:** FastAPI는 자동으로 OpenAPI (Swagger UI) 문서를 생성하므로, 이를 활용하여 API 명세를 최신 상태로 유지합니다.
*   **위치:** `/docs` (FastAPI 기본 경로)
