# alembic

Alembic environment for schema migrations.

| Path | Purpose |
| --- | --- |
| [`versions/`](versions/README.md) | The migration revisions, applied in order |
| `env.py` | Connects with `DATABASE_URL` from app settings and compares against `app.models.Base.metadata` |
| `script.py.mako` | Template for new revision files |

## Behaviour

`env.py` reads the URL from the same settings as the app, so migrations and the API never disagree about the database. Comparing against `Base.metadata` lets `alembic revision --autogenerate` and `alembic check` see every table registered in `app/models.py`. Offline mode (`alembic upgrade head --sql`) prints the SQL for review without connecting.

## Trade-offs

- **The Base naming convention applies inside migrations too.** Write explicit names as `op.f("...")` so Alembic does not prefix them a second time.
- **Migrations run as their own Compose job** before the API starts, rather than inside API startup. Several API processes can never race to migrate, and a failed migration leaves the previous release running.
