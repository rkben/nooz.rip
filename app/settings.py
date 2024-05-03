from functools import lru_cache

from pydantic import IPvAnyAddress
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB: str = "db.sqlite3"
    HOST: IPvAnyAddress
    PORT: int
    DEBUG: bool = False
    JSON_LOGS: bool = False
    RELOAD: bool = True if DEBUG else False

    class Config:
        env_file = "./.env"  # if is_dbg else "./.env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
