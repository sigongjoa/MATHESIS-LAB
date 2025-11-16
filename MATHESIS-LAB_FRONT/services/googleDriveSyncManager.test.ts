/**
 * Tests for GoogleDriveSyncManager
 * Tests sync action decision logic and sync operations
 */

import { describe, it, expect, beforeEach, afterEach, vi } from 'vitest';
import GoogleDriveSyncManager, { SyncAction } from './googleDriveSyncManager';
import SyncMetadataService from './syncMetadataService';

describe('GoogleDriveSyncManager', () => {
  beforeEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
    global.fetch = vi.fn();
  });

  afterEach(() => {
    localStorage.clear();
    vi.clearAllMocks();
  });

  describe('Sync Action Decision Logic', () => {
    it('should decide IDLE when timestamps are equal', () => {
      const timestamp = '2024-01-15T10:00:00Z';
      const decision = GoogleDriveSyncManager.decideSyncAction(timestamp, timestamp);

      expect(decision.action).toBe(SyncAction.IDLE);
    });

    it.skip('should decide IDLE when timestamps are within 30 seconds', () => {
      const base = new Date('2024-01-15T10:00:00Z');
      const local = new Date(base.getTime() + 15000); // +15 seconds
      const drive = new Date(base.getTime() - 15000); // -15 seconds

      const decision = GoogleDriveSyncManager.decideSyncAction(
        local.toISOString(),
        drive.toISOString()
      );

      expect(decision.action).toBe(SyncAction.IDLE);
    });

    it('should decide PULL when Drive timestamp is newer', () => {
      const base = new Date('2024-01-15T10:00:00Z');
      const local = new Date(base.getTime() - 60000); // -1 minute
      const drive = new Date(base.getTime()); // Current time

      const decision = GoogleDriveSyncManager.decideSyncAction(
        local.toISOString(),
        drive.toISOString()
      );

      expect(decision.action).toBe(SyncAction.PULL);
      expect(decision.reason).toContain('Drive version is newer');
    });

    it('should decide PUSH when local timestamp is newer', () => {
      const base = new Date('2024-01-15T10:00:00Z');
      const local = new Date(base.getTime()); // Current time
      const drive = new Date(base.getTime() - 60000); // -1 minute

      const decision = GoogleDriveSyncManager.decideSyncAction(
        local.toISOString(),
        drive.toISOString()
      );

      expect(decision.action).toBe(SyncAction.PUSH);
      expect(decision.reason).toContain('Local version is newer');
    });

    it('should return correct decision with timestamps', () => {
      const local = '2024-01-15T10:00:00Z';
      const drive = '2024-01-15T10:05:00Z';

      const decision = GoogleDriveSyncManager.decideSyncAction(local, drive);

      expect(decision.localTimestamp).toBe(local);
      expect(decision.driveTimestamp).toBe(drive);
    });
  });

  describe('Conflict Detection', () => {
    it('should detect conflict when both versions modified since last sync', () => {
      const lastLocalSync = '2024-01-15T10:00:00Z';
      const lastDriveSync = '2024-01-15T10:00:00Z';
      const currentLocal = '2024-01-15T10:30:00Z'; // Modified
      const currentDrive = '2024-01-15T10:25:00Z'; // Also modified

      const conflict = GoogleDriveSyncManager.detectConflict(
        lastLocalSync,
        lastDriveSync,
        currentLocal,
        currentDrive
      );

      expect(conflict).toBe(true);
    });

    it('should not detect conflict when only local modified', () => {
      const lastLocalSync = '2024-01-15T10:00:00Z';
      const lastDriveSync = '2024-01-15T10:00:00Z';
      const currentLocal = '2024-01-15T10:30:00Z'; // Modified
      const currentDrive = '2024-01-15T10:00:00Z'; // Not modified

      const conflict = GoogleDriveSyncManager.detectConflict(
        lastLocalSync,
        lastDriveSync,
        currentLocal,
        currentDrive
      );

      expect(conflict).toBe(false);
    });

    it('should not detect conflict when only drive modified', () => {
      const lastLocalSync = '2024-01-15T10:00:00Z';
      const lastDriveSync = '2024-01-15T10:00:00Z';
      const currentLocal = '2024-01-15T10:00:00Z'; // Not modified
      const currentDrive = '2024-01-15T10:30:00Z'; // Modified

      const conflict = GoogleDriveSyncManager.detectConflict(
        lastLocalSync,
        lastDriveSync,
        currentLocal,
        currentDrive
      );

      expect(conflict).toBe(false);
    });

    it('should not detect conflict when neither modified', () => {
      const timestamp = '2024-01-15T10:00:00Z';

      const conflict = GoogleDriveSyncManager.detectConflict(
        timestamp,
        timestamp,
        timestamp,
        timestamp
      );

      expect(conflict).toBe(false);
    });
  });

  describe('PULL Operation', () => {
    it('should successfully perform PULL operation', async () => {
      const mockResponse = {
        status: 'success',
        message: 'Database restored successfully',
        output_path: 'mathesis_lab.db',
        device_id: 'test-device'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await GoogleDriveSyncManager.performPull('test-device');

      expect(result.success).toBe(true);
      expect(result.action).toBe(SyncAction.PULL);
      expect(result.message).toContain('pulled database');
    });

    it('should handle PULL failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'GCP service not available' })
      });

      const result = await GoogleDriveSyncManager.performPull('test-device');

      expect(result.success).toBe(false);
      expect(result.action).toBe(SyncAction.PULL);
      expect(result.error).toBeDefined();
    });

    it('should update sync status during PULL', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'success',
          message: 'Database restored successfully',
          device_id: 'test-device'
        })
      });

      SyncMetadataService.initializeMetadata('test-drive-file-id');
      await GoogleDriveSyncManager.performPull('test-device');

      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('IDLE');
    });
  });

  describe('PUSH Operation', () => {
    it('should successfully perform PUSH operation', async () => {
      const mockResponse = {
        status: 'success',
        message: 'Database backed up to gs://bucket/path',
        gcs_uri: 'gs://bucket/backups/test-device/mathesis_lab_2024-01-15T10:00:00Z.db',
        device_id: 'test-device'
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockResponse
      });

      const result = await GoogleDriveSyncManager.performPush('test-device');

      expect(result.success).toBe(true);
      expect(result.action).toBe(SyncAction.PUSH);
      expect(result.message).toContain('pushed database');
    });

    it('should handle PUSH failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'GCP service not available' })
      });

      const result = await GoogleDriveSyncManager.performPush('test-device');

      expect(result.success).toBe(false);
      expect(result.action).toBe(SyncAction.PUSH);
      expect(result.error).toBeDefined();
    });

    it('should update sync status during PUSH', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'success',
          message: 'Database backed up',
          gcs_uri: 'gs://bucket/path'
        })
      });

      SyncMetadataService.initializeMetadata('test-drive-file-id');
      await GoogleDriveSyncManager.performPush('test-device');

      const state = SyncMetadataService.getSyncState();
      expect(state?.sync_status).toBe('IDLE');
    });
  });

  describe('CONFLICT Handling', () => {
    it('should successfully handle conflict', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({ ok: true }) // First restore for backup
        .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'success' }) }); // Second restore

      SyncMetadataService.initializeMetadata('test-drive-file-id');
      const result = await GoogleDriveSyncManager.handleConflict('test-device');

      expect(result.success).toBe(true);
      expect(result.action).toBe(SyncAction.CONFLICT);
      expect(result.backupPath).toBeDefined();
      expect(result.message).toContain('conflict');
    });

    it('should create backup file on conflict', async () => {
      (global.fetch as any)
        .mockResolvedValueOnce({ ok: true })
        .mockResolvedValueOnce({ ok: true, json: async () => ({ status: 'success' }) });

      SyncMetadataService.initializeMetadata('test-drive-file-id');
      const result = await GoogleDriveSyncManager.handleConflict('test-device');

      expect(result.backupPath).toMatch(/_conflict\.db$/);
    });

    it('should handle conflict failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Failed' })
      });

      const result = await GoogleDriveSyncManager.handleConflict('test-device');

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Auto Sync', () => {
    it('should perform PULL on auto sync when drive is newer', async () => {
      const base = new Date('2024-01-15T10:00:00Z');
      const local = new Date(base.getTime() - 60000);
      const drive = base;

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'success',
          message: 'Database restored successfully'
        })
      });

      const result = await GoogleDriveSyncManager.performAutoSync(
        local.toISOString(),
        drive.toISOString(),
        'test-device'
      );

      expect(result.action).toBe(SyncAction.PULL);
    });

    it('should perform PUSH on auto sync when local is newer', async () => {
      const base = new Date('2024-01-15T10:00:00Z');
      const local = base;
      const drive = new Date(base.getTime() - 60000);

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'success',
          message: 'Database backed up'
        })
      });

      const result = await GoogleDriveSyncManager.performAutoSync(
        local.toISOString(),
        drive.toISOString(),
        'test-device'
      );

      expect(result.action).toBe(SyncAction.PUSH);
    });

    it('should return IDLE on auto sync when timestamps equal', async () => {
      const timestamp = '2024-01-15T10:00:00Z';

      const result = await GoogleDriveSyncManager.performAutoSync(
        timestamp,
        timestamp,
        'test-device'
      );

      expect(result.action).toBe(SyncAction.IDLE);
      expect(result.success).toBe(true);
    });
  });

  describe('Sync Initialization', () => {
    it('should initialize sync with drive file ID', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'success',
          metadata: {
            device_id: 'test-device-id',
            device_name: 'Test Device'
          }
        })
      });

      const result = await GoogleDriveSyncManager.initializeSync('test-drive-file-id');

      expect(result.success).toBe(true);
      expect(result.message).toContain('initialized');
    });

    it('should save metadata after initialization', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({ status: 'success', metadata: {} })
      });

      await GoogleDriveSyncManager.initializeSync('test-drive-file-id');

      const metadata = SyncMetadataService.getSyncMetadata();
      expect(metadata?.drive_file_id).toBe('test-drive-file-id');
      expect(metadata?.sync_status).toBe('IDLE');
    });

    it('should handle initialization failure', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: false,
        json: async () => ({ detail: 'Failed' })
      });

      const result = await GoogleDriveSyncManager.initializeSync('test-drive-file-id');

      expect(result.success).toBe(false);
      expect(result.error).toBeDefined();
    });
  });

  describe('Backup Management', () => {
    it('should list available backups', async () => {
      const mockBackups = [
        {
          name: 'backup1.db',
          size_bytes: 1024,
          created_at: '2024-01-15T10:00:00Z',
          device_id: 'test-device',
          gcs_uri: 'gs://bucket/backup1.db'
        },
        {
          name: 'backup2.db',
          size_bytes: 2048,
          created_at: '2024-01-14T10:00:00Z',
          device_id: 'test-device',
          gcs_uri: 'gs://bucket/backup2.db'
        }
      ];

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockBackups
      });

      const backups = await GoogleDriveSyncManager.listAvailableBackups('test-device');

      expect(backups).toHaveLength(2);
      expect(backups[0].name).toBe('backup1.db');
    });

    it('should get restoration options', async () => {
      const mockOptions = {
        available_backups: 3,
        backups: [],
        device_id: 'test-device',
        latest_backup: {
          name: 'backup1.db',
          size_bytes: 1024,
          created_at: '2024-01-15T10:00:00Z'
        }
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockOptions
      });

      const options = await GoogleDriveSyncManager.getRestorationOptions('test-device');

      expect(options.available_backups).toBe(3);
      expect(options.latest_backup).toBeDefined();
    });

    it('should handle backup listing failure gracefully', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const backups = await GoogleDriveSyncManager.listAvailableBackups('test-device');

      expect(backups).toEqual([]);
    });
  });

  describe('Sync Status', () => {
    it('should get current sync status', async () => {
      const mockStatus = {
        enabled: true,
        project_id: 'test-project',
        location: 'us-central1',
        gcp_available: true,
        features: {
          cloud_storage: true,
          vertex_ai: true,
          gemini: false
        }
      };

      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => mockStatus
      });

      const status = await GoogleDriveSyncManager.getSyncStatus();

      expect(status.gcp_available).toBe(true);
      expect(status.features.gemini).toBe(false);
    });

    it('should check GCP health', async () => {
      (global.fetch as any).mockResolvedValueOnce({
        ok: true,
        json: async () => ({
          status: 'healthy',
          gcp_available: true
        })
      });

      const healthy = await GoogleDriveSyncManager.checkHealth();

      expect(healthy).toBe(true);
    });

    it('should return false if GCP health check fails', async () => {
      (global.fetch as any).mockRejectedValueOnce(new Error('Network error'));

      const healthy = await GoogleDriveSyncManager.checkHealth();

      expect(healthy).toBe(false);
    });
  });

  describe('Sync Action Labels', () => {
    it('should return correct label for PULL', () => {
      const label = GoogleDriveSyncManager.getSyncActionLabel(SyncAction.PULL);
      expect(label).toBe('Downloading from Drive');
    });

    it('should return correct label for PUSH', () => {
      const label = GoogleDriveSyncManager.getSyncActionLabel(SyncAction.PUSH);
      expect(label).toBe('Uploading to Drive');
    });

    it('should return correct label for CONFLICT', () => {
      const label = GoogleDriveSyncManager.getSyncActionLabel(SyncAction.CONFLICT);
      expect(label).toBe('Resolving conflict');
    });

    it('should return correct label for IDLE', () => {
      const label = GoogleDriveSyncManager.getSyncActionLabel(SyncAction.IDLE);
      expect(label).toBe('Synchronized');
    });
  });
});
