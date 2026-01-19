from typing import Optional

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    DATABASE_URL: str = "postgresql://postgres:postgres@localhost:5432/mes_edms"
    DB_POOL_SIZE: int = 10
    DB_MAX_OVERFLOW: int = 20
    DB_POOL_PRE_PING: bool = True
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30
    DB_CONNECT_TIMEOUT: int = 5
    DB_ECHO_POOL: bool = False
    
    # Security
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 480  # 8 hours
    
    # File Storage
    FILE_STORAGE_PATH: str = "/var/app/storage/documents"
    TECH_FILE_STORAGE_PATH: Optional[str] = None
    MAX_FILE_SIZE_MB: int = 100
    
    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]
    
    # Admin seed
    ADMIN_EMAIL: str = "animobit12@mail.ru"
    ADMIN_PASSWORD: str = "adminpassword"
    ADMIN_NAME: str = "Administrator"
    
    class Config:
        env_file = ".env"


settings = Settings()
