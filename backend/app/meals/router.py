"""HTTP layer for meals: parse the request, call the service, shape the response."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Form, Header, Response, status
from sqlalchemy.orm import Session

from app.accounts.auth import current_owner
from app.core.db import get_session
from app.meals import service
from app.meals.models import Meal
from app.meals.schemas import MealIn, MealOut
from app.media.images import MAX_BYTES
from app.media.storage import ObjectStorage, get_storage

router = APIRouter(prefix="/api/v1")

# Request body budget: the photo plus the other form fields (notes is at most 2000 characters)
# and multipart framing. Enforced by BodySizeLimitMiddleware before the body is read.
MAX_REQUEST_BYTES = MAX_BYTES + 64 * 1024


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
    submission = service.MealSubmission(
        captured_at=meal_in.captured_at,
        meal_type=meal_in.meal_type,
        notes=meal_in.notes,
        # Read one byte past the limit so the service can tell an oversized photo apart.
        photo=meal_in.photo.file.read(MAX_BYTES + 1),
    )
    result = service.create_meal(
        session, storage, owner_id=owner_id, idempotency_key=idempotency_key, submission=submission
    )
    if result.replayed:
        response.status_code = status.HTTP_200_OK
    return result.meal
