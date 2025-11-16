"""
OAuth2 Handler for MATHESIS LAB

Handles Google OAuth2 integration including token verification and user creation.
Supports linking OAuth2 accounts to existing user accounts.
"""

import os
from typing import Optional, Dict, Any
from datetime import datetime, UTC

from google.auth.transport import requests
from google.oauth2 import id_token
import httpx

from backend.app.models.user import User


class OAuthError(Exception):
    """Base exception for OAuth errors"""
    pass


class InvalidOAuthTokenError(OAuthError):
    """Raised when OAuth token is invalid or expired"""
    pass


class OAuthUserError(OAuthError):
    """Raised when user info cannot be retrieved"""
    pass


class GoogleOAuthHandler:
    """
    Google OAuth2 Handler

    Handles verification of Google OAuth2 ID tokens and user information extraction.
    Supports both Authorization Code flow and ID Token verification.
    """

    def __init__(self, google_client_id: Optional[str] = None):
        """
        Initialize Google OAuth handler.

        Args:
            google_client_id: Google OAuth2 Client ID.
                             If None, loads from GOOGLE_OAUTH_CLIENT_ID environment variable.
        """
        self.google_client_id = google_client_id or os.getenv("GOOGLE_OAUTH_CLIENT_ID")
        if not self.google_client_id:
            raise OAuthError(
                "GOOGLE_OAUTH_CLIENT_ID environment variable not set. "
                "Please set it to your Google OAuth2 Client ID."
            )

    def verify_id_token(self, id_token_str: str) -> Dict[str, Any]:
        """
        Verify and decode Google ID token.

        Args:
            id_token_str: Google ID token string from client

        Returns:
            Token payload containing user information

        Raises:
            InvalidOAuthTokenError: If token is invalid or expired

        Token payload includes:
        - sub: User's Google ID
        - email: User's email address
        - name: User's name
        - picture: User's profile picture URL
        - email_verified: Whether email is verified
        """
        try:
            # Verify the token signature using Google's public keys
            # This validates that the token is actually from Google
            payload = id_token.verify_oauth2_token(
                id_token_str,
                requests.Request(),
                self.google_client_id
            )

            # Additional validation
            if payload.get("aud") != self.google_client_id:
                raise InvalidOAuthTokenError("Token audience does not match client ID")

            return payload

        except Exception as e:
            raise InvalidOAuthTokenError(f"Invalid Google ID token: {str(e)}") from e

    def verify_access_token(self, access_token: str) -> Dict[str, Any]:
        """
        Verify Google access token and retrieve user information.

        Args:
            access_token: Google access token from OAuth2 flow

        Returns:
            User information dictionary

        Raises:
            InvalidOAuthTokenError: If token is invalid
            OAuthUserError: If user info cannot be retrieved
        """
        try:
            # Use Google's userinfo endpoint to verify token and get user info
            url = "https://www.googleapis.com/oauth2/v2/userinfo"
            headers = {"Authorization": f"Bearer {access_token}"}

            response = httpx.get(url, headers=headers, timeout=10)

            if response.status_code != 200:
                raise InvalidOAuthTokenError("Access token is invalid or expired")

            return response.json()

        except httpx.RequestError as e:
            raise OAuthUserError(f"Failed to retrieve user info: {str(e)}") from e
        except Exception as e:
            raise InvalidOAuthTokenError(f"Token verification failed: {str(e)}") from e

    def extract_user_info(self, token_payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract user information from OAuth token payload.

        Args:
            token_payload: Token payload from verify_id_token or verify_access_token

        Returns:
            User information dictionary with keys:
            - google_id: User's Google ID (sub claim)
            - email: User's email
            - name: User's display name
            - profile_picture_url: User's profile picture
            - email_verified: Whether email is verified by Google
        """
        return {
            "google_id": token_payload.get("sub"),
            "email": token_payload.get("email"),
            "name": token_payload.get("name", "Google User"),
            "profile_picture_url": token_payload.get("picture"),
            "email_verified": token_payload.get("email_verified", False),
        }

    def get_authorization_url(
        self,
        redirect_uri: str,
        scope: Optional[str] = None,
        state: Optional[str] = None
    ) -> str:
        """
        Generate Google OAuth2 authorization URL.

        Args:
            redirect_uri: Redirect URI registered with Google OAuth2 (e.g., http://localhost:3000/auth/google/callback)
            scope: Space-separated scopes (default: "openid email profile")
            state: CSRF protection state parameter

        Returns:
            Full authorization URL to redirect user to

        Example:
            >>> handler = GoogleOAuthHandler()
            >>> url = handler.get_authorization_url(
            ...     redirect_uri="http://localhost:3000/auth/google/callback",
            ...     state="random-state-value"
            ... )
        """
        if scope is None:
            scope = "openid email profile"

        params = {
            "client_id": self.google_client_id,
            "redirect_uri": redirect_uri,
            "response_type": "code",
            "scope": scope,
        }

        if state:
            params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in params.items())
        return f"https://accounts.google.com/o/oauth2/v2/auth?{query_string}"

    def exchange_code_for_token(
        self,
        code: str,
        redirect_uri: str,
        client_secret: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Exchange authorization code for tokens (backend flow).

        Args:
            code: Authorization code from Google
            redirect_uri: Same redirect URI used in authorization request
            client_secret: Google OAuth2 Client Secret (loaded from env if not provided)

        Returns:
            Token response containing access_token, id_token, etc.

        Raises:
            InvalidOAuthTokenError: If code is invalid or exchange fails

        Note:
            This is typically used in backend-to-backend token exchange.
            For frontend (Google Sign-In), use verify_id_token() instead.
        """
        client_secret = client_secret or os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        if not client_secret:
            raise OAuthError("GOOGLE_OAUTH_CLIENT_SECRET not configured")

        try:
            url = "https://oauth2.googleapis.com/token"
            data = {
                "client_id": self.google_client_id,
                "client_secret": client_secret,
                "code": code,
                "grant_type": "authorization_code",
                "redirect_uri": redirect_uri,
            }

            response = httpx.post(url, data=data, timeout=10)

            if response.status_code != 200:
                raise InvalidOAuthTokenError(
                    f"Token exchange failed: {response.text}"
                )

            return response.json()

        except httpx.RequestError as e:
            raise OAuthError(f"Token exchange request failed: {str(e)}") from e


# Global OAuth handler instance
_oauth_handler_instance: Optional[GoogleOAuthHandler] = None


def get_oauth_handler(google_client_id: Optional[str] = None) -> GoogleOAuthHandler:
    """
    Get or create Google OAuth handler instance.

    Args:
        google_client_id: Google OAuth2 Client ID (optional)

    Returns:
        GoogleOAuthHandler instance
    """
    global _oauth_handler_instance
    if _oauth_handler_instance is None:
        _oauth_handler_instance = GoogleOAuthHandler(google_client_id)
    return _oauth_handler_instance


def reset_oauth_handler():
    """Reset OAuth handler instance (useful for testing)"""
    global _oauth_handler_instance
    _oauth_handler_instance = None
