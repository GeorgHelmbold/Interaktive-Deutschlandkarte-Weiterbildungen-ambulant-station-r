from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional, List, Set, Dict

class ConnectionConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    host: str
    port: int
    database: str
    db_username: str
    password: str

class GeocodingConfig(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    mapatlas_api_key: str