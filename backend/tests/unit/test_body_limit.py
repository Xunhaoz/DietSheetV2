from collections.abc import Iterator

from fastapi.testclient import TestClient
from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import PlainTextResponse
from starlette.routing import Route

from app.core.body_limit import BodySizeLimitMiddleware


async def _echo_length(request: Request) -> PlainTextResponse:
    return PlainTextResponse(str(len(await request.body())))


def _client(max_bytes: int) -> TestClient:
    inner = Starlette(routes=[Route("/", _echo_length, methods=["GET", "POST"])])
    return TestClient(BodySizeLimitMiddleware(inner, max_bytes=max_bytes))


def test_passes_bodies_within_the_limit() -> None:
    # Arrange
    client = _client(max_bytes=10)

    # Act
    response = client.post("/", content=b"x" * 10)

    # Assert
    assert (response.status_code, response.text) == (200, "10")


def test_rejects_declared_oversized_body_and_closes_connection() -> None:
    # Arrange
    client = _client(max_bytes=10)

    # Act
    response = client.post("/", content=b"x" * 11)

    # Assert
    assert response.status_code == 413
    assert response.headers["connection"] == "close"


def test_rejects_chunked_body_without_content_length() -> None:
    # Arrange
    client = _client(max_bytes=10)

    def chunks() -> Iterator[bytes]:
        yield b"x"

    # Act
    response = client.post("/", content=chunks())

    # Assert
    assert response.status_code == 411


def test_passes_requests_without_a_body() -> None:
    # Arrange
    client = _client(max_bytes=10)

    # Act
    response = client.get("/")

    # Assert
    assert response.status_code == 200
