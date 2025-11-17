"""
Authentication API Endpoints

Handles user registration, login, logout, token refresh, and profile management.
Also handles Google OAuth2 integration.
"""

from fastapi import APIRouter, HTTPException, status, Depends, Request
from sqlalchemy.orm import Session
import uuid
import os

from backend.app.db.session import get_db
from backend.app.services.auth_service import (
    AuthService,
    InvalidCredentialsError,
    UserAlreadyExistsError,
    WeakPasswordError,
    TokenRefreshError,
)
from backend.app.auth.jwt_handler import get_jwt_handler, InvalidTokenFormatError
from backend.app.auth.password_handler import get_password_handler
from backend.app.auth.oauth_handler import get_oauth_handler, InvalidOAuthTokenError, OAuthError
from backend.app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    RefreshTokenRequest,
    TokenResponse,
    UserResponse,
    PasswordChangeRequest,
    GoogleOAuthTokenRequest,
    GoogleOAuthCallbackRequest,
    GoogleOAuthUrlResponse,
)
from backend.app.models.user import User

router = APIRouter(prefix="/auth", tags=["auth"])


def get_auth_service(db: Session = Depends(get_db)) -> AuthService:
    """Dependency: Get AuthService instance"""
    jwt_handler = get_jwt_handler()
    password_handler = get_password_handler()
    return AuthService(db, jwt_handler, password_handler)


def get_current_user(
    request: Request,
    db: Session = Depends(get_db)
) -> User:
    """Dependency: Get current authenticated user from JWT token"""
    # Extract token from Authorization header
    auth_header = request.headers.get("Authorization", "")
    token = auth_header.replace("Bearer ", "") if auth_header.startswith("Bearer ") else ""

    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token"
        )

    try:
        jwt_handler = get_jwt_handler()
        claims = jwt_handler.verify_access_token(token)
        user_id = claims.get("sub")

        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        return user
    except InvalidTokenFormatError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )


@router.post(
    "/register",
    response_model=TokenResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new user",
    responses={
        201: {"description": "User registered successfully"},
        400: {"description": "Invalid input or weak password"},
        409: {"description": "Email already registered"},
    }
)
async def register(
    request: RegisterRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Register a new user account."""
    try:
        user, access_token, refresh_token = auth_service.register(
            email=request.email,
            name=request.name,
            password=request.password
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )

    except UserAlreadyExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except WeakPasswordError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="User login",
    responses={
        200: {"description": "Login successful"},
        401: {"description": "Invalid credentials"},
    }
)
async def login(
    request: LoginRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Authenticate user and return JWT tokens."""
    try:
        user, access_token, refresh_token = auth_service.login(
            email=request.email,
            password=request.password
        )

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user)
        )

    except InvalidCredentialsError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")


@router.post(
    "/refresh",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    responses={
        200: {"description": "Token refreshed successfully"},
        401: {"description": "Invalid or expired refresh token"},
    }
)
async def refresh_token(
    request: RefreshTokenRequest,
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """Refresh access token using refresh token."""
    try:
        new_access_token, new_refresh_token = auth_service.refresh_token(
            refresh_token=request.refresh_token
        )

        jwt_handler = get_jwt_handler()
        claims = jwt_handler.verify_refresh_token(request.refresh_token)
        user_id = claims.get("sub")
        user = auth_service.get_user_by_id(user_id)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=new_refresh_token,
            token_type="bearer",
            user=UserResponse.from_orm(user) if user else None
        )

    except TokenRefreshError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=str(e))


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
    current_user: User = Depends(get_current_user),
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Log out user by revoking refresh token."""
    auth_service.logout(user_id=current_user.user_id)
    return {"message": "Logout successful", "status": "success"}


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    responses={
        200: {"description": "User profile retrieved"},
        401: {"description": "Not authenticated"},
    }
)
async def get_profile(
    current_user: User = Depends(get_current_user)
) -> UserResponse:
    """Get current authenticated user profile."""
    return UserResponse.from_orm(current_user)


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
    auth_service: AuthService = Depends(get_auth_service)
) -> dict:
    """Change user password."""
    try:
        auth_service.change_password(
            user_id=current_user.user_id,
            current_password=request.current_password,
            new_password=request.new_password
        )
        return {"message": "Password changed successfully", "status": "success"}
    except InvalidCredentialsError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Current password is incorrect")
    except WeakPasswordError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


# Google OAuth2 Endpoints


@router.get(
    "/google/auth-url",
    response_model=GoogleOAuthUrlResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate Google OAuth authorization URL",
    responses={
        200: {"description": "Authorization URL generated"},
        422: {"description": "Missing redirect_uri parameter"},
    }
)
async def get_google_auth_url(
    redirect_uri: str,
    state: str = None
) -> GoogleOAuthUrlResponse:
    """
    Generate Google OAuth2 authorization URL for frontend to redirect to.

    Args:
        redirect_uri: Where Google will redirect after user authorization (e.g., http://localhost:3000/auth/google/callback)
        state: Optional CSRF protection state parameter

    Returns:
        Google OAuth2 authorization URL
    """
    oauth_handler = get_oauth_handler()
    auth_url = oauth_handler.get_authorization_url(
        redirect_uri=redirect_uri,
        state=state
    )
    return GoogleOAuthUrlResponse(auth_url=auth_url)


@router.post(
    "/google/verify-token",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Verify Google ID token and authenticate user",
    responses={
        200: {"description": "Token verified, user authenticated"},
        400: {"description": "Invalid ID token"},
        401: {"description": "User inactive"},
    }
)
async def verify_google_token(
    request: GoogleOAuthTokenRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Verify Google ID token and create/login user.

    This endpoint is used for frontend Google Sign-In flow where the client
    receives an ID token from Google and sends it to backend for verification.

    Args:
        id_token: Google ID token from Google Sign-In

    Returns:
        JWT tokens and user information
    """
    if not request.id_token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing id_token in request")

    try:
        oauth_handler = get_oauth_handler()

        # Verify the token signature and get user info
        token_payload = oauth_handler.verify_id_token(request.id_token)
        user_info = oauth_handler.extract_user_info(token_payload)

        # Check if user exists
        user = db.query(User).filter(User.email == user_info["email"]).first()

        if user:
            # Existing user
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")

            # Update profile picture if provided
            if user_info.get("profile_picture_url"):
                user.profile_picture_url = user_info["profile_picture_url"]
            db.commit()
        else:
            # New user - create account
            user = User(
                user_id=str(uuid.uuid4()),
                email=user_info["email"],
                name=user_info["name"],
                profile_picture_url=user_info.get("profile_picture_url"),
                password_hash=None,  # OAuth users don't have password
                role="user",
                is_active=True
            )
            db.add(user)
            db.commit()

        # Generate JWT tokens
        jwt_handler = get_jwt_handler()
        access_token = jwt_handler.create_access_token(user.user_id)
        refresh_token = jwt_handler.create_refresh_token(user.user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            user=UserResponse.from_orm(user)
        )

    except InvalidOAuthTokenError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Invalid token: {str(e)}")


@router.post(
    "/google/callback",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Handle Google OAuth callback",
    responses={
        200: {"description": "Callback processed, user authenticated"},
        400: {"description": "Invalid authorization code or missing ID token"},
        401: {"description": "Token exchange failed"},
        422: {"description": "Missing required parameters"},
    }
)
async def handle_google_callback(
    request: GoogleOAuthCallbackRequest,
    db: Session = Depends(get_db),
    auth_service: AuthService = Depends(get_auth_service)
) -> TokenResponse:
    """
    Handle OAuth2 authorization code callback from Google.

    This endpoint is used in the backend OAuth flow where the backend
    handles the authorization code exchange with Google.

    Args:
        code: Authorization code from Google
        redirect_uri: Same redirect URI used in authorization request
        state: State parameter for CSRF protection (optional)

    Returns:
        JWT tokens and user information
    """
    try:
        oauth_handler = get_oauth_handler()

        # Exchange authorization code for tokens
        token_response = oauth_handler.exchange_code_for_token(
            code=request.code,
            redirect_uri=request.redirect_uri,
            client_secret=os.getenv("GOOGLE_OAUTH_CLIENT_SECRET")
        )

        # Extract ID token from response
        id_token_str = token_response.get("id_token")
        if not id_token_str:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No id token in token exchange response")

        # Verify ID token and get user info
        token_payload = oauth_handler.verify_id_token(id_token_str)
        user_info = oauth_handler.extract_user_info(token_payload)

        # Check if user exists
        user = db.query(User).filter(User.email == user_info["email"]).first()

        if user:
            # Existing user
            if not user.is_active:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User account is inactive")

            # Update profile picture if provided
            if user_info.get("profile_picture_url"):
                user.profile_picture_url = user_info["profile_picture_url"]
            db.commit()
        else:
            # New user - create account
            user = User(
                user_id=str(uuid.uuid4()),
                email=user_info["email"],
                name=user_info["name"],
                profile_picture_url=user_info.get("profile_picture_url"),
                password_hash=None,  # OAuth users don't have password
                role="user",
                is_active=True
            )
            db.add(user)
            db.commit()

        # Generate JWT tokens
        jwt_handler = get_jwt_handler()
        access_token = jwt_handler.create_access_token(user.user_id)
        refresh_token = jwt_handler.create_refresh_token(user.user_id)

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token,
            token_type="Bearer",
            user=UserResponse.from_orm(user)
        )

    except HTTPException:
        # Re-raise HTTPExceptions (like "No id token" or "User inactive")
        raise
    except InvalidOAuthTokenError as e:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")
