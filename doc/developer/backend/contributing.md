# Contributing

## Understand the project

Read in this order; together it takes about half an hour.

1. [Repository README](../../../README.md): what the project is and where things live.
2. [Design: Architecture](../design.md#architecture): the components and how an upload is processed.
3. [Implementation status](README.md#implementation-status): what is built and where it deliberately differs from the design.
4. [`backend/app/README.md`](../../../backend/app/README.md), then each feature folder's README: business logic and trade-offs.
5. [Conventions](conventions.md): the rules every change follows.

## Make a change

1. Branch from `main`: `git switch -c <type>/<topic>`, for example `fix/upload-timeout`.
2. Put the code in the right place (table below). For a bug, first write a test that fails.
3. Update the README of each folder you changed, and the design documents if a decision changed.
4. Run `./scripts/ci.sh` until it passes.
5. Commit in small, logical steps with messages like `feat: ...` or `fix: ...` that explain why ([Conventions](conventions.md#commits)).

## Where a change goes

| I want to… | Change |
| --- | --- |
| Add or change an endpoint of a feature | That feature's `router.py`, `schemas.py` and `service.py`; queries in `repository.py` |
| Add a feature | A new package under `backend/app/` with a README; register its models in `app/models.py`; add it to the import-linter contracts in `pyproject.toml` (not automatic) |
| Change the database schema | The feature's `models.py`, then a new migration ([Conventions](conventions.md#migrations)) |
| Add a setting | `app/core/config.py`, `.env.example` and `compose.yaml` |
| Add a dependency | `uv add <package>`, then commit `pyproject.toml` and `uv.lock` |
