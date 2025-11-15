# Node Management System

## Overview

Nodes are the building blocks of a Curriculum Map in MATHESIS LAB. Each node represents a distinct learning unit, concept, or section within a curriculum.

**Current Status:** Basic CRUD implemented, advanced features in development

## Table of Contents

1. [Node Structure](#node-structure)
2. [Core Features](#core-features)
3. [Node Types](#node-types)
4. [Relationships](#relationships)
5. [Implementation Details](#implementation-details)
6. [API Endpoints](#api-endpoints)
7. [Frontend Integration](#frontend-integration)

## Node Structure

### Database Schema

```sql
CREATE TABLE nodes (
    node_id VARCHAR(36) PRIMARY KEY,
    curriculum_id VARCHAR(36) NOT NULL,
    parent_node_id VARCHAR(36),
    title VARCHAR(255) NOT NULL,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (curriculum_id) REFERENCES curriculums(curriculum_id),
    FOREIGN KEY (parent_node_id) REFERENCES nodes(node_id)
);

CREATE TABLE node_contents (
    content_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL UNIQUE,
    markdown_content TEXT,
    ai_summary TEXT,
    ai_extension TEXT,
    manim_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);

CREATE TABLE node_links (
    link_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL,
    link_type VARCHAR(50), -- 'YOUTUBE', 'ZOTERO', 'EXTERNAL'
    youtube_video_id VARCHAR(255),
    zotero_item_id VARCHAR(255),
    external_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (node_id) REFERENCES nodes(node_id)
);
```

### Node Object (TypeScript)

```typescript
interface Node {
    node_id: string;
    curriculum_id: string;
    parent_node_id?: string;
    title: string;
    order_index: number;
    created_at: string;
    updated_at: string;
    content?: NodeContent;
    links?: NodeLink[];
    children?: Node[]; // Sub-nodes
}

interface NodeContent {
    content_id: string;
    node_id: string;
    markdown_content: string;
    ai_summary?: string;
    ai_extension?: string;
    manim_guidelines?: string;
    created_at: string;
    updated_at: string;
}

interface NodeLink {
    link_id: string;
    node_id: string;
    link_type: 'YOUTUBE' | 'ZOTERO' | 'EXTERNAL';
    youtube_video_id?: string;
    zotero_item_id?: string;
    external_url?: string;
    created_at: string;
}
```

## Core Features

### 1. Node Creation

**Requirements:**
- Title (required)
- Parent curriculum (required)
- Parent node (optional - for hierarchy)
- Order index (auto-generated)

**Example:**
```python
# Backend - Create Node
POST /api/v1/curriculums/{curriculum_id}/nodes
{
    "title": "Introduction to Derivatives",
    "parent_node_id": null
}

# Response
{
    "node_id": "node-123",
    "curriculum_id": "curr-456",
    "title": "Introduction to Derivatives",
    "order_index": 0,
    "created_at": "2025-11-15T00:00:00Z"
}
```

### 2. Node Content Management

**Supported Content:**
- Markdown text
- AI-generated summaries
- Extended explanations
- Manim animation guidelines

**Example:**
```python
# Create/Update Node Content
POST /api/v1/nodes/{node_id}/content
{
    "markdown_content": "## Introduction\n\nDerivatives measure rate of change..."
}

# Get Node Content
GET /api/v1/nodes/{node_id}/content
```

### 3. Node Linking

**External Resource Types:**
- YouTube videos
- Zotero literature items
- External URLs

**Example:**
```python
# Add YouTube Link
POST /api/v1/nodes/{node_id}/links/youtube
{
    "youtube_video_id": "dQw4w9WgXcQ"
}

# Add Zotero Link
POST /api/v1/nodes/{node_id}/links/zotero
{
    "zotero_item_id": "item-789"
}

# Get All Links
GET /api/v1/nodes/{node_id}/links
```

### 4. Node Hierarchy

**Features:**
- Parent-child relationships
- Automatic ordering
- Nested content structure
- Depth limiting (recommended max: 5 levels)

**Example:**
```
Curriculum: Calculus 101
├── Unit 1: Limits (parent_node_id: null, order_index: 0)
│   ├── 1.1: Definition (parent_node_id: "unit-1", order_index: 0)
│   ├── 1.2: Properties (parent_node_id: "unit-1", order_index: 1)
│   └── 1.3: Examples (parent_node_id: "unit-1", order_index: 2)
├── Unit 2: Derivatives (parent_node_id: null, order_index: 1)
│   ├── 2.1: Power Rule (parent_node_id: "unit-2", order_index: 0)
│   └── 2.2: Chain Rule (parent_node_id: "unit-2", order_index: 1)
└── Unit 3: Integration (parent_node_id: null, order_index: 2)
```

## Node Types

### Type 1: Chapter Node
- **Purpose:** Major section or chapter
- **Properties:** Title, order_index
- **Children:** Section nodes, Content nodes
- **Example:** "Chapter 1: Introduction"

### Type 2: Section Node
- **Purpose:** Subsection with related content
- **Properties:** Title, parent_node_id, order_index
- **Children:** Topic nodes, Content nodes
- **Example:** "Section 1.1: Fundamentals"

### Type 3: Content Node
- **Purpose:** Actual learning content
- **Properties:** Title, markdown_content, links
- **Children:** None (leaf node)
- **Example:** "What is a Derivative?"

### Type 4: Assessment Node
- **Purpose:** Quizzes, exercises, evaluations
- **Properties:** Title, questions, answers
- **Children:** Question nodes
- **Example:** "Practice Problems Set 1"

**Note:** Node types are not explicitly stored; determined by position and content.

## Relationships

### Node-to-Curriculum (Many-to-One)
- Multiple nodes belong to one curriculum
- Deleting curriculum cascades to nodes
- Query: `GET /api/v1/curriculums/{id}/nodes`

### Node-to-Node (Parent-Child)
- Nodes form tree structure
- Self-referencing foreign key: `parent_node_id`
- Query: `GET /api/v1/nodes/{id}/children`

### Node-to-Content (One-to-One)
- Each node has optional content
- Content auto-created with node
- Query: `GET /api/v1/nodes/{id}/content`

### Node-to-Links (One-to-Many)
- Nodes can have multiple external links
- Links are optional
- Query: `GET /api/v1/nodes/{id}/links`

## Implementation Details

### Backend Implementation

**Service Layer:** `backend/app/services/node_service.py`

```python
class NodeService:
    def create_node(self, curriculum_id: str, title: str, parent_node_id: str = None) -> Node
    def get_node(self, node_id: str) -> Node
    def update_node(self, node_id: str, data: dict) -> Node
    def delete_node(self, node_id: str) -> bool
    def get_node_content(self, node_id: str) -> NodeContent
    def update_node_content(self, node_id: str, content: str) -> NodeContent
    def add_node_link(self, node_id: str, link_type: str, **kwargs) -> NodeLink
    def get_node_links(self, node_id: str) -> List[NodeLink]
    def delete_node_link(self, link_id: str) -> bool
```

**API Endpoints:** `backend/app/api/v1/endpoints/nodes.py`

Currently implemented:
- ✅ POST `/api/v1/curriculums/{curriculum_id}/nodes` - Create node
- ✅ GET `/api/v1/nodes/{node_id}` - Get node details
- ✅ PUT `/api/v1/nodes/{node_id}` - Update node (partial)
- ✅ DELETE `/api/v1/nodes/{node_id}` - Delete node
- ✅ POST `/api/v1/nodes/{node_id}/content` - Create/update content
- ✅ GET `/api/v1/nodes/{node_id}/content` - Get content
- ✅ POST `/api/v1/nodes/{node_id}/links/youtube` - Add YouTube link
- ✅ POST `/api/v1/nodes/{node_id}/links/zotero` - Add Zotero link
- ✅ GET `/api/v1/nodes/{node_id}/links` - Get all links
- ✅ DELETE `/api/v1/nodes/{node_id}/links/{link_id}` - Delete link

### Frontend Implementation

**Components:**
- `NodeEditor.tsx` - Main node editing interface
- `NodeList.tsx` - Display node hierarchy
- `AIAssistant.tsx` - AI content enhancement

**Services:**
- `nodeService.ts` - API client for node operations

## API Endpoints

### Node CRUD

```
POST   /api/v1/curriculums/{curriculum_id}/nodes
GET    /api/v1/nodes/{node_id}
PUT    /api/v1/nodes/{node_id}
DELETE /api/v1/nodes/{node_id}
```

### Content Management

```
POST   /api/v1/nodes/{node_id}/content
GET    /api/v1/nodes/{node_id}/content
PUT    /api/v1/nodes/{node_id}/content
```

### Link Management

```
POST   /api/v1/nodes/{node_id}/links/youtube
POST   /api/v1/nodes/{node_id}/links/zotero
POST   /api/v1/nodes/{node_id}/links/external
GET    /api/v1/nodes/{node_id}/links
DELETE /api/v1/nodes/{node_id}/links/{link_id}
```

### Hierarchy Operations

```
GET    /api/v1/nodes/{node_id}/children
POST   /api/v1/nodes/{node_id}/reorder
```

## Frontend Integration

### NodeEditor Component Flow

```
CurriculumDetail Page
  ├── NodeList (display hierarchy)
  ├── NodeEditor (edit selected node)
  │   ├── Node Properties (title, order)
  │   ├── Content Editor (markdown)
  │   ├── LinkManager (external resources)
  │   └── AIAssistant (content enhancement)
  └── NodeActions (add, delete, duplicate)
```

### User Interactions

**Create Node:**
1. Click "Add Node" button
2. Enter node title
3. Click "Create"
4. Node appears in list
5. Click node to edit content

**Edit Node:**
1. Click node in list
2. Update content in editor
3. Click "Save"
4. Changes persist to database

**Add Link:**
1. Open node editor
2. Click "Add Link"
3. Select link type (YouTube/Zotero)
4. Enter resource ID/URL
5. Click "Add"

**Reorder Node:**
1. Drag node in list (drag-and-drop)
2. Drop to new position
3. Order updates automatically

## Next Steps

### Phase 1: UI Enhancement (Week 1)
- [ ] Implement "Add Node" button and modal
- [ ] Create node hierarchy visualization
- [ ] Add drag-and-drop reordering
- [ ] Improve node list display

### Phase 2: Advanced Features (Week 2-3)
- [ ] Node duplication
- [ ] Bulk operations
- [ ] Template nodes
- [ ] Node versioning

### Phase 3: AI Integration (Week 3-4)
- [ ] Integrate Gemini for auto-summarization
- [ ] Auto-generate Manim guidelines
- [ ] Content suggestion engine
- [ ] Learning path optimization

### Phase 4: Collaboration (Week 4-5)
- [ ] Multi-user editing
- [ ] Change tracking
- [ ] Comments and discussions
- [ ] Publishing workflows

## Testing

### Unit Tests
- NodeService CRUD operations
- Content management
- Link operations
- Hierarchy validation

### Integration Tests
- Full node workflow (create, edit, delete)
- Cascade delete behavior
- Link management

### E2E Tests
- Add node via UI
- Edit node content
- Add external links
- Reorder nodes

## Common Issues and Solutions

### Issue: Parent node not found
- Ensure parent_node_id exists
- Verify parent is in same curriculum
- Check parent hasn't been deleted

### Issue: Content not saving
- Verify node_id is correct
- Check markdown is valid
- Ensure content_id exists

### Issue: Links not displaying
- Verify link_type is correct
- Check resource ID format
- Ensure external API is accessible

## References

- [Node.js Concepts in Graph Theory](https://en.wikipedia.org/wiki/Node_(discrete_mathematics))
- [Tree Data Structures](https://en.wikipedia.org/wiki/Tree_(data_structure))
- [Curriculum Design Principles](https://en.wikipedia.org/wiki/Curriculum)
