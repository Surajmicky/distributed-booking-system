from pydantic_settings import BaseSettings
from typing import Optional
class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    ENVIRONMENT: str

class Config:
    env_file=".env"

settings = Settings()