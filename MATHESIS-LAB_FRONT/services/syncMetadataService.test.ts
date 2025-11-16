/**
 * Tests for SyncMetadataService
 * Tests local storage management for sync metadata and state
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import SyncMetadataService, { SyncMetadata, LocalSyncState } from './syncMetadataService';

describe('SyncMetadataService', () => {
  beforeEach(() => {
    // Clear localStorage before each test
    localStorage.clear();
    vi.clearAllMocks();
  });

  afterEach(() => {
    // Clean up after tests
    localStorage.clear();
  });

  describe('Device ID Management', () => {
    it('should create a new device ID on first call', () => {
      const deviceId = SyncMetadataService.getOrCreateDeviceId();
      expect(deviceId).toBeDefined();
      expect(deviceId).toMatch(/^[0-9a-f-]{36}$/); // UUID format
    });

    it('should return the same device ID on subsequent calls', () => {
      const deviceId1 = SyncMetadataService.getOrCreateDeviceId();
      const deviceId2 = SyncMetadataService.getOrCreateDeviceId();
      expect(deviceId1).toBe(deviceId2);
    });

    it('should persist device ID in localStorage', () => {
      const deviceId = SyncMetadataService.getOrCreateDeviceId();
      const stored = localStorage.getItem('mathesis_device_id');
      expect(stored).toBe(deviceId);
    });
  });

  describe('Device Name Management', () => {
    it('should set and retrieve device name', () => {
      const name = 'My Device';
      SyncMetadataService.setDeviceName(name);
      expect(SyncMetadataService.getDeviceName()).toBe(name);
    });

    it('should generate default device name if not set', () => {
      const name = SyncMetadataService.getDeviceName();
      expect(name).toBeDefined();
      expect(name).toMatch(/^Device-[a-f0-9]{8}$/);
    });

    it('should persist device name in localStorage', () => {
      const name = 'My Device';
      SyncMetadataService.setDeviceName(name);
      const stored = localStorage.getItem('mathesis_device_name');
      expect(stored).toBe(name);
    });
  });

  describe('Sync Metadata Management', () => {
    it('should save and retrieve sync metadata', () => {
      const metadata: SyncMetadata = {
        device_id: 'test-device-id',
        device_name: 'Test Device',
        drive_file_id: 'test-drive-file-id',
        last_synced_drive_timestamp: '2024-01-01T00:00:00Z',
        last_synced_local_timestamp: '2024-01-01T00:00:00Z',
        sync_status: 'IDLE',
        conflict_files: []
      };

      SyncMetadataService.saveSyncMetadata(metadata);
      const retrieved = SyncMetadataService.getSyncMetadata();

      expect(retrieved).toEqual(metadata);
    });

    it('should return null if no metadata saved', () => {
      expect(SyncMetadataService.getSyncMetadata()).toBeNull();
    });
  });

  describe('Sync State Management', () => {
    it('should save and retrieve sync state', () => {
      const state: LocalSyncState = {
        device_id: 'test-device-id',
        device_name: 'Test Device',
        last_local_db_timestamp: '2024-01-01T00:00:00Z',
        last_drive_db_timestamp: '2024-01-01T00:00:00Z',
        last_sync_timestamp: '2024-01-01T00:00:00Z',
        sync_status: 'IDLE',
        conflict_files: []
      };

      SyncMetadataService.saveSyncState(state);
      const retrieved = SyncMetadataService.getSyncState();

      expect(retrieved).toEqual(state);
    });

    it('should return null if no state saved', () => {
      expect(SyncMetadataService.getSyncState()).toBeNull();
    });
  });

  describe('Timestamp Management', () => {
    it('should update local database timestamp', () => {
      const timestamp = '2024-01-15T10:30:00Z';
      SyncMetadataService.updateLocalDbTimestamp(timestamp);

      const state = SyncMetadataService.getSyncState();
      expect(state?.last_local_db_timestamp).toBe(timestamp);
    });

    it('should update drive database timestamp', () => {
      const timestamp = '2024-01-15T10:30:00Z';
      SyncMetadataService.updateDriveDbTimestamp(timestamp);

      const state = SyncMetadataService.getSyncState();
      expect(state?.last_drive_db_timestamp).toBe(timestamp);
    });

    it('should update last sync timestamp when updating timestamps', () => {
      const before = new Date().toISOString();
      SyncMetadataService.updateLocalDbTimestamp('2024-01-15T10:30:00Z');
      const after = new Date().toISOString();

      const state = SyncMetadataService.getSyncState();
      expect(state?.last_sync_timestamp).toBeDefined();

      if (state?.last_sync_timestamp) {
        const syncTime = new Date(state.last_sync_timestamp);
        const beforeTime = new Date(before);
        const afterTime = new Date(after);
        expect(syncTime.getTime()).toBeGreaterThanOrEqual(beforeTime.getTime());
        expect(syncTime.getTime()).toBeLessThanOrEqual(afterTime.getTime());
      }
    });
  });

  describe('Sync Status Management', () => {
    it('should set sync status to SYNCING', () => {
      SyncMetadataService.setSyncStatus('SYNCING');
      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('SYNCING');
    });

    it('should set sync status to CONFLICT', () => {
      SyncMetadataService.setSyncStatus('CONFLICT');
      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('CONFLICT');
    });

    it('should clear conflict files when setting status to IDLE', () => {
      SyncMetadataService.addConflictFile('file1.db');
      SyncMetadataService.addConflictFile('file2.db');
      SyncMetadataService.setSyncStatus('IDLE');

      const files = SyncMetadataService.getConflictFiles();
      expect(files).toHaveLength(0);
    });
  });

  describe('Conflict File Management', () => {
    it('should add conflict file', () => {
      SyncMetadataService.addConflictFile('mathesis_lab_conflict.db');
      const files = SyncMetadataService.getConflictFiles();
      expect(files).toContain('mathesis_lab_conflict.db');
    });

    it('should not add duplicate conflict files', () => {
      SyncMetadataService.addConflictFile('file.db');
      SyncMetadataService.addConflictFile('file.db');
      const files = SyncMetadataService.getConflictFiles();
      expect(files).toHaveLength(1);
    });

    it('should set status to CONFLICT when adding files', () => {
      SyncMetadataService.addConflictFile('file.db');
      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('CONFLICT');
    });

    it('should clear all conflict files', () => {
      SyncMetadataService.addConflictFile('file1.db');
      SyncMetadataService.addConflictFile('file2.db');
      SyncMetadataService.clearConflictFiles();

      const files = SyncMetadataService.getConflictFiles();
      expect(files).toHaveLength(0);
    });

    it('should set status to IDLE when clearing conflict files', () => {
      SyncMetadataService.addConflictFile('file.db');
      SyncMetadataService.clearConflictFiles();

      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('IDLE');
    });

    it('should get empty array if no conflict files', () => {
      const files = SyncMetadataService.getConflictFiles();
      expect(files).toEqual([]);
    });
  });

  describe('Sync Readiness', () => {
    it('should return false if metadata not initialized', () => {
      expect(SyncMetadataService.isReadyForSync()).toBe(false);
    });

    it('should return true if metadata is initialized with drive file ID', () => {
      SyncMetadataService.initializeMetadata('test-drive-file-id');
      expect(SyncMetadataService.isReadyForSync()).toBe(true);
    });
  });

  describe('Metadata Initialization', () => {
    it('should initialize metadata with drive file ID', () => {
      const driveFileId = 'test-drive-file-id';
      const metadata = SyncMetadataService.initializeMetadata(driveFileId);

      expect(metadata.drive_file_id).toBe(driveFileId);
      expect(metadata.device_id).toBeDefined();
      expect(metadata.device_name).toBeDefined();
      expect(metadata.sync_status).toBe('IDLE');
      expect(metadata.conflict_files).toHaveLength(0);
    });

    it('should save metadata and state on initialization', () => {
      SyncMetadataService.initializeMetadata('test-drive-file-id');

      const savedMetadata = SyncMetadataService.getSyncMetadata();
      const savedState = SyncMetadataService.getSyncState();

      expect(savedMetadata).toBeDefined();
      expect(savedState).toBeDefined();
      expect(savedMetadata?.drive_file_id).toBe('test-drive-file-id');
    });

    it('should use same device ID across initialization', () => {
      const deviceId1 = SyncMetadataService.getOrCreateDeviceId();
      SyncMetadataService.initializeMetadata('test-drive-file-id');
      const metadata = SyncMetadataService.getSyncMetadata();

      expect(metadata?.device_id).toBe(deviceId1);
    });
  });

  describe('Sync Info', () => {
    it('should return sync info with correct device details', () => {
      SyncMetadataService.setDeviceName('My Device');
      SyncMetadataService.initializeMetadata('test-drive-file-id');

      const info = SyncMetadataService.getSyncInfo();

      expect(info.deviceId).toBeDefined();
      expect(info.deviceName).toBe('My Device');
      expect(info.isReady).toBe(true);
      expect(info.syncStatus).toBe('IDLE');
    });

    it('should return null for last sync if no sync performed', () => {
      const info = SyncMetadataService.getSyncInfo();
      expect(info.lastSync).toBeNull();
    });
  });

  describe('Clear All', () => {
    it('should clear all stored data', () => {
      SyncMetadataService.setDeviceName('Test');
      SyncMetadataService.initializeMetadata('test-drive-file-id');

      SyncMetadataService.clearAll();

      expect(localStorage.getItem('mathesis_sync_metadata')).toBeNull();
      expect(localStorage.getItem('mathesis_sync_state')).toBeNull();
      expect(localStorage.getItem('mathesis_device_id')).toBeNull();
      expect(localStorage.getItem('mathesis_device_name')).toBeNull();
    });

    it('should allow reinitialization after clearAll', () => {
      SyncMetadataService.initializeMetadata('test-drive-file-id');
      SyncMetadataService.clearAll();

      const newMetadata = SyncMetadataService.initializeMetadata('new-drive-file-id');
      expect(newMetadata.drive_file_id).toBe('new-drive-file-id');
      expect(SyncMetadataService.isReadyForSync()).toBe(true);
    });
  });
});
