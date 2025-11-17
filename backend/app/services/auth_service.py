"""
Authentication Service for MATHESIS LAB

Handles user authentication, registration, token management, and related business logic.
"""

import logging
from datetime import datetime, timedelta, UTC
from typing import Optional, Tuple

from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError

logger = logging.getLogger(__name__)

from backend.app.models.user import User
from backend.app.models.user_session import UserSession
from backend.app.auth.jwt_handler import JWTHandler, JWTTokenError, TokenExpiredError, InvalidTokenFormatError
from backend.app.auth.password_handler import PasswordHandler, WeakPasswordError
from backend.app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    UserResponse,
)


class AuthError(Exception):
    """Base exception for authentication errors"""
    pass


class InvalidCredentialsError(AuthError):
    """Raised when login credentials are invalid"""
    pass


class UserAlreadyExistsError(AuthError):
    """Raised when trying to register with existing email"""
    pass


class TokenRefreshError(AuthError):
    """Raised when token refresh fails"""
    pass


class AuthService:
    """
    Authentication Service

    Handles user authentication operations including:
    - User registration
    - User login
    - Token refresh
    - Token verification
    - Password management
    - Session management
    """

    def __init__(self, db: Session, jwt_handler: JWTHandler, password_handler: PasswordHandler):
        """
        Initialize authentication service.

        Args:
            db: Database session
            jwt_handler: JWT token handler
            password_handler: Password handler
        """
        self.db = db
        self.jwt_handler = jwt_handler
        self.password_handler = password_handler

    def register(
        self,
        email: str,
        name: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Register a new user.

        Args:
            email: User email address
            name: User full name
            password: Plaintext password

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            UserAlreadyExistsError: If email already registered
            WeakPasswordError: If password doesn't meet requirements
            AuthError: If registration fails
        """
        # Validate password strength
        is_valid, error_msg = self.password_handler.validate_password_strength(password)
        if not is_valid:
            raise WeakPasswordError(error_msg)

        # Check if email already exists
        existing_user = self.db.query(User).filter(User.email == email).first()
        if existing_user:
            raise UserAlreadyExistsError(f"Email {email} is already registered")

        try:
            # Create new user
            hashed_password = self.password_handler.hash_password(password)
            new_user = User(
                email=email,
                name=name,
                password_hash=hashed_password,
                role="user",
                is_active=True
            )

            # Save user to database
            self.db.add(new_user)
            self.db.flush()  # Flush to ensure user_id is generated

            # Create tokens
            access_token = self.jwt_handler.create_access_token(
                subject=new_user.user_id,
                additional_claims={"email": new_user.email, "name": new_user.name}
            )
            refresh_token = self.jwt_handler.create_refresh_token(
                subject=new_user.user_id
            )

            # Create session for refresh token
            self._create_session(new_user.user_id, refresh_token)

            # Commit transaction
            self.db.commit()

            return new_user, access_token, refresh_token

        except IntegrityError as e:
            self.db.rollback()
            raise UserAlreadyExistsError(f"Email {email} is already registered") from e
        except WeakPasswordError:
            raise  # Re-raise password validation errors
        except UserAlreadyExistsError:
            raise  # Re-raise user already exists errors
        except Exception as e:
            self.db.rollback()
            logger.exception(f"Unexpected error during user registration for {email}")
            raise AuthError(f"Registration failed: {str(e)}") from e

    def login(
        self,
        email: str,
        password: str
    ) -> Tuple[User, str, str]:
        """
        Authenticate user and generate tokens.

        Args:
            email: User email address
            password: Plaintext password

        Returns:
            Tuple of (user, access_token, refresh_token)

        Raises:
            InvalidCredentialsError: If email/password is wrong
            AuthError: If login fails
        """
        try:
            # Find user by email
            user = self.db.query(User).filter(User.email == email).first()
            if not user:
                raise InvalidCredentialsError("Invalid email or password")

            # Verify password
            if not user.password_hash or not self.password_handler.verify_password(password, user.password_hash):
                raise InvalidCredentialsError("Invalid email or password")

            # Check if user is active
            if not user.is_active:
                raise InvalidCredentialsError("Account is inactive")

            # Create tokens
            access_token = self.jwt_handler.create_access_token(
                subject=user.user_id,
                additional_claims={"email": user.email, "name": user.name}
            )
            refresh_token = self.jwt_handler.create_refresh_token(
                subject=user.user_id
            )

            # Create session for refresh token
            self._create_session(user.user_id, refresh_token)

            # Update last login time
            user.last_login = datetime.now(UTC)
            self.db.add(user)
            self.db.commit()

            return user, access_token, refresh_token

        except (InvalidCredentialsError, AuthError):
            raise
        except Exception as e:
            raise AuthError(f"Login failed: {str(e)}") from e

    def refresh_token(self, refresh_token: str) -> Tuple[str, str]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            Tuple of (new_access_token, new_refresh_token)

        Raises:
            TokenRefreshError: If refresh fails
            TokenExpiredError: If refresh token is expired
        """
        try:
            # Verify refresh token
            claims = self.jwt_handler.verify_refresh_token(refresh_token)
            user_id = claims.get("sub")

            # Get user
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise TokenRefreshError("User not found")

            if not user.is_active:
                raise TokenRefreshError("Account is inactive")

            # Create new tokens
            new_access_token = self.jwt_handler.create_access_token(
                subject=user.user_id,
                additional_claims={"email": user.email, "name": user.name}
            )
            new_refresh_token = self.jwt_handler.create_refresh_token(
                subject=user.user_id
            )

            # Create new session
            self._create_session(user.user_id, new_refresh_token)

            self.db.commit()

            return new_access_token, new_refresh_token

        except TokenExpiredError:
            raise TokenRefreshError("Refresh token has expired") from None
        except InvalidTokenFormatError as e:
            raise TokenRefreshError("Invalid refresh token") from e
        except (TokenRefreshError, AuthError):
            raise
        except Exception as e:
            raise TokenRefreshError(f"Token refresh failed: {str(e)}") from e

    def logout(self, user_id: str, refresh_token: Optional[str] = None) -> bool:
        """
        Log out user by revoking refresh token(s).

        Args:
            user_id: User ID
            refresh_token: Specific refresh token to revoke (optional).
                          If not provided, revokes all active sessions.

        Returns:
            True if logout successful

        Raises:
            AuthError: If logout fails
        """
        try:
            if refresh_token:
                # Verify refresh token
                claims = self.jwt_handler.verify_refresh_token(refresh_token)
                # Revoke specific session
                session = self.db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.refresh_token_hash == refresh_token
                ).first()
                if session:
                    session.revoked_at = datetime.now(UTC)
                    self.db.add(session)
            else:
                # Revoke all active sessions for user
                sessions = self.db.query(UserSession).filter(
                    UserSession.user_id == user_id,
                    UserSession.revoked_at.is_(None)
                ).all()
                for session in sessions:
                    session.revoked_at = datetime.now(UTC)
                    self.db.add(session)

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            raise AuthError(f"Logout failed: {str(e)}") from e

    def verify_access_token(self, token: str) -> dict:
        """
        Verify access token and return claims.

        Args:
            token: JWT access token

        Returns:
            Token claims dictionary

        Raises:
            InvalidTokenFormatError: If token is invalid or expired
        """
        try:
            claims = self.jwt_handler.verify_access_token(token)
            return claims
        except JWTTokenError as e:
            raise InvalidTokenFormatError("Invalid or expired access token") from e

    def get_current_user(self, token: str) -> Optional[User]:
        """
        Get current user from access token.

        Args:
            token: JWT access token

        Returns:
            User object or None if token invalid

        Raises:
            InvalidTokenFormatError: If token is invalid
        """
        try:
            claims = self.verify_access_token(token)
            user_id = claims.get("sub")
            user = self.db.query(User).filter(User.user_id == user_id).first()
            return user
        except Exception:
            return None

    def change_password(self, user_id: str, current_password: str, new_password: str) -> bool:
        """
        Change user password.

        Args:
            user_id: User ID
            current_password: Current password for verification
            new_password: New password

        Returns:
            True if password changed successfully

        Raises:
            InvalidCredentialsError: If current password is wrong
            WeakPasswordError: If new password doesn't meet requirements
            AuthError: If change fails
        """
        try:
            # Get user
            user = self.db.query(User).filter(User.user_id == user_id).first()
            if not user:
                raise AuthError("User not found")

            # Verify current password
            if not user.password_hash or not self.password_handler.verify_password(
                current_password, user.password_hash
            ):
                raise InvalidCredentialsError("Current password is incorrect")

            # Validate new password
            is_valid, error_msg = self.password_handler.validate_password_strength(new_password)
            if not is_valid:
                raise WeakPasswordError(error_msg)

            # Update password
            user.password_hash = self.password_handler.hash_password(new_password)
            user.updated_at = datetime.now(UTC)
            self.db.add(user)
            self.db.commit()

            return True

        except (InvalidCredentialsError, WeakPasswordError, AuthError):
            raise
        except Exception as e:
            self.db.rollback()
            raise AuthError(f"Password change failed: {str(e)}") from e

    def get_user_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email

        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.email == email).first()

    def get_user_by_id(self, user_id: str) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User ID

        Returns:
            User object or None if not found
        """
        return self.db.query(User).filter(User.user_id == user_id).first()

    def _create_session(self, user_id: str, refresh_token: str) -> UserSession:
        """
        Create a new user session for refresh token.

        Args:
            user_id: User ID
            refresh_token: Refresh token string

        Returns:
            Created UserSession object

        Internal method - does not commit transaction.
        """
        # Hash the refresh token before storing
        token_hash = self.password_handler.hash_password(refresh_token)

        # Create session
        expires_at = datetime.now(UTC) + timedelta(days=7)
        session = UserSession(
            user_id=user_id,
            refresh_token_hash=token_hash,
            expires_at=expires_at
        )

        self.db.add(session)
        return session

    def get_user_sessions(self, user_id: str) -> list:
        """
        Get all valid sessions for a user.

        Args:
            user_id: User ID

        Returns:
            List of valid UserSession objects
        """
        sessions = self.db.query(UserSession).filter(
            UserSession.user_id == user_id,
            UserSession.revoked_at.is_(None),
            UserSession.expires_at > datetime.now(UTC)
        ).all()
        return sessions

    def get_password_requirements(self) -> dict:
        """
        Get password strength requirements for client-side validation.

        Returns:
            Dictionary with password requirements
        """
        return self.password_handler.get_password_strength_requirements()
