# API Specification for MATHESIS LAB

This document outlines the API endpoints and their expected request/response schemas for the MATHESIS LAB application.

---

## 1. Curriculums API

**Base URL:** `/api/v1/curriculums`

### 1.1. Get All Curriculums

-   **Endpoint:** `GET /`
-   **Description:** Retrieves a list of all available curriculums.
-   **Response:** `List[CurriculumResponse]`

### 1.2. Create Curriculum

-   **Endpoint:** `POST /`
-   **Description:** Creates a new curriculum.
-   **Request Body:** `CurriculumCreate`
-   **Response:** `CurriculumResponse` (HTTP 201 Created)

### 1.3. Get Single Curriculum

-   **Endpoint:** `GET /{curriculum_id}`
-   **Description:** Retrieves details of a specific curriculum, including its associated nodes.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the curriculum.
-   **Response:** `CurriculumResponse`

### 1.4. Update Curriculum

-   **Endpoint:** `PUT /{curriculum_id}`
-   **Description:** Updates an existing curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the curriculum.
-   **Request Body:** `CurriculumUpdate`
-   **Response:** `CurriculumResponse`

### 1.5. Delete Curriculum

-   **Endpoint:** `DELETE /{curriculum_id}`
-   **Description:** Deletes a specific curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the curriculum.
-   **Response:** Empty (HTTP 204 No Content)

---

## 2. Nodes API (Nested under Curriculums)

**Base URL:** `/api/v1/curriculums/{curriculum_id}/nodes`

### 2.1. Create Node for Curriculum

-   **Endpoint:** `POST /`
-   **Description:** Creates a new node within a specific curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
-   **Request Body:** `NodeCreate`
-   **Response:** `NodeResponse` (HTTP 201 Created)

### 2.2. Get Single Node

-   **Endpoint:** `GET /{node_id}`
-   **Description:** Retrieves details of a specific node within a curriculum, including its content and linked resources.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Response:** `NodeResponse`

### 2.3. Update Node

-   **Endpoint:** `PUT /{node_id}`
-   **Description:** Updates an existing node within a curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `NodeUpdate`
-   **Response:** `NodeResponse`

### 2.4. Delete Node

-   **Endpoint:** `DELETE /{node_id}`
-   **Description:** Deletes a specific node within a curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Response:** Empty (HTTP 204 No Content)

### 2.5. Reorder Nodes

-   **Endpoint:** `PUT /reorder`
-   **Description:** Reorders nodes within a curriculum.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the curriculum.
-   **Request Body:** `List[NodeReorder]`
-   **Response:** `List[NodeResponse]`

---

## 3. Node Content API (Nested under Nodes)

**Base URL:** `/api/v1/curriculums/{curriculum_id}/nodes/{node_id}/content`

### 3.1. Get Node Content

-   **Endpoint:** `GET /`
-   **Description:** Retrieves the content of a specific node.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Response:** `NodeContentResponse`

### 3.2. Update Node Content

-   **Endpoint:** `PUT /`
-   **Description:** Updates the content of a specific node.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `NodeContentUpdate`
-   **Response:** `NodeContentResponse`

### 3.3. Summarize Node Content (AI)

-   **Endpoint:** `POST /summarize`
-   **Description:** Generates an AI summary of the node's content.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Response:** `NodeContentResponse`

### 3.4. Extend Node Content (AI)

-   **Endpoint:** `POST /extend`
-   **Description:** Extends the node's content using AI.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `NodeContentExtendRequest` (optional `prompt` field)
-   **Response:** `NodeContentResponse`

### 3.5. Generate Manim Guidelines (AI)

-   **Endpoint:** `POST /manim-guidelines`
-   **Description:** Generates Manim animation guidelines for the node's content using AI.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `ManimGuidelinesRequest` (optional `prompt` and `image_bytes` fields)
-   **Response:** `NodeContentResponse`

---

## 4. Node Links API (Nested under Nodes)

**Base URL:** `/api/v1/curriculums/{curriculum_id}/nodes/{node_id}/links`

### 4.1. Get Node Links

-   **Endpoint:** `GET /`
-   **Description:** Retrieves all linked resources for a specific node.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Response:** `List[NodeLinkResponse]`

### 4.2. Create Zotero Link

-   **Endpoint:** `POST /zotero`
-   **Description:** Links a Zotero item to a node.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `NodeLinkZoteroCreate`
-   **Response:** `NodeLinkResponse` (HTTP 201 Created)

### 4.3. Create YouTube Link

-   **Endpoint:** `POST /youtube`
-   **Description:** Links a YouTube video to a node.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
-   **Request Body:** `NodeLinkYouTubeCreate`
-   **Response:** `NodeLinkResponse` (HTTP 201 Created)

### 4.4. Delete Node Link

-   **Endpoint:** `DELETE /{link_id}`
-   **Description:** Deletes a specific node link.
-   **Path Parameters:**
    -   `curriculum_id` (UUID): The unique identifier of the parent curriculum.
    -   `node_id` (UUID): The unique identifier of the node.
    -   `link_id` (UUID): The unique identifier of the link to delete.
-   **Response:** Empty (HTTP 204 No Content)

---

## 5. Schemas (Updated)

### 5.1. Curriculum Schemas (No Change)

#### `CurriculumBase`
-   `title` (str): Curriculum title (min_length=1, max_length=255)
-   `description` (Optional[str]): Curriculum description
-   `is_public` (Optional[bool]): Whether the curriculum is public (default: False)

#### `CurriculumCreate` (inherits from `CurriculumBase`)

#### `CurriculumUpdate`
-   `title` (Optional[str]): Curriculum title (min_length=1, max_length=255)
-   `description` (Optional[str]): Curriculum description
-   `is_public` (Optional[bool]): Whether the curriculum is public

#### `CurriculumResponse` (inherits from `CurriculumBase`)
-   `curriculum_id` (UUID): Unique identifier for the curriculum
-   `is_public` (bool): Whether the curriculum is public
-   `created_at` (datetime): Timestamp of creation
-   `updated_at` (datetime): Timestamp of last update
-   `nodes` (List[`NodeResponse`]): List of associated nodes

### 5.2. Node Schemas (Updated)

#### `NodeBase`
-   `title` (str): Node title (min_length=1, max_length=255)
-   `parent_node_id` (Optional[UUID]): Parent node ID (NULL for top-level nodes)

#### `NodeCreate` (inherits from `NodeBase`)

#### `NodeUpdate`
-   `title` (Optional[str]): Node title (min_length=1, max_length=255)
-   `parent_node_id` (Optional[UUID]): Parent node ID

#### `NodeResponse` (inherits from `NodeBase`)
-   `node_id` (UUID): Unique identifier for the node
-   `curriculum_id` (UUID): ID of the parent curriculum
-   `order_index` (int): Order of the node within the curriculum
-   `created_at` (datetime): Timestamp of creation
-   `updated_at` (datetime): Timestamp of last update
-   `content` (Optional[`NodeContentResponse`]): Associated node content
-   `links` (List[`NodeLinkResponse`]): List of associated node links

#### `NodeReorder`
-   `node_id` (UUID): ID of the node to reorder
-   `new_parent_id` (Optional[UUID]): New parent node ID (NULL for top-level)
-   `new_order_index` (int): New order index

#### `NodeContentResponse`
-   `content_id` (UUID): Unique identifier for the node content
-   `node_id` (UUID): ID of the associated node
-   `markdown_content` (Optional[str]): Markdown content of the node
-   `ai_generated_summary` (Optional[str]): AI-generated summary
-   `ai_generated_extension` (Optional[str]): AI-generated extension
-   `manim_guidelines` (Optional[str]): AI-generated Manim guidelines
-   `created_at` (datetime): Timestamp of creation
-   `updated_at` (datetime): Timestamp of last update

#### `NodeContentExtendRequest`
-   `prompt` (Optional[str]): Specific instructions for AI content extension

#### `ManimGuidelinesRequest`
-   `prompt` (Optional[str]): Specific instructions for AI Manim guidelines
-   `image_bytes` (Optional[bytes]): Image data for Manim guidelines generation

#### `NodeLinkResponse`
-   `link_id` (UUID): Unique identifier for the link
-   `node_id` (UUID): ID of the associated node
-   `link_type` (str): Type of link (e.g., "ZOTERO", "YOUTUBE")
-   `zotero_item_id` (Optional[UUID]): ID of the linked Zotero item
-   `youtube_video_id` (Optional[UUID]): ID of the linked YouTube video
-   `created_at` (datetime): Timestamp of creation

#### `NodeLinkZoteroCreate`
-   `zotero_item_id` (UUID): ID of the Zotero item to link

#### `NodeLinkYouTubeCreate`
-   `youtube_url` (str): URL of the YouTube video to link

---

## 6. Error Handling (NEW - Error Handling Architecture)

### 6.1. Error Handling Principles

All APIs follow a **defensive programming** approach where:

1. **Service Layer**: Returns `None` or `False` for validation failures (no exceptions)
2. **Endpoint Layer**: Catches exceptions and converts them to proper HTTP responses
3. **No Error Suppression**: All errors are either explicitly handled or propagated

### 6.2. Standard HTTP Status Codes

| Status Code | Scenario | Example |
|-------------|----------|---------|
| `200 OK` | Successful GET/PUT request | Retrieve curriculum successfully |
| `201 Created` | Successful POST request | Create new node |
| `204 No Content` | Successful DELETE request | Delete curriculum |
| `400 Bad Request` | Invalid input or validation error | Invalid YouTube URL, circular dependency |
| `401 Unauthorized` | Authentication failure | Invalid or expired token |
| `404 Not Found` | Resource not found | Node doesn't exist in curriculum |
| `409 Conflict` | Business logic conflict | Create content when it already exists |
| `500 Internal Server Error` | Server-side error | AI service failure, database error |

### 6.3. Error Response Format

All error responses follow this format:

```json
{
  "detail": "Human-readable error message",
  "status_code": 400,
  "type": "HTTP_400_BAD_REQUEST"
}
```

### 6.4. Common Error Scenarios

#### Resource Not Found (404)
```json
{
  "detail": "Node not found",
  "status_code": 404
}
```

#### Validation Error (400)
```json
{
  "detail": "Invalid YouTube URL",
  "status_code": 400
}
```

#### Circular Dependency (409)
```json
{
  "detail": "Circular dependency detected in node hierarchy",
  "status_code": 409
}
```

#### Authentication Failure (401)
```json
{
  "detail": "Token verification failed: invalid token",
  "status_code": 401
}
```

#### Server Error (500)
```json
{
  "detail": "AI summarization failed: service unavailable",
  "status_code": 500
}
```

### 6.5. Error Propagation Strategy

**Frontend Implementation:**

When implementing frontend services, follow this pattern:

```typescript
async function createNode(curriculumId: string, data: NodeCreate) {
  const response = await fetch(`/api/v1/curriculums/${curriculumId}/nodes`, {
    method: 'POST',
    body: JSON.stringify(data)
  });

  // Always check status
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || 'Failed to create node');
  }

  return response.json();
}
```

**Key Points:**
- ❌ Never suppress errors with empty `catch` blocks
- ✅ Always `throw` errors to propagate to UI error handlers
- ✅ Use HTTP status codes to determine error type
- ✅ Display `error.detail` to users for context

### 6.6. Specific API Error Conditions

#### Node Operations

| Endpoint | Condition | Status | Error Message |
|----------|-----------|--------|----------------|
| `POST /curriculums/{id}/nodes` | Curriculum not found | 404 | "Curriculum not found" |
| `PUT /curriculums/{id}/nodes/{nodeId}` | Node not found | 404 | "Node not found" |
| `PUT /curriculums/{id}/nodes/reorder` | Circular dependency | 409 | "Circular dependency detected" |
| `PUT /curriculums/{id}/nodes/{nodeId}` | Reorder fails | 400 | "Failed to reorder nodes" |

#### Node Content Operations

| Endpoint | Condition | Status | Error Message |
|----------|-----------|--------|----------------|
| `PUT /curriculums/{id}/nodes/{nodeId}/content` | Content not found | 404 | "Node content not found" |
| `POST /curriculums/{id}/nodes/{nodeId}/content/summarize` | AI service error | 500 | "AI summarization failed: {service error}" |
| `POST /curriculums/{id}/nodes/{nodeId}/content/extend` | AI service error | 500 | "AI extension failed: {service error}" |

#### Node Links Operations

| Endpoint | Condition | Status | Error Message |
|----------|-----------|--------|----------------|
| `POST /curriculums/{id}/nodes/{nodeId}/links/youtube` | Invalid YouTube URL | 404 | "Invalid YouTube URL" |
| `POST /curriculums/{id}/nodes/{nodeId}/links/zotero` | Zotero API not configured | 404 | "Zotero API base URL is not configured" |
| `DELETE /curriculums/{id}/nodes/{nodeId}/links/{linkId}` | Link not found | 404 | "Node link not found" |

#### Authentication Operations

| Endpoint | Condition | Status | Error Message |
|----------|-----------|--------|----------------|
| `POST /auth/verify-token` | Invalid token | 400 | "Token verification failed: invalid token" |
| `POST /auth/google/callback` | Token exchange failed | 401 | "Token exchange failed" |
| `POST /auth/verify-token` | Invalid audience | 400 | "Token audience does not match client ID" |