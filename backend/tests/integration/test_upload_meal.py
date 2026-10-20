import uuid
from typing import Any

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import Engine, select
from sqlalchemy.orm import Session

from app.meals.models import Meal
from app.media.images import MAX_BYTES
from app.media.models import MediaKind, MediaObject
from tests.support import FakeStorage, make_jpeg, new_key, upload

USER_KEY = "meal-20260925002732419-557692"  # the format the iPhone Shortcut generates


def test_creates_meal_and_stores_the_source_photo(
    client: TestClient, storage: FakeStorage, migrated_engine: Engine
) -> None:
    # Arrange
    photo = make_jpeg(768, 1024)

    # Act
    response = upload(client, key=USER_KEY, photo=photo, notes="雞腿飯")

    # Assert
    assert response.status_code == 201
    body = response.json()
    assert (body["mealType"], body["notes"]) == ("lunch", "雞腿飯")
    assert body["capturedAt"] == "2026-10-18T04:30:00Z"
    assert body["media"] == {}
    assert list(storage.objects.values()) == [photo]
    with Session(migrated_engine) as session:
        meal = session.scalars(select(Meal)).one()
        assert meal.idempotency_key == USER_KEY
        assert [(m.kind, m.width, m.height) for m in meal.media] == [(MediaKind.source, 768, 1024)]


def test_replay_with_same_payload_returns_the_original_meal(client: TestClient, storage: FakeStorage) -> None:
    # Arrange
    first = upload(client, key=USER_KEY)

    # Act
    replay = upload(client, key=USER_KEY)

    # Assert
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]
    assert len(storage.objects) == 1


def test_replay_in_another_timezone_offset_is_the_same_submission(client: TestClient) -> None:
    # Arrange
    first = upload(client, key=USER_KEY, capturedAt="2026-10-18T12:30:00+08:00")

    # Act: the same instant written in UTC
    replay = upload(client, key=USER_KEY, capturedAt="2026-10-18T04:30:00Z")

    # Assert
    assert replay.status_code == 200
    assert replay.json()["id"] == first.json()["id"]


@pytest.mark.parametrize(
    "changed",
    [
        {"capturedAt": "2026-10-18T12:31:00+08:00"},
        {"mealType": "dinner"},
        {"notes": "noodles"},
        {"photo": make_jpeg(1024, 768)},
    ],
    ids=["capturedAt", "mealType", "notes", "photo"],
)
def test_same_key_with_different_payload_conflicts(client: TestClient, changed: dict[str, Any]) -> None:
    # Arrange
    upload(client, key=USER_KEY)

    # Act
    response = upload(client, key=USER_KEY, **changed)

    # Assert
    assert response.status_code == 409


def test_notes_are_optional(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, notes=None)

    # Assert
    assert (response.status_code, response.json()["notes"]) == (201, None)


def test_rejects_capture_time_without_timezone(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, capturedAt="2026-10-18T12:30:00")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["loc"] == ["body", "capturedAt"]


def test_rejects_unknown_form_fields(client: TestClient) -> None:
    # Arrange / Act: a leftover field from the old JSON Shortcut
    response = upload(client, mimeType="image/jpeg")

    # Assert
    assert response.status_code == 422
    assert response.json()["detail"][0]["type"] == "extra_forbidden"


def test_rejects_missing_photo(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, send_photo=False)

    # Assert
    assert response.status_code == 422


def test_rejects_meal_type_outside_the_enum(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, mealType="午餐")

    # Assert
    assert response.status_code == 422


def test_rejects_missing_or_wrong_token(client: TestClient) -> None:
    # Arrange / Act
    responses = [upload(client, token=None), upload(client, token="x" * 64)]

    # Assert
    assert [r.status_code for r in responses] == [401, 401]


def test_rejects_malformed_idempotency_key(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, key="short")

    # Assert
    assert response.status_code == 422


def test_rejects_photo_over_the_byte_limit(client: TestClient) -> None:
    # Arrange: trailing bytes after the JPEG end marker still decode
    photo = make_jpeg() + b"\0" * MAX_BYTES

    # Act
    response = upload(client, photo=photo)

    # Assert
    assert response.status_code == 413


def test_rejects_invalid_photo_with_its_status(client: TestClient) -> None:
    # Arrange / Act
    response = upload(client, photo=make_jpeg(2048, 1536))

    # Assert
    assert response.status_code == 422


def test_response_lists_public_variants_once_they_exist(client: TestClient, migrated_engine: Engine) -> None:
    # Arrange: simulate the future worker producing derivatives
    key = new_key()
    meal_id = uuid.UUID(upload(client, key=key).json()["id"])
    with Session(migrated_engine) as session:
        for kind in (MediaKind.display, MediaKind.thumb):
            session.add(
                MediaObject(
                    meal_id=meal_id,
                    kind=kind,
                    processor_version=1,
                    object_key=f"test/{kind}/{uuid.uuid4()}",
                    sha256="0" * 64,
                    content_type="image/jpeg",
                    byte_size=1,
                    width=768,
                    height=1024,
                )
            )
        session.commit()

    # Act
    replay = upload(client, key=key)

    # Assert
    assert set(replay.json()["media"]) == {"display", "thumb"}
