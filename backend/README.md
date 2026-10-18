# backend

The DietSheet API: a FastAPI service that stores meal photos in S3-compatible storage (SeaweedFS) and meal records in PostgreSQL. Setup and workflow: [backend developer guide](../doc/developer/backend/README.md).

| Path | Purpose |
| --- | --- |
| [`app/`](app/README.md) | Application code |
| [`alembic/`](alembic/README.md) | Database schema migrations |
| [`tests/`](tests/README.md) | Unit and integration tests |
| `pyproject.toml` | Dependencies and tool settings: ruff, mypy, pytest, import-linter contracts |
| `uv.lock` | Exact versions of every dependency |
| `Dockerfile` | Image for the API and the migration job |
| `alembic.ini` | Alembic settings; the database URL comes from `DATABASE_URL` |

## Trade-offs

- **uv with a committed lockfile.** Builds and CI install identical versions (`uv sync --frozen`). Changing a dependency means re-locking and committing `uv.lock`.
- **One image, two commands.** The API and the `migrate` job run the same image, so the schema and the code that expects it always ship together.
- **Dependencies are installed before the source is copied** in the Dockerfile, so code-only changes rebuild in seconds.
