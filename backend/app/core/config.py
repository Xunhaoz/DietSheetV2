from uuid import UUID

from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # Keep secret values out of startup validation errors.
    model_config = SettingsConfigDict(hide_input_in_errors=True)

    database_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "diet-media"
    # Minimal version: one owner and one static Bearer token instead of sessions.
    owner_id: UUID
    # Refuse to start with an empty or guessable token (e.g. API_TOKEN= left blank in .env).
    api_token: SecretStr = Field(min_length=32)


settings = Settings()
