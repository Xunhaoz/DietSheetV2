# Testing

## Kinds of tests

| Kind | Location | Uses | Runs with |
| --- | --- | --- | --- |
| Unit | `backend/tests/unit/` | Pure code, fakes, in-process ASGI apps; no database or network | `uv run pytest` |
| Integration | `backend/tests/integration/` | Real PostgreSQL, the full FastAPI app, an in-memory storage fake | `./scripts/ci.sh` |

Prefer a unit test when the behaviour does not depend on Postgres. Cover a database constraint, migration or HTTP flow with an integration test.

## Writing a test

- Follow [Delivery](../delivery.md): explicit `# Arrange`, `# Act`, `# Assert` sections, one behaviour per test, fresh fixtures.
- Name tests after the behaviour, e.g. `test_same_key_with_different_payload_conflicts`.
- Build inputs with `tests/support.py` (`make_jpeg`, `upload`, `FakeStorage`). Photos are deterministic, so repeating an upload is a true replay.
- Replace external systems at their boundary with `app.dependency_overrides` (for example `get_storage`), never by patching internals.
- A bug fix comes with a test that fails without the fix.

## What CI checks

`./scripts/ci.sh` runs, in order, and stops at the first failure:

1. `uv sync --frozen`: the lockfile matches `pyproject.toml`
2. `ruff check` and `ruff format --check`
3. `mypy` in strict mode, over `app`, `alembic` and `tests`
4. `lint-imports`: the layering rules in [Conventions](conventions.md#layout-one-package-per-feature)
5. `pytest` against a throwaway Postgres on a random port
6. Image smoke test: build the Docker image, then import the app and load the migrations inside it. Tests run the editable source checkout, so only this step catches packaging mistakes such as a package left out of the image

Run it before pushing. The pre-commit hooks cover steps 2–4 only.
