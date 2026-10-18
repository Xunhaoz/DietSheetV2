FROM python:3.12-slim AS build
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

# Install locked dependencies first so code-only changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
RUN uv sync --frozen --no-dev --no-editable


# Same base as the build stage, so the copied virtualenv's interpreter paths stay valid.
FROM python:3.12-slim

WORKDIR /srv
# Only the installed environment, not the app/ source folder: the API and migrations both
# import the packaged code, so a packaging mistake fails here instead of being masked.
COPY --from=build /srv/.venv /srv/.venv
COPY alembic.ini ./
COPY alembic ./alembic
ENV PATH="/srv/.venv/bin:$PATH"

RUN useradd --system --uid 10001 app
USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
