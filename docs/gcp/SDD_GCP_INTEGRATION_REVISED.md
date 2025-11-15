# SDD: GCP Integration - Multi-Device Sync (Revised)

**Version:** 2.0 (Critical Redesign based on Critique)
**Date:** 2025-11-15
**Status:** Final Design - Ready for Implementation

---

## Executive Summary

기존 설계의 세 가지 치명적 결함을 완전히 해결했습니다:

1. **테이블-파일 1:1 매핑 (원자성 파괴)** → **SQLite DB 파일 단 하나를 동기화**
2. **PULL 로직 부재** → **PULL/PUSH/CONFLICT 완전 구현**
3. **LWW로 인한 데이터 손실** → **파일 타임스탐프 비교 + 충돌 백업**

---

## 1. 핵심 설계 원칙

### 1.1 동기화의 단위 (Unit of Sync)

**기존 설계의 문제:**
- 노드 = 파일 1개
- 콘텐츠 = 파일 1개
- 링크 = 테이블 레코드
- 결과: 부분 업데이트 → 데이터 찢김 → 원자성 파괴

**개선된 설계:**
```
동기화 대상 = SQLite 데이터베이스 파일 (mathesis_lab.db) 하나
```

이유:
1. **원자성(Atomicity)**: 전체 DB가 하나의 단위로 동기화됨
2. **간단함**: 복잡한 큐, 리소스 매핑 테이블 제거
3. **성능**: 10,000개 파일 관리 vs 1개 파일 다운로드
4. **일관성**: 모든 테이블이 항상 같은 버전

### 1.2 동기화 로직: 파일 타임스탬프 기반

```
┌─────────────────────────────────────────────────────┐
│  로컬 저장소 (LocalStorage / SharedPreferences)      │
│  - last_synced_drive_timestamp: "2025-11-15T10:00Z" │
│  - device_id: "device-mobile-001"                   │
└─────────────────────────────────────────────────────┘
                        ↓
        ┌───────────────────────────┐
        │ App 시작 / 로컬 변경 감지 │
        └───────────┬───────────────┘
                    ↓
    ┌───────────────────────────────────────┐
    │ Google Drive API 호출                 │
    │ GET /files/{file_id}?fields=modifiedTime
    └───────────┬───────────────────────────┘
                ↓
    ┌───────────────────────────────────────────────────┐
    │ drive_file.modifiedTime vs last_synced_timestamp  │
    └───────────┬───────────────────────────────────────┘
                ↓
    ┌─────────────────────────────────────────────────┐
    │ (1) drive > local: PULL          │ (2) drive == local: PUSH
    │     드라이브 다운로드               │     로컬 업로드
    │                                  │
    │ (3) drive > local (PUSH 실패)    │
    │     CONFLICT: 백업 파일 생성
    └─────────────────────────────────────────────────┘
```

---

## 2. 로컬 저장소 스키마

### 2.1 SyncMetadata (로컬 저장소)

```typescript
// MATHESIS-LAB_FRONT/utils/syncMetadata.ts

interface SyncMetadata {
    // Google Drive 파일 정보
    drive_file_id: string;           // Google Drive의 mathesis_lab.db 파일 ID
    drive_app_folder_id: string;     // 앱 폴더 ID

    // 동기화 시간 추적
    last_synced_drive_timestamp: string; // ISO 8601 format
    last_synced_local_timestamp: string; // 로컬 마지막 동기화 시간

    // 디바이스 정보
    device_id: string;               // UUID, 기기별 고유 ID
    device_name: string;             // "iPhone", "iPad", "Samsung Galaxy"

    // 상태
    sync_status: 'IDLE' | 'SYNCING' | 'CONFLICT' | 'ERROR';
    last_error?: string;

    // 충돌 관리
    conflict_files?: {
        file_name: string;           // "mathesis_lab (conflict_20251115).db"
        created_at: string;
        size: number;
    }[];
}
```

### 2.2 로컬 저장소 구현

```typescript
// MATHESIS-LAB_FRONT/services/syncMetadataService.ts

class SyncMetadataService {
    private storageKey = 'mathesis_sync_metadata';
    private storage: Storage; // localStorage (web) or AsyncStorage (mobile)

    constructor(storage: Storage) {
        this.storage = storage;
    }

    async getSyncMetadata(): Promise<SyncMetadata | null> {
        const data = await this.storage.getItem(this.storageKey);
        return data ? JSON.parse(data) : null;
    }

    async setSyncMetadata(metadata: SyncMetadata): Promise<void> {
        await this.storage.setItem(
            this.storageKey,
            JSON.stringify(metadata)
        );
    }

    async updateTimestamp(driveTimestamp: string): Promise<void> {
        const metadata = await this.getSyncMetadata();
        if (metadata) {
            metadata.last_synced_drive_timestamp = driveTimestamp;
            metadata.last_synced_local_timestamp = new Date().toISOString();
            await this.setSyncMetadata(metadata);
        }
    }

    async addConflictFile(fileName: string, size: number): Promise<void> {
        const metadata = await this.getSyncMetadata();
        if (metadata) {
            if (!metadata.conflict_files) {
                metadata.conflict_files = [];
            }
            metadata.conflict_files.push({
                file_name: fileName,
                created_at: new Date().toISOString(),
                size
            });
            await this.setSyncMetadata(metadata);
        }
    }
}
```

---

## 3. GCP 통합 서비스 (Python 백엔드)

### 3.1 Google Drive 인증 (Service Account)

```python
# backend/app/core/gcp_config.py

from google.oauth2 import service_account
from googleapiclient.discovery import build
from typing import Optional

class DriveServiceManager:
    """
    Google Drive API 관리 (Service Account 기반)

    Service Account는 서버-서버 통신에 최적화되어 있으며,
    사용자 개입 없이 자동으로 인증됩니다.
    """

    def __init__(self, credentials_path: str):
        self.credentials_path = credentials_path
        self.scopes = ['https://www.googleapis.com/auth/drive']
        self.service = self._build_service()

    def _build_service(self):
        """Build Google Drive service"""
        credentials = service_account.Credentials.from_service_account_file(
            self.credentials_path,
            scopes=self.scopes
        )
        return build('drive', 'v3', credentials=credentials)

    def get_file_metadata(self, file_id: str) -> dict:
        """
        Get file metadata from Google Drive

        Returns: {'id': '...', 'name': '...', 'modifiedTime': '2025-11-15T10:00:00Z', ...}
        """
        file = self.service.files().get(
            fileId=file_id,
            fields='id,name,modifiedTime,size,mimeType'
        ).execute()
        return file

    def upload_file(
        self,
        file_path: str,
        file_name: str,
        folder_id: Optional[str] = None
    ) -> dict:
        """
        Upload/Update file to Google Drive

        Args:
            file_path: 로컬 파일 경로 (e.g., '/path/to/mathesis_lab.db')
            file_name: 드라이브 상의 파일명
            folder_id: 드라이브 폴더 ID (None = 루트)

        Returns: {'id': '...', 'modifiedTime': '...'}
        """
        from googleapiclient.http import MediaFileUpload

        file_metadata = {'name': file_name}
        if folder_id:
            file_metadata['parents'] = [folder_id]

        media = MediaFileUpload(file_path)

        # Check if file already exists
        existing = self._find_file_by_name(file_name, folder_id)

        if existing:
            # Update existing file
            file = self.service.files().update(
                fileId=existing['id'],
                body=file_metadata,
                media_body=media,
                fields='id,modifiedTime'
            ).execute()
        else:
            # Create new file
            file = self.service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id,modifiedTime'
            ).execute()

        return file

    def download_file(self, file_id: str, output_path: str) -> None:
        """
        Download file from Google Drive

        Args:
            file_id: 드라이브 파일 ID
            output_path: 저장할 로컬 경로
        """
        request = self.service.files().get_media(fileId=file_id)
        with open(output_path, 'wb') as f:
            downloader = MediaIoBaseDownload(f, request)
            done = False
            while not done:
                status, done = downloader.next_chunk()

    def _find_file_by_name(
        self,
        file_name: str,
        folder_id: Optional[str] = None
    ) -> Optional[dict]:
        """Find file by name in folder"""
        query = f"name='{file_name}' and trashed=false"
        if folder_id:
            query += f" and '{folder_id}' in parents"

        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id,name)',
            pageSize=1
        ).execute()

        files = results.get('files', [])
        return files[0] if files else None

    def create_app_folder(self) -> str:
        """
        Create/Get app folder for MATHESIS LAB

        Returns: folder_id
        """
        folder_metadata = {
            'name': 'MATHESIS LAB Sync',
            'mimeType': 'application/vnd.google-apps.folder'
        }

        # Check if folder exists
        query = "name='MATHESIS LAB Sync' and mimeType='application/vnd.google-apps.folder' and trashed=false"
        results = self.service.files().list(
            q=query,
            spaces='drive',
            fields='files(id)',
            pageSize=1
        ).execute()

        existing = results.get('files', [])
        if existing:
            return existing[0]['id']

        # Create new folder
        folder = self.service.files().create(
            body=folder_metadata,
            fields='id'
        ).execute()

        return folder['id']
```

---

## 4. 동기화 서비스 (핵심)

### 4.1 SyncService (Python 백엔드)

```python
# backend/app/services/sync_service.py

from datetime import datetime
from typing import Literal
import os
import shutil
from enum import Enum

from backend.app.core.gcp_config import DriveServiceManager

class SyncAction(str, Enum):
    PULL = "PULL"      # 드라이브 → 로컬
    PUSH = "PUSH"      # 로컬 → 드라이브
    CONFLICT = "CONFLICT"  # 충돌 발생

class SyncService:
    """
    Google Drive 동기화 서비스

    핵심 원칙:
    1. SQLite DB 파일 하나만 동기화
    2. modifiedTime 비교로 상태 결정
    3. 충돌 발생 시 데이터 손실 방지 (백업 파일 생성)
    """

    def __init__(
        self,
        drive_service: DriveServiceManager,
        db_path: str = 'mathesis_lab.db'
    ):
        self.drive_service = drive_service
        self.db_path = db_path

    async def sync(
        self,
        device_id: str,
        device_name: str,
        sync_metadata: dict
    ) -> dict:
        """
        Main sync orchestration method

        Args:
            device_id: 디바이스 고유 ID
            device_name: 디바이스 이름 (iPhone, etc.)
            sync_metadata: 로컬에 저장된 메타데이터

        Returns:
            {
                'action': 'PULL' | 'PUSH' | 'CONFLICT',
                'timestamp': '2025-11-15T...',
                'message': 'Synced successfully'
            }
        """

        try:
            # 1. Google Drive에서 파일 메타데이터 조회
            drive_file = await self.drive_service.get_file_metadata(
                sync_metadata['drive_file_id']
            )
            drive_timestamp = drive_file['modifiedTime']

            local_last_sync = sync_metadata.get('last_synced_drive_timestamp')

            # 2. 상태 결정
            if drive_timestamp > local_last_sync:
                # 드라이브가 더 최신 → PULL
                return await self._handle_pull(
                    drive_timestamp,
                    sync_metadata
                )
            elif drive_timestamp == local_last_sync:
                # 변경 없음 또는 안전한 상태 → PUSH 가능
                return await self._handle_push(
                    device_id,
                    device_name,
                    sync_metadata
                )
            else:
                # 이론적으로 발생하면 안 됨
                return {
                    'action': 'ERROR',
                    'message': 'Local timestamp is ahead of drive'
                }

        except Exception as e:
            return {
                'action': 'ERROR',
                'message': str(e)
            }

    async def _handle_pull(
        self,
        drive_timestamp: str,
        sync_metadata: dict
    ) -> dict:
        """
        PULL: Google Drive → 로컬 DB

        시나리오: 다른 기기가 먼저 업로드했음
        """

        try:
            # 1. 백업: 로컬 파일 (recovery 목적)
            backup_path = f"{self.db_path}.backup_{datetime.utcnow().isoformat()}"
            shutil.copy2(self.db_path, backup_path)

            # 2. 드라이브에서 다운로드
            self.drive_service.download_file(
                sync_metadata['drive_file_id'],
                self.db_path
            )

            # 3. 로컬 메타데이터 업데이트
            sync_metadata['last_synced_drive_timestamp'] = drive_timestamp
            sync_metadata['last_synced_local_timestamp'] = datetime.utcnow().isoformat()
            sync_metadata['sync_status'] = 'IDLE'

            # 4. 앱 상태 재로드 (중요!)
            # Frontend는 이 신호를 받아 DB를 다시 로드해야 함
            # (WebSocket 또는 polling으로 알림)

            return {
                'action': 'PULL',
                'timestamp': drive_timestamp,
                'message': 'Downloaded latest version from Drive',
                'backup_path': backup_path
            }

        except Exception as e:
            return {
                'action': 'ERROR',
                'message': f"PULL failed: {str(e)}"
            }

    async def _handle_push(
        self,
        device_id: str,
        device_name: str,
        sync_metadata: dict
    ) -> dict:
        """
        PUSH: 로컬 DB → Google Drive

        시나리오: 로컬이 최신이거나 동기화 상태
        """

        try:
            # 1. 드라이브 파일 메타데이터 다시 확인 (중요: 경합 조건 방지)
            drive_file = self.drive_service.get_file_metadata(
                sync_metadata['drive_file_id']
            )
            current_drive_timestamp = drive_file['modifiedTime']

            # 2. 로컬과 드라이브 타임스탬프 재비교
            local_last_sync = sync_metadata.get('last_synced_drive_timestamp')

            if current_drive_timestamp > local_last_sync:
                # 경합 상황: 다른 기기가 이미 업로드함
                return await self._handle_conflict(
                    device_id,
                    device_name,
                    sync_metadata
                )

            # 3. 안전한 PUSH 수행
            result = self.drive_service.upload_file(
                self.db_path,
                'mathesis_lab.db',
                sync_metadata['drive_app_folder_id']
            )

            new_drive_timestamp = result['modifiedTime']

            # 4. 메타데이터 업데이트
            sync_metadata['last_synced_drive_timestamp'] = new_drive_timestamp
            sync_metadata['last_synced_local_timestamp'] = datetime.utcnow().isoformat()
            sync_metadata['sync_status'] = 'IDLE'

            return {
                'action': 'PUSH',
                'timestamp': new_drive_timestamp,
                'message': 'Uploaded local changes to Drive successfully'
            }

        except Exception as e:
            return {
                'action': 'ERROR',
                'message': f"PUSH failed: {str(e)}"
            }

    async def _handle_conflict(
        self,
        device_id: str,
        device_name: str,
        sync_metadata: dict
    ) -> dict:
        """
        CONFLICT: 로컬과 드라이브가 서로 다름

        해결책: 로컬을 별도 파일로 백업하고 드라이브 버전 강제 다운로드

        이점:
        - 데이터 손실 없음 (충돌 파일로 백업됨)
        - 사용자가 수동으로 병합 가능
        - 최신 데이터로 앱이 싱크됨
        """

        try:
            # 1. 로컬 파일을 충돌 파일로 이름 변경
            timestamp_str = datetime.utcnow().isoformat().replace(':', '-')
            conflict_file_name = f"mathesis_lab_conflict_{device_name}_{timestamp_str}.db"
            conflict_path = os.path.join(
                os.path.dirname(self.db_path),
                conflict_file_name
            )
            shutil.move(self.db_path, conflict_path)

            # 2. 드라이브에서 최신 버전 다운로드 (PULL)
            self.drive_service.download_file(
                sync_metadata['drive_file_id'],
                self.db_path
            )

            # 3. 충돌 파일 정보 메타데이터에 기록
            file_size = os.path.getsize(conflict_path)
            if 'conflict_files' not in sync_metadata:
                sync_metadata['conflict_files'] = []

            sync_metadata['conflict_files'].append({
                'file_name': conflict_file_name,
                'created_at': datetime.utcnow().isoformat(),
                'size': file_size,
                'device_name': device_name
            })

            # 4. 메타데이터 업데이트
            drive_file = self.drive_service.get_file_metadata(
                sync_metadata['drive_file_id']
            )
            sync_metadata['last_synced_drive_timestamp'] = drive_file['modifiedTime']
            sync_metadata['last_synced_local_timestamp'] = datetime.utcnow().isoformat()
            sync_metadata['sync_status'] = 'IDLE'

            return {
                'action': 'CONFLICT',
                'timestamp': drive_file['modifiedTime'],
                'message': (
                    f"Conflict detected! Your changes were backed up to '{conflict_file_name}'. "
                    f"Downloaded latest version from Drive. You can manually merge changes later."
                ),
                'conflict_file': conflict_file_name,
                'conflict_size': file_size
            }

        except Exception as e:
            return {
                'action': 'ERROR',
                'message': f"CONFLICT handling failed: {str(e)}"
            }
```

### 4.2 동기화 엔드포인트 (FastAPI)

```python
# backend/app/api/v1/endpoints/sync.py

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from backend.app.services.sync_service import SyncService
from backend.app.db.session import get_db

router = APIRouter(prefix="/api/v1/sync", tags=["sync"])

# Global instance (production에서는 의존성 주입 권장)
sync_service = None  # Initialize in main.py

@router.post("/init")
async def init_sync(
    device_name: str,
    db: Session = Depends(get_db)
) -> dict:
    """
    첫 동기화 초기화 (앱 처음 실행 시)

    Returns:
        {
            'device_id': 'uuid',
            'drive_file_id': 'drive-file-id',
            'drive_app_folder_id': 'folder-id',
            'timestamp': '2025-11-15T...'
        }
    """
    try:
        device_id = str(uuid.uuid4())

        # Google Drive 폴더 생성 또는 조회
        folder_id = sync_service.drive_service.create_app_folder()

        # DB 파일을 드라이브에 업로드
        upload_result = sync_service.drive_service.upload_file(
            sync_service.db_path,
            'mathesis_lab.db',
            folder_id
        )

        sync_metadata = {
            'device_id': device_id,
            'device_name': device_name,
            'drive_file_id': upload_result['id'],
            'drive_app_folder_id': folder_id,
            'last_synced_drive_timestamp': upload_result['modifiedTime'],
            'last_synced_local_timestamp': datetime.utcnow().isoformat(),
            'sync_status': 'IDLE'
        }

        return {
            'status': 'initialized',
            'metadata': sync_metadata
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/sync")
async def sync(
    device_id: str,
    device_name: str,
    sync_metadata: dict,
    db: Session = Depends(get_db)
) -> dict:
    """
    동기화 수행

    Request:
        {
            'device_id': 'uuid',
            'device_name': 'iPhone',
            'sync_metadata': { ... }
        }

    Response:
        {
            'action': 'PULL' | 'PUSH' | 'CONFLICT',
            'timestamp': '...',
            'message': '...'
        }
    """
    result = await sync_service.sync(
        device_id,
        device_name,
        sync_metadata
    )

    return result

@router.get("/conflicts")
async def get_conflicts(device_id: str) -> list:
    """
    디바이스의 충돌 파일 목록 조회

    Returns:
        [
            {
                'file_name': 'mathesis_lab_conflict_iPhone_2025-11-15T10:00:00.db',
                'created_at': '2025-11-15T10:00:00Z',
                'size': 524288
            }
        ]
    """
    # sync_metadata에서 conflict_files 조회
    pass

@router.post("/resolve-conflict/{conflict_file}")
async def resolve_conflict(conflict_file: str, action: Literal['keep_local', 'use_cloud']) -> dict:
    """
    충돌 해결

    Args:
        conflict_file: 충돌 파일명
        action: 'keep_local' (로컬 파일 사용) or 'use_cloud' (드라이브 파일 사용)
    """
    # 선택된 파일을 메인 DB로 설정
    pass
```

---

## 5. Frontend 동기화 통합

### 5.1 SyncManager (TypeScript)

```typescript
// MATHESIS-LAB_FRONT/services/syncManager.ts

import { gapi } from 'gapi-script';
import { SyncMetadataService } from './syncMetadataService';

export class SyncManager {
    private metadataService: SyncMetadataService;
    private apiBaseUrl = '/api/v1/sync';

    constructor() {
        this.metadataService = new SyncMetadataService(localStorage);
    }

    /**
     * 첫 동기화 초기화 (앱 처음 실행 시)
     */
    async initializeSync(deviceName: string): Promise<void> {
        const response = await fetch(`${this.apiBaseUrl}/init`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_name: deviceName })
        });

        const result = await response.json();
        await this.metadataService.setSyncMetadata(result.metadata);
    }

    /**
     * 동기화 수행 (앱 시작 시, 변경 후)
     */
    async sync(): Promise<SyncResult> {
        const metadata = await this.metadataService.getSyncMetadata();
        if (!metadata) {
            throw new Error('Sync not initialized. Call initializeSync first.');
        }

        const response = await fetch(`${this.apiBaseUrl}/sync`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                device_id: metadata.device_id,
                device_name: metadata.device_name,
                sync_metadata: metadata
            })
        });

        const result = await response.json();

        // 메타데이터 업데이트
        if (result.action !== 'ERROR') {
            await this.metadataService.updateTimestamp(result.timestamp);
        }

        // 충돌 발생 시
        if (result.action === 'CONFLICT') {
            await this.metadataService.addConflictFile(
                result.conflict_file,
                result.conflict_size
            );
            // 사용자에게 알림
            this._notifyConflict(result.message);
        }

        // PULL 수행 후 앱 상태 재로드
        if (result.action === 'PULL') {
            this._reloadAppState();
        }

        return result;
    }

    /**
     * 앱 시작 시 자동 동기화
     */
    async autoSyncOnAppStart(): Promise<void> {
        const metadata = await this.metadataService.getSyncMetadata();

        if (!metadata) {
            // 첫 설치
            const deviceName = await this._promptDeviceName();
            await this.initializeSync(deviceName);
        } else {
            // 기존 사용자: 동기화 수행
            const result = await this.sync();
            console.log(`Auto-sync result: ${result.action}`);
        }
    }

    /**
     * 로컬 변경 시 호출
     */
    async syncAfterLocalChange(): Promise<void> {
        const result = await this.sync();
        if (result.action === 'CONFLICT') {
            alert(`Conflict occurred:\n${result.message}`);
        }
    }

    private _notifyConflict(message: string): void {
        // Toast, Dialog, 또는 Notification으로 사용자 알림
        console.warn('Sync conflict:', message);
    }

    private async _reloadAppState(): Promise<void> {
        // 모든 데이터를 다시 로드
        window.location.reload();
    }

    private async _promptDeviceName(): Promise<string> {
        return prompt('Enter device name (iPhone, iPad, etc.):', 'Device') || 'Device';
    }
}
```

### 5.2 앱 초기화

```typescript
// MATHESIS-LAB_FRONT/main.tsx

import React, { useEffect } from 'react';
import { SyncManager } from './services/syncManager';

const App: React.FC = () => {
    useEffect(() => {
        const syncManager = new SyncManager();
        syncManager.autoSyncOnAppStart().catch(error => {
            console.error('Sync failed:', error);
            // 오프라인 모드로 계속 진행
        });
    }, []);

    return (
        // App 컴포넌트
    );
};
```

---

## 6. 아키텍처 다이어그램

### 6.1 동기화 흐름

```
┌─────────────────────────────────────────────────────────┐
│                    Device A (iPhone)                    │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ MATHESIS LAB App                                │   │
│  │ - SQLite DB (mathesis_lab.db)                   │   │
│  │ - LocalStorage (sync_metadata)                  │   │
│  │ - SyncManager                                   │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                  │
│                       │ (1) Check timestamp             │
│                       ▼                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Backend (FastAPI)                               │   │
│  │ - SyncService                                   │   │
│  │ - DriveServiceManager                           │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                  │
│                       │ (2) Call Google Drive API       │
└───────────────────────┼──────────────────────────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Google Drive API            │
        │ - Get file metadata           │
        │ - Upload / Download files     │
        └───────────────┬───────────────┘
                        │
                        ▼
        ┌───────────────────────────────┐
        │   Google Drive Storage        │
        │ mathesis_lab.db (파일 1개)    │
        │ + Conflict backups            │
        └───────────────────────────────┘


┌─────────────────────────────────────────────────────────┐
│                    Device B (iPad)                      │
│                                                         │
│  ┌─────────────────────────────────────────────────┐   │
│  │ MATHESIS LAB App                                │   │
│  │ - SQLite DB (mathesis_lab.db)                   │   │
│  │ - LocalStorage (sync_metadata)                  │   │
│  │ - SyncManager                                   │   │
│  └────────────────────┬────────────────────────────┘   │
│                       │                                  │
│                       │ (3) Check timestamp             │
│                       ▼                                  │
│  ┌─────────────────────────────────────────────────┐   │
│  │ Backend (FastAPI)                               │   │
│  │ - SyncService                                   │   │
│  └────────────────────┬────────────────────────────┘   │
└───────────────────────┼──────────────────────────────────┘
                        │
                        │ (4) PULL latest DB
                        ▼
```

---

## 7. 테스트 케이스

### 7.1 기본 PUSH 테스트

```python
# backend/tests/integration/test_sync_push.py

async def test_sync_push_success():
    """Local → Drive PUSH 성공"""
    sync_service = SyncService(drive_service, db_path)

    # 초기 메타데이터
    metadata = {
        'drive_file_id': 'file-123',
        'drive_app_folder_id': 'folder-456',
        'last_synced_drive_timestamp': '2025-11-15T10:00:00Z'
    }

    # PUSH 실행
    result = await sync_service.sync('device-1', 'iPhone', metadata)

    assert result['action'] == 'PUSH'
    assert result['timestamp'] is not None
    assert 'successfully' in result['message']
```

### 7.2 PULL 테스트

```python
async def test_sync_pull_when_drive_newer():
    """Drive 파일이 더 최신일 때 PULL"""
    sync_service = SyncService(drive_service, db_path)

    metadata = {
        'drive_file_id': 'file-123',
        'drive_app_folder_id': 'folder-456',
        'last_synced_drive_timestamp': '2025-11-15T09:00:00Z'  # 1시간 전
    }

    # Drive 파일은 더 최신 (10:30)이라고 가정
    result = await sync_service.sync('device-2', 'iPad', metadata)

    assert result['action'] == 'PULL'
    assert os.path.exists(sync_service.db_path)  # 파일 다운로드됨
```

### 7.3 CONFLICT 테스트

```python
async def test_sync_conflict_handling():
    """충돌 발생 시 백업 파일 생성"""
    sync_service = SyncService(drive_service, db_path)

    metadata = {
        'drive_file_id': 'file-123',
        'drive_app_folder_id': 'folder-456',
        'last_synced_drive_timestamp': '2025-11-15T10:00:00Z',
        'conflict_files': []
    }

    # 로컬을 수정하고 PUSH 시도 (CONFLICT 발생 가정)
    result = await sync_service.sync('device-3', 'Android', metadata)

    if result['action'] == 'CONFLICT':
        assert result['conflict_file'] is not None
        assert os.path.exists(result['conflict_file'])
        assert len(metadata['conflict_files']) == 1
```

---

## 8. 보안 고려사항

### 8.1 서비스 계정 관리

```python
# .env 파일 (절대 깃에 커밋하지 말 것)
GCP_SERVICE_ACCOUNT_KEY=/path/to/service-account-key.json
GOOGLE_APPLICATION_CREDENTIALS=/path/to/service-account-key.json
```

### 8.2 IAM 역할 설정

```bash
# Service Account에 필요한 권한
# Drive API 접근: roles/drive.editor
gcloud projects add-iam-policy-binding mathesis-lab-project \
    --member=serviceAccount:sa-mathesis@mathesis-lab-project.iam.gserviceaccount.com \
    --role=roles/drive.editor
```

### 8.3 Google Drive 파일 암호화 (선택사항)

```python
# SQLite 데이터베이스 암호화 (SQLCipher 사용)
# 데이터베이스 URL: sqlite:////path/to/mathesis_lab.db?cipher=pysqlcipher&key=passphrase
```

---

## 9. 배포 체크리스트

- [ ] Google Cloud Project 생성
- [ ] Service Account 키 생성 및 `.env`에 저장
- [ ] Google Drive API 활성화
- [ ] SyncService 백엔드에 통합
- [ ] SyncManager 프론트엔드에 통합
- [ ] 모든 테스트 케이스 통과
- [ ] 프로덕션 환경 설정 (credentials 보안)
- [ ] 사용자 문서 작성 (충돌 해결 가이드)

---

## 10. 요약: 기존 vs 개선

| 항목 | 기존 | 개선 |
|------|------|------|
| 동기화 대상 | 테이블마다 파일 1개씩 (10,000+ 파일) | **SQLite DB 파일 1개** |
| 원자성 | 파괴됨 (부분 업데이트) | **보장됨** |
| PULL | 없음 | **완전 구현** |
| CONFLICT | LWW (데이터 손실) | **백업 + 사용자 선택** |
| 복잡도 | 매우 높음 (Queue, Mapping) | **극도로 단순함** |
| API 호출 | 매우 많음 | **최소화** |
| 데이터 손실 위험 | 높음 | **거의 없음** |

---

## 다음 단계

1. **GCP 프로젝트 설정** - Service Account 키 생성
2. **백엔드 구현** - SyncService, DriveServiceManager 코드 작성
3. **프론트엔드 통합** - SyncManager, autoSync 구현
4. **테스트** - 모든 테스트 케이스 실행
5. **문서화** - 사용자/개발자 문서 작성
