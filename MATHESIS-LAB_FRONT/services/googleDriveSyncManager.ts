/**
 * Google Drive Sync Manager for Multi-Device Synchronization
 *
 * Handles synchronization logic with Google Drive:
 * - PULL: Download database when Drive version is newer
 * - PUSH: Upload database when local version is newer
 * - CONFLICT: Detect and handle conflicting versions
 * - Backup: Generate backup copies when conflicts occur
 *
 * Based on SDD_GCP_INTEGRATION_REVISED specification
 */

import SyncMetadataService, { SyncMetadata } from './syncMetadataService';

export enum SyncAction {
  PULL = 'PULL',
  PUSH = 'PUSH',
  CONFLICT = 'CONFLICT',
  IDLE = 'IDLE'
}

export interface SyncDecision {
  action: SyncAction;
  localTimestamp: string;
  driveTimestamp: string;
  reason: string;
}

export interface SyncResult {
  success: boolean;
  action: SyncAction;
  message: string;
  backupPath?: string;
  localTimestamp?: string;
  driveTimestamp?: string;
  error?: string;
}

/**
 * GoogleDriveSyncManager handles all sync operations with Google Drive
 */
export class GoogleDriveSyncManager {
  private static readonly GCP_API_BASE = '/api/v1/gcp';
  private static readonly CONFLICT_SUFFIX = '_conflict';
  private static readonly DB_FILENAME = 'mathesis_lab.db';

  /**
   * Determine sync action based on timestamp comparison
   */
  static decideSyncAction(
    localTimestamp: string,
    driveTimestamp: string
  ): SyncDecision {
    const localTime = new Date(localTimestamp).getTime();
    const driveTime = new Date(driveTimestamp).getTime();
    const timeDiffMs = Math.abs(localTime - driveTime);
    const timeDiffMinutes = timeDiffMs / (1000 * 60);

    // If timestamps are within 30 seconds, consider them equal
    if (timeDiffMs < 30000) {
      return {
        action: SyncAction.IDLE,
        localTimestamp,
        driveTimestamp,
        reason: 'Timestamps are synchronized (within 30 seconds)'
      };
    }

    // If Drive is newer, need to PULL
    if (driveTime > localTime) {
      return {
        action: SyncAction.PULL,
        localTimestamp,
        driveTimestamp,
        reason: `Drive version is newer by ${Math.round(timeDiffMinutes)} minutes`
      };
    }

    // If local is newer, can PUSH
    if (localTime > driveTime) {
      return {
        action: SyncAction.PUSH,
        localTimestamp,
        driveTimestamp,
        reason: `Local version is newer by ${Math.round(timeDiffMinutes)} minutes`
      };
    }

    // Fallback to IDLE
    return {
      action: SyncAction.IDLE,
      localTimestamp,
      driveTimestamp,
      reason: 'Timestamps are equal'
    };
  }

  /**
   * Detect conflicts between local and Drive versions
   * Conflicts occur when both versions have been modified since last sync
   */
  static detectConflict(
    lastLocalSync: string,
    lastDriveSync: string,
    currentLocalTimestamp: string,
    currentDriveTimestamp: string
  ): boolean {
    const localModified = new Date(currentLocalTimestamp).getTime() >
                         new Date(lastLocalSync).getTime();
    const driveModified = new Date(currentDriveTimestamp).getTime() >
                         new Date(lastDriveSync).getTime();

    return localModified && driveModified;
  }

  /**
   * Perform PULL operation: Download database from Drive
   */
  static async performPull(deviceId: string, outputPath: string = 'mathesis_lab.db'): Promise<SyncResult> {
    SyncMetadataService.setSyncStatus('SYNCING');

    const response = await fetch(`${this.GCP_API_BASE}/restore`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: deviceId,
        output_path: outputPath
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Failed to restore database');
    }

    const data = await response.json();

    // Update sync timestamps
    const now = new Date().toISOString();
    SyncMetadataService.updateDriveDbTimestamp(now);
    SyncMetadataService.updateLocalDbTimestamp(now);
    SyncMetadataService.setSyncStatus('IDLE');

    return {
      success: true,
      action: SyncAction.PULL,
      message: `Successfully pulled database from Drive: ${data.message}`,
      localTimestamp: now,
      driveTimestamp: now
    };
  }

  /**
   * Perform PUSH operation: Upload database to Drive
   */
  static async performPush(deviceId: string): Promise<SyncResult> {
    SyncMetadataService.setSyncStatus('SYNCING');

    const response = await fetch(`${this.GCP_API_BASE}/backup`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: deviceId
      })
    });

    if (!response.ok) {
      const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
      throw new Error(error.detail || 'Failed to backup database');
    }

    const data = await response.json();

    // Update sync timestamps
    const now = new Date().toISOString();
    SyncMetadataService.updateLocalDbTimestamp(now);
    SyncMetadataService.updateDriveDbTimestamp(now);
    SyncMetadataService.setSyncStatus('IDLE');

    return {
      success: true,
      action: SyncAction.PUSH,
      message: `Successfully pushed database to Drive: ${data.message}`,
      localTimestamp: now,
      driveTimestamp: now
    };
  }

  /**
   * Handle CONFLICT: Create backup and resolve via PULL
   * Conflict resolution strategy: Keep Drive version, backup local version
   */
  static async handleConflict(
    deviceId: string,
    localPath: string = 'mathesis_lab.db'
  ): Promise<SyncResult> {
    SyncMetadataService.setSyncStatus('SYNCING');

    // Generate backup filename with timestamp
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupFilename = `${this.DB_FILENAME.replace('.db', '')}_${timestamp}${this.CONFLICT_SUFFIX}.db`;

    // Record conflict file
    SyncMetadataService.addConflictFile(backupFilename);

    // Attempt backup by downloading to conflict path
    const backupResponse = await fetch(`${this.GCP_API_BASE}/restore`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: deviceId,
        output_path: backupFilename
      })
    });

    if (!backupResponse.ok) {
      throw new Error('Failed to create conflict backup');
    }

    // Now pull the Drive version (overwrite local)
    const pullResponse = await fetch(`${this.GCP_API_BASE}/restore`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: deviceId,
        output_path: localPath
      })
    });

    if (!pullResponse.ok) {
      throw new Error('Failed to restore after conflict');
    }

    // Clear conflict status
    SyncMetadataService.clearConflictFiles();
    SyncMetadataService.setSyncStatus('IDLE');

    const now = new Date().toISOString();
    SyncMetadataService.updateDriveDbTimestamp(now);
    SyncMetadataService.updateLocalDbTimestamp(now);

    return {
      success: true,
      action: SyncAction.CONFLICT,
      message: `Conflict resolved: Drive version restored. Local version backed up to ${backupFilename}`,
      backupPath: backupFilename,
      localTimestamp: now,
      driveTimestamp: now
    };
  }

  /**
   * Perform automatic sync based on timestamp comparison
   * Decides and executes appropriate sync action
   */
  static async performAutoSync(
    localTimestamp: string,
    driveTimestamp: string,
    deviceId: string,
    localPath: string = 'mathesis_lab.db'
  ): Promise<SyncResult> {
    // Decide action based on timestamps
    const decision = this.decideSyncAction(localTimestamp, driveTimestamp);

    switch (decision.action) {
      case SyncAction.PULL:
        return await this.performPull(deviceId, localPath);

      case SyncAction.PUSH:
        return await this.performPush(deviceId);

      case SyncAction.CONFLICT:
        return await this.handleConflict(deviceId, localPath);

      case SyncAction.IDLE:
      default:
        SyncMetadataService.setSyncStatus('IDLE');
        return {
          success: true,
          action: SyncAction.IDLE,
          message: 'Databases are already synchronized',
          localTimestamp,
          driveTimestamp
        };
    }
  }

  /**
   * Initialize sync by creating initial metadata on Drive
   */
  static async initializeSync(
    driveFileId: string,
    deviceId?: string
  ): Promise<SyncResult> {
    const metadata = SyncMetadataService.initializeMetadata(driveFileId);
    deviceId = deviceId || metadata.device_id;

    // Create sync metadata on backend
    const response = await fetch(`${this.GCP_API_BASE}/sync-metadata`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      },
      body: JSON.stringify({
        device_id: metadata.device_id,
        device_name: metadata.device_name,
        drive_file_id: driveFileId,
        last_synced_timestamp: new Date().toISOString()
      })
    });

    if (!response.ok) {
      throw new Error('Failed to initialize sync metadata on backend');
    }

    const now = new Date().toISOString();
    SyncMetadataService.updateLocalDbTimestamp(now);
    SyncMetadataService.updateDriveDbTimestamp(now);

    return {
      success: true,
      action: SyncAction.IDLE,
      message: `Sync initialized for device: ${metadata.device_name}`,
      localTimestamp: now,
      driveTimestamp: now
    };
  }

  /**
   * Get list of available backups from Drive for potential recovery
   */
  static async listAvailableBackups(deviceId: string): Promise<any[]> {
    const response = await fetch(`${this.GCP_API_BASE}/backups?device_id=${deviceId}`);

    if (!response.ok) {
      throw new Error('Failed to fetch backups');
    }

    return await response.json();
  }

  /**
   * Get available restoration options (previous backups) for a device
   */
  static async getRestorationOptions(deviceId: string): Promise<any> {
    const response = await fetch(`${this.GCP_API_BASE}/restoration-options/${deviceId}`);

    if (!response.ok) {
      throw new Error('Failed to get restoration options');
    }

    return await response.json();
  }

  /**
   * Get current GCP sync status
   */
  static async getSyncStatus(): Promise<any> {
    const response = await fetch(`${this.GCP_API_BASE}/status`);

    if (!response.ok) {
      throw new Error('Failed to get sync status');
    }

    return await response.json();
  }

  /**
   * Check GCP service health
   */
  static async checkHealth(): Promise<boolean> {
    const response = await fetch(`${this.GCP_API_BASE}/health`);

    if (!response.ok) {
      return false;
    }

    const data = await response.json();
    return data.gcp_available === true;
  }

  /**
   * Get sync action string for UI display
   */
  static getSyncActionLabel(action: SyncAction): string {
    const labels: Record<SyncAction, string> = {
      [SyncAction.PULL]: 'Downloading from Drive',
      [SyncAction.PUSH]: 'Uploading to Drive',
      [SyncAction.CONFLICT]: 'Resolving conflict',
      [SyncAction.IDLE]: 'Synchronized'
    };
    return labels[action];
  }
}

export default GoogleDriveSyncManager;
