# meals

Recording meals. Today this covers one use case: uploading a meal with its photo (`POST /api/v1/meals`).

| Module | Layer | Responsibility |
| --- | --- | --- |
| `router.py` | HTTP | Reads the multipart form and `Idempotency-Key`, calls the service, returns 201 or 200 |
| `schemas.py` | HTTP | `MealIn` (form fields) and `MealOut` (response) |
| `service.py` | Use case | `create_meal`: validation, idempotency, storage, persistence |
| `repository.py` | Data access | Finds a meal by owner and idempotency key; adds a meal |
| `models.py` | Data | `Meal` table and `MealType` enum |

## Upload flow

1. **Parse.** `MealIn` requires `photo`, a `capturedAt` with a timezone offset, and a `mealType` from the six types; `notes` is optional (at most 2000 characters). Unknown fields are rejected, so a misspelled Shortcut field fails loudly instead of being dropped.
2. **Validate the photo.** It must be at most 2 MiB (413); the remaining rules come from `media`.
3. **Check for a replay.** The request hash is a SHA-256 of the capture instant in UTC, meal type, notes and the photo's own hash. If the owner already used this `Idempotency-Key`, the same hash returns the existing meal (200) and a different hash returns 409.
4. **Store the photo, then the record.** The photo goes to object storage first; then one transaction writes the meal and its `source` media row (201).
5. **Concurrent duplicates.** If two identical requests race, the unique `(user_id, idempotency_key)` constraint lets one commit; the other falls back to the replay check.

The response's `media` maps public size variants (`display`, `thumb`) to their dimensions. `source` keeps the original bytes, including EXIF such as GPS, so it is never returned, and a fresh upload shows `{}`.

## Trade-offs

- **Photo before row.** A crash between the two leaves an unreferenced object, never a row whose photo is missing. Unreferenced objects need a periodic sweep, which does not exist yet.
- **Idempotency key plus payload hash.** The key alone would silently return an old meal when a client reuses a key by mistake; the hash turns that into a 409. Keys are kept as long as the meal exists, and legacy Sheet `requestId` values import into the same column.
- **201 instead of the designed 202.** Nothing runs in the background yet. When workers arrive, the service will also create the job, and the response becomes 202.
- **The service owns the transaction.** The repository never commits, so a use case touching several tables stays atomic.
