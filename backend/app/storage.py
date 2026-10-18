from functools import lru_cache
from typing import TYPE_CHECKING

import boto3
from botocore.config import Config
from botocore.exceptions import BotoCoreError, ClientError

from app.config import settings

if TYPE_CHECKING:  # stubs come from the boto3-stubs dev dependency
    from mypy_boto3_s3 import S3Client


class StorageUnavailable(Exception):
    """Object storage could not be reached or failed on its side; the request can be retried."""


class ObjectStorage:
    """Thin S3 adapter; SeaweedFS is reached by pointing endpoint_url at its S3 port."""

    def __init__(self, client: "S3Client", bucket: str):
        self.client = client
        self.bucket = bucket

    def ensure_bucket(self) -> None:
        try:
            self.client.head_bucket(Bucket=self.bucket)
        except ClientError as exc:
            # HEAD responses have no body, so a missing bucket is only visible as HTTP 404.
            # Anything else (bad credentials, server errors) must surface, not trigger a create.
            if exc.response["ResponseMetadata"]["HTTPStatusCode"] != 404:
                raise
            self.client.create_bucket(Bucket=self.bucket)

    def put(self, key: str, data: bytes, content_type: str) -> None:
        try:
            self.client.put_object(Bucket=self.bucket, Key=key, Body=data, ContentType=content_type)
        except BotoCoreError as exc:  # connection errors and timeouts
            raise StorageUnavailable from exc
        except ClientError as exc:
            # 5xx is an outage; 4xx such as bad credentials is a configuration bug and stays a 500.
            if exc.response["ResponseMetadata"]["HTTPStatusCode"] >= 500:
                raise StorageUnavailable from exc
            raise

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
        config=Config(
            connect_timeout=5,
            read_timeout=30,
            retries={"max_attempts": 3, "mode": "standard"},
            # SeaweedFS on the private network only resolves path-style URLs.
            s3={"addressing_style": "path"},
        ),
    )
    return ObjectStorage(client, settings.s3_bucket)
