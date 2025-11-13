from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

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

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()