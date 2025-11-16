"""
Authentication Endpoints for MATHESIS LAB

Provides REST API endpoints for user authentication, registration, token management.
"""

from datetime import timedelta, datetime, UTC
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.auth.jwt_handler import get_jwt_handler, JWTHandler, JWTTokenError
from backend.app.auth.password_handler import get_password_handler, PasswordHandler, WeakPasswordError
from backend.app.auth.oauth_handler import get_oauth_handler, GoogleOAuthHandler, OAuthError, InvalidOAuthTokenError
from backend.app.core.dependencies import get_db, get_current_user
from backend.app.models.user import User
from backend.app.schemas.auth import (
    LoginRequest,
    LoginResponse,
    RegisterRequest,
    RegisterResponse,
    RefreshTokenRequest,
    RefreshTokenResponse,
    TokenResponse,
    UserResponse,
    LogoutRequest,
    PasswordChangeRequest,
    GoogleOAuthCallbackRequest,
)
from backend.app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    TokenRefreshError,
)

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    password_handler: PasswordHandler = Depends(get_password_handler),
) -> AuthService:
    """
    Dependency to get authentication service.

    Args:
        db: Database session
        jwt_handler: JWT handler instance
        password_handler: Password handler instance

    Returns:
        AuthService instance
    """
    return AuthService(db, jwt_handler, password_handler)


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Invalid input or user already exists"},
        422: {"description": "Validation error"},
    }
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RegisterResponse:
    """
    Register a new user account.

    **Request Body:**
    - email: User email address (must be unique)
    - name: User full name
    - password: Password (must meet strength requirements)

    **Password Requirements:**
    - Minimum 8 characters
    - At least one uppercase letter (A-Z)
    - At least one lowercase letter (a-z)
    - At least one digit (0-9)
    - At least one special character (!@#$%^&*...)

    **Response:**
    Returns user information and authentication tokens (access + refresh)

    **Raises:**
    - 400: User already exists or weak password
    - 422: Validation error
    """
    try:
        user, access_token, refresh_token = auth_service.register(
            email=request.email,
            name=request.name,
            password=request.password,
        )

        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )

        return RegisterResponse(
            user=user_response,
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=15 * 60,  # 15 minutes in seconds
        )

    except UserAlreadyExistsError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Password does not meet requirements: {str(e)}",
        )


@router.post(
    "/login",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    }
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> LoginResponse:
    """
    Authenticate user and return tokens.

    **Request Body:**
    - email: User email address
    - password: User password

    **Response:**
    Returns authentication tokens (access + refresh) and user information

    **Raises:**
    - 401: Invalid email or password
    - 422: Validation error
    """
    try:
        user, access_token, refresh_token = auth_service.login(
            email=request.email,
            password=request.password,
        )

        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=15 * 60,  # 15 minutes in seconds
            user=user_response,
        )

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/refresh",
    response_model=RefreshTokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
        422: {"description": "Validation error"},
    }
)
async def refresh(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service),
) -> RefreshTokenResponse:
    """
    Refresh access token using refresh token.

    **Request Body:**
    - refresh_token: Valid refresh token (issued during login/register)

    **Response:**
    Returns new access token and refresh token

    **Raises:**
    - 401: Invalid or expired refresh token
    - 422: Validation error
    """
    try:
        access_token, refresh_token = auth_service.refresh_token(request.refresh_token)

        return RefreshTokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=15 * 60,  # 15 minutes in seconds
        )

    except TokenRefreshError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="User logout",
    responses={
        200: {"description": "Logout successful"},
        401: {"description": "Not authenticated"},
    }
)
async def logout(
    request: Optional[LogoutRequest] = None,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Logout user by revoking refresh token(s).

    **Request Body (Optional):**
    - refresh_token: Specific refresh token to revoke (optional)
                    If not provided, revokes all active sessions

    **Response:**
    Success message

    **Raises:**
    - 401: Not authenticated
    """
    try:
        refresh_token = request.refresh_token if request else None
        auth_service.logout(current_user.user_id, refresh_token)

        return {
            "message": "Logged out successfully",
            "user_id": current_user.user_id,
        }

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Logout failed: {str(e)}",
        )


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user",
    responses={
        200: {"description": "Current user information"},
        401: {"description": "Not authenticated"},
    }
)
async def get_me(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Get information about the current authenticated user.

    **Response:**
    Returns current user information

    **Raises:**
    - 401: Not authenticated
    """
    return UserResponse(
        user_id=current_user.user_id,
        email=current_user.email,
        name=current_user.name,
        profile_picture_url=current_user.profile_picture_url,
        role=current_user.role,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        updated_at=current_user.updated_at,
        last_login=current_user.last_login,
    )


@router.post(
    "/change-password",
    status_code=status.HTTP_200_OK,
    summary="Change user password",
    responses={
        200: {"description": "Password changed successfully"},
        400: {"description": "Invalid current password or weak new password"},
        401: {"description": "Not authenticated"},
    }
)
async def change_password(
    request: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Change password for the current user.

    **Request Body:**
    - current_password: Current password for verification
    - new_password: New password (must meet strength requirements)

    **Response:**
    Success message

    **Raises:**
    - 400: Invalid current password or weak new password
    - 401: Not authenticated
    """
    try:
        auth_service.change_password(
            current_user.user_id,
            request.current_password,
            request.new_password,
        )

        return {
            "message": "Password changed successfully",
            "user_id": current_user.user_id,
        }

    except InvalidCredentialsError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )
    except WeakPasswordError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"New password does not meet requirements: {str(e)}",
        )


@router.get(
    "/password-requirements",
    status_code=status.HTTP_200_OK,
    summary="Get password strength requirements",
    responses={
        200: {"description": "Password requirements"},
    }
)
async def get_password_requirements(
    auth_service: AuthService = Depends(get_auth_service),
) -> dict:
    """
    Get password strength requirements for client-side validation.

    **Response:**
    Returns password strength requirements
    """
    return auth_service.get_password_requirements()


# ============================================================================
# Google OAuth2 Endpoints
# ============================================================================


@router.post(
    "/google/verify-token",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Google OAuth2 ID token and login",
    responses={
        200: {"description": "Login successful"},
        400: {"description": "Invalid or expired token"},
        401: {"description": "Invalid credentials"},
    }
)
async def verify_google_token(
    request: dict,  # {"id_token": "google_id_token_string"}
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler),
) -> LoginResponse:
    """
    Verify Google OAuth2 ID token and create/login user.

    **Request Body:**
    - id_token: Google ID token from Google Sign-In (from frontend)

    **Response:**
    Returns authentication tokens and user information

    **Process:**
    1. Verify Google ID token signature
    2. Extract user information from token
    3. Find or create user in database
    4. Generate JWT access and refresh tokens
    5. Return tokens and user info

    **Raises:**
    - 400: Invalid or expired Google token
    - 401: Token verification failed
    """
    id_token_str = request.get("id_token")
    if not id_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="id_token required in request body",
        )

    try:
        # Verify Google ID token
        token_payload = oauth_handler.verify_id_token(id_token_str)
        user_info = oauth_handler.extract_user_info(token_payload)

        # Find or create user
        email = user_info.get("email")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user from Google OAuth data
            user = User(
                email=email,
                name=user_info.get("name", "Google User"),
                password_hash=None,  # OAuth users don't have password
                profile_picture_url=user_info.get("profile_picture_url"),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.flush()
        elif not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        # Create JWT tokens
        access_token = jwt_handler.create_access_token(
            subject=user.user_id,
            additional_claims={"email": user.email, "name": user.name, "oauth_provider": "google"}
        )
        refresh_token = jwt_handler.create_refresh_token(subject=user.user_id)

        # Update last login
        user.last_login = datetime.now(UTC)
        db.add(user)
        db.commit()

        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=15 * 60,
            user=user_response,
        )

    except InvalidOAuthTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google OAuth verification failed: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth login failed",
        ) from e


@router.get(
    "/google/auth-url",
    status_code=status.HTTP_200_OK,
    summary="Get Google OAuth2 authorization URL",
    responses={
        200: {"description": "Authorization URL"},
    }
)
async def get_google_auth_url(
    redirect_uri: str,
    state: Optional[str] = None,
    oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler),
) -> dict:
    """
    Get Google OAuth2 authorization URL for Authorization Code flow.

    **Query Parameters:**
    - redirect_uri: Redirect URI where user will be sent after Google login
                   (must match registered URI in Google Console)
    - state: CSRF protection state parameter (optional)

    **Response:**
    Returns the authorization URL to redirect user to

    **Example Frontend Usage:**
    ```javascript
    const response = await fetch('/api/v1/auth/google/auth-url?redirect_uri=http://localhost:3000/auth/google/callback');
    const { auth_url } = await response.json();
    window.location.href = auth_url;
    ```
    """
    try:
        auth_url = oauth_handler.get_authorization_url(
            redirect_uri=redirect_uri,
            state=state
        )
        return {"auth_url": auth_url}
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post(
    "/google/callback",
    response_model=LoginResponse,
    status_code=status.HTTP_200_OK,
    summary="Google OAuth2 authorization code callback",
    responses={
        200: {"description": "Login successful"},
        400: {"description": "Invalid authorization code"},
        401: {"description": "Token exchange failed"},
    }
)
async def google_oauth_callback(
    request: GoogleOAuthCallbackRequest,
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
    oauth_handler: GoogleOAuthHandler = Depends(get_oauth_handler),
) -> LoginResponse:
    """
    Handle Google OAuth2 authorization code callback.

    **Request Body:**
    - code: Authorization code from Google OAuth2 flow
    - redirect_uri: Same redirect_uri used in authorization request
    - state: CSRF protection state parameter (optional, for validation)

    **Response:**
    Returns authentication tokens and user information

    **Process:**
    1. Exchange authorization code for access and ID tokens
    2. Verify ID token signature
    3. Extract user information from token
    4. Find or create user in database
    5. Generate JWT access and refresh tokens
    6. Return tokens and user info

    **Raises:**
    - 400: Invalid authorization code
    - 401: Token exchange or verification failed

    **Example Frontend Usage:**
    ```typescript
    const response = await fetch('/api/v1/auth/google/callback', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        code: 'authorization_code_from_google',
        redirect_uri: 'http://localhost:3000/auth/google/callback',
        state: 'csrf_state_value'
      })
    });
    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    ```
    """
    try:
        # Exchange authorization code for tokens
        token_response = oauth_handler.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri
        )

        # Extract ID token from response
        id_token_str = token_response.get("id_token")
        if not id_token_str:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No ID token in authorization response",
            )

        # Verify ID token
        token_payload = oauth_handler.verify_id_token(id_token_str)
        user_info = oauth_handler.extract_user_info(token_payload)

        # Find or create user
        email = user_info.get("email")
        user = db.query(User).filter(User.email == email).first()

        if not user:
            # Create new user from Google OAuth data
            user = User(
                email=email,
                name=user_info.get("name", "Google User"),
                password_hash=None,  # OAuth users don't have password
                profile_picture_url=user_info.get("profile_picture_url"),
                role="user",
                is_active=True,
            )
            db.add(user)
            db.flush()
        elif not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Account is inactive",
            )

        # Create JWT tokens
        access_token = jwt_handler.create_access_token(
            subject=user.user_id,
            additional_claims={
                "email": user.email,
                "name": user.name,
                "oauth_provider": "google"
            }
        )
        refresh_token = jwt_handler.create_refresh_token(subject=user.user_id)

        # Update last login
        user.last_login = datetime.now(UTC)
        db.add(user)
        db.commit()

        user_response = UserResponse(
            user_id=user.user_id,
            email=user.email,
            name=user.name,
            profile_picture_url=user.profile_picture_url,
            role=user.role,
            is_active=user.is_active,
            created_at=user.created_at,
            updated_at=user.updated_at,
            last_login=user.last_login,
        )

        return LoginResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            expires_in=15 * 60,
            user=user_response,
        )

    except InvalidOAuthTokenError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except OAuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Google OAuth callback failed: {str(e)}",
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Google OAuth callback processing failed",
        ) from e
