"""
Authentication Schemas for MATHESIS LAB

Pydantic models for request/response validation in authentication endpoints.
"""

from typing import Optional
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field, field_validator


class LoginRequest(BaseModel):
    """Request schema for user login"""

    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=1, description="User password")

    class Config:
        example = {
            "email": "user@example.com",
            "password": "MyPassword123!"
        }


class RegisterRequest(BaseModel):
    """Request schema for user registration"""

    email: EmailStr = Field(..., description="User email address")
    name: str = Field(..., min_length=1, max_length=255, description="User full name")
    password: str = Field(..., min_length=8, description="User password")

    @field_validator("password")
    @classmethod
    def validate_password(cls, v):
        """Validate password meets requirements"""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v

    class Config:
        example = {
            "email": "user@example.com",
            "name": "John Doe",
            "password": "MyPassword123!"
        }


class RefreshTokenRequest(BaseModel):
    """Request schema for token refresh"""

    refresh_token: str = Field(..., description="Refresh token for getting new access token")

    class Config:
        example = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }


class TokenResponse(BaseModel):
    """Response schema for authentication endpoints"""

    access_token: str = Field(..., description="JWT access token (short-lived, 15 minutes)")
    refresh_token: str = Field(..., description="JWT refresh token (long-lived, 7 days)")
    token_type: str = Field(default="Bearer", description="Token type (always 'Bearer')")
    expires_in: int = Field(..., description="Access token expiration time in seconds")

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 900  # 15 minutes
        }


class UserResponse(BaseModel):
    """Response schema for user data"""

    user_id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    profile_picture_url: Optional[str] = Field(None, description="User profile picture URL")
    role: str = Field(default="user", description="User role (user, admin, moderator)")
    is_active: bool = Field(default=True, description="Whether user account is active")
    created_at: Optional[datetime] = Field(None, description="Account creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last account update timestamp")
    last_login: Optional[datetime] = Field(None, description="Last login timestamp")

    class Config:
        example = {
            "user_id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "user@example.com",
            "name": "John Doe",
            "profile_picture_url": "https://example.com/profile.jpg",
            "role": "user",
            "is_active": True,
            "created_at": "2024-01-01T00:00:00",
            "updated_at": "2024-01-01T00:00:00",
            "last_login": "2024-01-02T00:00:00"
        }


class LoginResponse(BaseModel):
    """Response schema for login endpoint"""

    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")
    user: UserResponse = Field(..., description="User information")

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 900,
            "user": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe"
            }
        }


class RegisterResponse(BaseModel):
    """Response schema for registration endpoint"""

    user: UserResponse = Field(..., description="Created user information")
    access_token: str = Field(..., description="JWT access token")
    refresh_token: str = Field(..., description="JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    class Config:
        example = {
            "user": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "user@example.com",
                "name": "John Doe"
            },
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 900
        }


class RefreshTokenResponse(BaseModel):
    """Response schema for token refresh endpoint"""

    access_token: str = Field(..., description="New JWT access token")
    refresh_token: str = Field(..., description="New JWT refresh token")
    token_type: str = Field(default="Bearer", description="Token type")
    expires_in: int = Field(..., description="Access token expiration in seconds")

    class Config:
        example = {
            "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
            "token_type": "Bearer",
            "expires_in": 900
        }


class LogoutRequest(BaseModel):
    """Request schema for logout endpoint"""

    refresh_token: Optional[str] = Field(None, description="Refresh token to revoke (optional)")

    class Config:
        example = {
            "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
        }


class PasswordChangeRequest(BaseModel):
    """Request schema for password change endpoint"""

    current_password: str = Field(..., description="Current password")
    new_password: str = Field(..., min_length=8, description="New password")

    @field_validator("new_password")
    @classmethod
    def validate_password(cls, v):
        """Validate new password meets requirements"""
        if not any(char.isupper() for char in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(char.islower() for char in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(char.isdigit() for char in v):
            raise ValueError("Password must contain at least one digit")
        if not any(char in "!@#$%^&*()_+-=[]{}|;:,.<>?" for char in v):
            raise ValueError("Password must contain at least one special character")
        return v

    class Config:
        example = {
            "current_password": "OldPassword123!",
            "new_password": "NewPassword456!"
        }


class ErrorResponse(BaseModel):
    """Standard error response"""

    detail: str = Field(..., description="Error message")
    code: Optional[str] = Field(None, description="Error code")

    class Config:
        example = {
            "detail": "Invalid credentials",
            "code": "INVALID_CREDENTIALS"
        }


class GoogleOAuthTokenRequest(BaseModel):
    """Request schema for Google OAuth2 token verification"""

    id_token: str = Field(..., description="Google ID token from Google Sign-In")

    class Config:
        example = {
            "id_token": "eyJhbGciOiJSUzI1NiIsImtpZCI6IjEifQ..."
        }


class GoogleOAuthCallbackRequest(BaseModel):
    """Request schema for Google OAuth2 callback"""

    code: str = Field(..., description="Authorization code from Google")
    state: Optional[str] = Field(None, description="State parameter for CSRF protection")
    redirect_uri: str = Field(..., description="Redirect URI used in authorization request")

    class Config:
        example = {
            "code": "4/0AY-...",
            "state": "random-state-value",
            "redirect_uri": "http://localhost:3000/auth/google/callback"
        }


class GoogleOAuthUrlResponse(BaseModel):
    """Response schema for Google OAuth2 authorization URL"""

    auth_url: str = Field(..., description="Google OAuth2 authorization URL")

    class Config:
        example = {
            "auth_url": "https://accounts.google.com/o/oauth2/v2/auth?client_id=...&redirect_uri=...&response_type=code&scope=..."
        }
