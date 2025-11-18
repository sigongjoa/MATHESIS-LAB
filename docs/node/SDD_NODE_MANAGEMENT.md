# SDD: Node Management System (Revised)

**Version:** 2.0 (Critical Redesign based on Critique)
**Date:** 2025-11-15
**Status:** Final Design - Ready for Implementation

---

## Executive Summary

기존 설계의 세 가지 치명적 결함을 완전히 개선했습니다:

1. **암시적 노드 타입 제거** → `node_type` 컬럼 추가 (명시적, 쿼리 가능)
2. **Race Condition** → 트랜잭션 락(SELECT ... FOR UPDATE) 사용
3. **혼란스러운 삭제 전략** → 일관된 소프트 삭제(deleted_at 타임스탬프)

---

## 1. 데이터 모델 (개정)

### 1.1 수정된 Nodes 테이블

```sql
CREATE TABLE nodes (
    node_id VARCHAR(36) PRIMARY KEY,
    curriculum_id VARCHAR(36) NOT NULL,
    parent_node_id VARCHAR(36),

    -- [NEW] 명시적 노드 타입 (쿼리 가능, 확장 가능)
    -- ENUM 타입 또는 VARCHAR(50)
    -- 값: 'CONTENT', 'SECTION', 'CHAPTER', 'ASSESSMENT', 'PROJECT'
    node_type VARCHAR(50) NOT NULL DEFAULT 'CONTENT',

    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- [NEW] 소프트 삭제를 위한 타임스탬프 (NULL = 활성, NOT NULL = 삭제됨)
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY (curriculum_id) REFERENCES curriculums(curriculum_id),
    FOREIGN KEY (parent_node_id) REFERENCES nodes(node_id),

    -- [NEW] 인덱스: 성능 최적화
    INDEX idx_curriculum_id (curriculum_id),
    INDEX idx_parent_node_id (parent_node_id),
    INDEX idx_node_type (node_type),
    INDEX idx_deleted_at (deleted_at)
);
```

**주요 변경사항:**
- `node_type`: ENUM 대신 VARCHAR(50)를 사용하여 새 타입 추가 시 마이그레이션 불필요
- `deleted_at`: 소프트 삭제를 위한 타임스탬프 필드 추가
- 인덱스: 자주 쿼리되는 컬럼에 인덱스 추가

### 1.2 수정된 NodeContents 테이블

```sql
CREATE TABLE node_contents (
    content_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL UNIQUE,
    markdown_content TEXT,
    ai_summary TEXT,
    ai_extension TEXT,
    manim_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- [NEW] 소프트 삭제
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY (node_id) REFERENCES nodes(node_id),
    INDEX idx_deleted_at (deleted_at)
);
```

### 1.3 수정된 NodeLinks 테이블

```sql
CREATE TABLE node_links (
    link_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL,
    link_type VARCHAR(50), -- 'YOUTUBE', 'ZOTERO', 'EXTERNAL'
    youtube_video_id VARCHAR(255),
    zotero_item_id VARCHAR(255),
    external_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- [NEW] 소프트 삭제
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY (node_id) REFERENCES nodes(node_id),
    INDEX idx_node_id (node_id),
    INDEX idx_deleted_at (deleted_at)
);
```

### 1.4 노드 타입 정의 (Explicit)

이제 쿼리로 노드 타입을 필터링할 수 있습니다:

```python
# Backend: 모든 평가 노드 조회 가능
assessment_nodes = db.query(Node).filter(
    Node.node_type == 'ASSESSMENT',
    Node.deleted_at.is_(None)  # 활성 노드만
).all()

# SQL: 특정 커리큘럼의 챕터 노드만 조회
SELECT * FROM nodes
WHERE curriculum_id = 'curr-456'
AND node_type = 'CHAPTER'
AND deleted_at IS NULL;
```

**Node Type 정의:**
| Type | 설명 | 부모 | 자식 | 특징 |
|------|------|------|------|------|
| `CHAPTER` | 챕터 (큰 섹션) | Curriculum | SECTION, CONTENT | 최상위 계층 |
| `SECTION` | 섹션 (중간 섹션) | CHAPTER, Curriculum | TOPIC, CONTENT | 계층적 구조 |
| `TOPIC` | 주제 (소단위) | SECTION | CONTENT | 상세 학습 단위 |
| `CONTENT` | 학습 콘텐츠 | 모두 | None (Leaf) | 실제 콘텐츠 |
| `ASSESSMENT` | 평가/퀴즈 | SECTION, CHAPTER | QUESTION | 평가 문제 모음 |
| `QUESTION` | 개별 질문 | ASSESSMENT | None (Leaf) | 단일 평가 항목 |
| `PROJECT` | 프로젝트 | SECTION | CONTENT | 실습/프로젝트 |

---

## 2. 노드 생성 (Race Condition 해결)

### 2.1 문제점 (기존 설계)

동시에 두 요청이 같은 부모에서 order_index를 계산하면:

```python
# 요청 A: 마지막 형제 order_index = 2
# 요청 B: 마지막 형제 order_index = 2
# 결과: 둘 다 order_index = 3으로 생성 (Race Condition!)
```

### 2.2 해결책: 트랜잭션 락

```python
# backend/app/services/node_service.py

from sqlalchemy import func
from contextlib import contextmanager

class NodeService:
    def create_node(
        self,
        db_session,
        curriculum_id: str,
        title: str,
        parent_node_id: Optional[str] = None,
        node_type: str = 'CONTENT'
    ) -> Node:
        """
        Create node with transaction-level lock to prevent race conditions.

        [SOLUTION] 전체 로직을 트랜잭션으로 묶고, 부모에 배타적 락을 겁니다.
        """

        try:
            # 1. 부모 검증 (락 포함)
            if parent_node_id:
                parent = db_session.query(Node).filter(
                    Node.node_id == parent_node_id,
                    Node.deleted_at.is_(None)  # 삭제된 노드는 부모가 될 수 없음
                ).with_for_update().first()  # [SOLUTION] SELECT ... FOR UPDATE

                if not parent:
                    raise ValueError(f"Parent node {parent_node_id} not found or deleted")

            # 2. Order index 계산 (이 시점에서는 이 트랜잭션만 실행됨)
            last_sibling = db_session.query(Node).filter(
                Node.parent_node_id == parent_node_id,
                Node.deleted_at.is_(None)
            ).order_by(Node.order_index.desc()).first()

            order_index = (last_sibling.order_index + 1) if last_sibling else 0

            # 3. 콘텐츠 생성 (필수)
            node_content = NodeContent(
                content_id=str(uuid.uuid4()),
                node_id=None,  # 아래에서 설정
                markdown_content="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )

            # 4. 노드 생성
            node = Node(
                node_id=str(uuid.uuid4()),
                curriculum_id=curriculum_id,
                parent_node_id=parent_node_id,
                title=title,
                node_type=node_type,
                order_index=order_index,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                deleted_at=None
            )

            node_content.node_id = node.node_id
            db_session.add(node_content)
            db_session.add(node)
            db_session.commit()  # 트랜잭션 종료, 락 해제

            return node

        except Exception as e:
            db_session.rollback()
            raise e
```

**동작 원리:**
- `with_for_update()`: 부모 노드를 SELECT ... FOR UPDATE로 잠급니다
- 다른 트랜잭션이 같은 부모를 조회하려면 이 트랜잭션이 끝날 때까지 대기
- order_index 계산과 INSERT가 원자적으로 실행됨

---

## 3. 노드 삭제 (일관된 소프트 삭제)

### 3.1 문제점 (기존 설계)

- 부모는 하드 삭제 → DB에서 제거됨
- 자식은 소프트 삭제 → is_deleted = True
- 결과: 고아(Orphan) 레코드 발생, 데이터 무결성 손상

### 3.2 해결책: 일관된 소프트 삭제

```python
class NodeService:
    def delete_node(
        self,
        db_session,
        node_id: str
    ) -> bool:
        """
        [SOLUTION] 모든 관련 데이터를 일관되게 소프트 삭제합니다.
        - 해당 노드
        - 모든 하위 자손 노드 (재귀적)
        - 콘텐츠
        - 링크
        """

        try:
            # 1. 삭제할 노드 및 모든 하위 노드 ID 수집 (재귀적)
            def get_all_descendant_ids(node_id: str, visited=set()) -> set:
                if node_id in visited:
                    return set()
                visited.add(node_id)

                children = db_session.query(Node.node_id).filter(
                    Node.parent_node_id == node_id,
                    Node.deleted_at.is_(None)
                ).all()

                all_ids = {node_id}
                for child_id, in children:
                    all_ids.update(get_all_descendant_ids(child_id, visited))

                return all_ids

            descendant_ids = get_all_descendant_ids(node_id)

            # 2. 모든 노드를 소프트 삭제
            now = datetime.utcnow()
            db_session.query(Node).filter(
                Node.node_id.in_(descendant_ids)
            ).update({Node.deleted_at: now})

            # 3. 모든 콘텐츠를 소프트 삭제
            db_session.query(NodeContent).filter(
                NodeContent.node_id.in_(descendant_ids)
            ).update({NodeContent.deleted_at: now})

            # 4. 모든 링크를 소프트 삭제
            db_session.query(NodeLink).filter(
                NodeLink.node_id.in_(descendant_ids)
            ).update({NodeLink.deleted_at: now})

            db_session.commit()
            return True

        except Exception as e:
            db_session.rollback()
            raise e
```

**이점:**
- 데이터 복구 가능 (휴지통 기능)
- 데이터 무결성 100% 보장
- deleted_at IS NULL 필터만으로 활성 데이터 조회

### 3.3 "휴지통" 기능 구현

```python
class NodeService:
    def get_deleted_nodes(
        self,
        db_session,
        curriculum_id: str,
        limit: int = 100
    ) -> List[Node]:
        """삭제된 노드 조회 (관리자용)"""
        return db_session.query(Node).filter(
            Node.curriculum_id == curriculum_id,
            Node.deleted_at.is_not(None)
        ).order_by(Node.deleted_at.desc()).limit(limit).all()

    def restore_node(
        self,
        db_session,
        node_id: str
    ) -> Node:
        """삭제된 노드 복원"""
        node = db_session.query(Node).filter(
            Node.node_id == node_id
        ).first()

        if not node or node.deleted_at is None:
            raise ValueError(f"Node {node_id} not found or not deleted")

        node.deleted_at = None
        db_session.commit()
        return node
```

---

## 4. 수정된 API 엔드포인트

### 4.1 노드 생성

```
POST /api/v1/curriculums/{curriculum_id}/nodes
```

**Request:**
```json
{
    "title": "Introduction to Derivatives",
    "node_type": "CONTENT",
    "parent_node_id": null,
    "description": "Learn the fundamentals..."
}
```

**Response (201):**
```json
{
    "node_id": "node-123",
    "curriculum_id": "curr-456",
    "parent_node_id": null,
    "title": "Introduction to Derivatives",
    "node_type": "CONTENT",
    "order_index": 0,
    "created_at": "2025-11-15T10:00:00Z",
    "updated_at": "2025-11-15T10:00:00Z",
    "deleted_at": null,
    "content": {
        "content_id": "cont-789",
        "node_id": "node-123",
        "markdown_content": "",
        "created_at": "2025-11-15T10:00:00Z"
    }
}
```

### 4.2 노드 업데이트

```
PUT /api/v1/nodes/{node_id}
```

**Request:**
```json
{
    "title": "Updated Title",
    "node_type": "SECTION",
    "description": "Updated description"
}
```

**Response (200):**
```json
{
    "node_id": "node-123",
    "title": "Updated Title",
    "node_type": "SECTION",
    "updated_at": "2025-11-15T11:00:00Z"
}
```

### 4.3 노드 삭제

```
DELETE /api/v1/nodes/{node_id}
```

**Response (204):**
```
No Content
```

**Server-side:**
- node_id와 모든 하위 노드의 deleted_at 타임스탬프 설정
- 콘텐츠와 링크도 함께 소프트 삭제

### 4.4 노드 타입 필터 조회 (NEW)

```
GET /api/v1/curriculums/{curriculum_id}/nodes?node_type=ASSESSMENT
```

**Response:**
```json
{
    "nodes": [
        {
            "node_id": "node-201",
            "title": "Practice Problems",
            "node_type": "ASSESSMENT",
            "order_index": 5
        }
    ],
    "total": 1
}
```

### 4.5 삭제된 노드 조회 (NEW - 관리자용)

```
GET /api/v1/curriculums/{curriculum_id}/trash
```

**Response:**
```json
{
    "deleted_nodes": [
        {
            "node_id": "node-999",
            "title": "Old Content",
            "deleted_at": "2025-11-15T12:00:00Z"
        }
    ]
}
```

### 4.6 노드 복원 (NEW)

```
POST /api/v1/nodes/{node_id}/restore
```

**Response (200):**
```json
{
    "node_id": "node-999",
    "title": "Old Content",
    "deleted_at": null
}
```

---

## 5. 백엔드 구현 (Python/FastAPI)

### 5.1 NodeService 전체 코드

```python
# backend/app/services/node_service.py

from datetime import datetime
from typing import List, Optional
from uuid import uuid4
from sqlalchemy.orm import Session
from sqlalchemy import and_

from backend.app.models import Node, NodeContent, NodeLink
from backend.app.schemas import NodeCreate, NodeUpdate

class NodeService:
    """
    Node management with explicit types and soft deletion.

    Features:
    - Explicit node_type for queryability
    - Transaction-level locks for race condition prevention
    - Consistent soft deletion
    - Recursive deletion handling
    """

    @staticmethod
    def create_node(
        db: Session,
        curriculum_id: str,
        title: str,
        parent_node_id: Optional[str] = None,
        node_type: str = "CONTENT",
        description: Optional[str] = None
    ) -> Node:
        """
        Create node with transaction-level lock.

        Prevents race condition in order_index calculation.
        """
        try:
            # 1. Validate parent (with lock)
            if parent_node_id:
                parent = db.query(Node).filter(
                    and_(
                        Node.node_id == parent_node_id,
                        Node.deleted_at.is_(None)
                    )
                ).with_for_update().first()

                if not parent:
                    raise ValueError(f"Parent node {parent_node_id} not found or deleted")

            # 2. Calculate order_index (atomic)
            last_sibling = db.query(Node).filter(
                and_(
                    Node.parent_node_id == parent_node_id,
                    Node.deleted_at.is_(None)
                )
            ).order_by(Node.order_index.desc()).first()

            order_index = (last_sibling.order_index + 1) if last_sibling else 0

            # 3. Create content (mandatory)
            node_content = NodeContent(
                content_id=str(uuid4()),
                markdown_content="",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                deleted_at=None
            )

            # 4. Create node
            node = Node(
                node_id=str(uuid4()),
                curriculum_id=curriculum_id,
                parent_node_id=parent_node_id,
                title=title,
                node_type=node_type,
                description=description,
                order_index=order_index,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow(),
                deleted_at=None
            )

            node_content.node_id = node.node_id

            db.add(node_content)
            db.add(node)
            db.commit()

            return node

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_node(db: Session, node_id: str) -> Optional[Node]:
        """Get active node by ID"""
        return db.query(Node).filter(
            and_(
                Node.node_id == node_id,
                Node.deleted_at.is_(None)
            )
        ).first()

    @staticmethod
    def update_node(
        db: Session,
        node_id: str,
        data: NodeUpdate
    ) -> Optional[Node]:
        """Update node properties"""
        node = NodeService.get_node(db, node_id)
        if not node:
            raise ValueError(f"Node {node_id} not found")

        update_dict = data.dict(exclude_unset=True)
        update_dict['updated_at'] = datetime.utcnow()

        db.query(Node).filter(Node.node_id == node_id).update(update_dict)
        db.commit()

        return NodeService.get_node(db, node_id)

    @staticmethod
    def delete_node(db: Session, node_id: str) -> bool:
        """
        Soft-delete node and all descendants.
        """
        try:
            # 1. Get all descendant IDs recursively
            def get_descendant_ids(nid: str, visited=None) -> set:
                if visited is None:
                    visited = set()
                if nid in visited:
                    return set()
                visited.add(nid)

                children = db.query(Node.node_id).filter(
                    and_(
                        Node.parent_node_id == nid,
                        Node.deleted_at.is_(None)
                    )
                ).all()

                result = {nid}
                for (child_id,) in children:
                    result.update(get_descendant_ids(child_id, visited))

                return result

            descendant_ids = get_descendant_ids(node_id)

            # 2. Soft-delete all nodes
            now = datetime.utcnow()
            db.query(Node).filter(
                Node.node_id.in_(descendant_ids)
            ).update({Node.deleted_at: now})

            # 3. Soft-delete contents
            db.query(NodeContent).filter(
                NodeContent.node_id.in_(descendant_ids)
            ).update({NodeContent.deleted_at: now})

            # 4. Soft-delete links
            db.query(NodeLink).filter(
                NodeLink.node_id.in_(descendant_ids)
            ).update({NodeLink.deleted_at: now})

            db.commit()
            return True

        except Exception as e:
            db.rollback()
            raise e

    @staticmethod
    def get_deleted_nodes(
        db: Session,
        curriculum_id: str,
        limit: int = 100
    ) -> List[Node]:
        """Get deleted nodes for trash/recovery"""
        return db.query(Node).filter(
            and_(
                Node.curriculum_id == curriculum_id,
                Node.deleted_at.is_not(None)
            )
        ).order_by(Node.deleted_at.desc()).limit(limit).all()

    @staticmethod
    def restore_node(db: Session, node_id: str) -> Node:
        """Restore soft-deleted node"""
        node = db.query(Node).filter(
            Node.node_id == node_id
        ).first()

        if not node or node.deleted_at is None:
            raise ValueError(f"Node {node_id} not found or not deleted")

        node.deleted_at = None
        db.commit()

        return node

    @staticmethod
    def get_nodes_by_type(
        db: Session,
        curriculum_id: str,
        node_type: str
    ) -> List[Node]:
        """[NEW] Query nodes by explicit type"""
        return db.query(Node).filter(
            and_(
                Node.curriculum_id == curriculum_id,
                Node.node_type == node_type,
                Node.deleted_at.is_(None)
            )
        ).all()
```

---

## 6. Frontend 구현 (React/TypeScript)

### 6.1 수정된 타입 정의

```typescript
// MATHESIS-LAB_FRONT/types.ts

export type NodeType = 'CHAPTER' | 'SECTION' | 'TOPIC' | 'CONTENT' | 'ASSESSMENT' | 'QUESTION' | 'PROJECT';

export interface Node {
    node_id: string;
    curriculum_id: string;
    parent_node_id?: string;
    title: string;
    node_type: NodeType;  // [NEW] 명시적 타입
    description?: string;
    order_index: number;
    created_at: string;
    updated_at: string;
    deleted_at?: string | null;  // [NEW] 소프트 삭제 타임스탬프
    content?: NodeContent;
    links?: NodeLinkResponse[];
    children?: Node[];
}

export interface NodeContent {
    content_id: string;
    node_id: string;
    markdown_content: string;
    ai_summary?: string;
    ai_extension?: string;
    manim_guidelines?: string;
    created_at: string;
    updated_at: string;
    deleted_at?: string | null;  // [NEW]
}

export interface NodeCreate {
    title: string;
    node_type?: NodeType;
    parent_node_id?: string | null;
    description?: string;
}

export interface NodeUpdate {
    title?: string;
    node_type?: NodeType;
    description?: string;
}
```

### 6.2 NodeEditor 컴포넌트 (수정)

```typescript
// MATHESIS-LAB_FRONT/pages/NodeEditor.tsx

import React, { useState, useEffect } from 'react';
import { Node, NodeType } from '../types';
import { nodeService } from '../services/nodeService';

const NodeTypeOptions: NodeType[] = [
    'CHAPTER', 'SECTION', 'TOPIC', 'CONTENT', 'ASSESSMENT', 'QUESTION', 'PROJECT'
];

export const NodeEditor: React.FC<NodeEditorProps> = ({
    node,
    onSave,
    onDelete
}) => {
    const [title, setTitle] = useState(node.title);
    const [nodeType, setNodeType] = useState<NodeType>(node.node_type);
    const [description, setDescription] = useState(node.description || '');

    const handleSaveTitle = async () => {
        const updated = await nodeService.updateNode(node.node_id, {
            title,
            node_type: nodeType,
            description
        });
        onSave(updated);
    };

    const handleDelete = async () => {
        if (confirm('Delete this node and all children?')) {
            await nodeService.deleteNode(node.node_id);
            onDelete(node.node_id);
        }
    };

    return (
        <div className="node-editor">
            <input
                type="text"
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                placeholder="Node title"
            />

            {/* [NEW] Node Type Selector */}
            <select
                value={nodeType}
                onChange={(e) => setNodeType(e.target.value as NodeType)}
            >
                {NodeTypeOptions.map(type => (
                    <option key={type} value={type}>{type}</option>
                ))}
            </select>

            <textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                placeholder="Description (optional)"
            />

            <button onClick={handleSaveTitle}>Save</button>
            <button onClick={handleDelete} className="danger">Delete</button>
        </div>
    );
};
```

---

## 7. 테스트 케이스

### 7.1 Race Condition 테스트

```python
# backend/tests/integration/test_node_race_condition.py

import threading
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_node_creation(db_session, client):
    """
    Test that concurrent node creation doesn't cause order_index duplicates.

    [SOLUTION 검증] Transaction lock이 race condition을 방지하는지 확인
    """
    curriculum_id = "curr-123"
    parent_id = "parent-456"

    # Create parent first
    parent = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={"title": "Parent", "node_type": "SECTION"}
    ).json()
    parent_id = parent['node_id']

    # Concurrent create requests
    def create_node(index):
        response = client.post(
            f"/api/v1/curriculums/{curriculum_id}/nodes",
            json={
                "title": f"Child {index}",
                "parent_node_id": parent_id,
                "node_type": "CONTENT"
            }
        )
        return response.json()

    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(create_node, range(5)))

    # Verify no duplicate order_index
    order_indices = [r['order_index'] for r in results]
    assert len(order_indices) == len(set(order_indices)), \
        f"Duplicate order_index: {order_indices}"
```

### 7.2 소프트 삭제 테스트

```python
def test_soft_delete_with_children(db_session, client):
    """
    Test that soft-delete cascades to children and content.
    """
    # Create hierarchy
    parent = client.post(
        "/api/v1/curriculums/curr-123/nodes",
        json={"title": "Parent"}
    ).json()

    child = client.post(
        "/api/v1/curriculums/curr-123/nodes",
        json={
            "title": "Child",
            "parent_node_id": parent['node_id']
        }
    ).json()

    # Delete parent
    client.delete(f"/api/v1/nodes/{parent['node_id']}")

    # Verify parent is soft-deleted
    response = client.get(f"/api/v1/nodes/{parent['node_id']}")
    assert response.status_code == 404  # Should not be found in active query

    # Verify child is also soft-deleted (orphan check)
    response = client.get(f"/api/v1/nodes/{child['node_id']}")
    assert response.status_code == 404
```

### 7.3 노드 타입 필터 테스트

```python
def test_query_nodes_by_type(db_session, client):
    """
    [NEW] Test explicit node_type filtering.
    """
    curriculum_id = "curr-123"

    # Create nodes of different types
    chapter = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={"title": "Chapter 1", "node_type": "CHAPTER"}
    ).json()

    assessment = client.post(
        f"/api/v1/curriculums/{curriculum_id}/nodes",
        json={"title": "Quiz 1", "node_type": "ASSESSMENT"}
    ).json()

    # Filter by type
    response = client.get(
        f"/api/v1/curriculums/{curriculum_id}/nodes?node_type=ASSESSMENT"
    ).json()

    assert len(response['nodes']) == 1
    assert response['nodes'][0]['node_id'] == assessment['node_id']
```

---

## 8. 마이그레이션 가이드

### 8.1 기존 DB → 새 스키마

```sql
-- 1. node_type 컬럼 추가 (기본값 'CONTENT')
ALTER TABLE nodes ADD COLUMN node_type VARCHAR(50) NOT NULL DEFAULT 'CONTENT';

-- 2. deleted_at 컬럼 추가
ALTER TABLE nodes ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE node_contents ADD COLUMN deleted_at TIMESTAMP NULL;
ALTER TABLE node_links ADD COLUMN deleted_at TIMESTAMP NULL;

-- 3. 인덱스 생성
CREATE INDEX idx_nodes_type ON nodes(node_type);
CREATE INDEX idx_nodes_deleted ON nodes(deleted_at);
CREATE INDEX idx_contents_deleted ON node_contents(deleted_at);
CREATE INDEX idx_links_deleted ON node_links(deleted_at);

-- 4. 기존 데이터 마이그레이션 (선택사항: 타입 자동 추론)
-- UPDATE nodes SET node_type = 'CHAPTER' WHERE order_index = 0 AND parent_node_id IS NULL;
-- (이 로직은 커리큘럼별로 다르므로 수동 검토 권장)
```

---

## 9. 성능 최적화

### 9.1 인덱스 전략

```sql
-- 자주 쿼리되는 조합
CREATE INDEX idx_curriculum_active ON nodes(curriculum_id, deleted_at);
CREATE INDEX idx_parent_active ON nodes(parent_node_id, deleted_at);
CREATE INDEX idx_type_active ON nodes(node_type, deleted_at);
```

### 9.2 쿼리 최적화

```python
# ❌ 나쁜 예: N+1 문제
for node in nodes:
    content = db.query(NodeContent).filter(...).first()  # 매번 쿼리

# ✅ 좋은 예: Eager loading
from sqlalchemy.orm import joinedload

nodes = db.query(Node).options(
    joinedload(Node.content)
).filter(...).all()
```

---

## 10. 요약

| 항목 | 기존 | 개선 |
|------|------|------|
| 노드 타입 | 암시적 (위치/내용 기반) | **명시적 (node_type 컬럼)** |
| Race Condition | 없음 (경합 가능성 높음) | **트랜잭션 락으로 방지** |
| 삭제 전략 | 혼란스러움 (하드/소프트 혼용) | **일관된 소프트 삭제** |
| 쿼리 가능성 | 제한적 | **완전히 가능** |
| 데이터 복구 | 불가능 | **휴지통 기능 지원** |

---

## 다음 단계

1. **데이터베이스 마이그레이션** - 실서버에 스키마 변경 적용
2. **백엔드 구현** - NodeService 수정된 코드 적용
3. **Frontend 구현** - Node Type Selector 추가
4. **테스트** - Race condition과 soft deletion 테스트 케이스 실행
5. **GCP 동기화** - 다음 문서에서 다룸
