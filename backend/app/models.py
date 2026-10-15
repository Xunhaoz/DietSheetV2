import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    MetaData,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Predictable constraint names so later migrations can alter or drop them by name.
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_N_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    metadata = MetaData(naming_convention=NAMING_CONVENTION)


class MealType(str, enum.Enum):
    breakfast = "breakfast"
    lunch = "lunch"
    dinner = "dinner"
    snack = "snack"
    late_snack = "late_snack"
    drink = "drink"


class MediaKind(str, enum.Enum):
    source = "source"
    display = "display"
    ai = "ai"
    thumb = "thumb"


class Meal(Base):
    __tablename__ = "meal"
    __table_args__ = (
        UniqueConstraint("user_id", "request_id"),
        Index("ix_meal_user_captured", "user_id", "captured_at", "id"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # No app_user table yet; add the FK when accounts are implemented.
    user_id: Mapped[UUID]
    request_id: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    captured_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    meal_type: Mapped[MealType] = mapped_column(Enum(MealType, name="meal_type"))
    notes: Mapped[str | None] = mapped_column(Text)
    version: Mapped[int] = mapped_column(default=1)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    media: Mapped[list["MediaObject"]] = relationship(back_populates="meal", lazy="selectin")


class MediaObject(Base):
    __tablename__ = "media_object"
    __table_args__ = (
        UniqueConstraint("meal_id", "kind", "processor_version"),
        CheckConstraint("byte_size > 0 AND width > 0 AND height > 0", name="positive_size"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    meal_id: Mapped[UUID] = mapped_column(ForeignKey("meal.id"))
    kind: Mapped[MediaKind] = mapped_column(Enum(MediaKind, name="media_kind"))
    processor_version: Mapped[int]
    object_key: Mapped[str] = mapped_column(Text, unique=True)
    sha256: Mapped[str] = mapped_column(String(64))
    content_type: Mapped[str] = mapped_column(String(100))
    byte_size: Mapped[int] = mapped_column(BigInteger)
    width: Mapped[int]
    height: Mapped[int]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    meal: Mapped[Meal] = relationship(back_populates="media")
