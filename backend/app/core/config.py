from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    PROJECT_NAME: str = "MATHESIS LAB"
    API_V1_STR: str = "/api/v1"

    DATABASE_URL: str = "postgresql+psycopg2://user:password@db:5432/mathesis_lab_db" # Placeholder, will be replaced by environment variable

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()