from datetime import datetime
from uuid import UUID

from fastapi import UploadFile
from pydantic import AwareDatetime, ConfigDict, Field, field_validator

from app.core.schemas import CamelModel
from app.meals.models import MealType
from app.media.models import MediaKind

# source is only for regenerating derivatives and ai is provider input; neither is served to clients.
PUBLIC_MEDIA_KINDS = (MediaKind.display, MediaKind.thumb)


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
    width: int
    height: int


class MealOut(CamelModel):
    id: UUID
    captured_at: datetime
    meal_type: MealType
    notes: str | None
    version: int
    # One photo per meal; keys are its available public size variants.
    media: dict[MediaKind, MediaOut]
    created_at: datetime
    updated_at: datetime

    @field_validator("media", mode="before")
    @classmethod
    def _public_variants(cls, value: object) -> object:
        if isinstance(value, dict):
            return value
        assert isinstance(value, list)  # Meal.media from the ORM
        return {obj.kind: obj for obj in value if obj.kind in PUBLIC_MEDIA_KINDS}
