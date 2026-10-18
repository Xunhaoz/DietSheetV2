# DietSheet

A self-hosted meal log: photos sent from an iPhone Shortcut are stored with their meal details, and nutrition is estimated in the background.

| Path | Purpose |
| --- | --- |
| [`doc/`](doc/developer/README.md) | Design, data, API and delivery documents, the [backend developer guide](doc/developer/backend/README.md) and the [user guide](doc/user/README.md) |
| [`backend/`](backend/README.md) | The API service |
| [`scripts/`](scripts/README.md) | Automation entry points |
| `compose.yaml` | Local and host stack: PostgreSQL, SeaweedFS, migrations and the API |
| `.env.example` | Settings the stack needs; copy to `.env` |

Start with the [backend developer guide](doc/developer/backend/README.md).
