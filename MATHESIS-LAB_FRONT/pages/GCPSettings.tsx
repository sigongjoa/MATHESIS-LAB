import React, { useState, useEffect } from 'react';
import gcpService from '../services/gcpService';
import BackupManager from '../components/BackupManager';
import type { GCPStatus, SyncMetadata, DeviceSyncStatus } from '../types';
import '../styles/GCPSettings.css';

export const GCPSettings: React.FC = () => {
    const [gcpStatus, setGcpStatus] = useState<GCPStatus | null>(null);
    const [syncDevices, setSyncDevices] = useState<SyncMetadata[]>([]);
    const [deviceStatus, setDeviceStatus] = useState<DeviceSyncStatus | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [activeTab, setActiveTab] = useState<'overview' | 'backup' | 'sync'>('overview');

    useEffect(() => {
        loadGCPStatus();
    }, []);

    const loadGCPStatus = async () => {
        try {
            setLoading(true);
            setError(null);
            const status = await gcpService.getGCPStatus();
            setGcpStatus(status);

            // Try to load sync devices
            try {
                const devices = await gcpService.listSyncDevices();
                setSyncDevices(devices);
            } catch {
                // Sync devices might not be available
            }
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load GCP status');
        } finally {
            setLoading(false);
        }
    };

    const loadDeviceStatus = async (deviceId: string) => {
        try {
            const status = await gcpService.getDeviceSyncStatus(deviceId);
            setDeviceStatus(status);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to load device status');
        }
    };

    const handleHealthCheck = async () => {
        try {
            setLoading(true);
            const health = await gcpService.healthCheck();
            alert(`Health Check Passed ✓\nStatus: ${health.status}\nMessage: ${health.message}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Health check failed');
        } finally {
            setLoading(false);
        }
    };

    const handleCreateSyncMetadata = async () => {
        const deviceName = prompt('Enter device name (e.g., "My Laptop"):');
        if (!deviceName) return;

        try {
            setLoading(true);
            const metadata = await gcpService.createSyncMetadata(deviceName);
            setSyncDevices([metadata, ...syncDevices]);
            alert(`✓ Device registered: ${metadata.device_name}`);
        } catch (err) {
            setError(err instanceof Error ? err.message : 'Failed to create sync metadata');
        } finally {
            setLoading(false);
        }
    };

    return (
        <div className="gcp-settings">
            <div className="settings-header">
                <h1>⚙️ GCP Settings</h1>
                <p>Manage Google Cloud Platform integration, backups, and synchronization</p>
            </div>

            {error && (
                <div className="error-banner">
                    <p>{error}</p>
                    <button onClick={() => setError(null)} className="dismiss-btn">✕</button>
                </div>
            )}

            {/* Tab Navigation */}
            <div className="tab-navigation">
                <button
                    className={`tab-button ${activeTab === 'overview' ? 'active' : ''}`}
                    onClick={() => setActiveTab('overview')}
                >
                    📊 Overview
                </button>
                <button
                    className={`tab-button ${activeTab === 'backup' ? 'active' : ''}`}
                    onClick={() => setActiveTab('backup')}
                >
                    💾 Backup & Restore
                </button>
                <button
                    className={`tab-button ${activeTab === 'sync' ? 'active' : ''}`}
                    onClick={() => setActiveTab('sync')}
                >
                    🔄 Multi-Device Sync
                </button>
            </div>

            {/* Overview Tab */}
            {activeTab === 'overview' && (
                <div className="tab-content">
                    {loading && !gcpStatus ? (
                        <div className="loading-state">Loading GCP status...</div>
                    ) : gcpStatus ? (
                        <div className="overview-content">
                            {/* Status Card */}
                            <div className={`status-card ${gcpStatus.enabled ? 'enabled' : 'disabled'}`}>
                                <div className="status-icon">
                                    {gcpStatus.enabled ? '✓' : '⚠'}
                                </div>
                                <div className="status-info">
                                    <h3>GCP Integration Status</h3>
                                    <p className="status-text">
                                        {gcpStatus.enabled ? 'Enabled' : 'Disabled'}
                                    </p>
                                    {gcpStatus.project_id && (
                                        <p className="project-id">Project: {gcpStatus.project_id}</p>
                                    )}
                                    {gcpStatus.location && (
                                        <p className="location">Location: {gcpStatus.location}</p>
                                    )}
                                </div>
                            </div>

                            {/* Features Available */}
                            <div className="features-section">
                                <h3>📦 Available Features</h3>
                                <div className="features-grid">
                                    <div
                                        className={`feature-card ${
                                            gcpStatus.features_available?.cloud_storage ? 'available' : 'unavailable'
                                        }`}
                                    >
                                        <span className="feature-icon">☁️</span>
                                        <span className="feature-name">Cloud Storage</span>
                                        <span className="feature-status">
                                            {gcpStatus.features_available?.cloud_storage ? '✓' : '✕'}
                                        </span>
                                    </div>

                                    <div
                                        className={`feature-card ${
                                            gcpStatus.features_available?.backup_restore ? 'available' : 'unavailable'
                                        }`}
                                    >
                                        <span className="feature-icon">💾</span>
                                        <span className="feature-name">Backup & Restore</span>
                                        <span className="feature-status">
                                            {gcpStatus.features_available?.backup_restore ? '✓' : '✕'}
                                        </span>
                                    </div>

                                    <div
                                        className={`feature-card ${
                                            gcpStatus.features_available?.multi_device_sync ? 'available' : 'unavailable'
                                        }`}
                                    >
                                        <span className="feature-icon">🔄</span>
                                        <span className="feature-name">Multi-Device Sync</span>
                                        <span className="feature-status">
                                            {gcpStatus.features_available?.multi_device_sync ? '✓' : '✕'}
                                        </span>
                                    </div>

                                    <div
                                        className={`feature-card ${
                                            gcpStatus.features_available?.ai_features ? 'available' : 'unavailable'
                                        }`}
                                    >
                                        <span className="feature-icon">✨</span>
                                        <span className="feature-name">AI Features</span>
                                        <span className="feature-status">
                                            {gcpStatus.features_available?.ai_features ? '✓' : '✕'}
                                        </span>
                                    </div>
                                </div>
                            </div>

                            {/* Services Info */}
                            {gcpStatus.available_services.length > 0 && (
                                <div className="services-section">
                                    <h3>🔧 Active Services</h3>
                                    <ul className="services-list">
                                        {gcpStatus.available_services.map((service) => (
                                            <li key={service}>✓ {service}</li>
                                        ))}
                                    </ul>
                                </div>
                            )}

                            {/* Action Buttons */}
                            <div className="action-buttons">
                                <button
                                    className="btn btn-primary"
                                    onClick={loadGCPStatus}
                                    disabled={loading}
                                >
                                    🔄 Refresh Status
                                </button>
                                <button
                                    className="btn btn-secondary"
                                    onClick={handleHealthCheck}
                                    disabled={loading}
                                >
                                    🏥 Health Check
                                </button>
                            </div>

                            {/* Last Check Time */}
                            <div className="last-check">
                                Last health check: {gcpService.formatDate(gcpStatus.last_health_check)}
                            </div>
                        </div>
                    ) : null}
                </div>
            )}

            {/* Backup & Restore Tab */}
            {activeTab === 'backup' && (
                <div className="tab-content">
                    <BackupManager
                        onBackupCreated={() => loadGCPStatus()}
                        onRestoreCompleted={() => loadGCPStatus()}
                    />
                </div>
            )}

            {/* Multi-Device Sync Tab */}
            {activeTab === 'sync' && (
                <div className="tab-content">
                    <div className="sync-content">
                        <div className="sync-header">
                            <h2>🔄 Multi-Device Synchronization</h2>
                            <p>Manage devices and synchronize curriculums across multiple devices</p>
                        </div>

                        {/* Register Device */}
                        <div className="register-device">
                            <button
                                className="btn btn-primary"
                                onClick={handleCreateSyncMetadata}
                                disabled={loading}
                            >
                                ➕ Register New Device
                            </button>
                        </div>

                        {/* Devices List */}
                        <div className="devices-section">
                            <h3>📱 Registered Devices ({syncDevices.length})</h3>

                            {syncDevices.length === 0 ? (
                                <div className="empty-state">
                                    <p>No devices registered yet</p>
                                    <p>Click "Register New Device" to add your first device</p>
                                </div>
                            ) : (
                                <div className="devices-list">
                                    {syncDevices.map((device) => (
                                        <div key={device.sync_id} className="device-card">
                                            <div className="device-header">
                                                <h4>📱 {device.device_name}</h4>
                                                <span className={`status-badge ${device.sync_status}`}>
                                                    {device.sync_status === 'pending' && '⏳ Pending'}
                                                    {device.sync_status === 'in_progress' && '🔄 Syncing'}
                                                    {device.sync_status === 'completed' && '✓ Synced'}
                                                    {device.sync_status === 'failed' && '✕ Failed'}
                                                </span>
                                            </div>

                                            <div className="device-info">
                                                <div className="info-row">
                                                    <span className="label">Device ID:</span>
                                                    <span className="value">{device.device_id}</span>
                                                </div>
                                                <div className="info-row">
                                                    <span className="label">Last Sync:</span>
                                                    <span className="value">
                                                        {gcpService.formatDate(device.last_sync)}
                                                    </span>
                                                </div>
                                                <div className="info-row">
                                                    <span className="label">Last Modified:</span>
                                                    <span className="value">
                                                        {gcpService.formatRelativeTime(device.last_modified)}
                                                    </span>
                                                </div>
                                                {device.error_message && (
                                                    <div className="error-message">
                                                        ⚠️ {device.error_message}
                                                    </div>
                                                )}
                                            </div>

                                            <button
                                                className="btn btn-small btn-secondary"
                                                onClick={() => loadDeviceStatus(device.device_id)}
                                            >
                                                View Details
                                            </button>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        {/* Device Details */}
                        {deviceStatus && (
                            <div className="device-details">
                                <h3>📊 Device Details</h3>
                                <div className="details-card">
                                    <div className="details-row">
                                        <span>Device:</span>
                                        <strong>{deviceStatus.device_name}</strong>
                                    </div>
                                    <div className="details-row">
                                        <span>Status:</span>
                                        <strong>{deviceStatus.sync_status}</strong>
                                    </div>
                                    <div className="details-row">
                                        <span>Last Sync:</span>
                                        <strong>{gcpService.formatDate(deviceStatus.last_sync)}</strong>
                                    </div>
                                    <div className="details-row">
                                        <span>Pending Changes:</span>
                                        <strong>{deviceStatus.pending_changes}</strong>
                                    </div>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            )}
        </div>
    );
};

export default GCPSettings;
