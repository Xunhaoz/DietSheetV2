from datetime import UTC, datetime, timedelta, timezone

from app.meals.models import MealType
from app.meals.service import request_hash

TAIPEI = timezone(timedelta(hours=8))


def test_same_instant_in_different_offsets_hashes_equally() -> None:
    # Arrange
    local = datetime(2026, 10, 18, 12, 30, tzinfo=TAIPEI)
    utc = datetime(2026, 10, 18, 4, 30, tzinfo=UTC)

    # Act
    hashes = {request_hash(moment, MealType.lunch, "rice", "a" * 64) for moment in (local, utc)}

    # Assert
    assert len(hashes) == 1


def test_any_changed_field_changes_the_hash() -> None:
    # Arrange
    moment = datetime(2026, 10, 18, 12, 30, tzinfo=TAIPEI)
    base = (moment, MealType.lunch, "rice", "a" * 64)
    variants = [
        (moment + timedelta(minutes=1), MealType.lunch, "rice", "a" * 64),
        (moment, MealType.dinner, "rice", "a" * 64),
        (moment, MealType.lunch, "noodles", "a" * 64),
        (moment, MealType.lunch, "rice", "b" * 64),
    ]

    # Act
    changed = [request_hash(*variant) != request_hash(*base) for variant in variants]

    # Assert
    assert all(changed)
