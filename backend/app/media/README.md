# media

Photos as files: what is accepted, where bytes are stored, and how each stored file is recorded. Has no knowledge of meals.

| Module | Responsibility |
| --- | --- |
| `images.py` | `inspect_image`: enforces the upload rules and returns the photo's displayed dimensions |
| `storage.py` | `ObjectStorage`, a thin S3 adapter, and the `get_storage` dependency |
| `models.py` | `MediaObject` table (one row per stored file) and `MediaKind` variants |

## Photo rules

Clients resize photos before upload, so the rules are strict rather than corrective:

- JPEG only; other formats, including multi-picture JPEG (MPO), get 415.
- Long edge at most 1024 px, checked from the header **before decoding**, so a forged header cannot exhaust memory (422).
- After applying EXIF orientation, the ratio must be 3:4 or 4:3 within one pixel (422).
- Data that cannot be decoded gets 422, never 500. A fuzz test guards this.

The size limit in bytes (`MAX_BYTES`, 2 MiB) lives here too. The largest 1024×768 JPEG measured was about 1.3 MiB.

## Storage

`get_storage` builds the S3 client on first use (`lru_cache`), so importing the app needs no S3, and tests replace it with `dependency_overrides`. The client uses path-style URLs (SeaweedFS on a private network), 5 s connect and 30 s read timeouts, and at most 3 attempts. `ensure_bucket` creates the bucket only on 404. Failures map to two cases: unreachable or 5xx becomes `StorageUnavailable` (503, safe to retry), and 4xx such as bad credentials stays an error (500) because retrying cannot fix configuration.

## Records

Each stored file is one `MediaObject`: object key, SHA-256, content type, size and displayed dimensions. Kinds are `source` (the upload, private), `display`, `ai` (private provider input) and `thumb`, unique per meal, kind and `processor_version`, so derivatives can be regenerated under a new version without overwriting. `meal_id` refers to the meal table by name only, keeping this package independent of `meals`.

## Trade-offs

- **Reject, do not resize.** Keeps the server simple and the stored source exactly what the client chose, but every client must resize correctly. The detail view is limited to 1024 px.
- **SeaweedFS behind an S3 adapter.** Any S3-compatible store works by changing the endpoint. Backups must include SeaweedFS metadata, not only data files.
- **Full decode on upload.** This catches corrupt files early, at about 2.4 MB of memory per 1024×768 photo.
