from collections.abc import Iterator

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.db import get_session
from app.main import app
from app.media.storage import StorageUnavailable, get_storage
from tests.support import FakeStorage, new_key, upload


class UnavailableStorage(FakeStorage):
    def put(self, key: str, data: bytes, content_type: str) -> None:
        raise StorageUnavailable


def test_storage_outage_returns_503_and_retry_with_same_key_succeeds(
    client: TestClient, storage: FakeStorage
) -> None:
    # Arrange
    key = new_key()
    outage = UnavailableStorage()
    app.dependency_overrides[get_storage] = lambda: outage

    # Act
    during = upload(client, key=key)
    app.dependency_overrides[get_storage] = lambda: storage
    after = upload(client, key=key)

    # Assert
    assert during.status_code == 503
    assert after.status_code == 201


def test_database_outage_returns_503(client: TestClient) -> None:
    # Arrange
    unreachable = create_engine("postgresql+psycopg://x:x@127.0.0.1:1/x")

    def broken_session() -> Iterator[Session]:
        with Session(unreachable) as session:
            yield session

    app.dependency_overrides[get_session] = broken_session

    # Act
    response = upload(client)

    # Assert
    assert response.status_code == 503
