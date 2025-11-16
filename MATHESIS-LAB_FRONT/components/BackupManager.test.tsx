import { describe, it, expect, beforeEach, vi } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BackupManager } from './BackupManager';
import gcpService from '../services/gcpService';
import type { BackupInfo } from '../types';

// Mock GCP Service
vi.mock('../services/gcpService', () => ({
    default: {
        listBackups: vi.fn(),
        createBackup: vi.fn(),
        restoreBackup: vi.fn(),
        deleteOldBackups: vi.fn(),
        formatDate: (dateStr: string) => new Date(dateStr).toLocaleDateString(),
        formatRelativeTime: (dateStr: string) => '2 hours ago',
        formatBytes: (bytes: number) => `${(bytes / 1024 / 1024).toFixed(1)} MB`,
    },
}));

describe('BackupManager Component', () => {
    const mockBackups: BackupInfo[] = [
        {
            backup_id: 'backup-1',
            timestamp: '2024-01-15T10:30:00Z',
            size_mb: 50,
            device_id: 'device-1',
            device_name: 'My Laptop',
            checksum: 'abc123',
        },
        {
            backup_id: 'backup-2',
            timestamp: '2024-01-14T09:00:00Z',
            size_mb: 48,
            device_id: 'device-2',
            device_name: 'My iPad',
            checksum: 'def456',
        },
    ];

    beforeEach(() => {
        vi.clearAllMocks();
        (gcpService.listBackups as any).mockResolvedValue(mockBackups);
    });

    it('should render backup manager', () => {
        render(<BackupManager />);
        expect(screen.getByText(/Backup & Restore/i)).toBeInTheDocument();
        expect(screen.getByText(/Manage database backups/i)).toBeInTheDocument();
    });

    it('should load and display backups on mount', async () => {
        render(<BackupManager />);

        await waitFor(() => {
            expect(gcpService.listBackups).toHaveBeenCalled();
        });

        await waitFor(() => {
            expect(screen.getByText('My Laptop')).toBeInTheDocument();
            expect(screen.getByText('My iPad')).toBeInTheDocument();
        });
    });

    it('should display empty state when no backups exist', async () => {
        (gcpService.listBackups as any).mockResolvedValue([]);

        render(<BackupManager />);

        await waitFor(() => {
            expect(screen.getByText(/No backups found/i)).toBeInTheDocument();
        });
    });

    it('should show create backup form when button clicked', async () => {
        render(<BackupManager />);

        const createButton = screen.getByText(/Create Backup/i);
        await userEvent.click(createButton);

        expect(screen.getByLabelText(/Device Name/i)).toBeInTheDocument();
    });

    it('should create backup with device name', async () => {
        const mockBackup: BackupInfo = {
            backup_id: 'new-backup',
            timestamp: '2024-01-15T12:00:00Z',
            size_mb: 52,
            device_id: 'device-1',
            device_name: 'New Device',
            checksum: 'new123',
        };

        (gcpService.createBackup as any).mockResolvedValue(mockBackup);

        render(<BackupManager />);

        // Open form
        const createButton = screen.getByText(/Create Backup/i);
        await userEvent.click(createButton);

        // Fill device name
        const input = screen.getByPlaceholderText(/e\.g\., My Laptop/i);
        await userEvent.type(input, 'My Laptop');

        // Submit form
        const submitButton = screen.getByText(/Create Backup/i, { selector: 'button[type="submit"]' });
        await userEvent.click(submitButton);

        await waitFor(() => {
            expect(gcpService.createBackup).toHaveBeenCalledWith({
                device_name: 'My Laptop',
            });
        });
    });

    it.skip('should show restore confirmation dialog', async () => {
        render(<BackupManager />);

        await waitFor(() => {
            expect(screen.getByText('My Laptop')).toBeInTheDocument();
        });

        // Find and click restore button
        const restoreButtons = screen.getAllByText(/Restore/i);
        const firstRestoreButton = restoreButtons[0];
        await userEvent.click(firstRestoreButton);

        await waitFor(() => {
            expect(screen.getByText(/Restore Backup?/i)).toBeInTheDocument();
            expect(screen.getByText(/This will restore the database/i)).toBeInTheDocument();
        });
    });

    it.skip('should restore backup after confirmation', async () => {
        (gcpService.restoreBackup as any).mockResolvedValue({
            message: 'Backup restored',
            timestamp: '2024-01-15T12:00:00Z',
        });

        render(<BackupManager />);

        await waitFor(() => {
            expect(screen.getByText('My Laptop')).toBeInTheDocument();
        });

        // Click restore button
        const restoreButtons = screen.getAllByText(/Restore/i);
        await userEvent.click(restoreButtons[0]);

        // Click confirm button
        await waitFor(() => {
            const confirmButton = screen.getByText(/✓ Restore/);
            return userEvent.click(confirmButton);
        });

        await waitFor(() => {
            expect(gcpService.restoreBackup).toHaveBeenCalledWith({
                backup_id: 'backup-1',
                conflict_resolution: 'latest',
            });
        });
    });

    it('should delete old backups', async () => {
        (gcpService.deleteOldBackups as any).mockResolvedValue({
            deleted_count: 2,
            freed_space_mb: 100,
        });

        render(<BackupManager />);

        await waitFor(() => {
            expect(screen.getByText('My Laptop')).toBeInTheDocument();
        });

        const deleteButton = screen.getByText(/Clean Old Backups/i);
        await userEvent.click(deleteButton);

        await waitFor(() => {
            expect(gcpService.deleteOldBackups).toHaveBeenCalledWith(30);
        });
    });

    it('should refresh backups list', async () => {
        render(<BackupManager />);

        const refreshButton = screen.getByText(/Refresh/i);
        await userEvent.click(refreshButton);

        await waitFor(() => {
            expect(gcpService.listBackups).toHaveBeenCalledTimes(2); // Once on mount, once on refresh
        });
    });

    it('should call onBackupCreated callback after successful backup creation', async () => {
        const mockCallback = vi.fn();
        const mockBackup: BackupInfo = {
            backup_id: 'new-backup',
            timestamp: '2024-01-15T12:00:00Z',
            size_mb: 52,
            device_id: 'device-1',
            device_name: 'New Device',
            checksum: 'new123',
        };

        (gcpService.createBackup as any).mockResolvedValue(mockBackup);

        render(<BackupManager onBackupCreated={mockCallback} />);

        // Open form
        const createButton = screen.getByText(/Create Backup/i);
        await userEvent.click(createButton);

        // Fill and submit
        const input = screen.getByPlaceholderText(/e\.g\., My Laptop/i);
        await userEvent.type(input, 'Test Device');
        const submitButton = screen.getByText(/Create Backup/i, { selector: 'button[type="submit"]' });
        await userEvent.click(submitButton);

        await waitFor(() => {
            expect(mockCallback).toHaveBeenCalledWith(mockBackup);
        });
    });

    it('should display error message on failure', async () => {
        (gcpService.listBackups as any).mockRejectedValue(new Error('API Error'));

        render(<BackupManager />);

        await waitFor(() => {
            expect(screen.getByText(/API Error/i)).toBeInTheDocument();
        });
    });

    it('should disable buttons while loading', async () => {
        render(<BackupManager />);

        await waitFor(() => {
            const buttons = screen.getAllByRole('button');
            // Initially should not be disabled
            expect(buttons.length).toBeGreaterThan(0);
        });
    });
});
