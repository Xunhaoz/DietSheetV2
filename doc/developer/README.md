# DietSheet design

Status: proposed, documentation only. Baseline: [`5edb1bd`](https://github.com/Xunhaoz/DeitSheet/tree/5edb1bd8f972376e3d9d6ddb3caf684fdbd200ce), plus the supplied Apps Script. No application, infrastructure, or workflow changes are activated by this draft.

| Document | Purpose |
| --- | --- |
| [Design](design.md) | Current behavior, user journeys, architecture, image processing |
| [Data](data.md) | Complete proposed relational model, object storage, migration |
| [API](api.md) | Frontend/backend contract |
| [Delivery](delivery.md) | Compose, updates, GitHub Actions, recovery, testing |
| [User guide](../user/README.md) | Intended user workflows |

Deployment target: **114.32.210.249**, with external access. Assume one owner initially; every domain record is owner-scoped. Hardware capacity is sufficient according to the owner. CPU architecture, public hostname, SSH identity/port and backup destination remain deployment parameters.

Host application services, PostgreSQL, object storage, queue, container registry and CI execution locally. No AWS services. Gemini remains the explicitly permitted external AI service. GitHub Actions remains the requested workflow control plane; self-hosted runners execute jobs. Package downloads and certificate issuance are operational network dependencies.

Interpret “object database” as **S3-compatible object storage for photos**; PostgreSQL stores structured data and object metadata. An object-oriented database would serve a different requirement.

## Implementation order

1. Establish FastAPI, authentication, schema migrations, Compose and backup/restore.
2. Add upload, image variants, Celery jobs, provider adapter and API contracts.
3. Add dated goals, body measurements, daily gallery and overflow charts; retain visual style.
4. Rehearse the Sheet import, run acceptance tests, then enable the release workflow.

Public hostname/TLS, deployment credentials and CPU architecture must be supplied before deployment. Revisit this draft before implementation; the examples describe future files and commands.

## Diagrams

All diagrams use PlantUML. The domain and identity ER diagrams together cover the proposed database. SVG files are generated previews; `.puml` files are authoritative.

| Diagram | Source | Preview |
| --- | --- | --- |
| Architecture | [PlantUML](diagrams/architecture.puml) | [SVG](diagrams/architecture.svg) |
| Domain ER | [PlantUML](diagrams/er-domain.puml) | [SVG](diagrams/er-domain.svg) |
| Identity ER | [PlantUML](diagrams/er-identity.puml) | [SVG](diagrams/er-identity.svg) |
| Upload and analysis | [PlantUML](diagrams/processing.puml) | [SVG](diagrams/processing.svg) |

Render locally with a pinned PlantUML JAR and Java:

```sh
java -jar plantuml.jar --check-syntax doc/developer/diagrams/*.puml
java -jar plantuml.jar -tsvg doc/developer/diagrams/*.puml
```

Sources were consulted on 2026-09-28. Framework capabilities are linked next to the relevant decisions; sizing, limits and latency budgets are proposed project requirements, not measured results.
