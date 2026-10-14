# Delivery and verification

Implementation contract for deployment and verification.

## Compose topology

Target Linux with Docker Engine/Compose; select `linux/amd64` or `linux/arm64` after confirming the host CPU. Publish the application at a hostname resolving to **114.32.210.249**. Route public TCP 80/443 to Caddy and provision a trusted certificate. Restrict SSH to the deployment/admin network. Bind database, broker, S3, registry and monitoring ports to private networks.

| Service | Image / persistent storage |
| --- | --- |
| `proxy` | Caddy; certificate/configuration volumes |
| `frontend` | Immutable static asset image |
| `api` | FastAPI/Uvicorn backend image |
| `worker` | Same backend digest; Celery image/analysis/maintenance queues |
| `beat` | Same backend digest; one scheduler, local schedule volume |
| `migrate` | Same backend digest; one-shot `alembic upgrade head` |
| `db` | PostgreSQL; database volume |
| `broker` | RabbitMQ; durable queue volume |
| `objects` | MinIO single-node single-drive; data volume including bucket metadata; mounted credential configuration |
| `registry` | Local Distribution registry; filesystem volume, internal TLS and credentials |

Keep registry/runner infrastructure separate from application restarts. Use private Compose networks, persistent named volumes, service health checks, non-root application containers and restart policies. API/worker reuse one backend image but run separate commands. Start with worker concurrency 2 and tune after measuring memory and Gemini limits. [Compose production](https://docs.docker.com/compose/how-tos/production/), [local registry](https://hub.docker.com/_/registry).

Store credentials in restricted host files mounted as Compose secrets: database, S3, broker, application signing key and Gemini key. Protect the mounted secret files with host filesystem permissions. Set public hostname, trusted proxy, reporting timezone and model through configuration. Use synthetic data in CI artifacts. Self-host fonts and API-doc assets.

First installation: provision host/DNS/TLS, initialize volumes and registry credentials, pull pinned service images, run migrations, create the owner via `python -m app.cli create-owner` using interactive password input, start services, then smoke-test login/upload/gallery.

## Updates

Use a versioned release directory containing Compose/config references and a manifest of exact frontend/backend image digests plus expected schema revision. Below, commands run in that release directory; Compose reads the pinned image references from its release environment file.

| Update | Procedure |
| --- | --- |
| Frontend only | Verify API compatibility; `docker compose pull frontend`, then `docker compose up -d --no-deps frontend`; smoke-test all three RWD layouts |
| Backend only | Pull `api worker beat migrate`; drain worker and stop Beat; apply required migrations once; replace API/worker/Beat using the same digest; check readiness and a complete job |
| DB schema | Back up; review `alembic upgrade head --sql`; run `docker compose run --rm migrate`; verify expected `alembic current`; generate and review migrations during development |
| PostgreSQL engine | Separate maintenance release; logical dump/restore into a new major-version volume or a rehearsed `pg_upgrade` |

For a coordinated release, the host-side deploy command acquires a file lock, pre-pulls images, enters maintenance mode, stops Beat, drains/stops workers, stops the API, creates a consistent backup, runs migrations, starts services, then removes maintenance only after health and authenticated smoke tests pass. Keep object storage and DB available to the backup step. Schedule a brief maintenance window. [Alembic operations](https://alembic.sqlalchemy.org/en/latest/tutorial.html).

Use expand/backfill/contract migrations across releases. Failed migration or smoke test stops the release and retains the prior manifest. Roll back images only if the schema remains compatible. Otherwise remain in maintenance and restore the paired database/object backup. Frontend can roll back independently if its API contract still matches.

## GitHub Actions

The [workflow example](examples/release.yml.example) is intentionally outside `.github/workflows`. Activate it only after the referenced scripts and deployment preconditions exist. Pin action references to verified commit SHAs before activation.

1. Pull requests: lint, unit, contract, integration and responsive browser tests on an ephemeral **local CI VM**, with disposable test volumes, test credentials and an isolated Docker daemon. Untrusted forks require approval before using local runner capacity. Use the `pull_request` event for contribution tests.
2. Protected `main`: rerun tests; build frontend/backend images for `DEPLOY_PLATFORM`; publish into the **local registry** under the commit SHA; record digests.
3. Deployment: an isolated trusted runner sends a release request over SSH to `DEPLOY_HOST=114.32.210.249`. Verify a pre-provisioned host key. A restricted deploy account invokes only the host-owned release command, which validates digest references and executes the update procedure above.
4. Serialize releases and allow active migrations to finish. Record commit, digests, backup ID, schema revision and result on the host; notify through the Actions job result. Deploy tested commits from protected `main`.

Required configuration: `DEPLOY_HOST`, `DEPLOY_PORT`, `DEPLOY_USER`, `DEPLOY_PLATFORM`, internal `REGISTRY_HOST`, public `APP_HOSTNAME`; protected SSH key/known-hosts and registry credentials. The runner must reach the local registry. If the LAN cannot hairpin to the public IP, configure an explicit internal SSH route to the same host and retain the public target mapping. [GitHub runner security](https://docs.github.com/en/actions/reference/security/secure-use).

Planned script contracts: `ci.sh` creates disposable Compose dependencies, runs all tests and removes only its own test volumes; `publish.sh` builds/pushes both images and verifies returned digests; `request-deploy.sh` validates the commit argument and submits it to the host command. Release manifests live in the local registry or host release store; tests and logs contain synthetic data only.

## Recovery and operating targets

Nightly and pre-migration backups: pause writers and drain workers, take a PostgreSQL custom-format dump plus a coordinated snapshot of all MinIO data/metadata and required host configuration. Encrypt copies on a separate owner-controlled disk/NAS; retain 7 daily and 4 weekly backups. Rehearse restore into empty volumes, compare row/object checksums, and rebuild queued work from PostgreSQL. [PostgreSQL dumps](https://www.postgresql.org/docs/current/backup-dump.html).

Expose minimal `/health/live` and `/health/ready` responses; readiness requires DB and object storage, while broker/Gemini failures are reported as degraded background processing. Monitor oldest pending job, retry/failure counts, disk usage, backup age and request latency. Log request/job IDs and durations, excluding tokens, images and meal/body content.

Proposed budgets on the target host with 10,000 meals and five concurrent clients: warm metadata reads p95 < 300 ms; acceptance < 2 s after request-body transfer, excluding AI; gallery initial payload <= 100 KiB excluding thumbnails. Validate query counts and indexes before adding caches. Target nightly-backup RPO <= 24 h and restore RTO <= 2 h, subject to a measured restore drill. Gemini completion time is an external dependency; readings and goal/body edits remain available during outages.

## Testing: Arrange, Act, Assert

Use pytest, real PostgreSQL integration tests, synthetic photos, a deterministic Gemini stub, Vitest and Playwright. Every test has explicit Arrange/Act/Assert sections, one behavioral focus and a fresh fixture. Mock external boundaries and define expected values from behavioral requirements.

| Arrange | Act | Assert |
| --- | --- | --- |
| Positive target; totals 0%, 100%, 125%, 300%, null | Render each gauge | Exact percentages, proportional overflow, unknown stays unknown |
| Two dated goals; records around local midnight | Query day/trend | Correct day boundary, historical target, unknown values preserved |
| 101 meals, mixed ratios and pending/failed states | Open gallery and follow cursors | All records once, chronological order, ratios preserved |
| Valid photo, rotated EXIF, invalid bytes or size limit | Upload/process | Correct dimensions/variants, stripped derivative metadata, rejected invalid input |
| Same upload key; changed payload; broker offline | Submit and recover | One meal, conflict on change, persisted job eventually dispatched |
| Worker crashes before/after commit; notes edited during AI | Redeliver job | Attempt cap holds, current revision preserved |
| Valid session, another owner, missing CSRF or expired token | Access/mutate meal and media | Authorization and CSRF enforced; sensitive fields redacted |
| Body history and unrelated meal/goal records | Correct one measurement | Only measurement changes; latest sidebar value updates |
| Old release schema plus paired backup | Migrate, fail a smoke test, restore | Consistent DB/object state and safe rollback behavior |
| Duplicate legacy IDs, nulls, missing photos, invalid dates | Import twice | Stable counts/totals, explicit exceptions, imported estimates preserved |

Run Chromium and WebKit at every acceptance viewport in [Design](design.md), including both photo orientations, overflow values, long text, dialogs and loading/error states. Assert that content fits the viewport horizontally and actions remain reachable. Manually verify Dock-visible Safari, touch/keyboard interactions and 200% zoom. Pixel baselines must preserve the current grayscale style. Run these acceptance tests during implementation.
