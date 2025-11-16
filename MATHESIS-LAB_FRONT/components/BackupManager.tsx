import React, { useState, useEffect } from 'react';
import gcpService from '../services/gcpService';
import type { BackupInfo } from '../types';
import '../styles/BackupManager.css';

interface BackupManagerProps {
    onBackupCreated?: (backup: BackupInfo) => void;
    onRestoreCompleted?: () => void;
}

export const BackupManager: React.FC<BackupManagerProps> = ({ onBackupCreated, onRestoreCompleted }) => {
    const [backups, setBackups] = useState<BackupInfo[]>([]);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [selectedBackup, setSelectedBackup] = useState<BackupInfo | null>(null);
    const [deviceName, setDeviceName] = useState('');
    const [showCreateForm, setShowCreateForm] = useState(false);
    const [showRestoreConfirm, setShowRestoreConfirm] = useState(false);

    // Load backups on mount
    useEffect(() => {
        loadBackups();
    }, []);

    const loadBackups = async () => {
        try {
            setLoading(true);
            setError(null);
            const data = await gcpService.listBackups();
            setBackups(data);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load backups');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateBackup = async (e: React.FormEvent) => {
        e.preventDefault();
        try {
            setLoading(true);
            setError(null);

            const backup = await gcpService.createBackup({
                device_name: deviceName || 'Manual Backup',
            });

            setBackups([backup, ...backups]);
            setDeviceName('');
            setShowCreateForm(false);

            if (onBackupCreated) {
                onBackupCreated(backup);
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create backup');
        } finally {
            setLoading(false);
        }
    };

    const handleRestoreBackup = async () => {
        if (!selectedBackup) return;

        try {
            setLoading(true);
            setError(null);

            await gcpService.restoreBackup({
                backup_id: selectedBackup.backup_id,
                conflict_resolution: 'latest',
            });

            setShowRestoreConfirm(false);
            setSelectedBackup(null);

            // Reload backups after restore
            loadBackups();

            if (onRestoreCompleted) {
                onRestoreCompleted();
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to restore backup');
        } finally {
            setLoading(false);
        }
    };

    const handleDeleteOldBackups = async () => {
        try {
            setLoading(true);
            setError(null);

            const result = await gcpService.deleteOldBackups(30);
            setError(null); // Clear error state
            alert(`Deleted ${result.deleted_count} old backups, freed ${result.freed_space_mb}MB`);

            // Reload backups after cleanup
            loadBackups();
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to delete old backups');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="backup-manager">
            <div className="backup-header">
                <h2>🔄 Backup & Restore</h2>
                <p>Manage database backups in Google Cloud Storage</p>
            </div>

            {error && <div className="error-message">{error}</div>}

            {/* Action Buttons */}
            <div className="backup-actions">
                <button
                    className="btn btn-primary"
                    onClick={() => setShowCreateForm(!showCreateForm)}
                    disabled={loading}
                >
                    {showCreateForm ? '✖ Cancel' : '➕ Create Backup'}
                </button>
                <button className="btn btn-secondary" onClick={loadBackups} disabled={loading}>
                    🔄 Refresh
                </button>
                <button
                    className="btn btn-danger"
                    onClick={handleDeleteOldBackups}
                    disabled={loading || backups.length === 0}
                >
                    🗑️ Clean Old Backups
                </button>
            </div>

            {/* Create Backup Form */}
            {showCreateForm && (
                <form onSubmit={handleCreateBackup} className="backup-form">
                    <div className="form-group">
                        <label htmlFor="deviceName">Device Name (Optional)</label>
                        <input
                            id="deviceName"
                            type="text"
                            value={deviceName}
                            onChange={(e) => setDeviceName(e.target.value)}
                            placeholder="e.g., My Laptop, iPad, etc."
                            disabled={loading}
                        />
                    </div>
                    <button type="submit" className="btn btn-primary" disabled={loading}>
                        {loading ? 'Creating...' : '✓ Create Backup'}
                    </button>
                </form>
            )}

            {/* Backups List */}
            <div className="backups-list">
                {loading && <div className="loading">Loading backups...</div>}

                {!loading && backups.length === 0 && (
                    <div className="empty-state">
                        <p>📦 No backups found</p>
                        <p>Create your first backup to get started</p>
                    </div>
                )}

                {!loading && backups.length > 0 && (
                    <table className="backups-table">
                        <thead>
                            <tr>
                                <th>Device</th>
                                <th>Date</th>
                                <th>Size</th>
                                <th>Actions</th>
                            </tr>
                        </thead>
                        <tbody>
                            {backups.map((backup) => (
                                <tr key={backup.backup_id} className={selectedBackup?.backup_id === backup.backup_id ? 'selected' : ''}>
                                    <td className="device-name">{backup.device_name}</td>
                                    <td className="date">
                                        <div>{gcpService.formatDate(backup.timestamp)}</div>
                                        <small>{gcpService.formatRelativeTime(backup.timestamp)}</small>
                                    </td>
                                    <td className="size">{gcpService.formatBytes(backup.size_mb * 1024 * 1024)}</td>
                                    <td className="actions">
                                        <button
                                            className="btn-small btn-restore"
                                            onClick={() => {
                                                setSelectedBackup(backup);
                                                setShowRestoreConfirm(true);
                                            }}
                                            disabled={loading}
                                        >
                                            ↻ Restore
                                        </button>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                )}
            </div>

            {/* Restore Confirmation Dialog */}
            {showRestoreConfirm && selectedBackup && (
                <div className="modal-overlay">
                    <div className="modal-content">
                        <h3>⚠️ Restore Backup?</h3>
                        <p>
                            This will restore the database from{' '}
                            <strong>{selectedBackup.device_name}</strong> created on{' '}
                            <strong>{gcpService.formatDate(selectedBackup.timestamp)}</strong>
                        </p>
                        <p className="warning-text">This action cannot be undone. Make sure to create a current backup first.</p>
                        <div className="modal-actions">
                            <button
                                className="btn btn-danger"
                                onClick={handleRestoreBackup}
                                disabled={loading}
                            >
                                {loading ? 'Restoring...' : '✓ Restore'}
                            </button>
                            <button
                                className="btn btn-secondary"
                                onClick={() => setShowRestoreConfirm(false)}
                                disabled={loading}
                            >
                                ✖ Cancel
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default BackupManager;
