# Software Design Document: Node Management System

## 1. Introduction

### 1.1 Purpose
This document defines the comprehensive design for the Node Management System in MATHESIS LAB, which enables users to create, organize, and manage learning content within curriculum maps.

### 1.2 Scope
- Node CRUD operations
- Content management (Markdown, AI enhancements)
- External resource linking (YouTube, Zotero)
- Node hierarchy and organization
- UI/UX for node editing and navigation

### 1.3 Target Audience
- Full-stack developers
- Frontend developers
- Backend developers
- QA engineers
- UX/UI designers

---

## 2. System Architecture

### 2.1 High-Level Architecture

```
┌────────────────────────────────────────────────────────────────┐
│                     Frontend (React)                            │
│                                                                  │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ CurriculumDetail Page                                   │   │
│  │                                                          │   │
│  │ ┌──────────────────┐    ┌──────────────────────────┐   │   │
│  │ │  NodeList        │    │  NodeEditor              │   │   │
│  │ │  (Hierarchy View)├───►│  (Edit Selected Node)    │   │   │
│  │ │                  │    │  ┌────────────────────┐  │   │   │
│  │ │ ┌─Node 1        │    │  │ Properties Panel   │  │   │   │
│  │ │ ├─Node 1.1      │    │  │ Content Editor     │  │   │   │
│  │ │ ├─Node 1.2      │    │  │ Link Manager       │  │   │   │
│  │ │ └─Node 1.3      │    │  │ AI Assistant       │  │   │   │
│  │ │                  │    │  └────────────────────┘  │   │   │
│  │ └──────────────────┘    └──────────────────────────┘   │   │
│  └─────────────────────────────────────────────────────────┘   │
└──────────────┬─────────────────────────────────────────────────┘
               │
        ┌──────▼──────────┐
        │  Node Service   │
        │  (API Client)   │
        └──────┬──────────┘
               │
    ┌──────────┼────────────┐
    │          │            │
┌───▼──┐  ┌───▼──┐  ┌──────▼──┐
│ CRUD │  │Content│  │ Links   │
│ API  │  │API    │  │API      │
└───┬──┘  └───┬──┘  └───┬─────┘
    │         │         │
    └─────────┼─────────┘
              │
    ┌─────────▼──────────────┐
    │  FastAPI Backend       │
    │                        │
    │ ┌────────────────────┐ │
    │ │ Node Service       │ │
    │ │ (Business Logic)   │ │
    │ └────────────────────┘ │
    │                        │
    │ ┌────────────────────┐ │
    │ │ Database Layer     │ │
    │ │ (SQLAlchemy ORM)   │ │
    │ └────────────────────┘ │
    └────────────┬───────────┘
                 │
        ┌────────▼───────────┐
        │  SQLite Database   │
        │                    │
        │ ├─ nodes           │
        │ ├─ node_contents   │
        │ └─ node_links      │
        └────────────────────┘
```

### 2.2 Component Architecture

**Backend Components:**
```
NodeService (business logic)
├── Node Operations
│   ├── create_node()
│   ├── get_node()
│   ├── update_node()
│   ├── delete_node()
│   └── get_node_children()
├── Content Operations
│   ├── get_content()
│   ├── update_content()
│   └── generate_content_preview()
├── Link Operations
│   ├── add_link()
│   ├── get_links()
│   └── delete_link()
└── Hierarchy Operations
    ├── reorder_nodes()
    ├── move_node()
    └── validate_hierarchy()

NodeRepository (data access)
├── Node Repository
│   ├── create()
│   ├── read()
│   ├── update()
│   ├── delete()
│   └── query()
├── Content Repository
│   ├── create()
│   ├── read()
│   └── update()
└── Link Repository
    ├── create()
    ├── read()
    └── delete()
```

**Frontend Components:**
```
CurriculumDetail (page)
├── NodeList (component)
│   ├── NodeItem (sub-component)
│   │   ├── NodeTitle
│   │   ├── NodeActions (edit, delete)
│   │   └── ToggleChildren
│   └── AddNodeButton
├── NodeEditor (component)
│   ├── NodeProperties
│   │   ├── TitleInput
│   │   └── OrderSelector
│   ├── ContentEditor
│   │   ├── MarkdownEditor
│   │   └── MarkdownPreview
│   ├── LinkManager
│   │   ├── LinkList
│   │   ├── AddLinkModal
│   │   └── DeleteLinkButton
│   └── AIAssistant
│       ├── SummarizeButton
│       ├── ExpandButton
│       └── ManimGuidelinesButton
└── NodeActions
    ├── SaveButton
    ├── DeleteButton
    └── DuplicateButton
```

---

## 3. Data Model

### 3.1 Entity Relationship Diagram

```
┌──────────────────────┐
│   Curriculum         │
│                      │
│ ├─ curriculum_id (PK)│
│ ├─ title             │
│ ├─ description       │
│ └─ created_at        │
└───────────┬──────────┘
            │ 1
            │
            │ N
    ┌───────▼────────────────────────┐
    │   Node                          │
    │                                 │
    │ ├─ node_id (PK)                 │
    │ ├─ curriculum_id (FK)           │
    │ ├─ parent_node_id (FK - Self)   │
    │ ├─ title                        │
    │ ├─ order_index                  │
    │ └─ created_at                   │
    └───────┬────────────────────────┬┘
            │ 1                    1 │
            │                        │
            │                   ┌────▼──────────────────┐
            │                   │   NodeContent         │
            │                   │                       │
            │                   │ ├─ content_id (PK)    │
            │                   │ ├─ node_id (FK)       │
            │                   │ ├─ markdown_content   │
            │                   │ ├─ ai_summary         │
            │                   │ ├─ ai_extension       │
            │                   │ ├─ manim_guidelines   │
            │                   │ └─ updated_at         │
            │                   └───────────────────────┘
            │
    ┌───────▼─────────────────────┐
    │   NodeLink                   │
    │                              │
    │ ├─ link_id (PK)              │
    │ ├─ node_id (FK)              │
    │ ├─ link_type (enum)          │
    │ ├─ youtube_video_id          │
    │ ├─ zotero_item_id            │
    │ ├─ external_url              │
    │ └─ created_at                │
    └──────────────────────────────┘
```

### 3.2 State Diagram

**Node Lifecycle:**
```
┌─────────┐
│ CREATED │  (node_id assigned, default properties set)
└────┬────┘
     │
     ▼
┌─────────────┐
│ INITIALIZED │  (properties validated, ready for editing)
└────┬────────┘
     │
     ├──────────────────────────────────┐
     │                                  │
     ▼                                  ▼
┌──────────────┐                ┌──────────────┐
│ WITH_CONTENT │                │ WITH_LINKS   │
│ (content     │                │ (resources   │
│ added)       │◄──────────────►│ linked)      │
└──────────────┘                └──────────────┘
     │                                  │
     │            ┌─────────────────────┘
     │            │
     ▼            ▼
┌──────────────────────────┐
│ READY_FOR_PUBLISHING     │
│ (complete, publishable)  │
└────┬─────────────────────┘
     │
     ├──────────────┬──────────────────┐
     │              │                  │
     ▼              ▼                  ▼
┌────────┐   ┌────────┐          ┌────────────┐
│ EDITED │   │ARCHIVED│          │ DELETED    │
│(modified)  │(hidden)│          │(soft delete)
└────────┘   └────────┘          └────────────┘
```

---

## 4. API Specifications

### 4.1 Node CRUD Endpoints

#### 4.1.1 Create Node

**Endpoint:** `POST /api/v1/curriculums/{curriculum_id}/nodes`

**Request:**
```json
{
    "title": "Introduction to Derivatives",
    "parent_node_id": null,
    "order_index": 0
}
```

**Response:**
```json
{
    "node_id": "550e8400-e29b-41d4-a716-446655440000",
    "curriculum_id": "660e8400-e29b-41d4-a716-446655440001",
    "parent_node_id": null,
    "title": "Introduction to Derivatives",
    "order_index": 0,
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-11-15T10:00:00Z"
}
```

**Validation Rules:**
- `title` required, max 255 chars
- `curriculum_id` must exist
- `parent_node_id` must exist if provided
- `order_index` auto-generated if not provided

**Test Cases:**
```python
# test_create_node.py

def test_create_node_success():
    """Test successful node creation"""
    response = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={"title": "Test Node"}
    )
    assert response.status_code == 201
    assert response.json()["title"] == "Test Node"

def test_create_node_missing_title():
    """Test node creation without title"""
    response = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={}
    )
    assert response.status_code == 422  # Validation error

def test_create_node_invalid_curriculum():
    """Test node creation with non-existent curriculum"""
    response = client.post(
        "/api/v1/curriculums/invalid-id/nodes",
        json={"title": "Test Node"}
    )
    assert response.status_code == 404

def test_create_node_with_parent():
    """Test creating child node"""
    response = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={
            "title": "Child Node",
            "parent_node_id": parent_node_id
        }
    )
    assert response.status_code == 201
    assert response.json()["parent_node_id"] == parent_node_id

def test_create_node_invalid_parent():
    """Test creating node with non-existent parent"""
    response = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={
            "title": "Child Node",
            "parent_node_id": "invalid-parent-id"
        }
    )
    assert response.status_code == 404
```

#### 4.1.2 Get Node

**Endpoint:** `GET /api/v1/nodes/{node_id}`

**Response:**
```json
{
    "node_id": "550e8400-e29b-41d4-a716-446655440000",
    "curriculum_id": "660e8400-e29b-41d4-a716-446655440001",
    "parent_node_id": null,
    "title": "Introduction to Derivatives",
    "order_index": 0,
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-11-15T10:00:00Z",
    "content": {
        "content_id": "770e8400-e29b-41d4-a716-446655440002",
        "markdown_content": "## Introduction\n\nDerivatives measure...",
        "ai_summary": "Derivatives are...",
        "ai_extension": "Extended explanation...",
        "manim_guidelines": "Animation guide..."
    },
    "links": [
        {
            "link_id": "880e8400-e29b-41d4-a716-446655440003",
            "link_type": "YOUTUBE",
            "youtube_video_id": "dQw4w9WgXcQ"
        }
    ],
    "children": [
        {
            "node_id": "990e8400-e29b-41d4-a716-446655440004",
            "title": "Child Node 1"
        }
    ]
}
```

**Test Cases:**
```python
def test_get_node_success():
    """Test successful node retrieval"""
    response = client.get(f"/api/v1/nodes/{node_id}")
    assert response.status_code == 200
    assert response.json()["node_id"] == node_id

def test_get_node_not_found():
    """Test getting non-existent node"""
    response = client.get("/api/v1/nodes/invalid-id")
    assert response.status_code == 404

def test_get_node_includes_content():
    """Test node retrieval includes content"""
    response = client.get(f"/api/v1/nodes/{node_id}")
    assert "content" in response.json()

def test_get_node_includes_links():
    """Test node retrieval includes links"""
    response = client.get(f"/api/v1/nodes/{node_id}")
    assert "links" in response.json()

def test_get_node_includes_children():
    """Test node retrieval includes child nodes"""
    response = client.get(f"/api/v1/nodes/{node_id}")
    assert "children" in response.json()
```

#### 4.1.3 Update Node

**Endpoint:** `PUT /api/v1/nodes/{node_id}`

**Request:**
```json
{
    "title": "Updated Title",
    "order_index": 1
}
```

**Response:**
```json
{
    "node_id": "550e8400-e29b-41d4-a716-446655440000",
    "title": "Updated Title",
    "order_index": 1,
    "updated_at": "2025-11-15T11:00:00Z"
}
```

**Validation Rules:**
- `title` optional, max 255 chars
- `order_index` optional, must be non-negative
- Cannot change `curriculum_id` or `parent_node_id`

**Test Cases:**
```python
def test_update_node_title():
    """Test updating node title"""
    response = client.put(
        f"/api/v1/nodes/{node_id}",
        json={"title": "New Title"}
    )
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"

def test_update_node_order():
    """Test updating node order"""
    response = client.put(
        f"/api/v1/nodes/{node_id}",
        json={"order_index": 2}
    )
    assert response.status_code == 200
    assert response.json()["order_index"] == 2

def test_update_node_both_fields():
    """Test updating multiple fields"""
    response = client.put(
        f"/api/v1/nodes/{node_id}",
        json={"title": "New Title", "order_index": 1}
    )
    assert response.status_code == 200

def test_update_node_invalid_title():
    """Test updating with invalid title"""
    response = client.put(
        f"/api/v1/nodes/{node_id}",
        json={"title": "a" * 256}  # Too long
    )
    assert response.status_code == 422

def test_update_node_not_found():
    """Test updating non-existent node"""
    response = client.put(
        "/api/v1/nodes/invalid-id",
        json={"title": "New Title"}
    )
    assert response.status_code == 404
```

#### 4.1.4 Delete Node

**Endpoint:** `DELETE /api/v1/nodes/{node_id}`

**Response:**
```json
{
    "success": true,
    "message": "Node deleted successfully",
    "deleted_node_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

**Cascade Behavior:**
- Delete associated content
- Delete associated links
- Delete child nodes (soft delete)
- Update parent's children count

**Test Cases:**
```python
def test_delete_node_success():
    """Test successful node deletion"""
    response = client.delete(f"/api/v1/nodes/{node_id}")
    assert response.status_code == 200

def test_delete_node_cascades_content():
    """Test that deleting node deletes content"""
    response = client.delete(f"/api/v1/nodes/{node_id}")
    assert response.status_code == 200

    # Verify content is deleted
    content_response = client.get(f"/api/v1/nodes/{node_id}/content")
    assert content_response.status_code == 404

def test_delete_node_cascades_links():
    """Test that deleting node deletes links"""
    response = client.delete(f"/api/v1/nodes/{node_id}")
    assert response.status_code == 200

    # Verify links are deleted
    links_response = client.get(f"/api/v1/nodes/{node_id}/links")
    assert links_response.status_code == 404

def test_delete_node_cascades_children():
    """Test that deleting parent soft-deletes children"""
    response = client.delete(f"/api/v1/nodes/{parent_node_id}")
    assert response.status_code == 200

    # Verify children are soft-deleted
    child_response = client.get(f"/api/v1/nodes/{child_node_id}")
    assert child_response.json()["is_deleted"] == True

def test_delete_node_not_found():
    """Test deleting non-existent node"""
    response = client.delete("/api/v1/nodes/invalid-id")
    assert response.status_code == 404
```

### 4.2 Content Management Endpoints

#### 4.2.1 Create/Update Content

**Endpoint:** `POST /api/v1/nodes/{node_id}/content`

**Request:**
```json
{
    "markdown_content": "## Introduction\n\nThis is the content..."
}
```

**Response:**
```json
{
    "content_id": "770e8400-e29b-41d4-a716-446655440002",
    "node_id": "550e8400-e29b-41d4-a716-446655440000",
    "markdown_content": "## Introduction\n\nThis is the content...",
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-11-15T10:00:00Z"
}
```

**Test Cases:**
```python
def test_create_content():
    """Test creating content for node"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/content",
        json={"markdown_content": "# Test Content"}
    )
    assert response.status_code == 201

def test_update_content():
    """Test updating existing content"""
    # Create first
    client.post(
        f"/api/v1/nodes/{node_id}/content",
        json={"markdown_content": "Old content"}
    )
    # Update
    response = client.post(
        f"/api/v1/nodes/{node_id}/content",
        json={"markdown_content": "New content"}
    )
    assert response.status_code == 200
    assert response.json()["markdown_content"] == "New content"

def test_markdown_validation():
    """Test markdown content validation"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/content",
        json={"markdown_content": "# Valid Markdown\n\nWith **bold** text"}
    )
    assert response.status_code == 201

def test_content_empty_allowed():
    """Test that empty content is allowed"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/content",
        json={"markdown_content": ""}
    )
    assert response.status_code == 201
```

#### 4.2.2 Get Content

**Endpoint:** `GET /api/v1/nodes/{node_id}/content`

**Response:**
```json
{
    "content_id": "770e8400-e29b-41d4-a716-446655440002",
    "node_id": "550e8400-e29b-41d4-a716-446655440000",
    "markdown_content": "## Introduction\n\nThis is the content...",
    "ai_summary": "Generated summary...",
    "ai_extension": "Generated extension...",
    "manim_guidelines": "Animation guidelines...",
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-11-15T10:00:00Z"
}
```

**Test Cases:**
```python
def test_get_content():
    """Test retrieving node content"""
    response = client.get(f"/api/v1/nodes/{node_id}/content")
    assert response.status_code == 200

def test_get_content_not_found():
    """Test getting content for node without content"""
    response = client.get(f"/api/v1/nodes/{node_without_content_id}/content")
    assert response.status_code == 404
```

### 4.3 Link Management Endpoints

#### 4.3.1 Add Link

**Endpoint:** `POST /api/v1/nodes/{node_id}/links/{link_type}`

**YouTube Link:**
```json
{
    "youtube_video_id": "dQw4w9WgXcQ"
}
```

**Zotero Link:**
```json
{
    "zotero_item_id": "item-123"
}
```

**External Link:**
```json
{
    "external_url": "https://example.com"
}
```

**Test Cases:**
```python
def test_add_youtube_link():
    """Test adding YouTube link"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/links/youtube",
        json={"youtube_video_id": "dQw4w9WgXcQ"}
    )
    assert response.status_code == 201

def test_add_zotero_link():
    """Test adding Zotero link"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/links/zotero",
        json={"zotero_item_id": "item-123"}
    )
    assert response.status_code == 201

def test_add_external_link():
    """Test adding external link"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/links/external",
        json={"external_url": "https://example.com"}
    )
    assert response.status_code == 201

def test_youtube_id_validation():
    """Test YouTube ID validation"""
    response = client.post(
        f"/api/v1/nodes/{node_id}/links/youtube",
        json={"youtube_video_id": "invalid"}
    )
    assert response.status_code == 422

def test_duplicate_youtube_link():
    """Test preventing duplicate YouTube links"""
    # Add first link
    client.post(
        f"/api/v1/nodes/{node_id}/links/youtube",
        json={"youtube_video_id": "dQw4w9WgXcQ"}
    )
    # Try to add same link again
    response = client.post(
        f"/api/v1/nodes/{node_id}/links/youtube",
        json={"youtube_video_id": "dQw4w9WgXcQ"}
    )
    assert response.status_code == 409  # Conflict
```

#### 4.3.2 Get Links

**Endpoint:** `GET /api/v1/nodes/{node_id}/links`

**Response:**
```json
[
    {
        "link_id": "880e8400-e29b-41d4-a716-446655440003",
        "node_id": "550e8400-e29b-41d4-a716-446655440000",
        "link_type": "YOUTUBE",
        "youtube_video_id": "dQw4w9WgXcQ",
        "created_at": "2025-11-15T10:00:00Z"
    },
    {
        "link_id": "990e8400-e29b-41d4-a716-446655440004",
        "node_id": "550e8400-e29b-41d4-a716-446655440000",
        "link_type": "ZOTERO",
        "zotero_item_id": "item-123",
        "created_at": "2025-11-15T10:01:00Z"
    }
]
```

#### 4.3.3 Delete Link

**Endpoint:** `DELETE /api/v1/nodes/{node_id}/links/{link_id}`

**Test Cases:**
```python
def test_delete_link():
    """Test deleting a link"""
    response = client.delete(
        f"/api/v1/nodes/{node_id}/links/{link_id}"
    )
    assert response.status_code == 200

def test_delete_link_not_found():
    """Test deleting non-existent link"""
    response = client.delete(
        f"/api/v1/nodes/{node_id}/links/invalid-link-id"
    )
    assert response.status_code == 404
```

### 4.4 Hierarchy Endpoints

#### 4.4.1 Get Node Children

**Endpoint:** `GET /api/v1/nodes/{node_id}/children`

**Response:**
```json
[
    {
        "node_id": "990e8400-e29b-41d4-a716-446655440004",
        "title": "Child Node 1",
        "order_index": 0
    },
    {
        "node_id": "a00e8400-e29b-41d4-a716-446655440005",
        "title": "Child Node 2",
        "order_index": 1
    }
]
```

#### 4.4.2 Reorder Nodes

**Endpoint:** `POST /api/v1/nodes/reorder`

**Request:**
```json
{
    "node_orders": [
        {"node_id": "node-1", "order_index": 0},
        {"node_id": "node-2", "order_index": 1},
        {"node_id": "node-3", "order_index": 2}
    ]
}
```

---

## 5. Implementation Details

### 5.1 Backend Service Implementation

**File:** `backend/app/services/node_service.py`

```python
from typing import List, Optional, Dict, Any
from sqlalchemy.orm import Session
from app.models import Node, NodeContent, NodeLink, Curriculum
from app.schemas import NodeCreate, NodeUpdate, ContentCreate, LinkCreate

class NodeService:
    def __init__(self, db: Session):
        self.db = db

    # ==================== CRUD Operations ====================

    def create_node(
        self,
        curriculum_id: str,
        title: str,
        parent_node_id: Optional[str] = None
    ) -> Node:
        """
        Create new node

        Algorithm:
        1. Validate curriculum exists
        2. Validate parent exists if provided
        3. Calculate order_index
        4. Create and save node
        5. Create empty content
        """
        curriculum = self.db.query(Curriculum).filter_by(id=curriculum_id).first()
        if not curriculum:
            raise ValueError(f"Curriculum {curriculum_id} not found")

        if parent_node_id:
            parent = self.db.query(Node).filter_by(id=parent_node_id).first()
            if not parent:
                raise ValueError(f"Parent node {parent_node_id} not found")

        # Calculate order_index
        last_sibling = self.db.query(Node).filter_by(
            parent_node_id=parent_node_id
        ).order_by(Node.order_index.desc()).first()

        order_index = (last_sibling.order_index + 1) if last_sibling else 0

        # Create node
        node = Node(
            node_id=generate_uuid(),
            curriculum_id=curriculum_id,
            parent_node_id=parent_node_id,
            title=title,
            order_index=order_index
        )

        self.db.add(node)

        # Create empty content
        content = NodeContent(
            content_id=generate_uuid(),
            node_id=node.node_id,
            markdown_content=""
        )
        self.db.add(content)

        self.db.commit()
        return node

    def get_node(self, node_id: str) -> Optional[Node]:
        """Get node with all related data"""
        return self.db.query(Node).filter_by(id=node_id).first()

    def update_node(self, node_id: str, data: Dict[str, Any]) -> Node:
        """Update node properties"""
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        if "title" in data:
            node.title = data["title"]
        if "order_index" in data:
            node.order_index = data["order_index"]

        self.db.commit()
        return node

    def delete_node(self, node_id: str) -> bool:
        """
        Delete node and cascade

        Algorithm:
        1. Find node
        2. Delete content
        3. Delete links
        4. Soft delete children
        5. Delete node
        """
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Delete content
        content = self.db.query(NodeContent).filter_by(node_id=node_id).first()
        if content:
            self.db.delete(content)

        # Delete links
        links = self.db.query(NodeLink).filter_by(node_id=node_id).all()
        for link in links:
            self.db.delete(link)

        # Soft delete children
        children = self.db.query(Node).filter_by(parent_node_id=node_id).all()
        for child in children:
            child.is_deleted = True

        # Delete node
        self.db.delete(node)
        self.db.commit()

        return True

    # ==================== Content Operations ====================

    def get_content(self, node_id: str) -> Optional[NodeContent]:
        """Get node content"""
        return self.db.query(NodeContent).filter_by(node_id=node_id).first()

    def update_content(self, node_id: str, markdown_content: str) -> NodeContent:
        """Update node content"""
        content = self.get_content(node_id)
        if not content:
            # Create new content
            content = NodeContent(
                content_id=generate_uuid(),
                node_id=node_id,
                markdown_content=markdown_content
            )
            self.db.add(content)
        else:
            content.markdown_content = markdown_content

        self.db.commit()
        return content

    # ==================== Link Operations ====================

    def add_link(
        self,
        node_id: str,
        link_type: str,
        **kwargs
    ) -> NodeLink:
        """Add external link to node"""
        node = self.get_node(node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        # Check for duplicates
        existing_link = self.db.query(NodeLink).filter_by(
            node_id=node_id,
            link_type=link_type
        )

        if link_type == "YOUTUBE":
            youtube_id = kwargs.get('youtube_video_id')
            existing_link = existing_link.filter_by(youtube_video_id=youtube_id).first()
            if existing_link:
                raise ValueError("YouTube link already exists")
        elif link_type == "ZOTERO":
            zotero_id = kwargs.get('zotero_item_id')
            existing_link = existing_link.filter_by(zotero_item_id=zotero_id).first()
            if existing_link:
                raise ValueError("Zotero link already exists")

        # Create link
        link = NodeLink(
            link_id=generate_uuid(),
            node_id=node_id,
            link_type=link_type,
            **kwargs
        )

        self.db.add(link)
        self.db.commit()
        return link

    def get_links(self, node_id: str) -> List[NodeLink]:
        """Get all links for node"""
        return self.db.query(NodeLink).filter_by(node_id=node_id).all()

    def delete_link(self, link_id: str) -> bool:
        """Delete a link"""
        link = self.db.query(NodeLink).filter_by(id=link_id).first()
        if not link:
            raise ValueError(f"Link {link_id} not found")

        self.db.delete(link)
        self.db.commit()
        return True

    # ==================== Hierarchy Operations ====================

    def get_children(self, node_id: str) -> List[Node]:
        """Get child nodes"""
        return self.db.query(Node).filter_by(
            parent_node_id=node_id
        ).order_by(Node.order_index).all()

    def reorder_nodes(self, node_orders: List[Dict[str, Any]]) -> None:
        """
        Reorder multiple nodes

        Input: [
            {"node_id": "node-1", "order_index": 0},
            {"node_id": "node-2", "order_index": 1}
        ]
        """
        for item in node_orders:
            node = self.get_node(item['node_id'])
            if node:
                node.order_index = item['order_index']

        self.db.commit()
```

### 5.2 Frontend Component Implementation

**File:** `MATHESIS-LAB_FRONT/components/NodeEditor.tsx`

```typescript
import React, { useState, useEffect } from 'react';
import { Node, NodeContent, NodeLink } from '../types';
import { nodeService } from '../services/nodeService';

interface NodeEditorProps {
    node: Node;
    onSave: (node: Node) => void;
    onDelete: (nodeId: string) => void;
}

export const NodeEditor: React.FC<NodeEditorProps> = ({
    node,
    onSave,
    onDelete
}) => {
    const [title, setTitle] = useState(node.title);
    const [content, setContent] = useState(node.content?.markdown_content || '');
    const [links, setLinks] = useState(node.links || []);
    const [isLoading, setIsLoading] = useState(false);

    // ==================== Save Handlers ====================

    const handleSaveTitle = async () => {
        try {
            setIsLoading(true);
            const updatedNode = await nodeService.updateNode(node.node_id, {
                title
            });
            onSave(updatedNode);
        } catch (error) {
            console.error('Error saving title:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleSaveContent = async () => {
        try {
            setIsLoading(true);
            await nodeService.updateContent(node.node_id, content);
            // Refresh node with updated content
            const updatedNode = await nodeService.getNode(node.node_id);
            onSave(updatedNode);
        } catch (error) {
            console.error('Error saving content:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddLink = async (linkType: string, linkData: any) => {
        try {
            setIsLoading(true);
            const newLink = await nodeService.addLink(
                node.node_id,
                linkType,
                linkData
            );
            setLinks([...links, newLink]);
        } catch (error) {
            console.error('Error adding link:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDeleteLink = async (linkId: string) => {
        try {
            setIsLoading(true);
            await nodeService.deleteLink(linkId);
            setLinks(links.filter(l => l.link_id !== linkId));
        } catch (error) {
            console.error('Error deleting link:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleDelete = async () => {
        if (confirm('Are you sure you want to delete this node?')) {
            try {
                setIsLoading(true);
                await nodeService.deleteNode(node.node_id);
                onDelete(node.node_id);
            } catch (error) {
                console.error('Error deleting node:', error);
            } finally {
                setIsLoading(false);
            }
        }
    };

    return (
        <div className="node-editor">
            {/* Properties Panel */}
            <div className="properties-panel">
                <div className="form-group">
                    <label>Title</label>
                    <input
                        type="text"
                        value={title}
                        onChange={(e) => setTitle(e.target.value)}
                        onBlur={handleSaveTitle}
                        disabled={isLoading}
                    />
                </div>
            </div>

            {/* Content Editor */}
            <div className="content-editor">
                <label>Content (Markdown)</label>
                <textarea
                    value={content}
                    onChange={(e) => setContent(e.target.value)}
                    onBlur={handleSaveContent}
                    disabled={isLoading}
                />
            </div>

            {/* Link Manager */}
            <div className="link-manager">
                <h3>External Resources</h3>
                {links.map(link => (
                    <LinkItem
                        key={link.link_id}
                        link={link}
                        onDelete={() => handleDeleteLink(link.link_id)}
                    />
                ))}
                <AddLinkButton onAdd={handleAddLink} />
            </div>

            {/* Actions */}
            <div className="actions">
                <button onClick={handleDelete} disabled={isLoading}>
                    Delete Node
                </button>
            </div>
        </div>
    );
};
```

---

## 6. Testing Strategy

### 6.1 Unit Tests

**Backend Unit Tests:**
- NodeService CRUD methods
- Content management
- Link validation
- Hierarchy validation

**Frontend Unit Tests:**
- NodeEditor component rendering
- Form input handling
- Save/delete functionality

### 6.2 Integration Tests

**Backend Integration Tests:**
- Full node creation workflow
- Content and links with node
- Cascade deletion
- Hierarchy operations

**Frontend Integration Tests:**
- Node editor with API calls
- Link management
- Error handling

### 6.3 E2E Tests

**User Workflows:**
1. Create curriculum
2. Add nodes to curriculum
3. Edit node content
4. Add YouTube link
5. Delete node

---

## 7. Performance Considerations

### 7.1 Database Optimization

- Index on `node_id`
- Index on `curriculum_id`
- Index on `parent_node_id`
- Index on `order_index`

### 7.2 Query Optimization

- Use `.select_in_load()` for relationships
- Limit recursion depth for hierarchy
- Cache frequently accessed nodes

### 7.3 Frontend Optimization

- Lazy load child nodes
- Debounce content save
- Pagination for large hierarchies

---

## 8. Error Handling

### 8.1 Common Errors

| Error | Cause | Resolution |
|-------|-------|-----------|
| Node not found | Invalid ID | Return 404 |
| Circular parent | Parent is child | Validate hierarchy |
| Duplicate link | Link exists | Return 409 |
| Invalid markdown | Parsing error | Log and continue |

### 8.2 Error Responses

```json
{
    "status": "error",
    "code": "NODE_NOT_FOUND",
    "message": "Node with ID node-123 not found",
    "details": {}
}
```

---

## 9. Future Enhancements

- [ ] Node duplication
- [ ] Bulk operations
- [ ] Node templates
- [ ] Version history
- [ ] Collaborative editing
- [ ] Real-time sync
- [ ] Node search
- [ ] Advanced metadata

---

## References

- Tree Data Structures: https://en.wikipedia.org/wiki/Tree_(data_structure)
- Markdown Specification: https://spec.commonmark.org/
- SQLAlchemy ORM: https://docs.sqlalchemy.org/
