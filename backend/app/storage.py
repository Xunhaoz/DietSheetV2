from functools import lru_cache

import boto3
from botocore.exceptions import ClientError

from app.config import settings


class ObjectStorage:
    """Thin S3 adapter; SeaweedFS is reached by pointing endpoint_url at its S3 port."""

    def __init__(self, client, bucket: str):
        self.client = client
        self.bucket = bucket

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError:
            self.client.create_bucket(Bucket=self.bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)

    def close(self) -> None:
        self.client.close()


@lru_cache
def get_storage() -> ObjectStorage:
    """Create the shared adapter on first use; tests replace it via dependency_overrides."""
    client = boto3.client(
        "s3",
        endpoint_url=settings.s3_endpoint_url,
        aws_access_key_id=settings.s3_access_key,
        aws_secret_access_key=settings.s3_secret_key,
        region_name="us-east-1",
    )
    return ObjectStorage(client, settings.s3_bucket)
