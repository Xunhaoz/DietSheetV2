# Conventions

## Layout: one package per feature

`backend/app/` holds one package per feature from [Design](../design.md) (`accounts`, `meals`, `media`, later `nutrition`, `measurements`, `jobs`) plus `core` for infrastructure no feature owns. A new feature gets a new package; it does not add files to another feature.

A feature package uses these modules, as needed:

| Module | Role | Must not |
| --- | --- | --- |
| `router.py` | HTTP: parse the request, call the service, set status codes | Contain business rules or queries |
| `schemas.py` | Request and response shapes (Pydantic, camelCase via `CamelModel`) | — |
| `service.py` | Use cases and the transaction boundary (`commit`) | Import FastAPI/Starlette or raise `HTTPException` |
| `repository.py` | Queries and inserts | Commit, or make business decisions |
| `models.py` | SQLAlchemy tables and enums | Import other layers |

Dependencies point one way: `router → schemas → service → repository → models`. Between packages, `meals` may use `media` and `accounts`; those two do not use `meals` or each other, and `core` uses no feature. These rules are contracts in `backend/pyproject.toml` and fail CI when broken (`uv run lint-imports`). Register each new feature's models in `app/models.py`.

## Errors

Services raise subclasses of `app.core.errors.DomainError` with a `status_code`. `app/core/error_handlers.py` turns them into responses, so services stay usable from background workers. Only the HTTP layer (routers, auth dependencies) raises `HTTPException`.

## Code style

- Formatting and lint: ruff (line length 110). Types: mypy `strict`; annotate everything.
- Settings come from environment variables via `app/core/config.py`; secrets use `SecretStr` and never appear in logs or errors.
- Logs carry method, path and IDs only: no tokens, photos, notes or body data ([Delivery](../delivery.md)).
- Comments explain why, not what.

## Migrations

- Alembic owns the schema. Change models, run `uv run alembic revision --autogenerate -m "..."`, then review the file: name constraints with `op.f(...)`, write `downgrade()`, and drop Postgres enum types explicitly.
- Never edit a migration that has run against data you keep; add a new one. Use expand/backfill/contract across releases ([Delivery](../delivery.md)).
- The integration tests verify that models and migrations match and that downgrade/upgrade round-trips.

## Documentation

- Every folder containing code has a `README.md` describing its responsibility, business logic and trade-offs.
- A README describes only its own folder. It may name and link child folders with a one-line purpose, but never explain their contents; the child's README does that.
- When a decision changes the design, update the design document in the same change. When the implementation deliberately differs, record it in [Implementation status](README.md#implementation-status).

## Commits

One logical change per commit, with a message stating what changed and why (`feat:`, `fix:`, `refactor:`, `test:`, `build:`, `docs:`). `./scripts/ci.sh` passes on every commit.
