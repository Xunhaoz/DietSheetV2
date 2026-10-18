# Getting started

## Prerequisites

- [uv](https://docs.astral.sh/uv/) 0.13 or newer (it installs Python 3.12 for the project if needed)
- Docker with Compose v2, running

## Set up

```bash
cd backend
uv sync                      # creates backend/.venv from uv.lock, including dev tools
uv run pre-commit install    # optional: run ruff, mypy and lint-imports on every commit
```

Only `uv.lock` decides installed versions. After changing dependencies in `pyproject.toml`, run `uv lock` and commit both files.

## Run every check

```bash
./scripts/ci.sh              # from the repository root; extra arguments go to pytest
```

It runs ruff, mypy (strict), the architecture rules and all tests against a throwaway Postgres, then removes it. `uv run pytest` alone runs unit tests and skips integration tests. See [Testing](testing.md).

## Run the stack

```bash
cp .env.example .env         # then fill in every value; .env is gitignored
docker compose up --build --wait
```

This starts PostgreSQL, SeaweedFS, a one-shot migration and the API on `http://localhost:8000`. Upload a meal the way the iPhone Shortcut does, with `API_TOKEN` exported from your `.env`:

```bash
curl -H "Authorization: Bearer $API_TOKEN" -H "Idempotency-Key: meal-$(date +%Y%m%d%H%M%S)-$RANDOM" \
  -F photo=@meal.jpg -F capturedAt=2026-10-18T12:30:00+08:00 -F mealType=lunch -F notes=rice \
  http://localhost:8000/api/v1/meals
```

The photo must be a JPEG with a long edge of at most 1024 px. Interactive API docs are at `http://localhost:8000/docs`.

## Common tasks

| Task | Command (in `backend/`) |
| --- | --- |
| Add a dependency | `uv add <package>` (dev tool: `uv add --dev <package>`) |
| Format and fix lint | `uv run ruff format . && uv run ruff check --fix .` |
| Create a migration | `uv run alembic revision --autogenerate -m "<change>"`, then review it (see [Conventions](conventions.md#migrations)) |
| Apply migrations to the stack | `docker compose run --rm migrate` (repository root) |
