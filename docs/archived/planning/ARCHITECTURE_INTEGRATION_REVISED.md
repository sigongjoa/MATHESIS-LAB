# Architecture Integration Document (Revised)

**Complete System Design: Node Management + GCP Multi-Device Sync**

**Version:** 2.0 (Critical Design Fixes)
**Date:** 2025-11-15

---

## Overview

MATHESIS LAB의 완전한 아키텍처:

1. **Node Management System** (로컬 데이터 관리)
   - 명시적 노드 타입 (node_type)
   - 일관된 소프트 삭제 (deleted_at)
   - 트랜잭션 락으로 Race Condition 방지

2. **GCP Multi-Device Sync** (클라우드 동기화)
   - SQLite DB 파일 기반 동기화
   - PULL/PUSH/CONFLICT 완전 구현
   - 데이터 손실 방지 (충돌 백업)

---

## 1. 시스템 전체 흐름도

```
┌──────────────────────────────────────────────────────────────────┐
│                      MATHESIS LAB System                         │
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │           Frontend (React 19 + TypeScript)                 │  │
│  │                                                            │  │
│  │  ┌──────────────────┐  ┌──────────────────────────────┐   │  │
│  │  │  UI Components   │  │  SyncManager                 │   │  │
│  │  │ - NodeEditor     │  │ - autoSync()                 │   │  │
│  │  │ - CurriculumList │  │ - handlePull/Push/Conflict   │   │  │
│  │  │ - NodeCreator    │  │ - notify user               │   │  │
│  │  └──────┬───────────┘  └──────────────┬───────────────┘   │  │
│  │         │                             │                   │  │
│  │         │                    ┌────────▼────────┐          │  │
│  │         │                    │  LocalStorage   │          │  │
│  │         │                    │ sync_metadata   │          │  │
│  │         │                    └─────────────────┘          │  │
│  │         │                                                 │  │
│  │         │          ┌─────────────────────────┐           │  │
│  │         └─────────►│  SQLite DB              │           │  │
│  │                    │  (mathesis_lab.db)      │           │  │
│  │                    │ - curriculums           │           │  │
│  │                    │ - nodes                 │           │  │
│  │                    │ - node_contents         │           │  │
│  │                    │ - node_links            │           │  │
│  │                    └──────────┬──────────────┘           │  │
│  │                               │                          │  │
│  └───────────────────────────────┼──────────────────────────┘  │
│                                  │                            │
│  ┌───────────────────────────────┼──────────────────────────┐  │
│  │      Backend (FastAPI)         │                         │  │
│  │                                │                         │  │
│  │  ┌────────────────────┐   ┌────▼─────────────────────┐  │  │
│  │  │ API Endpoints      │   │ Services                 │  │  │
│  │  │ /api/v1/nodes      │   │ - NodeService            │  │  │
│  │  │ /api/v1/sync       │   │ - SyncService            │  │  │
│  │  │ /api/v1/curriculums│   │ - DriveServiceManager    │  │  │
│  │  └────────────────────┘   └────────────────────────┘  │  │
│  │                                  │                     │  │
│  │  ┌──────────────────────────────▼─────────────────┐   │  │
│  │  │ SQLAlchemy ORM                               │   │  │
│  │  │ - Node, NodeContent, NodeLink models        │   │  │
│  │  │ - Transaction lock (SELECT ... FOR UPDATE)  │   │  │
│  │  └──────────────────────────────┬──────────────┘   │  │
│  │                                  │                  │  │
│  └──────────────────────────────────┼──────────────────┘  │
│                                     │                      │
└─────────────────────────────────────┼──────────────────────┘
                                      │
                        ┌─────────────┴──────────────┐
                        │                            │
                        ▼                            ▼
        ┌──────────────────────────┐   ┌─────────────────────────┐
        │  SQLite Database File    │   │ Google Drive API        │
        │  (Persistent Storage)    │   │ - Service Account auth  │
        │  - All user data         │   │ - File upload/download  │
        │  - Atomically synced     │   │ - Metadata checking     │
        └──────────────────────────┘   └─────────────────────────┘
                                               │
                                               ▼
                                    ┌─────────────────────┐
                                    │ Google Drive Cloud  │
                                    │                     │
                                    │ mathesis_lab.db     │
                                    │ (Latest version)    │
                                    │                     │
                                    │ Conflict backups:   │
                                    │ mathesis_lab_      │
                                    │ conflict_*.db       │
                                    └─────────────────────┘
```

---

## 2. 데이터 모델 (완전)

### 2.1 커리큘럼 관련 테이블

```sql
CREATE TABLE curriculums (
    curriculum_id VARCHAR(36) PRIMARY KEY,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL
);
```

### 2.2 노드 관련 테이블 (개정)

```sql
-- ★ 개선: node_type 추가, deleted_at 추가
CREATE TABLE nodes (
    node_id VARCHAR(36) PRIMARY KEY,
    curriculum_id VARCHAR(36) NOT NULL,
    parent_node_id VARCHAR(36),

    -- [REVISED] 명시적 노드 타입
    node_type VARCHAR(50) NOT NULL DEFAULT 'CONTENT',

    title VARCHAR(255) NOT NULL,
    description TEXT,
    order_index INT DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- [REVISED] 일관된 소프트 삭제
    deleted_at TIMESTAMP NULL,

    FOREIGN KEY (curriculum_id) REFERENCES curriculums(curriculum_id),
    FOREIGN KEY (parent_node_id) REFERENCES nodes(node_id),

    INDEX idx_curriculum_id (curriculum_id),
    INDEX idx_parent_node_id (parent_node_id),
    INDEX idx_node_type (node_type),
    INDEX idx_deleted_at (deleted_at),
    INDEX idx_curriculum_active (curriculum_id, deleted_at)
);

-- ★ 개선: deleted_at 추가
CREATE TABLE node_contents (
    content_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL UNIQUE,
    markdown_content TEXT,
    ai_summary TEXT,
    ai_extension TEXT,
    manim_guidelines TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,  -- [REVISED]

    FOREIGN KEY (node_id) REFERENCES nodes(node_id),
    INDEX idx_deleted_at (deleted_at)
);

-- ★ 개선: deleted_at 추가
CREATE TABLE node_links (
    link_id VARCHAR(36) PRIMARY KEY,
    node_id VARCHAR(36) NOT NULL,
    link_type VARCHAR(50),
    youtube_video_id VARCHAR(255),
    zotero_item_id VARCHAR(255),
    external_url VARCHAR(500),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP NULL,  -- [REVISED]

    FOREIGN KEY (node_id) REFERENCES nodes(node_id),
    INDEX idx_node_id (node_id),
    INDEX idx_deleted_at (deleted_at)
);
```

### 2.3 GCP 동기화 메타데이터 (로컬 저장소)

```typescript
// LocalStorage / SharedPreferences
interface SyncMetadata {
    // Google Drive
    drive_file_id: string;
    drive_app_folder_id: string;

    // 타임스탬프 추적
    last_synced_drive_timestamp: string;
    last_synced_local_timestamp: string;

    // 디바이스
    device_id: string;
    device_name: string;

    // 상태
    sync_status: 'IDLE' | 'SYNCING' | 'CONFLICT' | 'ERROR';

    // 충돌 파일 관리
    conflict_files?: Array<{
        file_name: string;
        created_at: string;
        size: number;
        device_name: string;
    }>;
}
```

---

## 3. 데이터 흐름 (CRUD + Sync)

### 3.1 CREATE: 새 노드 생성

```
User Input (NodeEditor)
        │
        ▼
┌──────────────────────────────┐
│ handleCreateNode()           │
│ (Frontend)                   │
└────────────┬─────────────────┘
             │
             ▼ POST /api/v1/curriculums/{id}/nodes
┌──────────────────────────────────────────┐
│ Backend: NodeService.create_node()       │
│                                          │
│ 1. with_for_update() on parent          │
│    (Race Condition 방지)                │
│                                          │
│ 2. Calculate order_index                │
│    (부모와 형제 노드 조회)              │
│                                          │
│ 3. Create NodeContent (자동)            │
│                                          │
│ 4. Create Node                          │
│                                          │
│ 5. db.commit() (트랜잭션 종료)          │
└────────────┬────────────────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ SQLite DB Update             │
│ - nodes 테이블에 레코드 추가  │
│ - node_contents 자동 생성     │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Response 반환                │
│ {node_id, order_index, ...}  │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Frontend State Update        │
│ - Node list 새로고침         │
│ - UI 업데이트               │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Trigger: syncAfterLocalChange()
│ (Sync 대기열에 추가)         │
└────────────┬─────────────────┘
             │
             ▼ Google Drive API
┌──────────────────────────────┐
│ Sync 시작                    │
│ - PUSH: 로컬 DB 업로드      │
└──────────────────────────────┘
```

### 3.2 DELETE: 노드 삭제 (Soft Deletion)

```
User Input (Delete Button)
        │
        ▼
┌──────────────────────────────────┐
│ handleDeleteNode()               │
│ (Frontend)                       │
└────────────┬─────────────────────┘
             │
             ▼ DELETE /api/v1/nodes/{node_id}
┌────────────────────────────────────────────┐
│ Backend: NodeService.delete_node()         │
│                                            │
│ 1. Get all descendant IDs recursively      │
│    (모든 하위 노드 조회)                  │
│                                            │
│ 2. Soft delete nodes                      │
│    UPDATE nodes SET deleted_at = NOW()    │
│                                            │
│ 3. Soft delete contents                   │
│    UPDATE node_contents SET deleted_at... │
│                                            │
│ 4. Soft delete links                      │
│    UPDATE node_links SET deleted_at...    │
│                                            │
│ 5. db.commit()                            │
└────────────┬─────────────────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ SQLite DB Update             │
│ - deleted_at 타임스탬프 설정  │
│ - 데이터는 DB에 남아있음     │
└────────────┬─────────────────┘
             │
             ▼
┌──────────────────────────────┐
│ Response 204 No Content      │
└────────────┬─────────────────┘
             │
             ▼ syncAfterLocalChange()
┌──────────────────────────────┐
│ Google Drive Sync            │
│ - 삭제된 DB → Google Drive   │
└──────────────────────────────┘
```

### 3.3 SYNC: 다중 기기 동기화

```
Device A (iPhone)                  Device B (iPad)
┌──────────────────────┐          ┌──────────────────────┐
│ App Start            │          │ App Start            │
│ syncManager.         │          │ syncManager.         │
│ autoSync()           │          │ autoSync()           │
└─────────┬────────────┘          └──────────┬───────────┘
          │                                  │
          ▼                                  ▼
┌─────────────────────────────────────────────────────────┐
│                Backend: SyncService                     │
│                                                         │
│  1. Read last_synced_drive_timestamp from LocalStorage │
│     Device A: "2025-11-15T10:00:00Z"                  │
│     Device B: "2025-11-15T10:00:00Z"                  │
│                                                         │
│  2. Call Google Drive API to get file metadata         │
│     current_drive_timestamp = "2025-11-15T11:30:00Z"  │
│                                                         │
│  3. Compare timestamps                                 │
│     device_timestamp vs drive_timestamp                │
└──────────────────┬──────────────────────┬──────────────┘
                   │                      │
        ┌──────────▼──────────┐           │
        │ device_ts < drive_ts│           │
        │ (Drive is newer)    │           │
        │ → PULL              │           │
        └──────────┬──────────┘           │
                   │                      │
                   ▼                      ▼
        ┌──────────────────────┐ ┌──────────────────────┐
        │ PULL                 │ │ device_ts == drive_ts│
        │ - Backup local DB    │ │ → PUSH               │
        │ - Download from Drive│ │ - Upload to Drive    │
        │ - Reload app state   │ └──────────┬───────────┘
        │ - Notify user        │            │
        └──────────┬───────────┘            ▼
                   │              ┌──────────────────────┐
                   │              │ PUSH Success         │
                   │              │ - Upload to Drive    │
                   │              │ - Update timestamp   │
                   │              └──────────┬───────────┘
                   │                         │
                   │                 [Device B now has
                   │                  the latest DB]
                   │
        [Device A now has
         the latest DB]
```

### 3.4 CONFLICT: 동시 수정 감지

```
Timeline:

2025-11-15T10:00:00Z
Device A 마지막 동기화: ts = 10:00
Device B 마지막 동기화: ts = 10:00
Google Drive: ts = 10:00

2025-11-15T11:00:00Z
Device A: 노드 수정 → PUSH
Google Drive: ts = 11:00

2025-11-15T11:30:00Z
Device B: 노드 수정 → PUSH 시도
  Device B의 local_ts = 10:00
  현재 drive_ts = 11:00

  11:00 > 10:00 → CONFLICT 감지!

Action:
1. Device B의 로컬 파일 백업
   mathesis_lab_conflict_iPad_2025-11-15T11:30:00.db

2. Google Drive에서 최신 버전 강제 다운로드
   (Device A의 변경 사항 포함)

3. Device B 사용자에게 알림
   "충돌 발생! Device A의 변경 사항이 더 최신입니다.
    현재 기기의 변경 사항은 백업되었습니다."

4. 사용자는 나중에 백업 파일을 열어 수동으로 병합 가능
```

---

## 4. API 엔드포인트 (완전)

### 4.1 Node Management APIs

```
# Create
POST   /api/v1/curriculums/{curriculum_id}/nodes
       Request: {title, node_type?, parent_node_id?, description?}
       Response: {node_id, order_index, created_at, ...}

# Read
GET    /api/v1/nodes/{node_id}
       Response: {node_id, title, node_type, content?, links?, children?}

GET    /api/v1/curriculums/{curriculum_id}/nodes
       Query: ?node_type=ASSESSMENT&page=1&limit=20
       Response: {nodes: [...], total, page}

# Update
PUT    /api/v1/nodes/{node_id}
       Request: {title?, node_type?, description?}
       Response: {node_id, updated_at, ...}

# Delete (Soft)
DELETE /api/v1/nodes/{node_id}
       Response: 204 No Content

# Restore
POST   /api/v1/nodes/{node_id}/restore
       Response: {node_id, deleted_at: null, ...}

# Trash/Deleted Nodes
GET    /api/v1/curriculums/{curriculum_id}/trash
       Response: {deleted_nodes: [...]}
```

### 4.2 Content Management APIs

```
# Create/Update Content
POST   /api/v1/nodes/{node_id}/content
       Request: {markdown_content, ai_summary?, manim_guidelines?}
       Response: {content_id, markdown_content, ...}

# Get Content
GET    /api/v1/nodes/{node_id}/content
       Response: {content_id, markdown_content, ...}
```

### 4.3 Link Management APIs

```
# Add YouTube Link
POST   /api/v1/nodes/{node_id}/links/youtube
       Request: {youtube_video_id}
       Response: {link_id, youtube_video_id, ...}

# Add Zotero Link
POST   /api/v1/nodes/{node_id}/links/zotero
       Request: {zotero_item_id}
       Response: {link_id, zotero_item_id, ...}

# Get All Links
GET    /api/v1/nodes/{node_id}/links
       Response: {links: [{link_id, link_type, ...}]}

# Delete Link
DELETE /api/v1/nodes/{node_id}/links/{link_id}
       Response: 204 No Content
```

### 4.4 Sync APIs (NEW)

```
# Initialize Sync
POST   /api/v1/sync/init
       Request: {device_name}
       Response: {device_id, drive_file_id, drive_app_folder_id, timestamp}

# Perform Sync
POST   /api/v1/sync/sync
       Request: {device_id, device_name, sync_metadata}
       Response: {action: PULL|PUSH|CONFLICT, timestamp, message}

# Get Conflicts
GET    /api/v1/sync/conflicts?device_id=...
       Response: {conflict_files: [{file_name, created_at, size}]}

# Resolve Conflict
POST   /api/v1/sync/resolve-conflict/{conflict_file}
       Request: {action: keep_local|use_cloud}
       Response: {status, message}
```

---

## 5. 구현 순서 (Roadmap)

### Phase 1: Node Management System (주 1)

- [ ] 데이터베이스 마이그레이션 (node_type, deleted_at 추가)
- [ ] NodeService 개정 코드 구현 (transaction lock 포함)
- [ ] NodeEditor 컴포넌트 수정 (NodeType Selector 추가)
- [ ] 테스트: Race Condition, Soft Deletion, Query by Type

### Phase 2: GCP 초기 설정 (주 2)

- [ ] Google Cloud Project 생성
- [ ] Service Account 생성 및 키 다운로드
- [ ] Google Drive API 활성화
- [ ] IAM 역할 설정

### Phase 3: Sync Backend 구현 (주 3)

- [ ] DriveServiceManager 구현 (인증, 파일 업로드/다운로드)
- [ ] SyncService 구현 (PULL/PUSH/CONFLICT 로직)
- [ ] Sync API 엔드포인트 구현

### Phase 4: Sync Frontend 통합 (주 4)

- [ ] SyncManager 구현
- [ ] SyncMetadataService 구현
- [ ] autoSync on app start
- [ ] Conflict UI 구현

### Phase 5: 테스트 및 배포 (주 5)

- [ ] 모든 테스트 케이스 통과
- [ ] E2E 테스트 (다중 기기 시뮬레이션)
- [ ] 사용자 문서 작성
- [ ] 프로덕션 배포

---

## 6. 성능 최적화

### 6.1 데이터베이스 인덱스

```sql
-- 빠른 쿼리를 위한 복합 인덱스
CREATE INDEX idx_nodes_curriculum_active
ON nodes(curriculum_id, deleted_at);

CREATE INDEX idx_nodes_parent_active
ON nodes(parent_node_id, deleted_at);

CREATE INDEX idx_nodes_type_active
ON nodes(node_type, deleted_at);

-- LIMIT 쿼리 최적화
CREATE INDEX idx_nodes_order
ON nodes(curriculum_id, parent_node_id, order_index);
```

### 6.2 Eager Loading (N+1 쿼리 방지)

```python
# ❌ Bad: N+1 문제
nodes = db.query(Node).filter(...).all()
for node in nodes:
    content = db.query(NodeContent).filter(...).first()

# ✅ Good: Eager loading
from sqlalchemy.orm import joinedload
nodes = db.query(Node).options(
    joinedload(Node.content),
    joinedload(Node.links)
).filter(...).all()
```

### 6.3 동기화 성능

```python
# SQLite 동기화는 전체 파일 크기만큼
# 예: 10,000 노드 × 1MB = ~10MB
# Google Drive API: 일반적으로 충분한 속도

# Compression (선택사항)
import gzip
with open('mathesis_lab.db', 'rb') as f_in:
    with gzip.open('mathesis_lab.db.gz', 'wb') as f_out:
        shutil.copyfileobj(f_in, f_out)
```

---

## 7. 보안 고려사항

### 7.1 데이터 암호화

```
로컬: SQLCipher로 SQLite 암호화
Google Drive: HTTPS 전송 + GCP 암호화 (자동)
로컬 저장소: LocalStorage (HTTPS only) 또는 Secure Storage
```

### 7.2 인증 보안

```bash
# Service Account 키는 절대 클라이언트에 노출하면 안 됨
# 백엔드에서만 관리

# .env 파일
GCP_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json

# .gitignore
service-account-key.json
.env
```

### 7.3 API 속도 제한

```python
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.util import get_remote_address

# Sync API는 사용자당 1분에 최대 3회 호출 제한
@limiter.limit("3/minute")
@router.post("/sync")
async def sync(...):
    pass
```

---

## 8. 모니터링 및 로깅

### 8.1 Sync 로깅

```python
import logging

logger = logging.getLogger('sync')

async def sync(device_id, ...):
    logger.info(f"Sync started: device={device_id}")

    try:
        result = await sync_service.sync(...)
        logger.info(f"Sync completed: action={result['action']}")
        return result
    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        raise
```

### 8.2 메트릭 수집

```python
from prometheus_client import Counter, Histogram

sync_attempts = Counter(
    'sync_attempts_total',
    'Total sync attempts',
    ['action', 'status']  # PULL|PUSH|CONFLICT, success|failure
)

sync_duration = Histogram(
    'sync_duration_seconds',
    'Sync duration in seconds'
)
```

---

## 9. 요약: 개선의 핵심

| 측면 | 개선 사항 |
|------|---------|
| **데이터 모델** | node_type 명시적 + deleted_at 추프트 |
| **동시성** | Transaction lock (SELECT FOR UPDATE) |
| **삭제 전략** | 일관된 소프트 삭제 + 휴지통 기능 |
| **동기화 단위** | 10,000+ 파일 → 1개 SQLite DB 파일 |
| **PULL/PUSH** | PULL 로직 추가 + 파일 타임스탬프 비교 |
| **충돌 처리** | LWW → 백업 + 사용자 선택 |
| **복잡도** | 극도로 단순화 (Queue, Mapping 제거) |
| **데이터 손실** | 거의 불가능 |

---

## 10. 다음 단계

1. 현재 문서 검토 및 피드백
2. 데이터베이스 마이그레이션 스크립트 작성
3. Phase 1: Node Management 구현 시작
4. 단계적으로 다른 Phases 진행

---

## References

- [SQLAlchemy Transaction Control](https://docs.sqlalchemy.org/en/20/orm/session_transaction.html)
- [Google Drive API v3](https://developers.google.com/drive/api)
- [SQLite File Format](https://www.sqlite.org/fileformat.html)
- [CRDT and Conflict-free Replicated Data Types](https://crdt.tech/)
