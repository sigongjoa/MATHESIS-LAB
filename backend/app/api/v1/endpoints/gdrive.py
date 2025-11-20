"""
Google Drive OAuth endpoints for MATHESIS LAB

Handles OAuth 2.0 authentication flow for Google Drive access.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime, timedelta, UTC
from typing import Optional

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build

from backend.app.db.session import get_db
from backend.app.models.user import User
from backend.app.core.config import settings
from backend.app.api.dependencies import get_current_user

router = APIRouter()

# OAuth 2.0 scopes for Google Drive
SCOPES = ['https://www.googleapis.com/auth/drive.file']


@router.get("/auth/url")
async def get_gdrive_auth_url(
    current_user: User = Depends(get_current_user)
):
    """
    Generate Google Drive OAuth authorization URL
    
    Returns:
        dict: Contains authorization_url for user to visit
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    
    authorization_url, state = flow.authorization_url(
        access_type='offline',
        include_granted_scopes='true',
        prompt='consent'
    )
    
    return {
        "authorization_url": authorization_url,
        "state": state
    }


@router.post("/auth/callback")
async def gdrive_auth_callback(
    code: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Handle OAuth callback and store tokens
    
    Args:
        code: Authorization code from Google
        current_user: Current authenticated user
        db: Database session
        
    Returns:
        dict: Success message
    """
    flow = Flow.from_client_config(
        {
            "web": {
                "client_id": settings.GOOGLE_OAUTH_CLIENT_ID,
                "client_secret": settings.GOOGLE_OAUTH_CLIENT_SECRET,
                "auth_uri": "https://accounts.google.com/o/oauth2/auth",
                "token_uri": "https://oauth2.googleapis.com/token",
                "redirect_uris": [settings.GOOGLE_OAUTH_REDIRECT_URI]
            }
        },
        scopes=SCOPES
    )
    
    flow.redirect_uri = settings.GOOGLE_OAUTH_REDIRECT_URI
    
    # Exchange authorization code for tokens
    flow.fetch_token(code=code)
    
    credentials = flow.credentials
    
    # Store tokens in database
    current_user.gdrive_access_token = credentials.token
    current_user.gdrive_refresh_token = credentials.refresh_token
    current_user.gdrive_token_expiry = credentials.expiry
    
    db.commit()
    
    return {
        "message": "Google Drive connected successfully",
        "expires_at": credentials.expiry.isoformat() if credentials.expiry else None
    }


@router.get("/auth/status")
async def get_gdrive_auth_status(
    current_user: User = Depends(get_current_user)
):
    """
    Check if user has connected Google Drive
    
    Returns:
        dict: Connection status and expiry
    """
    is_connected = bool(current_user.gdrive_access_token)
    
    return {
        "is_connected": is_connected,
        "expires_at": current_user.gdrive_token_expiry.isoformat() if current_user.gdrive_token_expiry else None
    }


@router.post("/auth/disconnect")
async def disconnect_gdrive(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Disconnect Google Drive by removing tokens
    
    Returns:
        dict: Success message
    """
    current_user.gdrive_access_token = None
    current_user.gdrive_refresh_token = None
    current_user.gdrive_token_expiry = None
    
    db.commit()
    
    return {"message": "Google Drive disconnected successfully"}
