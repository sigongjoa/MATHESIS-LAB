"""
Integration tests for Google OAuth2 API endpoints

Tests the complete OAuth2 flow including:
- Authorization URL generation
- ID token verification and user creation
- Authorization code exchange and token generation
- OAuth error handling
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from backend.app.main import app
from backend.app.models.user import User
from backend.app.core.dependencies import get_db


@pytest.fixture
def db_session():
    """Provide a test database session with tables created/dropped"""
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.app.models.base import Base
    from backend.app.core.config import settings

    # Create test database engine
    engine = create_engine(settings.DATABASE_URL)
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    # Create all tables
    Base.metadata.create_all(bind=engine)

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.rollback()
        Base.metadata.drop_all(bind=engine)
        db.close()


@pytest.fixture
def client(db_session):
    """Provide FastAPI test client with database dependency override"""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    return TestClient(app)


class TestGoogleAuthUrl:
    """Test GET /auth/google/auth-url endpoint"""

    def test_get_auth_url_success(self, client, monkeypatch):
        """Test successful authorization URL generation"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        response = client.get(
            "/api/v1/auth/google/auth-url?redirect_uri=http://localhost:3000/callback"
        )

        assert response.status_code == 200
        data = response.json()
        assert "auth_url" in data
        assert "accounts.google.com/o/oauth2" in data["auth_url"]
        assert "client_id=test-client-id" in data["auth_url"]

    def test_get_auth_url_with_state(self, client, monkeypatch):
        """Test authorization URL generation with CSRF state"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        response = client.get(
            "/api/v1/auth/google/auth-url"
            "?redirect_uri=http://localhost:3000/callback"
            "&state=test-state-123"
        )

        assert response.status_code == 200
        data = response.json()
        assert "state=test-state-123" in data["auth_url"]

    def test_get_auth_url_missing_redirect_uri(self, client, monkeypatch):
        """Test that missing redirect_uri returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        response = client.get("/api/v1/auth/google/auth-url")

        assert response.status_code == 422  # Validation error


class TestVerifyGoogleToken:
    """Test POST /auth/google/verify-token endpoint"""

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_google_token_success_new_user(self, mock_verify, client, db_session, monkeypatch):
        """Test successful ID token verification and new user creation"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_verify.return_value = {
            "sub": "google-user-123",
            "email": "newuser@example.com",
            "name": "New User",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
            "aud": "test-client-id",
        }

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "test-id-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "newuser@example.com"
        assert data["user"]["name"] == "New User"
        assert data["token_type"] == "Bearer"

        # Verify user was created in database
        user = db_session.query(User).filter(User.email == "newuser@example.com").first()
        assert user is not None
        assert user.name == "New User"
        assert user.password_hash is None  # OAuth users have no password
        assert user.is_active is True

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_google_token_existing_user(self, mock_verify, client, db_session, monkeypatch):
        """Test ID token verification for existing user"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        # Create existing user
        existing_user = User(
            email="existing@example.com",
            name="Existing User",
            password_hash=None,
            role="user",
            is_active=True,
        )
        db_session.add(existing_user)
        db_session.commit()

        mock_verify.return_value = {
            "sub": "google-user-456",
            "email": "existing@example.com",
            "name": "Existing User Updated",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
            "aud": "test-client-id",
        }

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "test-id-token"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["user"]["email"] == "existing@example.com"
        assert data["user"]["user_id"] == existing_user.user_id

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_google_token_inactive_user(self, mock_verify, client, db_session, monkeypatch):
        """Test that inactive user cannot login"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        # Create inactive user
        inactive_user = User(
            email="inactive@example.com",
            name="Inactive User",
            password_hash=None,
            is_active=False,
        )
        db_session.add(inactive_user)
        db_session.commit()

        mock_verify.return_value = {
            "sub": "google-user-789",
            "email": "inactive@example.com",
            "name": "Inactive User",
            "aud": "test-client-id",
        }

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "test-id-token"}
        )

        assert response.status_code == 401
        assert "inactive" in response.json()["detail"].lower()

    def test_verify_google_token_missing_id_token(self, client, monkeypatch):
        """Test that missing id_token returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={}
        )

        assert response.status_code == 400
        assert "id_token" in response.json()["detail"].lower()

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_google_token_invalid_token(self, mock_verify, client, monkeypatch):
        """Test that invalid ID token returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_verify.side_effect = Exception("Invalid signature")

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "invalid-token"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_verify_google_token_wrong_audience(self, mock_verify, client, monkeypatch):
        """Test that wrong audience raises error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        mock_verify.return_value = {
            "sub": "google-user-123",
            "email": "user@example.com",
            "aud": "wrong-client-id",
        }

        response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "test-id-token"}
        )

        assert response.status_code == 400
        assert "invalid" in response.json()["detail"].lower()


class TestGoogleOAuthCallback:
    """Test POST /auth/google/callback endpoint"""

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_google_callback_success(self, mock_post, mock_verify, client, db_session, monkeypatch):
        """Test successful OAuth2 callback with code exchange"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        # Mock token exchange response
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "access_token": "google-access-token",
            "id_token": "google-id-token",
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_post_response

        # Mock ID token verification
        mock_verify.return_value = {
            "sub": "google-user-123",
            "email": "callbackuser@example.com",
            "name": "Callback User",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
            "aud": "test-client-id",
        }

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "auth-code-123",
                "redirect_uri": "http://localhost:3000/auth/google/callback",
                "state": "test-state",
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["user"]["email"] == "callbackuser@example.com"

        # Verify user was created
        user = db_session.query(User).filter(User.email == "callbackuser@example.com").first()
        assert user is not None

    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_google_callback_invalid_code(self, mock_post, client, monkeypatch):
        """Test that invalid authorization code returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        # Mock failed token exchange
        mock_post_response = Mock()
        mock_post_response.status_code = 400
        mock_post_response.text = "Invalid authorization code"
        mock_post.return_value = mock_post_response

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "invalid-code",
                "redirect_uri": "http://localhost:3000/auth/google/callback",
            }
        )

        assert response.status_code == 401
        assert "failed" in response.json()["detail"].lower()

    def test_google_callback_missing_code(self, client, monkeypatch):
        """Test that missing authorization code returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "redirect_uri": "http://localhost:3000/auth/google/callback",
            }
        )

        assert response.status_code == 422  # Validation error

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    @patch("backend.app.auth.oauth_handler.httpx.post")
    def test_google_callback_no_id_token_in_response(self, mock_post, mock_verify, client, monkeypatch):
        """Test that missing ID token in response returns error"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_SECRET", "test-secret")

        # Mock token exchange response without ID token
        mock_post_response = Mock()
        mock_post_response.status_code = 200
        mock_post_response.json.return_value = {
            "access_token": "google-access-token",
            # No id_token
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_post_response

        response = client.post(
            "/api/v1/auth/google/callback",
            json={
                "code": "auth-code-123",
                "redirect_uri": "http://localhost:3000/auth/google/callback",
            }
        )

        assert response.status_code == 400
        assert "id token" in response.json()["detail"].lower()


class TestOAuthTokenUsage:
    """Test using OAuth-generated tokens to access protected endpoints"""

    @patch("backend.app.auth.oauth_handler.id_token.verify_oauth2_token")
    def test_use_oauth_access_token(self, mock_verify, client, db_session, monkeypatch):
        """Test that OAuth-generated JWT can access protected endpoints"""
        monkeypatch.setenv("GOOGLE_OAUTH_CLIENT_ID", "test-client-id")

        # Generate token through OAuth login
        mock_verify.return_value = {
            "sub": "google-user-123",
            "email": "tokentest@example.com",
            "name": "Token Test User",
            "picture": "https://example.com/photo.jpg",
            "email_verified": True,
            "aud": "test-client-id",
        }

        login_response = client.post(
            "/api/v1/auth/google/verify-token",
            json={"id_token": "test-id-token"}
        )

        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        # Use token to access protected endpoint
        me_response = client.get(
            "/api/v1/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )

        assert me_response.status_code == 200
        user_data = me_response.json()
        assert user_data["email"] == "tokentest@example.com"
        assert user_data["name"] == "Token Test User"
