# Google Drive 기반 노드 관리 시스템 구현 계획

## 📋 현재 상황 분석

### 문제점
1. **노드 저장소**: SQLite 데이터베이스만 사용 (로컬)
2. **Google Drive 연동**: 구조만 설계됨, API 호출 미구현
3. **동기화**: 다중 기기 동기화 기능 없음
4. **목표**: Google Drive를 중앙 저장소로 사용하는 노드 관리

---

## 🎯 목표

**Google Drive를 MATHESIS LAB의 중앙 저장소로 사용하여:**
1. ✅ 노드를 Google Drive 폴더/파일로 저장
2. ✅ 실시간 동기화 (로컬 DB ↔ Google Drive)
3. ✅ 다중 기기 지원 (여러 기기에서 동시 작업)
4. ✅ 버전 관리 (Google Drive의 버전 히스토리 활용)
5. ✅ 오프라인 작업 (로컬에서 수정 후 온라인 시 동기화)

---

## 🏗️ 아키텍처 설계

### Phase 1: 기본 구조 (1주)
```
┌─────────────────────────────────────────┐
│       Frontend (React + TypeScript)      │
├─────────────────────────────────────────┤
│    Backend (FastAPI + SQLAlchemy)       │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Local SQLite Database         │   │
│  │   (캐시 및 오프라인 작업용)      │   │
│  └─────────────────────────────────┘   │
│                                         │
│  ┌─────────────────────────────────┐   │
│  │   Google Drive Service Layer    │   │
│  │  - OAuth 인증                    │   │
│  │  - File Upload/Download         │   │
│  │  - Sync Logic                   │   │
│  └─────────────────────────────────┘   │
├─────────────────────────────────────────┤
│   Google Drive API (REST)               │
│   - Curriculum 폴더                     │
│   - Node JSON 파일                      │
│   - Metadata 추적                       │
└─────────────────────────────────────────┘
```

### Phase 2: 동기화 로직 (2주)
```
로컬 DB (SQLite)                    Google Drive Storage
    ↓                                      ↓
    │─────── Sync Engine ────────────────→│
    ←─────────────────────────────────────│
         (실시간 양방향 동기화)
```

---

## 📊 구현 계획 (단계별)

### **Phase 1: Google Drive 서비스 계층 구현**

#### 1.1 백엔드: Google Drive Service 클래스
**파일**: `backend/app/services/google_drive_service.py` (새로 생성)

```python
class GoogleDriveService:
    """
    Google Drive API를 통해 노드를 관리하는 서비스
    """

    def __init__(self):
        # Google Drive API 초기화
        self.service = build('drive', 'v3', credentials=credentials)
        self.root_folder_id = os.getenv('GOOGLE_DRIVE_CURRICULUM_FOLDER_ID')

    # 폴더 관리
    async def create_curriculum_folder(curriculum_name: str) -> str:
        """커리큘럼 폴더 생성 및 ID 반환"""

    async def get_curriculum_folder(curriculum_id: UUID) -> str:
        """커리큘럼 폴더 ID 조회"""

    # 파일 관리
    async def save_node_to_drive(node_id: UUID, node_data: dict) -> str:
        """노드를 JSON 파일로 Drive에 저장"""
        # node.json 형식:
        # {
        #   "id": "...",
        #   "title": "...",
        #   "content": "...",
        #   "created_at": "...",
        #   "modified_at": "...",
        #   "children": [...],
        #   "metadata": {...}
        # }

    async def load_node_from_drive(file_id: str) -> dict:
        """Drive의 JSON 파일에서 노드 데이터 로드"""

    async def update_node_on_drive(file_id: str, node_data: dict) -> None:
        """Drive의 노드 파일 업데이트"""

    async def delete_node_from_drive(file_id: str) -> None:
        """Drive의 노드 파일 삭제"""

    # 동기화
    async def list_nodes_on_drive(curriculum_folder_id: str) -> List[dict]:
        """Drive의 노드 목록 조회"""

    async def get_file_metadata(file_id: str) -> dict:
        """파일 메타데이터 조회 (수정 시간 등)"""
```

#### 1.2 백엔드: OAuth 설정
**파일**: `backend/app/core/oauth.py` (수정/확장)

```python
class GoogleDriveOAuth:
    """Google Drive OAuth 인증"""

    @staticmethod
    def get_auth_url(state: str) -> str:
        """사용자를 Google 로그인 화면으로 리디렉트"""

    @staticmethod
    async def exchange_code_for_token(code: str) -> dict:
        """인증 코드를 액세스 토큰으로 교환"""

    @staticmethod
    async def refresh_token(refresh_token: str) -> dict:
        """만료된 토큰 갱신"""
```

#### 1.3 백엔드: API 엔드포인트
**파일**: `backend/app/api/v1/endpoints/google_drive.py` (새로 생성)

```
POST   /google-drive/auth/start           - OAuth 로그인 시작
POST   /google-drive/auth/callback        - OAuth 콜백
POST   /google-drive/sync                 - 동기화 시작
GET    /google-drive/status               - 동기화 상태
POST   /google-drive/logout               - 로그아웃
```

#### 1.4 프론트엔드: Google Drive Service
**파일**: `MATHESIS-LAB_FRONT/services/googleDriveService.ts` (수정/확장)

```typescript
export class GoogleDriveService {
    // OAuth
    static startAuth(): void
    static handleAuthCallback(code: string): Promise<void>

    // 동기화
    static async syncCurriculums(): Promise<void>
    static async syncNodes(curriculumId: string): Promise<void>
    static async getLastSyncTime(): Promise<Date>

    // 상태
    static async getSyncStatus(): Promise<SyncStatus>
    static async isAuthenticated(): Promise<boolean>
}
```

---

### **Phase 2: 동기화 엔진 구현**

#### 2.1 백엔드: 동기화 로직
**파일**: `backend/app/services/sync_engine.py` (새로 생성)

```python
class SyncEngine:
    """
    로컬 DB와 Google Drive 간 양방향 동기화
    """

    async def sync_curriculum(curriculum_id: UUID):
        """
        1. Drive에서 최신 노드 목록 조회
        2. 로컬 DB와 비교
        3. 차이점 분석:
           - Local only: Drive에 업로드
           - Drive only: 로컬에 다운로드
           - Both exist: 수정 시간 기준 최신 버전으로 동기화
           - Conflict: 사용자에게 알림
        4. 메타데이터 업데이트
        """

    async def detect_changes(
        local_nodes: List[Node],
        drive_nodes: List[dict]
    ) -> SyncChanges:
        """로컬과 Drive의 변경사항 감지"""

    async def resolve_conflicts(
        node_id: UUID,
        local_modified: datetime,
        drive_modified: datetime
    ) -> Node:
        """충돌 해결 (최신 버전 선택 또는 병합)"""

    async def upload_local_changes(
        curriculum_id: UUID
    ) -> SyncResult:
        """로컬 변경사항을 Drive에 업로드"""

    async def download_remote_changes(
        curriculum_id: UUID
    ) -> SyncResult:
        """Drive의 변경사항을 로컬에 다운로드"""
```

#### 2.2 백엔드: 동기화 스케줄러
**파일**: `backend/app/core/scheduler.py` (새로 생성)

```python
class SyncScheduler:
    """
    백그라운드에서 정기적으로 동기화 수행
    """

    def start_background_sync():
        """5분마다 동기화 체크"""

    def trigger_manual_sync(curriculum_id: UUID):
        """수동 동기화 트리거"""

    def handle_sync_error(error: Exception):
        """동기화 실패 처리"""
```

#### 2.3 프론트엔드: 동기화 상태 관리
**파일**: `MATHESIS-LAB_FRONT/hooks/useSyncStatus.ts` (새로 생성)

```typescript
export function useSyncStatus() {
    const [syncStatus, setSyncStatus] = useState<SyncStatus>('idle')
    const [lastSyncTime, setLastSyncTime] = useState<Date | null>(null)
    const [syncProgress, setSyncProgress] = useState(0)
    const [syncErrors, setSyncErrors] = useState<string[]>([])

    async function triggerSync() {
        setSyncStatus('syncing')
        try {
            await GoogleDriveService.syncCurriculums()
            setSyncStatus('success')
        } catch (error) {
            setSyncStatus('error')
            setSyncErrors([...syncErrors, error.message])
        }
    }

    return {
        syncStatus,
        lastSyncTime,
        syncProgress,
        syncErrors,
        triggerSync
    }
}
```

---

### **Phase 3: 데이터 모델 업데이트**

#### 3.1 백엔드: DB 모델 추가
**파일**: `backend/app/models/models.py` (수정)

```python
class SyncMetadata(Base):
    """동기화 메타데이터"""
    __tablename__ = "sync_metadata"

    id: UUID
    curriculum_id: UUID          # 어느 커리큘럼
    node_id: UUID                # 어느 노드
    google_drive_file_id: str    # Drive의 파일 ID
    last_local_modified: datetime
    last_drive_modified: datetime
    last_sync_time: datetime
    sync_status: str             # 'synced', 'pending', 'conflict'

    curriculum = relationship("Curriculum", back_populates="sync_metadata")
    node = relationship("Node", back_populates="sync_metadata")

class CurriculumDriveFolder(Base):
    """커리큘럼과 Drive 폴더의 매핑"""
    __tablename__ = "curriculum_drive_folders"

    id: UUID
    curriculum_id: UUID
    google_drive_folder_id: str  # Drive 폴더 ID
    created_at: datetime
    updated_at: datetime
```

#### 3.2 프론트엔드: 타입 정의 추가
**파일**: `MATHESIS-LAB_FRONT/types.ts` (수정)

```typescript
interface SyncStatus {
    status: 'idle' | 'syncing' | 'success' | 'error'
    lastSyncTime?: Date
    progress: number            // 0-100
    pendingChanges: number
    conflicts: ConflictItem[]
}

interface ConflictItem {
    nodeId: string
    localModified: Date
    driveModified: Date
    action: 'use-local' | 'use-drive' | 'merge'
}
```

---

## 🔧 필수 환경 설정

### Backend .env
```bash
# Google Drive OAuth
GOOGLE_DRIVE_CLIENT_ID=your-client-id
GOOGLE_DRIVE_CLIENT_SECRET=your-client-secret
GOOGLE_DRIVE_REDIRECT_URI=http://localhost:8000/api/v1/google-drive/auth/callback

# Google Drive 저장소
GOOGLE_DRIVE_CURRICULUM_FOLDER_ID=root  # 커리큘럼을 저장할 루트 폴더

# 동기화 설정
SYNC_INTERVAL_MINUTES=5                 # 자동 동기화 간격
MAX_SYNC_RETRIES=3                      # 최대 재시도 횟수
CONFLICT_RESOLUTION_MODE=manual          # manual | auto_latest | auto_local
```

### Frontend .env.local
```bash
VITE_GOOGLE_DRIVE_CLIENT_ID=your-client-id
VITE_GOOGLE_DRIVE_REDIRECT_URI=http://localhost:3002/auth/google-drive/callback
```

---

## 📁 파일 구조 변경

```
backend/
  app/
    api/v1/endpoints/
      ├── google_drive.py          # NEW
      ├── curriculums.py           # (기존)
      └── nodes.py                 # (수정: Drive 필드 추가)

    services/
      ├── google_drive_service.py  # NEW
      ├── sync_engine.py           # NEW
      ├── curriculum_service.py    # (수정)
      └── node_service.py          # (수정)

    core/
      ├── oauth.py                 # NEW/수정
      ├── scheduler.py             # NEW
      └── config.py                # (수정: Drive 설정 추가)

    models/
      └── models.py                # (수정: SyncMetadata 추가)

MATHESIS-LAB_FRONT/
  services/
    ├── googleDriveService.ts      # NEW/수정
    └── ...

  hooks/
    └── useSyncStatus.ts           # NEW

  components/
    ├── SyncStatusIndicator.tsx    # NEW
    ├── ConflictResolver.tsx       # NEW
    └── ...
```

---

## 🚀 구현 순서

### **Week 1: Phase 1 - 기본 구조**
1. Google Drive OAuth 설정
2. GoogleDriveService 클래스 구현
3. API 엔드포인트 작성
4. 프론트엔드 GoogleDriveService 클래스 구현
5. UI: 로그인 버튼 추가

### **Week 2: Phase 2 - 동기화 엔진**
1. SyncEngine 클래스 구현
2. 동기화 로직 (업로드/다운로드)
3. 충돌 해결 로직
4. 백그라운드 스케줄러
5. 프론트엔드 동기화 UI

### **Week 3: Phase 3 - 테스트 및 최적화**
1. 단위 테스트 작성
2. E2E 테스트 작성
3. 성능 최적화
4. 에러 처리 강화
5. 문서화

---

## 🧪 테스트 계획

### 백엔드 테스트
```
backend/tests/
  integration/
    ├── test_google_drive_oauth.py
    ├── test_google_drive_service.py
    ├── test_sync_engine.py
    └── test_sync_scenarios.py
```

### 프론트엔드 테스트
```
MATHESIS-LAB_FRONT/
  ├── services/__tests__/
  │   └── googleDriveService.test.ts
  └── hooks/__tests__/
      └── useSyncStatus.test.ts
```

### E2E 테스트 (Playwright)
```
e2e/pages/
  └── google-drive-sync/
      └── sync.spec.ts
```

---

## 📈 예상 일정

| Phase | 작업 | 기간 | 상태 |
|-------|------|------|------|
| 1 | 기본 구조 (OAuth + Service) | 1주 | 대기 |
| 2 | 동기화 엔진 | 2주 | 대기 |
| 3 | 테스트 & 최적화 | 1주 | 대기 |
| **총합** | **Google Drive 기반 노드 관리** | **4주** | |

---

## ✅ 성공 기준

- [ ] Google Drive에 커리큘럼 폴더 생성
- [ ] 노드를 JSON으로 Drive에 저장
- [ ] 로컬 ↔ Drive 양방향 동기화
- [ ] 다중 기기 동기화 지원
- [ ] 충돌 감지 및 해결
- [ ] 오프라인 작업 지원
- [ ] 모든 테스트 통과
- [ ] 문서화 완료

---

## 🎯 최종 목표

**현재 상태**:
```
로컬 SQLite DB
    ↓
Basic CRUD (Create, Read, Update, Delete)
```

**변경 후**:
```
로컬 SQLite DB (캐시)
    ↓
Google Drive (중앙 저장소)
    ↓
다중 기기 동기화 + 버전 관리
```

---

**마지막 업데이트**: 2025-11-17
**작성자**: Claude Code (계획 수립)
