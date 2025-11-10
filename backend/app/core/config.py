from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "MATHESIS LAB"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "sqlite+pysqlite:///./mathesis_lab.db" # Default to local SQLite for development

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()