import os
from pathlib import Path
from pydantic import BaseSettings, Field, validator

class Settings(BaseSettings):
    # Core
    PROJECT_NAME: str = "AI Innovation Youth 2026 Competition Platform"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Database
    POSTGRES_USER: str = Field(default="postgres")
    POSTGRES_PASSWORD: str = Field(default="postgres")
    POSTGRES_SERVER: str = Field(default="db")  # Docker service name
    POSTGRES_DB: str = Field(default="competition_db")
    POSTGRES_URL: str | None = None

    # JWT
    SECRET_KEY: str = Field(default="super-secret-key-change-me")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 1440

    # AI Validation
    AI_API_KEY: str = Field(default="")
    AI_MODEL: str = "gpt-4o-mini"

    # File storage
    STORAGE_PATH: str = "./storage"

    @validator("POSTGRES_URL", pre=True, always=True)
    def assemble_db_url(cls, v, values):
        if isinstance(v, str) and v:
            return v
        user = values.get("POSTGRES_USER")
        pwd = values.get("POSTGRES_PASSWORD")
        server = values.get("POSTGRES_SERVER")
        db = values.get("POSTGRES_DB")
        return f"postgresql://{user}:{pwd}@{server}/{db}"

    class Config:
        env_file = os.path.join(Path(__file__).resolve().parents[2], ".env")
        env_file_encoding = "utf-8"

settings = Settings()
