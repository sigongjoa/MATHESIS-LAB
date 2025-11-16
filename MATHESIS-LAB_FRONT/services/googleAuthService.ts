/**
 * Google OAuth2 Authentication Service
 *
 * Handles Google OAuth2 login flow:
 * 1. User clicks "Login with Google"
 * 2. Google Sign-In returns ID token
 * 3. Send ID token to backend
 * 4. Backend verifies token and returns JWT
 * 5. Store JWT and redirect to dashboard
 */

import { API_BASE_URL } from '../constants';

export interface GoogleAuthResponse {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: {
    user_id: string;
    email: string;
    name: string;
    profile_picture_url: string | null;
    role: string;
    is_active: boolean;
    created_at: string;
    updated_at: string;
    last_login: string | null;
  };
}

class GoogleAuthService {
  /**
   * Verify Google ID token with backend
   * @param idToken - Google ID token from sign-in
   * @returns JWT access token and user info
   */
  async verifyGoogleToken(idToken: string): Promise<GoogleAuthResponse> {
    const response = await fetch(`${API_BASE_URL}/auth/google/verify-token`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        id_token: idToken,
      }),
    });

    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.detail || 'Google authentication failed');
    }

    return response.json();
  }

  /**
   * Store JWT tokens in localStorage
   * @param tokens - Access and refresh tokens
   */
  storeTokens(tokens: { access_token: string; refresh_token: string }) {
    localStorage.setItem('access_token', tokens.access_token);
    localStorage.setItem('refresh_token', tokens.refresh_token);
    localStorage.setItem('token_type', 'Bearer');
  }

  /**
   * Get stored access token
   */
  getAccessToken(): string | null {
    return localStorage.getItem('access_token');
  }

  /**
   * Get stored refresh token
   */
  getRefreshToken(): string | null {
    return localStorage.getItem('refresh_token');
  }

  /**
   * Clear stored tokens (logout)
   */
  clearTokens() {
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('token_type');
  }

  /**
   * Check if user is logged in
   */
  isLoggedIn(): boolean {
    return !!this.getAccessToken();
  }

  /**
   * Get authorization header for API requests
   */
  getAuthHeader(): { Authorization: string } | {} {
    const token = this.getAccessToken();
    return token ? { Authorization: `Bearer ${token}` } : {};
  }
}

export default new GoogleAuthService();
