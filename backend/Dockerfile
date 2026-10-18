FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /bin/uv

WORKDIR /srv
ENV UV_COMPILE_BYTECODE=1 UV_LINK_MODE=copy UV_PYTHON_DOWNLOADS=never

# Install locked dependencies first so code-only changes reuse this layer.
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project
COPY app ./app
RUN uv sync --frozen --no-dev --no-editable
COPY alembic.ini ./
COPY alembic ./alembic
ENV PATH="/srv/.venv/bin:$PATH"

RUN useradd --system --uid 10001 app
USER app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
