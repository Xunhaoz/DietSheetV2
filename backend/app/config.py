from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str
    s3_endpoint_url: str
    s3_access_key: str
    s3_secret_key: str
    s3_bucket: str = "diet-media"


settings = Settings()
