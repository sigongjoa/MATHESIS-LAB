/**
 * Sync Metadata Service for Multi-Device Synchronization
 *
 * Manages local storage of sync metadata for tracking:
 * - Device identification and naming
 * - File timestamps and sync state
 * - Conflict detection and resolution
 * - Drive file association for Google Drive integration
 */

import { v4 as uuidv4 } from 'uuid';

export interface SyncMetadata {
  device_id: string;
  device_name: string;
  drive_file_id: string;
  last_synced_drive_timestamp: string;
  last_synced_local_timestamp: string;
  sync_status: 'IDLE' | 'SYNCING' | 'CONFLICT';
  conflict_files: string[];
}

export interface LocalSyncState {
  device_id: string;
  device_name: string;
  last_local_db_timestamp: string;
  last_drive_db_timestamp: string;
  last_sync_timestamp: string;
  sync_status: 'IDLE' | 'SYNCING' | 'CONFLICT';
  conflict_files: string[];
}

const STORAGE_KEY_METADATA = 'mathesis_sync_metadata';
const STORAGE_KEY_STATE = 'mathesis_sync_state';
const STORAGE_KEY_DEVICE_ID = 'mathesis_device_id';
const STORAGE_KEY_DEVICE_NAME = 'mathesis_device_name';

/**
 * SyncMetadataService manages local sync state and metadata
 */
export class SyncMetadataService {
  /**
   * Initialize or get existing device ID
   * Device ID is persistent across sessions for device identification
   */
  static getOrCreateDeviceId(): string {
    let deviceId = localStorage.getItem(STORAGE_KEY_DEVICE_ID);
    if (!deviceId) {
      deviceId = uuidv4();
      localStorage.setItem(STORAGE_KEY_DEVICE_ID, deviceId);
    }
    return deviceId;
  }

  /**
   * Set device name (human-readable identifier)
   */
  static setDeviceName(name: string): void {
    localStorage.setItem(STORAGE_KEY_DEVICE_NAME, name);
  }

  /**
   * Get device name, defaults to "Device-{random}" if not set
   */
  static getDeviceName(): string {
    let deviceName = localStorage.getItem(STORAGE_KEY_DEVICE_NAME);
    if (!deviceName) {
      const deviceId = this.getOrCreateDeviceId();
      deviceName = `Device-${deviceId.substring(0, 8)}`;
      localStorage.setItem(STORAGE_KEY_DEVICE_NAME, deviceName);
    }
    return deviceName;
  }

  /**
   * Save sync metadata to local storage
   */
  static saveSyncMetadata(metadata: SyncMetadata): void {
    localStorage.setItem(STORAGE_KEY_METADATA, JSON.stringify(metadata));
  }

  /**
   * Retrieve sync metadata from local storage
   */
  static getSyncMetadata(): SyncMetadata | null {
    const stored = localStorage.getItem(STORAGE_KEY_METADATA);
    return stored ? JSON.parse(stored) : null;
  }

  /**
   * Save local sync state
   */
  static saveSyncState(state: LocalSyncState): void {
    localStorage.setItem(STORAGE_KEY_STATE, JSON.stringify(state));
  }

  /**
   * Retrieve local sync state
   */
  static getSyncState(): LocalSyncState | null {
    const stored = localStorage.getItem(STORAGE_KEY_STATE);
    return stored ? JSON.parse(stored) : null;
  }

  /**
   * Update last local database timestamp
   */
  static updateLocalDbTimestamp(timestamp: string): void {
    const state = this.getSyncState() || this.getInitialSyncState();
    state.last_local_db_timestamp = timestamp;
    state.last_sync_timestamp = new Date().toISOString();
    this.saveSyncState(state);
  }

  /**
   * Update last Drive database timestamp
   */
  static updateDriveDbTimestamp(timestamp: string): void {
    const state = this.getSyncState() || this.getInitialSyncState();
    state.last_drive_db_timestamp = timestamp;
    state.last_sync_timestamp = new Date().toISOString();
    this.saveSyncState(state);
  }

  /**
   * Set sync status
   */
  static setSyncStatus(status: 'IDLE' | 'SYNCING' | 'CONFLICT'): void {
    const state = this.getSyncState() || this.getInitialSyncState();
    state.sync_status = status;
    if (status === 'IDLE') {
      state.conflict_files = [];
    }
    this.saveSyncState(state);
  }

  /**
   * Add conflict file to tracking
   */
  static addConflictFile(filePath: string): void {
    const state = this.getSyncState() || this.getInitialSyncState();
    if (!state.conflict_files.includes(filePath)) {
      state.conflict_files.push(filePath);
    }
    state.sync_status = 'CONFLICT';
    this.saveSyncState(state);
  }

  /**
   * Clear conflict files
   */
  static clearConflictFiles(): void {
    const state = this.getSyncState() || this.getInitialSyncState();
    state.conflict_files = [];
    state.sync_status = 'IDLE';
    this.saveSyncState(state);
  }

  /**
   * Get conflict files list
   */
  static getConflictFiles(): string[] {
    const state = this.getSyncState();
    return state?.conflict_files || [];
  }

  /**
   * Check if device is ready for sync
   */
  static isReadyForSync(): boolean {
    const metadata = this.getSyncMetadata();
    return !!(metadata && metadata.device_id && metadata.drive_file_id);
  }

  /**
   * Initialize metadata for first-time sync
   */
  static initializeMetadata(driveFileId: string): SyncMetadata {
    const deviceId = this.getOrCreateDeviceId();
    const deviceName = this.getDeviceName();
    const now = new Date().toISOString();

    const metadata: SyncMetadata = {
      device_id: deviceId,
      device_name: deviceName,
      drive_file_id: driveFileId,
      last_synced_drive_timestamp: now,
      last_synced_local_timestamp: now,
      sync_status: 'IDLE',
      conflict_files: []
    };

    this.saveSyncMetadata(metadata);
    this.saveSyncState({
      device_id: deviceId,
      device_name: deviceName,
      last_local_db_timestamp: now,
      last_drive_db_timestamp: now,
      last_sync_timestamp: now,
      sync_status: 'IDLE',
      conflict_files: []
    });

    return metadata;
  }

  /**
   * Get initial sync state with current device info
   */
  private static getInitialSyncState(): LocalSyncState {
    const now = new Date().toISOString();
    return {
      device_id: this.getOrCreateDeviceId(),
      device_name: this.getDeviceName(),
      last_local_db_timestamp: now,
      last_drive_db_timestamp: now,
      last_sync_timestamp: now,
      sync_status: 'IDLE',
      conflict_files: []
    };
  }

  /**
   * Clear all sync metadata (for testing/reset)
   */
  static clearAll(): void {
    localStorage.removeItem(STORAGE_KEY_METADATA);
    localStorage.removeItem(STORAGE_KEY_STATE);
    localStorage.removeItem(STORAGE_KEY_DEVICE_ID);
    localStorage.removeItem(STORAGE_KEY_DEVICE_NAME);
  }

  /**
   * Get sync info for logging/debugging
   */
  static getSyncInfo(): {
    deviceId: string;
    deviceName: string;
    isReady: boolean;
    syncStatus: string;
    lastSync: string | null;
  } {
    const metadata = this.getSyncMetadata();
    const state = this.getSyncState();

    return {
      deviceId: this.getOrCreateDeviceId(),
      deviceName: this.getDeviceName(),
      isReady: this.isReadyForSync(),
      syncStatus: state?.sync_status || 'IDLE',
      lastSync: state?.last_sync_timestamp || null
    };
  }
}

export default SyncMetadataService;
