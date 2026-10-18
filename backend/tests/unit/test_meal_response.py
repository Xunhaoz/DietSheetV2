import uuid
from datetime import UTC, datetime
from types import SimpleNamespace

from app.meals.models import MealType
from app.meals.router import MealOut
from app.media.models import MediaKind


def _meal_with(*kinds: MediaKind) -> SimpleNamespace:
    now = datetime(2026, 10, 18, tzinfo=UTC)
    media = [SimpleNamespace(id=uuid.uuid4(), kind=kind, width=768, height=1024) for kind in kinds]
    return SimpleNamespace(
        id=uuid.uuid4(),
        captured_at=now,
        meal_type=MealType.lunch,
        notes=None,
        version=1,
        media=media,
        created_at=now,
        updated_at=now,
    )


def test_media_exposes_only_public_variants_keyed_by_kind() -> None:
    # Arrange
    meal = _meal_with(MediaKind.source, MediaKind.display, MediaKind.ai, MediaKind.thumb)

    # Act
    body = MealOut.model_validate(meal).model_dump(by_alias=True, mode="json")

    # Assert
    assert set(body["media"]) == {"display", "thumb"}
    assert set(body["media"]["thumb"]) == {"id", "width", "height"}


def test_media_is_empty_before_variants_exist() -> None:
    # Arrange
    meal = _meal_with(MediaKind.source)

    # Act
    body = MealOut.model_validate(meal).model_dump(by_alias=True, mode="json")

    # Assert
    assert body["media"] == {}
