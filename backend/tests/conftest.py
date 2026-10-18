"""Settings are read when app modules are imported, so they must exist before any test imports them."""

import os

# Unit tests never connect to these. scripts/ci.sh supplies a real DATABASE_URL for integration tests.
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://unused:unused@127.0.0.1:1/unused")
os.environ.setdefault("S3_ENDPOINT_URL", "http://127.0.0.1:1")
os.environ.setdefault("S3_ACCESS_KEY", "test")
os.environ.setdefault("S3_SECRET_KEY", "test")
os.environ.setdefault("OWNER_ID", "00000000-0000-0000-0000-000000000001")
os.environ.setdefault("API_TOKEN", "test-token-" + "0" * 32)
