import os
from collections.abc import Iterator
from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import Engine, text

from app.db import engine
from app.main import app
from app.storage import get_storage
from tests.support import FakeStorage

BACKEND = Path(__file__).resolve().parents[2]


def alembic_config() -> Config:
    config = Config(str(BACKEND / "alembic.ini"))
    config.set_main_option("script_location", str(BACKEND / "alembic"))
    return config


@pytest.fixture(scope="session")
def migrated_engine() -> Engine:
    if "unused" in os.environ["DATABASE_URL"]:
        pytest.skip("integration tests need Postgres; run scripts/ci.sh")
    command.downgrade(alembic_config(), "base")
    command.upgrade(alembic_config(), "head")
    return engine


@pytest.fixture(autouse=True)
def clean_tables(migrated_engine: Engine) -> None:
    with migrated_engine.begin() as connection:
        connection.execute(text("TRUNCATE media_object, meal"))


@pytest.fixture
def storage() -> FakeStorage:
    return FakeStorage()


@pytest.fixture
def client(storage: FakeStorage) -> Iterator[TestClient]:
    app.dependency_overrides[get_storage] = lambda: storage
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()
