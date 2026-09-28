# DietSheet design

Status: proposed design. Baseline: [`5edb1bd`](https://github.com/Xunhaoz/DeitSheet/tree/5edb1bd8f972376e3d9d6ddb3caf684fdbd200ce), plus the supplied Apps Script.

| Document | Purpose |
| --- | --- |
| [Design](design.md) | Current behavior, user journeys, architecture, image processing |
| [Data](data.md) | Complete proposed relational model, object storage, migration |
| [API](api.md) | Frontend/backend contract |
| [Delivery](delivery.md) | Compose, updates, GitHub Actions, recovery, testing |
| [User guide](../user/README.md) | Intended user workflows |

Deployment target: **114.32.210.249**, with external access. Assume one owner initially; every domain record is owner-scoped. Hardware capacity is sufficient according to the owner. CPU architecture, public hostname, SSH identity/port and backup destination remain deployment parameters.

Host application services, PostgreSQL, object storage, queue, container registry and CI execution locally. Gemini provides external AI analysis. GitHub Actions coordinates workflows; self-hosted runners execute jobs. Package downloads and certificate issuance are operational network dependencies.

Store photos in local **S3-compatible object storage**; PostgreSQL stores structured data and object metadata.

## Implementation order

1. Establish FastAPI, authentication, schema migrations, Compose and backup/restore.
2. Add upload, image variants, Celery jobs, provider adapter and API contracts.
3. Add dated goals, body measurements, daily gallery and overflow charts; retain visual style.
4. Rehearse the Sheet import, run acceptance tests, then enable the release workflow.

Public hostname/TLS, deployment credentials and CPU architecture must be supplied before deployment. Revisit this draft before implementation; the examples describe future files and commands.

## Diagrams

Diagrams are embedded as `plantuml` code blocks in the documents. Edit these blocks to update the diagrams.

| Diagram | Document |
| --- | --- |
| Architecture and processing | [Design](design.md) |
| Domain and identity ER | [Data](data.md) |

Sources were consulted on 2026-09-28. Framework capabilities are linked next to the relevant decisions; sizing, limits and latency budgets are project requirements to validate on the target host.
