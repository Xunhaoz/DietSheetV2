from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Receive, Scope, Send


class BodySizeLimitMiddleware:
    """Reject oversized or unsized request bodies before FastAPI reads them.

    FastAPI reads the whole body before running dependencies such as authentication,
    so without this any client could stream an arbitrarily large upload. Uvicorn frames
    the body by Content-Length and never delivers more, so checking the header suffices.
    """

    def __init__(self, app: ASGIApp, max_bytes: int):
        self.app = app
        self.max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] == "http":
            headers = dict(scope["headers"])
            length = headers.get(b"content-length")
            if length is None and b"transfer-encoding" in headers:
                # Chunked bodies have no declared size to check up front.
                return await _reject(411, "Content-Length is required", scope, receive, send)
            if length is not None and (not length.isdigit() or int(length) > self.max_bytes):
                return await _reject(413, "Request body is too large", scope, receive, send)
        await self.app(scope, receive, send)


async def _reject(status: int, message: str, scope: Scope, receive: Receive, send: Send) -> None:
    # Closing the connection stops Uvicorn from reading and discarding the unread body.
    response = JSONResponse({"detail": message}, status, headers={"Connection": "close"})
    await response(scope, receive, send)
