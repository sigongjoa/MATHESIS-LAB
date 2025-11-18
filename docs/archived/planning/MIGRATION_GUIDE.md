# Database Migration Guide

**System Update: Critical Design Improvements**

**Date:** 2025-11-15
**Version:** 1.0

---

## Overview

이 마이그레이션은 노드 관리 시스템의 세 가지 치명적 설계 결함을 해결합니다:

1. **암시적 노드 타입 → 명시적 `node_type` 컬럼**
2. **삭제 데이터 손실 → 일관된 소프트 삭제 (`deleted_at` 타임스탬프)**
3. **Race Condition → 트랜잭션 락 준비**

---

## Pre-Migration Checklist

마이그레이션 전에 다음을 확인하세요:

- [ ] 현재 데이터베이스 백업
- [ ] 모든 서버 중지 (동기성 보장)
- [ ] 변경 내용 검토
- [ ] 롤백 계획 수립

```bash
# 현재 DB 파일 백업
cp mathesis_lab.db mathesis_lab.db.backup.$(date +%Y%m%d_%H%M%S)
```

---

## Migration Steps

### Step 1: 가상 환경 활성화

```bash
cd /mnt/d/progress/MATHESIS\ LAB
source .venv/bin/activate
```

### Step 2: 마이그레이션 실행

```bash
# Option A: 직접 실행
python -m backend.app.db.migrations.001_add_node_type_and_soft_delete

# Option B: Python 스크립트에서 프로그래밍적 실행
python -c "
from backend.app.db.migrations.001_add_node_type_and_soft_delete import run_migration
run_migration()
"
```

**예상 출력:**

```
🔄 Starting migration: Adding node_type and soft deletion support...

📝 Modifying 'nodes' table...
  ✓ Adding 'node_type' column...
    ✅ 'node_type' column added
  ✓ Adding 'deleted_at' column...
    ✅ 'deleted_at' column added
  ✓ Creating indices...
    ✅ Index on node_type created
    ✅ Index on deleted_at created
    ✅ Composite index on (curriculum_id, deleted_at) created

📝 Modifying 'node_contents' table...
  ✓ Adding 'deleted_at' column...
    ✅ 'deleted_at' column added
  ✅ Index on deleted_at created

📝 Modifying 'node_links' table...
  ✓ Adding 'deleted_at' column...
    ✅ 'deleted_at' column added
  ✅ Index on deleted_at created

📝 Modifying 'curriculums' table...
  ✓ Adding 'deleted_at' column...
    ✅ 'deleted_at' column added

✅ Migration completed successfully!

🔍 Validating migration...

📋 Checking 'nodes' table...
  ✅ node_type: VARCHAR(50)
  ✅ deleted_at: TIMESTAMP

📋 Checking indices...
  ✅ idx_nodes_type
  ✅ idx_nodes_deleted
  ✅ idx_nodes_curriculum_active

✅ Validation complete!
```

### Step 3: SQLAlchemy 모델 업데이트

마이그레이션 후 SQLAlchemy 모델이 새 컬럼을 반영하도록 수정해야 합니다:

```python
# backend/app/models/node.py

from datetime import datetime
from sqlalchemy import Column, String, Integer, DateTime, ForeignKey
from sqlalchemy.orm import relationship

from backend.app.db.base import Base

class Node(Base):
    __tablename__ = "nodes"

    node_id = Column(String(36), primary_key=True)
    curriculum_id = Column(String(36), ForeignKey("curriculums.curriculum_id"), nullable=False)
    parent_node_id = Column(String(36), ForeignKey("nodes.node_id"), nullable=True)

    # [NEW] 명시적 노드 타입
    node_type = Column(String(50), nullable=False, default='CONTENT')

    title = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    order_index = Column(Integer, default=0)

    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # [NEW] 소프트 삭제 타임스탬프
    deleted_at = Column(DateTime, nullable=True)

    # Relationships
    curriculum = relationship("Curriculum", back_populates="nodes")
    content = relationship("NodeContent", back_populates="node", uselist=False)
    links = relationship("NodeLink", back_populates="node")
    children = relationship(
        "Node",
        remote_side=[node_id],
        backref="parent"
    )
```

### Step 4: 쿼리 필터 업데이트

모든 `SELECT` 쿼리에 `deleted_at IS NULL` 조건을 추가하세요:

```python
# ❌ Before
nodes = db.query(Node).filter(Node.curriculum_id == curriculum_id).all()

# ✅ After
from sqlalchemy import and_

nodes = db.query(Node).filter(
    and_(
        Node.curriculum_id == curriculum_id,
        Node.deleted_at.is_(None)  # [NEW] 활성 노드만
    )
).all()
```

또는 SQLAlchemy 필터 속성 사용:

```python
# ✅ Clean approach
class Node(Base):
    __tablename__ = "nodes"
    # ... columns ...

    @classmethod
    def active_nodes(cls):
        """Filter active nodes automatically"""
        return cls.query.filter(cls.deleted_at.is_(None))

# Usage
nodes = Node.active_nodes().filter(Node.curriculum_id == curriculum_id).all()
```

### Step 5: 기존 데이터 초기화 (선택사항)

기존 노드에 `node_type` 값을 자동으로 추론하려면:

```python
# backend/app/db/migrations/001_data_migration.py

from sqlalchemy import text

def initialize_node_types(db):
    """
    기존 노드에 node_type 값 추론

    휴리스틱 (Heuristic):
    - parent_node_id IS NULL & order_index = 0 → CHAPTER
    - parent_node_id IS NOT NULL → CONTENT (기본값)
    - 노드명에 'assessment', 'quiz', 'exam' 포함 → ASSESSMENT
    - 노드명에 'section', 'unit' 포함 → SECTION
    """

    with db.begin():
        # 1. CHAPTER: 최상위 노드 (부모 없음)
        db.execute(text("""
            UPDATE nodes
            SET node_type = 'CHAPTER'
            WHERE parent_node_id IS NULL
            AND deleted_at IS NULL;
        """))

        # 2. ASSESSMENT: 'assessment', 'quiz', 'exam' 키워드 포함
        db.execute(text("""
            UPDATE nodes
            SET node_type = 'ASSESSMENT'
            WHERE (LOWER(title) LIKE '%assessment%'
                OR LOWER(title) LIKE '%quiz%'
                OR LOWER(title) LIKE '%exam%')
            AND deleted_at IS NULL;
        """))

        # 3. SECTION: 'section', 'unit' 키워드 포함
        db.execute(text("""
            UPDATE nodes
            SET node_type = 'SECTION'
            WHERE (LOWER(title) LIKE '%section%'
                OR LOWER(title) LIKE '%unit%')
            AND deleted_at IS NULL;
        """))

        # 4. 나머지는 기본값 CONTENT 유지

    print("✅ Node types initialized")
```

---

## Rollback (위급 상황)

마이그레이션에 문제가 생기면 롤백할 수 있습니다:

⚠️ **경고:** 롤백하면 `node_type`과 `deleted_at` 정보가 모두 손실됩니다!

```bash
# 롤백 실행
python -m backend.app.db.migrations.001_add_node_type_and_soft_delete rollback

# 또는 백업에서 복원
rm mathesis_lab.db
cp mathesis_lab.db.backup.YYYYMMDD_HHMMSS mathesis_lab.db
```

---

## Post-Migration Verification

### 1. 데이터베이스 구조 확인

```sql
-- SQLite에서 직접 확인
sqlite3 mathesis_lab.db

-- 테이블 구조 확인
.schema nodes
.schema node_contents
.schema node_links

-- 데이터 샘플 확인
SELECT node_id, title, node_type, deleted_at FROM nodes LIMIT 5;
```

### 2. 인덱스 확인

```sql
-- 인덱스 목록
SELECT name FROM sqlite_master WHERE type='index' AND tbl_name='nodes';
```

### 3. 테스트 실행

```bash
# 모든 테스트 실행
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/ -v

# 노드 관련 테스트만
PYTHONPATH=/mnt/d/progress/MATHESIS\ LAB pytest backend/tests/unit/test_node_service.py -v
```

---

## 구현 변경 사항

마이그레이션 후 다음을 구현해야 합니다:

### 1. NodeService 업데이트

```python
# backend/app/services/node_service.py

class NodeService:
    @staticmethod
    def create_node(
        db: Session,
        curriculum_id: str,
        title: str,
        parent_node_id: Optional[str] = None,
        node_type: str = 'CONTENT'  # [NEW]
    ) -> Node:
        """Create node with transaction lock"""

        try:
            # [NEW] Parent validation with lock
            if parent_node_id:
                parent = db.query(Node).filter(
                    and_(
                        Node.node_id == parent_node_id,
                        Node.deleted_at.is_(None)  # [NEW]
                    )
                ).with_for_update().first()  # [NEW] Transaction lock

                if not parent:
                    raise ValueError(f"Parent not found")

            # 나머지 로직...

    @staticmethod
    def delete_node(db: Session, node_id: str) -> bool:
        """[NEW] Soft delete with cascading"""

        # 재귀적으로 모든 하위 노드 soft delete
        descendant_ids = get_all_descendant_ids(node_id)

        now = datetime.utcnow()
        db.query(Node).filter(
            Node.node_id.in_(descendant_ids)
        ).update({Node.deleted_at: now})

        # 콘텐츠, 링크도 soft delete
        db.query(NodeContent).filter(
            NodeContent.node_id.in_(descendant_ids)
        ).update({NodeContent.deleted_at: now})

        db.query(NodeLink).filter(
            NodeLink.node_id.in_(descendant_ids)
        ).update({NodeLink.deleted_at: now})

        db.commit()
        return True
```

### 2. API 엔드포인트 추가

```python
# backend/app/api/v1/endpoints/nodes.py

# [NEW] 노드 타입별 필터
@router.get("/curriculums/{curriculum_id}/nodes")
async def get_curriculum_nodes(
    curriculum_id: str,
    node_type: Optional[str] = Query(None),  # [NEW]
    db: Session = Depends(get_db)
):
    query = db.query(Node).filter(
        and_(
            Node.curriculum_id == curriculum_id,
            Node.deleted_at.is_(None)
        )
    )

    if node_type:
        query = query.filter(Node.node_type == node_type)

    return query.all()

# [NEW] 휴지통 조회
@router.get("/curriculums/{curriculum_id}/trash")
async def get_trash(curriculum_id: str, db: Session = Depends(get_db)):
    deleted_nodes = db.query(Node).filter(
        and_(
            Node.curriculum_id == curriculum_id,
            Node.deleted_at.is_not(None)
        )
    ).all()
    return deleted_nodes

# [NEW] 노드 복원
@router.post("/nodes/{node_id}/restore")
async def restore_node(node_id: str, db: Session = Depends(get_db)):
    node = db.query(Node).filter(Node.node_id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")

    node.deleted_at = None
    db.commit()
    return node
```

### 3. Frontend 수정

```typescript
// MATHESIS-LAB_FRONT/types.ts

export type NodeType =
    | 'CHAPTER'
    | 'SECTION'
    | 'TOPIC'
    | 'CONTENT'
    | 'ASSESSMENT'
    | 'QUESTION'
    | 'PROJECT';

export interface Node {
    // ... existing fields ...
    node_type: NodeType;  // [NEW]
    deleted_at?: string | null;  // [NEW]
}
```

---

## Performance Tuning

마이그레이션 후 쿼리 성능 최적화:

### 1. Index 생성 (이미 마이그레이션에 포함됨)

```sql
-- 자주 사용되는 복합 인덱스
CREATE INDEX idx_nodes_curriculum_active ON nodes(curriculum_id, deleted_at);
CREATE INDEX idx_nodes_type_active ON nodes(node_type, deleted_at);
```

### 2. 쿼리 계획 확인

```sql
-- EXPLAIN QUERY PLAN으로 성능 확인
EXPLAIN QUERY PLAN
SELECT * FROM nodes
WHERE curriculum_id = 'curr-123'
AND deleted_at IS NULL;
```

---

## FAQ

### Q: 마이그레이션 중 서버를 멈춰야 하나요?

**A:** 예. SQLite는 단일 파일 기반이므로, 동시에 여러 프로세스가 접근하면 "database is locked" 오류가 발생할 수 있습니다.

```bash
# 1. 서버 종료
pkill -f "uvicorn backend.app.main"
pkill -f "npm run dev"

# 2. 마이그레이션 실행
python -m backend.app.db.migrations.001_add_node_type_and_soft_delete

# 3. 서버 재시작
python -m uvicorn backend.app.main:app --reload
```

### Q: 롤백하려면?

**A:** 마이그레이션 스크립트에 `rollback` 파라미터를 사용하세요.

```bash
python -m backend.app.db.migrations.001_add_node_type_and_soft_delete rollback
```

### Q: 현재 데이터는 어떻게 되나요?

**A:** 기존 데이터는 그대로 유지됩니다. 새 컬럼은 초기값(node_type='CONTENT', deleted_at=NULL)으로 설정됩니다.

### Q: deleted_at이 NULL이면 활성, NOT NULL이면 삭제된 거죠?

**A:** 맞습니다. 모든 SELECT 쿼리에는 `WHERE deleted_at IS NULL` 조건을 추가해야 합니다.

---

## 다음 단계

1. ✅ 마이그레이션 실행
2. ✅ 모델 및 쿼리 업데이트
3. ✅ 테스트 실행
4. ⬜ GCP 동기화 구현 (별도 가이드)
5. ⬜ 프로덕션 배포

---

## Support

마이그레이션 중 문제가 생기면:

1. **로그 확인**: 마이그레이션 출력에서 오류 메시지 찾기
2. **롤백**: 문제가 심각하면 롤백 실행
3. **백업 복원**: 최악의 경우 백업 파일에서 복원

```bash
# 로그 저장
python -m backend.app.db.migrations.001_add_node_type_and_soft_delete > migration.log 2>&1

# 로그 확인
cat migration.log
```

---

**마이그레이션을 완료하신 후 GCP 동기화 구현을 진행하세요.**
