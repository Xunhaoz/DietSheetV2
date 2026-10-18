# core

Infrastructure shared by every feature. It must not import any feature package.

| Module | Responsibility |
| --- | --- |
| `config.py` | `Settings` read from environment variables at import time |
| `db.py` | SQLAlchemy engine, session dependency and the declarative `Base` |
| `errors.py` | `DomainError`, the base for expected failures raised by services |
| `error_handlers.py` | Turns `DomainError` and database outages into HTTP responses |
| `body_limit.py` | ASGI middleware that rejects oversized request bodies before parsing |
| `schemas.py` | `CamelModel`, the base for camelCase API schemas |

## Behaviour

- **Settings.** Startup fails if a variable is missing or `API_TOKEN` is shorter than 32 characters. The token is a `SecretStr`, and validation errors hide input values, so secrets never reach logs.
- **Database.** `Base` carries a naming convention (`pk_`, `uq_`, `fk_`, `ck_`, `ix_`), so every constraint has a predictable name that later migrations can target. Sessions are per request with `expire_on_commit=False`, so responses can read committed objects.
- **Errors.** A `DomainError` maps to `{"detail": message}` with its `status_code`; 5xx are logged as warnings. A SQLAlchemy `OperationalError` maps to 503.
- **Body limit.** Requests whose `Content-Length` exceeds the budget get 413; chunked bodies without a length get 411. Both close the connection, so Uvicorn does not keep reading an attacker's upload.

## Trade-offs

- **Pool defaults (5 connections + 10 overflow) per process.** Ample for one owner. If API processes multiply, size the pool so their total stays under Postgres `max_connections`, or add PgBouncer.
- **`OperationalError` is broad.** A wrong database password also returns 503 instead of 500, unlike S3 credential errors. Telling the cases apart needs driver-specific error codes and is deferred.
- **The body limit trusts `Content-Length`.** This is safe because Uvicorn never delivers more bytes than declared. Behind an HTTP/2 proxy that forwards chunked bodies, every upload would get 411; the proxy must buffer or set the length.
- **Errors use FastAPI's `detail` shape, not the `{code, message, requestId}` contract in api.md.** Adopting the contract later only touches `error_handlers.py`.
