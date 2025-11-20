from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional
from pathlib import Path
from dotenv import load_dotenv
import os

# Load .env file from backend directory
env_path = Path(__file__).parent.parent.parent / ".env"
if env_path.exists():
    load_dotenv(env_path)
elif Path("/mnt/d/progress/MATHESIS LAB/backend/.env").exists():
    load_dotenv(Path("/mnt/d/progress/MATHESIS LAB/backend/.env"))

class Settings(BaseSettings):
    PROJECT_NAME: str = "MATHESIS LAB"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite+pysqlite:///./mathesis_lab.db" # Default to local SQLite for development

    # Vertex AI Settings
    VERTEX_AI_PROJECT_ID: Optional[str] = None
    VERTEX_AI_LOCATION: Optional[str] = None
    ENABLE_AI_FEATURES: bool = False

    # Zotero API Settings
    ZOTERO_API_BASE_URL: Optional[str] = None
    ZOTERO_API_KEY: Optional[str] = None # If authentication is needed

    # YouTube Data API Settings
    YOUTUBE_API_KEY: Optional[str] = None

    # Google OAuth2 Settings
    GOOGLE_OAUTH_CLIENT_ID: Optional[str] = None
    GOOGLE_OAUTH_CLIENT_SECRET: Optional[str] = None
    GOOGLE_OAUTH_REDIRECT_URI: str = "http://localhost:3001/#/gdrive/callback"

    # Google Drive Settings
    GOOGLE_DRIVE_ENABLED: bool = False
    GOOGLE_DRIVE_CLIENT_ID: Optional[str] = None
    GOOGLE_DRIVE_CLIENT_SECRET: Optional[str] = None
    GOOGLE_DRIVE_REDIRECT_URI: str = "http://localhost:8000/api/v1/google-drive/auth/callback"
    GOOGLE_DRIVE_CURRICULUM_FOLDER_ID: str = "root"

    # Sync Configuration
    SYNC_INTERVAL_MINUTES: int = 5
    MAX_SYNC_RETRIES: int = 3
    CONFLICT_RESOLUTION_MODE: str = "manual"  # manual | auto_latest | auto_local

    # JWT Settings
    JWT_SECRET_KEY: str = "your-super-secret-jwt-key-change-this-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS Settings
    ALLOWED_ORIGINS: list = ["http://localhost:3000", "http://localhost:3002"]
    FRONTEND_URL: str = "http://localhost:3000"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).parent.parent.parent.parent / "backend" / ".env")
    )

settings = Settings()