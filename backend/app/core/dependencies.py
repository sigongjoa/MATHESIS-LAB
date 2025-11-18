"""
FastAPI Dependency Injection for MATHESIS LAB

Provides dependency functions for route handlers.
"""

from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from backend.app.db.session import SessionLocal
from backend.app.auth.jwt_handler import get_jwt_handler, JWTHandler, JWTTokenError
from backend.app.models.user import User

# HTTP Bearer authentication
security = HTTPBearer()


def get_db() -> Session:
    """
    Get database session dependency.

    Yields:
        Database session

    Example:
        >>> @router.get("/curriculums")
        >>> async def get_curriculums(db: Session = Depends(get_db)):
        >>>     return db.query(Curriculum).all()
    """
    db = SessionLocal()
    yield db
    db.close()


async def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> User:
    """
    Get current authenticated user from JWT token.

    Args:
        credentials: HTTP Bearer token
        db: Database session
        jwt_handler: JWT handler instance

    Returns:
        Current User object

    Raises:
        HTTPException: If token is missing, invalid, or expired
        JWTTokenError: If token verification fails (propagated from jwt_handler)

    Example:
        >>> @router.get("/me")
        >>> async def get_me(current_user: User = Depends(get_current_user)):
        >>>     return current_user
    """
    if not credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    # Verify and decode token - let JWTTokenError propagate
    claims = jwt_handler.verify_access_token(token)
    user_id = claims.get("sub")

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token claims",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Get user from database
    user = db.query(User).filter(User.user_id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="User account is inactive",
        )

    return user


async def get_current_user_optional(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security),
    db: Session = Depends(get_db),
    jwt_handler: JWTHandler = Depends(get_jwt_handler),
) -> Optional[User]:
    """
    Get current user if authenticated, otherwise return None.

    NOTE: This function intentionally does NOT catch JWTTokenError.
    Invalid tokens will cause errors to propagate, which is correct behavior
    for debugging. If you need to silently ignore invalid tokens, validate
    the token format BEFORE calling verify_access_token.

    Args:
        credentials: HTTP Bearer token (optional)
        db: Database session
        jwt_handler: JWT handler instance

    Returns:
        User object if authenticated, None otherwise

    Raises:
        JWTTokenError: If token is present but invalid (let it propagate for debugging)

    Example:
        >>> @router.get("/items")
        >>> async def get_items(current_user: Optional[User] = Depends(get_current_user_optional)):
        >>>     if current_user:
        >>>         return db.query(Item).filter(Item.owner_id == current_user.user_id).all()
        >>>     return db.query(Item).filter(Item.is_public == True).all()
    """
    if not credentials:
        return None

    token = credentials.credentials

    # Verify and decode token - let JWTTokenError propagate for debugging
    claims = jwt_handler.verify_access_token(token)
    user_id = claims.get("sub")

    if not user_id:
        return None

    # Get user from database
    user = db.query(User).filter(User.user_id == user_id).first()
    if user and user.is_active:
        return user

    return None


async def get_admin_user(
    current_user: User = Depends(get_current_user),
) -> User:
    """
    Get current user and verify they have admin role.

    Args:
        current_user: Current authenticated user

    Returns:
        User object if user is admin

    Raises:
        HTTPException: If user is not admin

    Example:
        >>> @router.post("/users")
        >>> async def create_user(user: UserCreate, admin: User = Depends(get_admin_user)):
        >>>     # Only admins can create users
        >>>     return create_new_user(user)
    """
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )

    return current_user
