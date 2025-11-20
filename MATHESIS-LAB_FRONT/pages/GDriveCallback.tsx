import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { handleGDriveCallback } from '../services/gdriveService';

const GDriveCallback: React.FC = () => {
    const [searchParams] = useSearchParams();
    const [status, setStatus] = useState<'processing' | 'success' | 'error'>('processing');
    const [errorMessage, setErrorMessage] = useState<string>('');

    useEffect(() => {
        const processCallback = async () => {
            const code = searchParams.get('code');
            const error = searchParams.get('error');

            if (error) {
                setStatus('error');
                setErrorMessage(`Authorization failed: ${error}`);
                return;
            }

            if (!code) {
                setStatus('error');
                setErrorMessage('No authorization code received');
                return;
            }

            try {
                await handleGDriveCallback(code);
                setStatus('success');

                // Notify parent window (if opened in popup)
                if (window.opener) {
                    window.opener.postMessage({ type: 'gdrive-auth-success' }, '*');
                    setTimeout(() => window.close(), 2000);
                } else {
                    // Redirect to settings page
                    setTimeout(() => {
                        window.location.href = '/#/settings';
                    }, 2000);
                }
            } catch (err) {
                console.error('Callback error:', err);
                setStatus('error');
                setErrorMessage('Failed to complete authorization');
            }
        };

        processCallback();
    }, [searchParams]);

    return (
        <div className="min-h-screen flex items-center justify-center bg-gray-50">
            <div className="max-w-md w-full bg-white rounded-xl shadow-lg p-8">
                {status === 'processing' && (
                    <div className="text-center">
                        <span className="material-symbols-outlined text-6xl text-primary animate-spin">refresh</span>
                        <h2 className="text-2xl font-bold mt-4 text-gray-900">Connecting...</h2>
                        <p className="text-gray-600 mt-2">Please wait while we connect your Google Drive</p>
                    </div>
                )}

                {status === 'success' && (
                    <div className="text-center">
                        <span className="material-symbols-outlined text-6xl text-green-500">check_circle</span>
                        <h2 className="text-2xl font-bold mt-4 text-gray-900">Success!</h2>
                        <p className="text-gray-600 mt-2">Google Drive connected successfully</p>
                        <p className="text-sm text-gray-500 mt-4">Redirecting...</p>
                    </div>
                )}

                {status === 'error' && (
                    <div className="text-center">
                        <span className="material-symbols-outlined text-6xl text-red-500">error</span>
                        <h2 className="text-2xl font-bold mt-4 text-gray-900">Error</h2>
                        <p className="text-gray-600 mt-2">{errorMessage}</p>
                        <button
                            onClick={() => window.location.href = '/#/settings'}
                            className="mt-6 px-6 py-2 bg-primary text-white rounded-lg hover:bg-primary-dark"
                        >
                            Go to Settings
                        </button>
                    </div>
                )}
            </div>
        </div>
    );
};

export default GDriveCallback;
