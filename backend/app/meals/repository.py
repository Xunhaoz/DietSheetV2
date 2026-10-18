"""Database access for meals. Queries only: no business rules and no commits."""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.meals.models import Meal


def find_by_idempotency_key(session: Session, owner_id: UUID, idempotency_key: str) -> Meal | None:
    return session.scalar(
        select(Meal).where(Meal.user_id == owner_id, Meal.idempotency_key == idempotency_key)
    )


def add(session: Session, meal: Meal) -> None:
    session.add(meal)
