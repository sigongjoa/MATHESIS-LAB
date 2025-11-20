/**
 * Google Drive OAuth Service
 * 
 * Handles Google Drive authentication and connection status
 */

const API_BASE_URL = '/api/v1/gdrive';

export interface GDriveAuthStatus {
    is_connected: boolean;
    expires_at: string | null;
}

export interface GDriveAuthUrl {
    authorization_url: string;
    state: string;
}

/**
 * Get Google Drive authorization URL
 */
export const getGDriveAuthUrl = async (): Promise<GDriveAuthUrl> => {
    const response = await fetch(`${API_BASE_URL}/auth/url`, {
        method: 'GET',
        credentials: 'include'
    });

    if (!response.ok) {
        throw new Error('Failed to get authorization URL');
    }

    return response.json();
};

/**
 * Handle OAuth callback with authorization code
 */
export const handleGDriveCallback = async (code: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/auth/callback`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        credentials: 'include',
        body: JSON.stringify({ code })
    });

    if (!response.ok) {
        throw new Error('Failed to complete authorization');
    }

    return response.json();
};

/**
 * Get current Google Drive connection status
 */
export const getGDriveStatus = async (): Promise<GDriveAuthStatus> => {
    const response = await fetch(`${API_BASE_URL}/auth/status`, {
        method: 'GET',
        credentials: 'include'
    });

    if (!response.ok) {
        throw new Error('Failed to get connection status');
    }

    return response.json();
};

/**
 * Disconnect Google Drive
 */
export const disconnectGDrive = async (): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/auth/disconnect`, {
        method: 'POST',
        credentials: 'include'
    });

    if (!response.ok) {
        throw new Error('Failed to disconnect');
    }

    return response.json();
};
