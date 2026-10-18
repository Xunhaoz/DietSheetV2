from fastapi.testclient import TestClient
from sqlalchemy import Engine, NullPool, create_engine, text

from app.main import app
from app.storage import get_storage
from tests.support import FakeStorage, upload


def _app_connections(engine: Engine) -> int:
    probe = create_engine(engine.url, poolclass=NullPool)
    with probe.connect() as connection:
        query = (
            "SELECT count(*) FROM pg_stat_activity"
            " WHERE datname = current_database() AND pid <> pg_backend_pid()"
        )
        return int(connection.execute(text(query)).scalar_one())


def test_shutdown_closes_storage_and_database_connections(migrated_engine: Engine) -> None:
    # Arrange
    storage = FakeStorage()
    app.dependency_overrides[get_storage] = lambda: storage
    migrated_engine.dispose()

    # Act
    with TestClient(app) as client:
        upload(client)
        while_running = _app_connections(migrated_engine)
    after_shutdown = _app_connections(migrated_engine)
    app.dependency_overrides.clear()

    # Assert
    assert while_running >= 1
    assert after_shutdown == 0
    assert storage.closed
