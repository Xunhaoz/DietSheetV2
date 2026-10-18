# app

The application package: a modular monolith with one package per feature.

| Path | Purpose |
| --- | --- |
| [`core/`](core/README.md) | Infrastructure no feature owns: settings, database, errors, request limits |
| [`accounts/`](accounts/README.md) | Who is calling |
| [`meals/`](meals/README.md) | Recording meals |
| [`media/`](media/README.md) | Photo rules, storage and image records |
| `main.py` | Assembles the app: lifespan, middleware, routers, error handlers |
| `models.py` | Imports every feature's models so `Base.metadata` is complete for Alembic and tests |

## How the app is assembled

`main.py` holds no business logic. On startup the lifespan hook makes sure the photo bucket exists; on shutdown it closes the S3 client and the database pool. It adds the request-size middleware with the meals upload budget, includes each feature's router, registers the shared error handlers, and serves `GET /health/live`.

Packages depend on each other in one direction: `meals` uses `accounts`, `media` and `core`; `accounts` and `media` use only `core`; `core` uses no feature. `lint-imports` enforces this.

## Trade-offs

- **Modular monolith, not services.** One process and one database keep deployment simple for a single owner. Package boundaries keep the code separable if a feature ever needs to move out.
- **Bucket created at startup.** A fresh SeaweedFS needs no manual setup, but the API refuses to start while object storage is unreachable. Compose starts the API only after storage is healthy.
- **Explicit model registry.** `models.py` must list each new feature's models. Forgetting it means Alembic and the schema tests ignore those tables, and the tests report that.
