import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from sqlalchemy.exc import OperationalError

from app.core.errors import DomainError

logger = logging.getLogger(__name__)

UNAVAILABLE = "Storage is temporarily unavailable"


async def _domain_error(request: Request, exc: Exception) -> JSONResponse:
    assert isinstance(exc, DomainError)
    if exc.status_code >= 500:
        logger.warning("%s %s failed: %s", request.method, request.url.path, exc.message, exc_info=exc)
    return JSONResponse({"detail": exc.message}, exc.status_code)


async def _database_unavailable(request: Request, exc: Exception) -> JSONResponse:
    # api.md: 503 for unavailable persistence, so clients know a retry with the same key is safe.
    logger.warning("Database unavailable for %s %s", request.method, request.url.path, exc_info=exc)
    return JSONResponse({"detail": UNAVAILABLE}, 503)


def register_error_handlers(app: FastAPI) -> None:
    app.add_exception_handler(DomainError, _domain_error)
    app.add_exception_handler(OperationalError, _database_unavailable)
