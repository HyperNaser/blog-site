from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
    )
    
    secret_key: SecretStr
    algorithm: str = "HS256"
    access_token_expire_duration: int = 30

    max_upload_size_bytes: int = 5 * 1024 * 1024

    posts_per_page: int = 10
    max_limit: int = 50
    pages_shown_window: int = 3

settings = Settings() #type: ignore[call-arg]