import React, { useState, useEffect } from 'react';
import { getGDriveAuthUrl, getGDriveStatus, disconnectGDrive, GDriveAuthStatus } from '../services/gdriveService';

const GDriveAuthButton: React.FC = () => {
    const [status, setStatus] = useState<GDriveAuthStatus | null>(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);

    const fetchStatus = async () => {
        try {
            setLoading(true);
            const currentStatus = await getGDriveStatus();
            setStatus(currentStatus);
        } catch (err) {
            console.error('Failed to fetch GDrive status:', err);
            setError('Failed to load connection status');
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchStatus();
    }, []);

    const handleConnect = async () => {
        try {
            setError(null);
            const { authorization_url } = await getGDriveAuthUrl();

            // Open OAuth popup
            const width = 600;
            const height = 700;
            const left = window.screenX + (window.outerWidth - width) / 2;
            const top = window.screenY + (window.outerHeight - height) / 2;

            const popup = window.open(
                authorization_url,
                'Google Drive Authorization',
                `width=${width},height=${height},left=${left},top=${top}`
            );

            // Listen for OAuth callback
            const handleMessage = (event: MessageEvent) => {
                if (event.data.type === 'gdrive-auth-success') {
                    popup?.close();
                    fetchStatus();
                    window.removeEventListener('message', handleMessage);
                }
            };

            window.addEventListener('message', handleMessage);
        } catch (err) {
            console.error('Failed to connect:', err);
            setError('Failed to connect to Google Drive');
        }
    };

    const handleDisconnect = async () => {
        if (!confirm('Are you sure you want to disconnect Google Drive?')) {
            return;
        }

        try {
            setError(null);
            await disconnectGDrive();
            fetchStatus();
        } catch (err) {
            console.error('Failed to disconnect:', err);
            setError('Failed to disconnect');
        }
    };

    if (loading) {
        return (
            <div className="flex items-center gap-2 text-gray-600">
                <span className="material-symbols-outlined animate-spin">refresh</span>
                <span>Loading...</span>
            </div>
        );
    }

    return (
        <div className="flex flex-col gap-3">
            <div className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                    <span className="material-symbols-outlined text-3xl text-primary">
                        {status?.is_connected ? 'cloud_done' : 'cloud_off'}
                    </span>
                    <div>
                        <h3 className="font-semibold text-gray-900">Google Drive</h3>
                        <p className="text-sm text-gray-600">
                            {status?.is_connected ? 'Connected' : 'Not connected'}
                        </p>
                        {status?.is_connected && status.expires_at && (
                            <p className="text-xs text-gray-500">
                                Expires: {new Date(status.expires_at).toLocaleDateString()}
                            </p>
                        )}
                    </div>
                </div>

                {status?.is_connected ? (
                    <button
                        onClick={handleDisconnect}
                        className="px-4 py-2 text-sm font-medium text-red-600 border border-red-600 rounded-lg hover:bg-red-50 transition-colors"
                    >
                        Disconnect
                    </button>
                ) : (
                    <button
                        onClick={handleConnect}
                        className="px-4 py-2 text-sm font-bold text-white bg-primary rounded-lg hover:bg-primary-dark transition-colors flex items-center gap-2"
                    >
                        <span className="material-symbols-outlined">link</span>
                        Connect Google Drive
                    </button>
                )}
            </div>

            {error && (
                <div className="p-3 bg-red-50 border border-red-200 rounded-lg">
                    <p className="text-sm text-red-600">{error}</p>
                </div>
            )}

            {status?.is_connected && (
                <div className="p-3 bg-green-50 border border-green-200 rounded-lg">
                    <p className="text-sm text-green-700">
                        ✓ Your curriculum maps and files will be automatically synced to your Google Drive.
                    </p>
                </div>
            )}
        </div>
    );
};

export default GDriveAuthButton;
