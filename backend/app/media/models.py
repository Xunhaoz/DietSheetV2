import enum
from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import (
    BigInteger,
    CheckConstraint,
    DateTime,
    Enum,
    ForeignKey,
    String,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class MediaKind(enum.StrEnum):
    source = "source"
    display = "display"
    ai = "ai"
    thumb = "thumb"


class MediaObject(Base):
    __tablename__ = "media_object"
    __table_args__ = (
        UniqueConstraint("meal_id", "kind", "processor_version"),
        CheckConstraint("byte_size > 0 AND width > 0 AND height > 0", name="positive_size"),
    )

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    # Referenced by table name only, so the media package does not depend on meals.
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
