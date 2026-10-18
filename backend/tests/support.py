"""Test doubles and builders shared by unit and integration tests."""

import io
import os
import random
import uuid
from typing import Any

import httpx2
from fastapi.testclient import TestClient
from PIL import Image

API_TOKEN = os.environ["API_TOKEN"]


def make_jpeg(width: int = 768, height: int = 1024, orientation: int | None = None) -> bytes:
    """A deterministic noise JPEG, optionally tagged with an EXIF orientation.

    Same arguments give the same bytes, so a repeated upload is a true replay.
    """
    buffer = io.BytesIO()
    options: dict[str, Any] = {}
    if orientation is not None:
        exif = Image.Exif()
        exif[0x0112] = orientation
        options["exif"] = exif.tobytes()
    noise = random.Random(f"{width}x{height}").randbytes(width * height)
    Image.frombytes("L", (width, height), noise).convert("RGB").save(buffer, "JPEG", **options)
    return buffer.getvalue()


def encode(image: Image.Image, fmt: str, **options: Any) -> bytes:
    buffer = io.BytesIO()
    image.save(buffer, fmt, **options)
    return buffer.getvalue()


class FakeStorage:
    """In-memory stand-in for ObjectStorage."""

    def __init__(self) -> None:
        self.objects: dict[str, bytes] = {}
        self.closed = False

    def ensure_bucket(self) -> None:
        pass

    def put(self, key: str, data: bytes, content_type: str) -> None:
        self.objects[key] = data

    def close(self) -> None:
        self.closed = True


def new_key() -> str:
    return f"meal-{uuid.uuid4().hex}"


def upload(
    client: TestClient,
    *,
    key: str | None = None,
    token: str | None = API_TOKEN,
    photo: bytes | None = None,
    send_photo: bool = True,
    **form: str | None,
) -> httpx2.Response:
    """POST /api/v1/meals the way the iPhone Shortcut does; form values of None are omitted."""
    headers = {"Idempotency-Key": key or new_key()}
    if token is not None:
        headers["Authorization"] = f"Bearer {token}"
    fields: dict[str, str | None] = {
        "capturedAt": "2026-10-18T12:30:00+08:00",
        "mealType": "lunch",
        "notes": "rice",
        **form,
    }
    files = {}
    if send_photo:
        files["photo"] = ("meal.jpg", photo if photo is not None else make_jpeg(), "image/jpeg")
    return client.post(
        "/api/v1/meals",
        headers=headers,
        data={name: value for name, value in fields.items() if value is not None},
        files=files,
    )
