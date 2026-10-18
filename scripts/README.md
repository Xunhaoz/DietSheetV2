# scripts

Entry points for automation, as named in [Delivery](../doc/developer/delivery.md).

| Script | Purpose |
| --- | --- |
| `ci.sh` | Runs every backend check: locked install, ruff, mypy, architecture rules, pytest against a throwaway Postgres, then a smoke test of the built image. Extra arguments go to pytest |

## Behaviour

`ci.sh` gives its Compose project a unique name per run and publishes Postgres on a random local port, so parallel runs do not collide. A trap removes the containers, volumes and image it created, and only those, even when a check fails. Checks run cheapest first and stop at the first failure.

## Trade-offs

- **Image smoke test, not a full stack run.** Tests use the editable source checkout and cannot see packaging mistakes, so the script imports the app and loads the migrations inside the built image. It does not start the API against real services; that remains the full-stack check in the backend guide.
- **One script for local runs and CI.** "Passes on my machine" and "passes in CI" mean the same thing. Docker is required locally.
- **`publish.sh` and `request-deploy.sh` from Delivery do not exist yet.** They arrive with the release workflow.
