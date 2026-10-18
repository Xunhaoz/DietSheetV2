import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app import meals
from app.body_limit import BodySizeLimitMiddleware
from app.db import engine
from app.storage import StorageUnavailable, get_storage

logger = logging.getLogger(__name__)


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
app.add_middleware(BodySizeLimitMiddleware)
app.include_router(meals.router)


@app.exception_handler(StorageUnavailable)
@app.exception_handler(OperationalError)
async def persistence_unavailable(request: Request, exc: Exception) -> JSONResponse:
    # api.md: 503 for unavailable persistence, so clients know a retry with the same key is safe.
    logger.warning("Persistence unavailable for %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse({"detail": "Storage is temporarily unavailable"}, 503)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
