import secrets
from uuid import UUID

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from app.config import settings

_bearer = HTTPBearer(auto_error=False)


def current_owner(credentials: HTTPAuthorizationCredentials | None = Depends(_bearer)) -> UUID:
    """Minimal auth: one static token maps to the single configured owner."""
    if credentials is None or not secrets.compare_digest(
        credentials.credentials.encode(), settings.api_token.get_secret_value().encode()
    ):
        raise HTTPException(
            status.HTTP_401_UNAUTHORIZED,
            "Missing or invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return settings.owner_id
