"""Meal use cases. Free of HTTP so background workers can call them too."""

import hashlib
import json
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID, uuid4

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.errors import DomainError
from app.meals import repository
from app.meals.models import Meal, MealType
from app.media.images import MAX_BYTES, inspect_image
from app.media.models import MediaKind, MediaObject
from app.media.storage import ObjectStorage

SOURCE_PROCESSOR_VERSION = 1


class PhotoTooLarge(DomainError):
    status_code = 413

    def __init__(self) -> None:
        super().__init__(f"Image exceeds {MAX_BYTES // (1024 * 1024)} MiB")


class IdempotencyConflict(DomainError):
    status_code = 409

    def __init__(self) -> None:
        super().__init__("Idempotency-Key was already used with a different submission")


@dataclass(frozen=True)
class MealSubmission:
    captured_at: datetime
    meal_type: MealType
    notes: str | None
    photo: bytes


@dataclass(frozen=True)
class CreateResult:
    meal: Meal
    # True when an earlier identical submission with the same key is returned instead of a new meal.
    replayed: bool


def create_meal(
    session: Session,
    storage: ObjectStorage,
    *,
    owner_id: UUID,
    idempotency_key: str,
    submission: MealSubmission,
) -> CreateResult:
    """Store the source photo, then record the meal; idempotent per (owner, key).

    Raises PhotoTooLarge, InvalidImage, IdempotencyConflict or StorageUnavailable.
    """
    notes = submission.notes or None
    photo = submission.photo
    if len(photo) > MAX_BYTES:
        raise PhotoTooLarge
    info = inspect_image(photo)

    photo_sha256 = hashlib.sha256(photo).hexdigest()
    payload_hash = _request_hash(submission.captured_at, submission.meal_type, notes, photo_sha256)

    existing = repository.find_by_idempotency_key(session, owner_id, idempotency_key)
    if existing is not None:
        return _replay(existing, payload_hash)

    meal_id = uuid4()
    object_key = (
        f"users/{owner_id}/meals/{meal_id}/{SOURCE_PROCESSOR_VERSION}/source/{uuid4()}.{info.extension}"
    )
    # Persist the object first; an interrupted request leaves only an unreferenced object.
    storage.put(object_key, photo, info.content_type)

    meal = Meal(
        id=meal_id,
        user_id=owner_id,
        idempotency_key=idempotency_key,
        request_hash=payload_hash,
        captured_at=submission.captured_at,
        meal_type=submission.meal_type,
        notes=notes,
        media=[
            MediaObject(
                kind=MediaKind.source,
                processor_version=SOURCE_PROCESSOR_VERSION,
                object_key=object_key,
                sha256=photo_sha256,
                content_type=info.content_type,
                byte_size=len(photo),
                width=info.width,
                height=info.height,
            )
        ],
    )
    repository.add(session, meal)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first.
        session.rollback()
        existing = repository.find_by_idempotency_key(session, owner_id, idempotency_key)
        if existing is None:
            raise
        return _replay(existing, payload_hash)
    session.refresh(meal)
    return CreateResult(meal, replayed=False)


def _request_hash(captured_at: datetime, meal_type: MealType, notes: str | None, photo_sha256: str) -> str:
    """Fingerprint of a submission; the instant is normalised to UTC and receipt time is excluded."""
    normalized = {
        "capturedAt": captured_at.astimezone(UTC).isoformat(),
        "mealType": meal_type.value,
        "notes": notes,
        "photoSha256": photo_sha256,
    }
    return hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()


def _replay(existing: Meal, payload_hash: str) -> CreateResult:
    if existing.request_hash != payload_hash:
        raise IdempotencyConflict
    return CreateResult(existing, replayed=True)
