"""Application assembly: lifespan, middleware, routers and error handlers. No business logic."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.core.body_limit import BodySizeLimitMiddleware
from app.core.db import engine
from app.core.error_handlers import register_error_handlers
from app.meals.router import MAX_REQUEST_BYTES
from app.meals.router import router as meals_router
from app.media.storage import get_storage


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    # Resolve through overrides so tests can start the app without a real S3 server.
    storage = app.dependency_overrides.get(get_storage, get_storage)()
    storage.ensure_bucket()
    try:
        yield
    finally:
        storage.close()
        engine.dispose()


app = FastAPI(title="DietSheet", lifespan=lifespan)
app.add_middleware(BodySizeLimitMiddleware, max_bytes=MAX_REQUEST_BYTES)
app.include_router(meals_router)
register_error_handlers(app)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
