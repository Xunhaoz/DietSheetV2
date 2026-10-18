from collections.abc import Iterator

import boto3
import pytest
from botocore.exceptions import ClientError, EndpointConnectionError
from botocore.stub import Stubber

from app.storage import ObjectStorage, StorageUnavailable


@pytest.fixture
def storage() -> ObjectStorage:
    client = boto3.client(
        "s3",
        endpoint_url="http://127.0.0.1:1",
        aws_access_key_id="test",
        aws_secret_access_key="test",
        region_name="us-east-1",
    )
    return ObjectStorage(client, "bucket")


@pytest.fixture
def stub(storage: ObjectStorage) -> Iterator[Stubber]:
    with Stubber(storage.client) as stubber:
        yield stubber
        stubber.assert_no_pending_responses()


def test_creates_bucket_only_when_missing(storage: ObjectStorage, stub: Stubber) -> None:
    # Arrange
    stub.add_client_error("head_bucket", service_error_code="404", http_status_code=404)
    stub.add_response("create_bucket", {}, {"Bucket": "bucket"})

    # Act
    storage.ensure_bucket()

    # Assert: the stubber verifies create_bucket was called


def test_surfaces_access_errors_instead_of_creating(storage: ObjectStorage, stub: Stubber) -> None:
    # Arrange
    stub.add_client_error("head_bucket", service_error_code="403", http_status_code=403)

    # Act
    with pytest.raises(ClientError) as raised:
        storage.ensure_bucket()

    # Assert
    assert raised.value.response["ResponseMetadata"]["HTTPStatusCode"] == 403


@pytest.mark.parametrize("status", [500, 503])
def test_put_server_errors_are_storage_unavailable(
    storage: ObjectStorage, stub: Stubber, status: int
) -> None:
    # Arrange
    stub.add_client_error("put_object", http_status_code=status)

    # Act / Assert
    with pytest.raises(StorageUnavailable):
        storage.put("key", b"data", "image/jpeg")


def test_put_client_errors_stay_configuration_bugs(storage: ObjectStorage, stub: Stubber) -> None:
    # Arrange
    stub.add_client_error("put_object", service_error_code="AccessDenied", http_status_code=403)

    # Act / Assert
    with pytest.raises(ClientError):
        storage.put("key", b"data", "image/jpeg")


def test_put_connection_errors_are_storage_unavailable(
    storage: ObjectStorage, monkeypatch: pytest.MonkeyPatch
) -> None:
    # Arrange
    def refuse(**kwargs: object) -> None:
        raise EndpointConnectionError(endpoint_url="http://127.0.0.1:1")

    monkeypatch.setattr(storage.client, "put_object", refuse)

    # Act / Assert
    with pytest.raises(StorageUnavailable):
        storage.put("key", b"data", "image/jpeg")
