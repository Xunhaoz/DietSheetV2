# integration

Tests that exercise the real app against real PostgreSQL. Object storage is replaced by an in-memory fake. They need `DATABASE_URL`, which `scripts/ci.sh` provides; without it they are skipped with a hint.

| File | Covers |
| --- | --- |
| `conftest.py` | Fixtures: migrate once per session, empty the tables before each test, app client with fake storage |
| `test_upload_meal.py` | `POST /api/v1/meals`: creation, replay (also with the same instant in another timezone offset), conflict when any field changes, validation and auth failures, size limits, response media |
| `test_outages.py` | Storage or database outages return 503, and a retry with the same key then succeeds |
| `test_migrations.py` | Downgrade/upgrade round trip; models match the migrated schema; constraint names follow the convention |
| `test_lifespan.py` | Shutdown closes the storage client and every database connection |

## Trade-offs

- **The schema comes from the migrations, not `create_all()`.** Tests run against exactly what deployments get, and a model change without a migration fails `test_migrations.py`.
- **Tables are truncated before each test** instead of wrapping each test in a rolled-back transaction. The app commits for real, as in production, at the cost of a little speed.
- **Storage is faked here** to keep the tests independent of SeaweedFS. Outages are simulated by swapping the fake, and the adapter itself is tested in `unit/`.
