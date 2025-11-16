"""
Unit tests for Google OAuth2 handler

Tests OAuth token verification, user info extraction, and URL generation.
"""

import os
import pytest
from unittest.mock import Mock, patch, MagicMock
from backend.app.auth.oauth_handler import (
    GoogleOAuthHandler,
    OAuthError,
    InvalidOAuthTokenError,
)


class TestGoogleOAuthHandlerInitialization:
    """Test GoogleOAuthHandler initialization"""

    def test_init_with_client_id_provided(self):
        """Test initialization with explicit client ID"""
        handler = GoogleOAuthHandler(google_client_id="test-client-id")
        assert handler.google_client_id == "test-client-id"

    def test_init_with_env_variable(self, monkeypatch):
        """Test initialization loading from environment variable"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "env-client-id")
        handler = GoogleOAuthHandler()
        assert handler.google_client_id == "env-client-id"

    def test_init_without_client_id_raises_error(self, monkeypatch):
        """Test that missing client ID raises OAuthError"""
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_ID", raising=False)
        with pytest.raises(OAuthError) as exc_info:
            GoogleOAuthHandler()
        assert "GOOGLE_OAUTH_CLIENT_ID" in str(exc_info.value)


class TestVerifyIdToken:
    """Test ID token verification"""

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_id_token_success(self, mock_verify, monkeypatch):
        """Test successful ID token verification"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_payload = {
            "sub": "123456789",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
            "aud": "test-client-id",
        }
        mock_verify.return_value = mock_payload

        handler = GoogleOAuthHandler()
        result = handler.verify_id_token("test-id-token")

        assert result == mock_payload
        mock_verify.assert_called_once()

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_id_token_invalid_audience(self, mock_verify, monkeypatch):
        """Test that invalid audience raises InvalidOAuthTokenError"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_payload = {
            "sub": "123456789",
            "email": "user@example.com",
            "aud": "wrong-client-id",
        }
        mock_verify.return_value = mock_payload

        handler = GoogleOAuthHandler()

        with pytest.raises(InvalidOAuthTokenError) as exc_info:
            handler.verify_id_token("test-id-token")
        assert "audience" in str(exc_info.value).lower()

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_id_token_invalid_signature(self, mock_verify, monkeypatch):
        """Test that invalid signature raises InvalidOAuthTokenError"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_verify.side_effect = Exception("Invalid signature")

        handler = GoogleOAuthHandler()

        with pytest.raises(InvalidOAuthTokenError):
            handler.verify_id_token("invalid-token")


class TestVerifyAccessToken:
    """Test access token verification"""

    @patch("backend.app.auth.oauth_handler.httpx.get")
    def test_verify_access_token_success(self, mock_get, monkeypatch):
        """Test successful access token verification"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "id": "123456789",
            "email": "user@example.com",
            "name": "Test User",
            "picture": "https://example.com/photo.jpg",
        }
        mock_get.return_value = mock_response

        handler = GoogleOAuthHandler()
        result = handler.verify_access_token("test-access-token")

        assert result["email"] == "user@example.com"
        mock_get.assert_called_once()

    @patch("backend.app.auth.oauth_handler.httpx.get")
    def test_verify_access_token_invalid(self, mock_get, monkeypatch):
        """Test that invalid access token raises InvalidOAuthTokenError"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_response = Mock()
        mock_response.status_code = 401
        mock_get.return_value = mock_response

        handler = GoogleOAuthHandler()

        with pytest.raises(InvalidOAuthTokenError) as exc_info:
            handler.verify_access_token("invalid-token")
        assert "invalid or expired" in str(exc_info.value).lower()


class TestExtractUserInfo:
    """Test user information extraction from token payload"""

    def test_extract_user_info_complete(self, monkeypatch):
        """Test extraction of complete user information"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        payload = {
            "sub": "google-id-123",
            "email": "user@example.com",
            "name": "John Doe",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
        }

        handler = GoogleOAuthHandler()
        result = handler.extract_user_info(payload)

        assert result["google_id"] == "google-id-123"
        assert result["email"] == "user@example.com"
        assert result["name"] == "John Doe"
        assert result["profile_picture_url"] == "https://example.com/photo.jpg"
        assert result["email_verified"] is True

    def test_extract_user_info_minimal(self, monkeypatch):
        """Test extraction with minimal required fields"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        payload = {
            "sub": "google-id-123",
            "email": "user@example.com",
        }

        handler = GoogleOAuthHandler()
        result = handler.extract_user_info(payload)

        assert result["google_id"] == "google-id-123"
        assert result["email"] == "user@example.com"
        assert result["name"] == "Google User"  # Default value
        assert result["profile_picture_url"] is None
        assert result["email_verified"] is False  # Default value


class TestGetAuthorizationUrl:
    """Test OAuth2 authorization URL generation"""

    def test_get_authorization_url_basic(self, monkeypatch):
        """Test basic authorization URL generation"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        handler = GoogleOAuthHandler()
        url = handler.get_authorization_url(
            redirect_uri="http://localhost:3000/callback"
        )

        assert "https://accounts.google.com/o/oauth2/v2/auth" in url
        assert "client_id=test-client-id" in url
        assert "redirect_uri=http://localhost:3000/callback" in url or "redirect_uri=http%3A%2F%2Flocalhost%3A3000%2Fcallback" in url
        assert "response_type=code" in url
        assert "scope=" in url and "openid" in url and "email" in url and "profile" in url

    def test_get_authorization_url_with_state(self, monkeypatch):
        """Test authorization URL generation with state parameter"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        handler = GoogleOAuthHandler()
        url = handler.get_authorization_url(
            redirect_uri="http://localhost:3000/callback",
            state="test-state-123"
        )

        assert "state=test-state-123" in url

    def test_get_authorization_url_custom_scope(self, monkeypatch):
        """Test authorization URL generation with custom scope"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        handler = GoogleOAuthHandler()
        url = handler.get_authorization_url(
            redirect_uri="http://localhost:3000/callback",
            scope="email profile"
        )

        assert ("scope=email+profile" in url or "scope=email profile" in url)


class TestExchangeCodeForToken:
    """Test authorization code to token exchange"""

    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_exchange_code_for_token_success(self, mock_post, monkeypatch):
        """Test successful code to token exchange"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "access-token-123",
            "id_token": "id-token-123",
            "token_type": "Bearer",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        handler = GoogleOAuthHandler()
        result = handler.exchange_code_for_token(
            code="auth-code-123",
            redirect_uri="http://localhost:3000/callback"
        )

        assert result["access_token"] == "access-token-123"
        assert result["id_token"] == "id-token-123"
        mock_post.assert_called_once()

    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_exchange_code_for_token_failure(self, mock_post, monkeypatch):
        """Test failed code to token exchange"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.text = "Invalid code"
        mock_post.return_value = mock_response

        handler = GoogleOAuthHandler()

        with pytest.raises(InvalidOAuthTokenError) as exc_info:
            handler.exchange_code_for_token(
                code="invalid-code",
                redirect_uri="http://localhost:3000/callback"
            )
        assert "failed" in str(exc_info.value).lower()

    def test_exchange_code_without_client_secret(self, monkeypatch):
        """Test that missing client secret raises OAuthError"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.delenv("GOOGLE_OAUTH_CLIENT_SECRET", raising=False)

        handler = GoogleOAuthHandler()

        with pytest.raises(OAuthError) as exc_info:
            handler.exchange_code_for_token(
                code="auth-code-123",
                redirect_uri="http://localhost:3000/callback"
            )
        assert "CLIENT_SECRET" in str(exc_info.value)

    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_exchange_code_network_error(self, mock_post, monkeypatch):
        """Test handling of network errors during token exchange"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        import httpx
        mock_post.side_effect = httpx.RequestError("Network error")

        handler = GoogleOAuthHandler()

        with pytest.raises(OAuthError) as exc_info:
            handler.exchange_code_for_token(
                code="auth-code-123",
                redirect_uri="http://localhost:3000/callback"
            )
        assert "failed" in str(exc_info.value).lower()
