import { API_BASE_URL } from '../constants';
import type {
    BackupInfo,
    BackupRestoreOptions,
    SyncMetadata,
    GCPStatus,
    BackupCreateRequest,
    BackupRestoreRequest,
    AIContentRequest,
    AIContentResponse,
    ManimGuidelinesRequest,
    DeviceSyncStatus,
} from '../types';

class GCPService {
    private baseURL = API_BASE_URL;

    // ============================================
    // Backup & Restore Operations
    // ============================================

    /**
     * Create a backup of the database to Google Cloud Storage
     */
    async createBackup(request: BackupCreateRequest): Promise<BackupInfo> {
        const response = await fetch(`${this.baseURL}/gcp/backup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Failed to create backup: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * List all available backups in Google Cloud Storage
     */
    async listBackups(): Promise<BackupInfo[]> {
        const response = await fetch(`${this.baseURL}/gcp/backups`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Failed to list backups: ${response.statusText}`);
        }

        const data = await response.json();
        return data.backups || [];
    }

    /**
     * Restore database from a backup
     */
    async restoreBackup(request: BackupRestoreRequest): Promise<{ message: string; timestamp: string }> {
        const response = await fetch(`${this.baseURL}/gcp/restore`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(request),
        });

        if (!response.ok) {
            throw new Error(`Failed to restore backup: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Delete old backups from Google Cloud Storage
     */
    async deleteOldBackups(retentionDays: number = 30): Promise<{ deleted_count: number; freed_space_mb: number }> {
        const response = await fetch(`${this.baseURL}/gcp/backups/cleanup`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ retention_days: retentionDays }),
        });

        if (!response.ok) {
            throw new Error(`Failed to delete old backups: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Get restoration options for a specific device
     */
    async getRestorationOptions(deviceId: string): Promise<BackupRestoreOptions> {
        const response = await fetch(`${this.baseURL}/gcp/restoration-options/${deviceId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Failed to get restoration options: ${response.statusText}`);
        }

        return response.json();
    }

    // ============================================
    // Multi-Device Synchronization
    // ============================================

    /**
     * Create sync metadata for multi-device synchronization
     */
    async createSyncMetadata(deviceName: string): Promise<SyncMetadata> {
        const response = await fetch(`${this.baseURL}/gcp/sync-metadata`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ device_name: deviceName }),
        });

        if (!response.ok) {
            throw new Error(`Failed to create sync metadata: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Get device sync status
     */
    async getDeviceSyncStatus(deviceId: string): Promise<DeviceSyncStatus> {
        const response = await fetch(`${this.baseURL}/gcp/sync-status/${deviceId}`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Failed to get sync status: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * List all connected devices
     */
    async listSyncDevices(): Promise<SyncMetadata[]> {
        const response = await fetch(`${this.baseURL}/gcp/sync-devices`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Failed to list sync devices: ${response.statusText}`);
        }

        const data = await response.json();
        return data.devices || [];
    }

    // ============================================
    // GCP Configuration & Health
    // ============================================

    /**
     * Get current GCP configuration status
     */
    async getGCPStatus(): Promise<GCPStatus> {
        const response = await fetch(`${this.baseURL}/gcp/status`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Failed to get GCP status: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Health check for GCP connectivity
     */
    async healthCheck(): Promise<{ status: string; message: string; timestamp: string }> {
        const response = await fetch(`${this.baseURL}/gcp/health`, {
            method: 'GET',
            headers: { 'Content-Type': 'application/json' },
        });

        if (!response.ok) {
            throw new Error(`Health check failed: ${response.statusText}`);
        }

        return response.json();
    }

    // ============================================
    // AI Features (Vertex AI / Gemini)
    // ============================================

    /**
     * Summarize node content using AI
     */
    async summarizeContent(nodeId: string, content: string): Promise<AIContentResponse> {
        const response = await fetch(`${this.baseURL}/nodes/${nodeId}/content/summarize`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) {
            throw new Error(`Failed to summarize content: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Extend node content using AI
     */
    async extendContent(nodeId: string, content: string): Promise<AIContentResponse> {
        const response = await fetch(`${this.baseURL}/nodes/${nodeId}/content/extend`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ content }),
        });

        if (!response.ok) {
            throw new Error(`Failed to extend content: ${response.statusText}`);
        }

        return response.json();
    }

    /**
     * Generate Manim guidelines from an image using vision AI
     */
    async generateManimGuidelines(
        nodeId: string,
        imageFile: File
    ): Promise<AIContentResponse> {
        const formData = new FormData();
        formData.append('image', imageFile);

        const response = await fetch(`${this.baseURL}/nodes/${nodeId}/content/manim-guidelines`, {
            method: 'POST',
            body: formData,
        });

        if (!response.ok) {
            throw new Error(`Failed to generate Manim guidelines: ${response.statusText}`);
        }

        return response.json();
    }

    // ============================================
    // Utility Methods
    // ============================================

    /**
     * Format bytes to human-readable format
     */
    formatBytes(bytes: number, decimals: number = 2): string {
        if (bytes === 0) return '0 Bytes';

        const k = 1024;
        const dm = decimals < 0 ? 0 : decimals;
        const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
        const i = Math.floor(Math.log(bytes) / Math.log(k));

        return Math.round((bytes / Math.pow(k, i)) * Math.pow(10, dm)) / Math.pow(10, dm) + ' ' + sizes[i];
    }

    /**
     * Format date to human-readable format
     */
    formatDate(dateString: string): string {
        return new Date(dateString).toLocaleString('en-US', {
            year: 'numeric',
            month: 'short',
            day: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    }

    /**
     * Format date for relative time display (e.g., "2 hours ago")
     */
    formatRelativeTime(dateString: string): string {
        const date = new Date(dateString);
        const now = new Date();
        const seconds = Math.floor((now.getTime() - date.getTime()) / 1000);

        if (seconds < 60) return 'just now';
        if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`;
        if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`;
        if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`;

        return this.formatDate(dateString);
    }
}

export default new GCPService();
