# Getting started

## Install the tools

You need git, [uv](https://docs.astral.sh/uv/) 0.13+ (it also installs Python 3.12) and Docker with Compose v2.

| OS | Commands |
| --- | --- |
| macOS | `brew install git uv` and `brew install --cask docker`, then open Docker Desktop once |
| Linux | Install git from your package manager, uv with `curl -LsSf https://astral.sh/uv/install.sh \| sh`, and [Docker Engine](https://docs.docker.com/engine/install/); add yourself to the `docker` group |
| Windows | Use WSL 2 and follow the Linux steps; `scripts/ci.sh` is a bash script |

Check that everything is ready (Docker must be running):

```bash
git --version && uv --version && docker compose version && docker info >/dev/null && echo ready
```

## Set up the project

```bash
git clone <repository-url> DietSheet && cd DietSheet/backend
uv sync                      # creates backend/.venv from uv.lock, including dev tools
uv run pre-commit install    # checks ruff, mypy and architecture rules before each commit
cd .. && ./scripts/ci.sh     # a green run means the machine is ready
```

The pre-commit hook runs on commits that touch `backend/**.py`; skip it once with `git commit --no-verify` only when you will run `ci.sh` before pushing.

Only `uv.lock` decides installed versions. After changing dependencies in `pyproject.toml`, run `uv lock` and commit both files.

## Run every check

```bash
./scripts/ci.sh              # from the repository root; extra arguments go to pytest
```

It runs ruff, mypy (strict), the architecture rules and all tests against a throwaway Postgres, then smoke-tests the built Docker image, and removes everything it created. `uv run pytest` alone runs unit tests and skips integration tests. See [Testing](testing.md).

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

The photo must be a JPEG with a long edge of at most 1024 px. Interactive API docs are at `http://localhost:8000/docs`. To run the stack on a host and reach it from a phone, see [Deployment](deployment.md).

## Common tasks

| Task | Command (in `backend/`) |
| --- | --- |
| Add a dependency | `uv add <package>` (dev tool: `uv add --dev <package>`) |
| Format and fix lint | `uv run ruff format . && uv run ruff check --fix .` |
| Create a migration | `uv run alembic revision --autogenerate -m "<change>"`, then review it (see [Conventions](conventions.md#migrations)) |
| Apply migrations to the stack | `docker compose run --rm migrate` (repository root) |
