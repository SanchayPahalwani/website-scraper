from pydantic_settings import BaseSettings
from pydantic import HttpUrl
from functools import lru_cache

class Settings(BaseSettings):
    redis_host: str = 'localhost'
    redis_port: int = 6379
    redis_db: int = 0
    auth_token: str = "SuperSecretStaticToken"
    json_storage_file: str = "products.json"

    class Config:
        evn_file = ".env"

@lru_cache
def get_settings():
    return Settings()
