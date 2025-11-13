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

---

## 3. Schemas

### 3.1. Curriculum Schemas

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

### 3.2. Node Schemas

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

#### `NodeContentResponse`
-   `content_id` (UUID): Unique identifier for the node content
-   `node_id` (UUID): ID of the associated node
-   `markdown_content` (Optional[str]): Markdown content of the node
-   `ai_generated_summary` (Optional[str]): AI-generated summary
-   `ai_generated_extension` (Optional[str]): AI-generated extension
-   `manim_guidelines` (Optional[str]): AI-generated Manim guidelines
-   `created_at` (datetime): Timestamp of creation
-   `updated_at` (datetime): Timestamp of last update

#### `NodeLinkResponse`
-   `link_id` (UUID): Unique identifier for the link
-   `node_id` (UUID): ID of the associated node
-   `link_type` (str): Type of link (e.g., "ZOTERO", "YOUTUBE")
-   `zotero_item_id` (Optional[UUID]): ID of the linked Zotero item
-   `youtube_video_id` (Optional[UUID]): ID of the linked YouTube video
-   `created_at` (datetime): Timestamp of creation
