import os
from typing import Final

from pydantic import BaseSettings, Field


BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


class Settings(BaseSettings):
    secret_key: Final[str] = Field(..., env='SECRET_KEY')
    algorithm: Final[str] = Field(..., env='ALGORITHM')
    token_expire: Final[int] = Field(..., env='TOKEN_EXPIRE')
    base_dir: Final[str] = Field(BASE_DIR, env='BASE_DIR')
    title: Final[str] = Field(..., env='TITLE')
    database_dsn: Final[str] = Field(..., env='DATABASE_DSN')
    app_name: Final[str] = Field(..., env='APP_NAME')
    app_host: Final[str] = Field(..., env='APP_HOST')
    app_port: Final[int] = Field(..., env='APP_PORT')
    redis_url: Final[str] = Field(..., env='REDIS_URL')
    redis_url_local: Final[str] = Field(..., env='LOCAL_REDIS_URL')
    redis_host: Final[str] = Field(..., env='REDIS_HOST')
    redis_port: Final[int] = Field(..., env='REDIS_PORT')
    static_url: Final[str] = Field(..., env='STATIC_URL')
    files_path: str = Field(os.path.join(BASE_DIR, 'files'), env='FILES_BASE_DIR')
    compression_types: list = Field(['zip', '7z', 'tar'], env='COMPRESSION_TYPES')

    class Config:
        env_file = os.path.join(BASE_DIR, '../../.env')
        env_file_encoding = 'utf-8'


settings = Settings()
