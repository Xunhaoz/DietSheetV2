# tests

Automated tests for the backend. How to run and write them: [Testing](../../doc/developer/backend/testing.md).

| Path | Purpose |
| --- | --- |
| [`unit/`](unit/README.md) | Tests without a database or network |
| [`integration/`](integration/README.md) | Tests against real PostgreSQL through the full app |
| `conftest.py` | Sets placeholder settings before any app module is imported |
| `support.py` | Shared builders and fakes: `make_jpeg`, `upload`, `FakeStorage` |
| `compose.yaml` | The throwaway Postgres that `scripts/ci.sh` starts for integration tests |

## Trade-offs

- **Settings come from the environment at import time**, so `conftest.py` must fill placeholders before anything imports `app`. The placeholder database URL points at a closed port, so an accidental connection fails fast rather than touching a real database.
- **Deterministic photos.** `make_jpeg` derives its noise from the dimensions, so the same call gives the same bytes and a repeated upload is a genuine replay, not a conflict.
- **Throwaway Postgres in memory** (`tmpfs`, random host port). Runs are isolated and leave no data behind, but nothing persists between runs.
