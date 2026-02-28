from pydantic import BaseSettings
import os

class Settings(BaseSettings):
    DATABASE_URL: str = "sqlite:///./voting_system"
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"

settings = Settings()