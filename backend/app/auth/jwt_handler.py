"""
JWT Token Handler for MATHESIS LAB

Handles creation, verification, and management of JWT tokens.
Uses HS256 algorithm with environment-based secret key.
"""

import os
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any

import jwt
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError, DecodeError


class JWTTokenError(Exception):
    """Base exception for JWT token errors"""
    pass


class TokenExpiredError(JWTTokenError):
    """Raised when token has expired"""
    pass


class InvalidTokenFormatError(JWTTokenError):
    """Raised when token format is invalid"""
    pass


class JWTHandler:
    """
    JWT Token Handler

    Manages JWT token generation, validation, and claims extraction.
    Supports both access tokens (short-lived) and refresh tokens (long-lived).
    """

    # Token configuration
    ALGORITHM = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES = 15  # 15 minutes
    REFRESH_TOKEN_EXPIRE_DAYS = 7     # 7 days

    def __init__(self, secret_key: Optional[str] = None):
        """
        Initialize JWT handler.

        Args:
            secret_key: Secret key for token signing.
                       If None, loads from JWT_SECRET_KEY environment variable.
                       If not found, raises error.

        Raises:
            JWTTokenError: If no secret key is available
        """
        self.secret_key = secret_key or os.getenv("JWT_SECRET_KEY")
        if not self.secret_key:
            raise JWTTokenError(
                "JWT_SECRET_KEY environment variable not set. "
                "Please set it before using JWT functionality."
            )

    def create_access_token(
        self,
        subject: str,  # user_id
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT access token.

        Args:
            subject: User ID to embed in token (as 'sub' claim)
            additional_claims: Additional claims to add to token (e.g., {'email': 'user@example.com'})
            expires_delta: Custom expiration time. If None, uses ACCESS_TOKEN_EXPIRE_MINUTES

        Returns:
            Encoded JWT token as string

        Example:
            >>> handler = JWTHandler()
            >>> token = handler.create_access_token(
            ...     subject="user123",
            ...     additional_claims={"email": "user@example.com"}
            ... )
        """
        if expires_delta is None:
            expires_delta = timedelta(minutes=self.ACCESS_TOKEN_EXPIRE_MINUTES)

        return self._create_token(
            data={"sub": subject, "type": "access", **(additional_claims or {})},
            expires_delta=expires_delta
        )

    def create_refresh_token(
        self,
        subject: str,  # user_id
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create a JWT refresh token.

        Args:
            subject: User ID to embed in token
            additional_claims: Additional claims to add to token
            expires_delta: Custom expiration time. If None, uses REFRESH_TOKEN_EXPIRE_DAYS

        Returns:
            Encoded JWT token as string

        Example:
            >>> handler = JWTHandler()
            >>> token = handler.create_refresh_token(subject="user123")
        """
        if expires_delta is None:
            expires_delta = timedelta(days=self.REFRESH_TOKEN_EXPIRE_DAYS)

        return self._create_token(
            data={"sub": subject, "type": "refresh", **(additional_claims or {})},
            expires_delta=expires_delta
        )

    def _create_token(
        self,
        data: Dict[str, Any],
        expires_delta: timedelta
    ) -> str:
        """
        Internal method to create JWT token.

        Args:
            data: Claims dictionary to encode
            expires_delta: Token expiration time delta

        Returns:
            Encoded JWT token
        """
        to_encode = data.copy()
        now = datetime.now(timezone.utc)
        expire = now + expires_delta

        to_encode.update({
            "exp": expire,
            "iat": now
        })

        encoded_jwt = jwt.encode(
            to_encode,
            self.secret_key,
            algorithm=self.ALGORITHM
        )

        return encoded_jwt

    def verify_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode JWT token.

        Args:
            token: JWT token string to verify

        Returns:
            Decoded token claims as dictionary

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenFormatError: If token format is invalid or signature is wrong

        Example:
            >>> handler = JWTHandler()
            >>> claims = handler.verify_token(token)
            >>> user_id = claims.get("sub")
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM]
            )
            return payload
        except ExpiredSignatureError as e:
            raise TokenExpiredError("Token has expired") from e
        except (InvalidTokenError, DecodeError) as e:
            raise InvalidTokenFormatError("Invalid token format or signature") from e

    def verify_access_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode an access token, ensuring it's the correct type.

        Args:
            token: JWT access token to verify

        Returns:
            Decoded token claims

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenFormatError: If token is invalid or not an access token
        """
        claims = self.verify_token(token)
        if claims.get("type") != "access":
            raise InvalidTokenFormatError("Token is not an access token")
        return claims

    def verify_refresh_token(self, token: str) -> Dict[str, Any]:
        """
        Verify and decode a refresh token, ensuring it's the correct type.

        Args:
            token: JWT refresh token to verify

        Returns:
            Decoded token claims

        Raises:
            TokenExpiredError: If token has expired
            InvalidTokenFormatError: If token is invalid or not a refresh token
        """
        claims = self.verify_token(token)
        if claims.get("type") != "refresh":
            raise InvalidTokenFormatError("Token is not a refresh token")
        return claims

    def extract_user_id(self, token: str) -> str:
        """
        Extract user ID from token without full verification.

        Useful for debugging or extracting claims without exceptions.

        Args:
            token: JWT token string

        Returns:
            User ID (subject claim) or None if token is invalid
        """
        try:
            claims = self.verify_token(token)
            return claims.get("sub")
        except JWTTokenError:
            return None

    def get_token_expiration_time(self, token: str) -> Optional[datetime]:
        """
        Get token expiration time without full verification.

        Args:
            token: JWT token string

        Returns:
            Expiration datetime in UTC or None if token is invalid
        """
        try:
            payload = jwt.decode(
                token,
                self.secret_key,
                algorithms=[self.ALGORITHM]
            )
            exp_timestamp = payload.get("exp")
            if exp_timestamp:
                return datetime.fromtimestamp(exp_timestamp, tz=timezone.utc)
            return None
        except Exception:
            return None

    def is_token_expired(self, token: str) -> bool:
        """
        Check if token is expired.

        Args:
            token: JWT token string

        Returns:
            True if token is expired, False otherwise
        """
        try:
            self.verify_token(token)
            return False
        except TokenExpiredError:
            return True
        except JWTTokenError:
            return None


# Singleton instance for application-wide use
_jwt_handler_instance: Optional[JWTHandler] = None


def get_jwt_handler(secret_key: Optional[str] = None) -> JWTHandler:
    """
    Get or create JWT handler instance.

    Args:
        secret_key: Secret key for JWT. If None, loads from environment.

    Returns:
        JWTHandler instance
    """
    global _jwt_handler_instance
    if _jwt_handler_instance is None:
        _jwt_handler_instance = JWTHandler(secret_key)
    return _jwt_handler_instance


def reset_jwt_handler():
    """Reset JWT handler instance (useful for testing)"""
    global _jwt_handler_instance
    _jwt_handler_instance = None
