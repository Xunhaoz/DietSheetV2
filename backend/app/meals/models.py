import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Enum, Index, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.media.models import MediaObject


class MealType(enum.StrEnum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    late_snack = "late_snack"
    drink = "drink"


class Meal(Base):
    __tablename__ = "meal"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key"),
        Index("ix_meal_user_captured", "user_id", "captured_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # No app_user table yet; add the FK when accounts are implemented.
    user_id: Mapped[UUID]
    # Client-chosen Idempotency-Key; legacy Sheet requestId values are imported here.
    idempotency_key: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType, name="meal_type"))
    notes: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    # onupdate covers ORM/Core updates only; raw SQL updates must set updated_at themselves.
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # One-directional: media does not reference Meal back, keeping that package independent.
    media: Mapped[list[MediaObject]] = relationship(lazy="selectin")
