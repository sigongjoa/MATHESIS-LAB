import { describe, it, expect, beforeEach, vi } from 'vitest';
import gcpService from './gcpService';
import type {
    BackupInfo,
    BackupRestoreOptions,
    SyncMetadata,
    GCPStatus,
    AIContentResponse,
    DeviceSyncStatus,
} from '../types';

// Mock fetch
global.fetch = vi.fn();

describe('GCPService', () => {
    beforeEach(() => {
        vi.clearAllMocks();
    });

    // ============================================
    // Backup & Restore Tests
    // ============================================

    describe('Backup Operations', () => {
        it('should create a backup', async () => {
            const mockBackup: BackupInfo = {
                backup_id: 'backup-123',
                timestamp: '2024-01-15T10:30:00Z',
                size_mb: 50,
                device_id: 'device-1',
                device_name: 'My Laptop',
                checksum: 'abc123',
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockBackup,
            });

            const result = await gcpService.createBackup({ device_name: 'My Laptop' });

            expect(result).toEqual(mockBackup);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/backup'),
                expect.any(Object)
            );
        });

        it('should list backups', async () => {
            const mockBackups: BackupInfo[] = [
                {
                    backup_id: 'backup-1',
                    timestamp: '2024-01-15T10:30:00Z',
                    size_mb: 50,
                    device_id: 'device-1',
                    device_name: 'Device 1',
                    checksum: 'abc123',
                },
                {
                    backup_id: 'backup-2',
                    timestamp: '2024-01-14T09:00:00Z',
                    size_mb: 48,
                    device_id: 'device-2',
                    device_name: 'Device 2',
                    checksum: 'def456',
                },
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ backups: mockBackups }),
            });

            const result = await gcpService.listBackups();

            expect(result).toEqual(mockBackups);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/backups'),
                expect.any(Object)
            );
        });

        it('should restore a backup', async () => {
            const mockResponse = {
                message: 'Backup restored successfully',
                timestamp: '2024-01-15T11:00:00Z',
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse,
            });

            const result = await gcpService.restoreBackup({
                backup_id: 'backup-123',
                conflict_resolution: 'latest',
            });

            expect(result).toEqual(mockResponse);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/restore'),
                expect.any(Object)
            );
        });

        it('should delete old backups', async () => {
            const mockResponse = {
                deleted_count: 3,
                freed_space_mb: 150,
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse,
            });

            const result = await gcpService.deleteOldBackups(30);

            expect(result).toEqual(mockResponse);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/backups/cleanup'),
                expect.any(Object)
            );
        });

        it('should get restoration options', async () => {
            const mockOptions: BackupRestoreOptions = {
                device_id: 'device-1',
                available_backups: [
                    {
                        backup_id: 'backup-1',
                        timestamp: '2024-01-15T10:30:00Z',
                        size_mb: 50,
                        device_id: 'device-1',
                        device_name: 'Device 1',
                        checksum: 'abc123',
                    },
                ],
                latest_backup: {
                    backup_id: 'backup-1',
                    timestamp: '2024-01-15T10:30:00Z',
                    size_mb: 50,
                    device_id: 'device-1',
                    device_name: 'Device 1',
                    checksum: 'abc123',
                },
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockOptions,
            });

            const result = await gcpService.getRestorationOptions('device-1');

            expect(result).toEqual(mockOptions);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/restoration-options/device-1'),
                expect.any(Object)
            );
        });
    });

    // ============================================
    // Synchronization Tests
    // ============================================

    describe('Synchronization Operations', () => {
        it('should create sync metadata', async () => {
            const mockMetadata: SyncMetadata = {
                sync_id: 'sync-123',
                device_id: 'device-1',
                device_name: 'My Laptop',
                last_sync: '2024-01-15T10:30:00Z',
                last_modified: '2024-01-15T10:29:00Z',
                sync_status: 'completed',
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockMetadata,
            });

            const result = await gcpService.createSyncMetadata('My Laptop');

            expect(result).toEqual(mockMetadata);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/sync-metadata'),
                expect.any(Object)
            );
        });

        it('should get device sync status', async () => {
            const mockStatus: DeviceSyncStatus = {
                device_id: 'device-1',
                device_name: 'My Laptop',
                last_sync: '2024-01-15T10:30:00Z',
                sync_status: 'synced',
                pending_changes: 0,
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockStatus,
            });

            const result = await gcpService.getDeviceSyncStatus('device-1');

            expect(result).toEqual(mockStatus);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/gcp/sync-status/device-1'),
                expect.any(Object)
            );
        });

        it('should list sync devices', async () => {
            const mockDevices: SyncMetadata[] = [
                {
                    sync_id: 'sync-1',
                    device_id: 'device-1',
                    device_name: 'Laptop',
                    last_sync: '2024-01-15T10:30:00Z',
                    last_modified: '2024-01-15T10:29:00Z',
                    sync_status: 'completed',
                },
            ];

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => ({ devices: mockDevices }),
            });

            const result = await gcpService.listSyncDevices();

            expect(result).toEqual(mockDevices);
        });
    });

    // ============================================
    // GCP Status & Health Tests
    // ============================================

    describe('GCP Status & Health', () => {
        it('should get GCP status', async () => {
            const mockStatus: GCPStatus = {
                enabled: true,
                project_id: 'my-project',
                location: 'us-central1',
                available_services: ['Cloud Storage', 'Vertex AI'],
                last_health_check: '2024-01-15T10:30:00Z',
                features_available: {
                    cloud_storage: true,
                    backup_restore: true,
                    multi_device_sync: true,
                    ai_features: true,
                },
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockStatus,
            });

            const result = await gcpService.getGCPStatus();

            expect(result).toEqual(mockStatus);
            expect(result.enabled).toBe(true);
            expect(result.features_available.ai_features).toBe(true);
        });

        it('should perform health check', async () => {
            const mockHealth = {
                status: 'healthy',
                message: 'All systems operational',
                timestamp: '2024-01-15T10:30:00Z',
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockHealth,
            });

            const result = await gcpService.healthCheck();

            expect(result).toEqual(mockHealth);
            expect(result.status).toBe('healthy');
        });
    });

    // ============================================
    // AI Features Tests
    // ============================================

    describe('AI Features', () => {
        it('should summarize content', async () => {
            const mockResponse: AIContentResponse = {
                result: 'Summarized text here...',
                tokens_used: 150,
                processing_time_ms: 2500,
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse,
            });

            const result = await gcpService.summarizeContent('node-1', 'Long content here...');

            expect(result).toEqual(mockResponse);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/nodes/node-1/content/summarize'),
                expect.any(Object)
            );
        });

        it('should extend content', async () => {
            const mockResponse: AIContentResponse = {
                result: 'Extended content here...',
                tokens_used: 200,
                processing_time_ms: 3000,
            };

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse,
            });

            const result = await gcpService.extendContent('node-1', 'Short content...');

            expect(result).toEqual(mockResponse);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/nodes/node-1/content/extend'),
                expect.any(Object)
            );
        });

        it('should generate Manim guidelines from image', async () => {
            const mockResponse: AIContentResponse = {
                result: 'Manim code guidelines...',
                tokens_used: 300,
                processing_time_ms: 4000,
            };

            const mockFile = new File(['dummy'], 'test.png', { type: 'image/png' });

            (global.fetch as any).mockResolvedValueOnce({
                ok: true,
                json: async () => mockResponse,
            });

            const result = await gcpService.generateManimGuidelines('node-1', mockFile);

            expect(result).toEqual(mockResponse);
            expect(global.fetch).toHaveBeenCalledWith(
                expect.stringContaining('/nodes/node-1/content/manim-guidelines'),
                expect.any(Object)
            );
        });
    });

    // ============================================
    // Utility Methods Tests
    // ============================================

    describe('Utility Methods', () => {
        it('should format bytes correctly', () => {
            expect(gcpService.formatBytes(0)).toBe('0 Bytes');
            expect(gcpService.formatBytes(1024)).toBe('1 KB');
            expect(gcpService.formatBytes(1024 * 1024)).toBe('1 MB');
            expect(gcpService.formatBytes(1024 * 1024 * 1024)).toBe('1 GB');
        });

        it('should format date correctly', () => {
            const dateStr = '2024-01-15T10:30:00Z';
            const formatted = gcpService.formatDate(dateStr);
            expect(formatted).toContain('Jan');
            expect(formatted).toContain('2024');
        });

        it('should format relative time correctly', () => {
            const now = new Date();
            const oneHourAgo = new Date(now.getTime() - 3600 * 1000);
            const formatted = gcpService.formatRelativeTime(oneHourAgo.toISOString());
            expect(formatted).toContain('hour');
        });

        it.skip('should handle invalid dates gracefully', () => {
            const result = gcpService.formatDate('invalid-date');
            expect(result).toBe('invalid-date');
        });
    });

    // ============================================
    // Error Handling Tests
    // ============================================

    describe('Error Handling', () => {
        it('should throw error on failed backup creation', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                statusText: 'Internal Server Error',
            });

            await expect(
                gcpService.createBackup({ device_name: 'Test' })
            ).rejects.toThrow('Failed to create backup');
        });

        it('should throw error on failed backup list', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                statusText: 'Unauthorized',
            });

            await expect(gcpService.listBackups()).rejects.toThrow('Failed to list backups');
        });

        it('should throw error on GCP status retrieval failure', async () => {
            (global.fetch as any).mockResolvedValueOnce({
                ok: false,
                statusText: 'Service Unavailable',
            });

            await expect(gcpService.getGCPStatus()).rejects.toThrow('Failed to get GCP status');
        });
    });
});
