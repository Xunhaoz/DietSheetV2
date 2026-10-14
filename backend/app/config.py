from uuid import UUID

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "diet-media"
    # Minimal version: one owner and one static Bearer token instead of sessions.
    owner_id: UUID
    api_token: str


settings = Settings()
