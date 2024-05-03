from functools import lru_cache

from pydantic import IPvAnyAddress
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DB: str = "nooz.db"
    HOST: IPvAnyAddress = "0.0.0.0"
    PORT: int = 9100
    DEBUG: bool = True
    WRITE_DB: bool = True
    JSON_LOGS: bool = False
    RELOAD: bool = True if DEBUG else False

    class Config:
        env_file = "./.env" or None # if is_dbg else "./.env"


@lru_cache
def get_settings():
    return Settings()


settings = get_settings()
