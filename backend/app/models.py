"""Every feature's models in one place, so Base.metadata is complete for Alembic and tests.

Add each new feature's models module here.
"""

from app.core.db import Base
from app.meals.models import Meal
from app.media.models import MediaObject

__all__ = ["Base", "Meal", "MediaObject"]
