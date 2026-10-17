import hashlib
import json
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import APIRouter, Depends, Form, Header, HTTPException, Response, UploadFile, status
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.auth import current_owner
from app.db import get_session
from app.images import MAX_BYTES, InvalidImage, inspect_image
from app.models import Meal, MealType, MediaKind, MediaObject
from app.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/api/v1")

SOURCE_PROCESSOR_VERSION = 1


class CamelModel(BaseModel):
    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, from_attributes=True)


class MealIn(CamelModel):
    """Multipart form fields of an upload; unknown fields are rejected to surface client typos."""

    model_config = ConfigDict(extra="forbid")

    photo: UploadFile
    # AwareDatetime rejects timestamps without a timezone offset.
    captured_at: AwareDatetime
    meal_type: MealType
    notes: str | None = Field(default=None, max_length=2000)


class MediaOut(CamelModel):
    id: UUID
    kind: MediaKind
    width: int
    height: int


class MealOut(CamelModel):
    id: UUID
    captured_at: datetime
    meal_type: MealType
    notes: str | None
    version: int
    media: list[MediaOut]
    created_at: datetime
    updated_at: datetime


@router.post(
    "/meals",
    status_code=status.HTTP_201_CREATED,
    response_model=MealOut,
    response_model_by_alias=True,
    responses={200: {"description": "Replay of an earlier identical submission"}},
)
def create_meal(
    response: Response,
    meal_in: Annotated[MealIn, Form()],
    idempotency_key: Annotated[str, Header(pattern=r"^[A-Za-z0-9_-]{16,80}$")],
    owner_id: UUID = Depends(current_owner),
    session: Session = Depends(get_session),
    storage: ObjectStorage = Depends(get_storage),
) -> Meal:
    captured_at, meal_type = meal_in.captured_at, meal_in.meal_type
    notes = meal_in.notes or None

    data = meal_in.photo.file.read(MAX_BYTES + 1)
    if len(data) > MAX_BYTES:
        raise HTTPException(413, f"Image exceeds {MAX_BYTES // (1024 * 1024)} MiB")
    try:
        info = inspect_image(data)
    except InvalidImage as exc:
        raise HTTPException(exc.status_code, exc.message)

    photo_sha256 = hashlib.sha256(data).hexdigest()
    request_hash = _request_hash(captured_at, meal_type, notes, photo_sha256)

    existing = _find_by_request(session, owner_id, idempotency_key)
    if existing is not None:
        return _replay(existing, request_hash, response)

    meal_id = uuid4()
    object_key = (
        f"users/{owner_id}/meals/{meal_id}/{SOURCE_PROCESSOR_VERSION}/source/{uuid4()}.{info.extension}"
    )
    # Persist the object first; an interrupted request leaves only an unreferenced object.
    storage.put(object_key, data, info.content_type)

    meal = Meal(
        id=meal_id,
        user_id=owner_id,
        idempotency_key=idempotency_key,
        request_hash=request_hash,
        captured_at=captured_at,
        meal_type=meal_type,
        notes=notes,
        media=[
            MediaObject(
                kind=MediaKind.source,
                processor_version=SOURCE_PROCESSOR_VERSION,
                object_key=object_key,
                sha256=photo_sha256,
                content_type=info.content_type,
                byte_size=len(data),
                width=info.width,
                height=info.height,
            )
        ],
    )
    session.add(meal)
    try:
        session.commit()
    except IntegrityError:
        # A concurrent request with the same key committed first.
        session.rollback()
        existing = _find_by_request(session, owner_id, idempotency_key)
        if existing is None:
            raise
        return _replay(existing, request_hash, response)
    session.refresh(meal)
    return meal


def _request_hash(captured_at: datetime, meal_type: MealType, notes: str | None, photo_sha256: str) -> str:
    normalized = {
        "capturedAt": captured_at.astimezone(timezone.utc).isoformat(),
        "mealType": meal_type.value,
        "notes": notes,
        "photoSha256": photo_sha256,
    }
    return hashlib.sha256(json.dumps(normalized, sort_keys=True).encode()).hexdigest()


def _find_by_request(session: Session, owner_id: UUID, idempotency_key: str) -> Meal | None:
    return session.scalar(
        select(Meal).where(Meal.user_id == owner_id, Meal.idempotency_key == idempotency_key)
    )


def _replay(existing: Meal, request_hash: str, response: Response) -> Meal:
    if existing.request_hash != request_hash:
        raise HTTPException(409, "Idempotency-Key was already used with a different submission")
    response.status_code = status.HTTP_200_OK
    return existing
