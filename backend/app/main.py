from contextlib import asynccontextmanager

from fastapi import FastAPI

from app import meals
from app.body_limit import BodySizeLimitMiddleware
from app.storage import get_storage


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Resolve through overrides so tests can start the app without a real S3 server.
    storage = app.dependency_overrides.get(get_storage, get_storage)()
    storage.ensure_bucket()
    try:
        yield
    finally:
        storage.close()


app = FastAPI(title="DietSheet", lifespan=lifespan)
app.add_middleware(BodySizeLimitMiddleware)
app.include_router(meals.router)


@app.get("/health/live")
def live() -> dict[str, str]:
    return {"status": "ok"}
