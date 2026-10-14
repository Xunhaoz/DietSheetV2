# API contract

Base: same-origin `/api/v1`. JSON uses camelCase, UTC ISO-8601 timestamps with offsets on input, local `YYYY-MM-DD` dates and numeric nutrient values (kcal/g). Generate OpenAPI from FastAPI/Pydantic during implementation; use it for client contract tests.

## Authentication and conventions

V1 uses an operator-provisioned Personal Access Token (PAT) for both the website and iPhone Shortcuts. Hardcode the application PAT in the frontend configuration and configure the same PAT in the shortcut; send `Authorization: Bearer <token>` on every API and media request over HTTPS. This is an intentional single-owner convenience tradeoff: anyone who can read the frontend bundle can obtain the PAT and exercise the owner's API permissions. The frontend PAT is not a confidential credential.

The API validates the PAT digest against an active owner and a non-revoked token record. There are no password login/logout endpoints, authentication cookies, sessions or CSRF tokens in v1. Accept authentication only through the Authorization header, never through a cookie or URL parameter. Browser requests use the application origin; do not enable cross-origin browser access. Native clients such as Shortcuts may omit Origin; a missing Origin is not an authentication failure. If Origin is present, validate it against the application origin. All clients still require a valid PAT.

Keep Gemini, database, object-storage and broker credentials on the host; only the application PAT is embedded in the frontend. Rate-limit failed authentication by client IP and uploads by owner in middleware using shared PostgreSQL counters initially. Scope every resource lookup by the token's owner, including media/jobs. Owners and PATs are operator-provisioned; rotation replaces the frontend and shortcut token and revokes the old record.

Lazy-load media with an authenticated fetch as images approach the viewport, convert the response to a Blob URL for image display, and revoke Blob URLs when discarded. Do not put the PAT in image URLs. iPhone Shortcuts uses multipart `POST /api/v1/meals` with `photo`, `capturedAt`, `mealType`, `notes` and an `Idempotency-Key`; keep that key and payload unchanged when retrying the same submission. Prepare the image before assigning the submission key: convert unsupported formats such as HEIC to JPEG, preserve or crop to 3:4 or 4:3, and enforce the existing 15 MiB / 24-megapixel limits.

Lists: `{items, nextCursor, total}`; default 50, maximum 100. Meals sort by `(capturedAt, id)` ascending; cursors contain the last tuple and filters, signed by the server. Gallery follows all pages. Concurrent edits may move records between pages; deduplicate by ID and refresh on mutation. `total` reflects that response's query and may change between pages.

Errors: `{code, message, fields?, requestId}` with HTTP status. Use 400 for malformed input, 422 for field/schema validation, 401 for missing/invalid/revoked PAT or inactive owner, 403 for forbidden operations or rejected Origin, 404 for unavailable owner-scoped resources, 409 for conflicts, 412 for stale versions, 413 for size, 415 for unsupported image format, 429 for throttling, 503 for unavailable persistence. Normalize FastAPI exception responses to this contract.

Reads return ETags. PATCH/DELETE and replacement PUT require `If-Match`; absence returns 428. Creating a dated goal uses `If-None-Match: *`; an existing date returns 412. Private data uses `Cache-Control: private, no-cache`; conditional GET can return 304. Media responses use private max-age=300 and checksum ETags; clients clear in-memory data and Blob URLs after an authentication failure or token change.

## Endpoints

| Method and path | Request / response | Success |
| --- | --- | --- |
| GET `/me` | `{id, timeZone}` | 200 |
| POST `/meals` | Multipart `photo`, `capturedAt`, `mealType`, `notes`; `Idempotency-Key` required | 202 + meal and job URLs |
| GET `/meals?date=...&cursor=...` | Day-scoped meal cards; alternatively bounded `from`/`to` dates | 200 |
| GET `/meals/{id}` | Full meal, selected result, media and latest job | 200 |
| PATCH `/meals/{id}` | `capturedAt`, `mealType`, `notes`; version precondition | 200 or 202 if analysis queued |
| DELETE `/meals/{id}` | Hide immediately; asynchronous purge | 202 + purge job URL |
| POST `/meals/{id}/analyses` | `{}`; `Idempotency-Key` and `If-Match`; regenerate failed/missing derivatives from source first if needed | 202 + job URL |
| GET `/jobs/{id}` | `{id, kind, state, attempts, nextAttemptAt, errorCode}` | 200 |
| GET `/days/{date}` | Totals, known/missing counts per nutrient, meal/state counts, effective goal | 200 |
| GET `/trends?from=...&to=...` | Inclusive range <= 366 days; same day summaries | 200 |
| GET `/nutrition-goals?cursor=...` | Effective-date history, including scheduled goals | 200 |
| PUT `/nutrition-goals/{effectiveDate}` | Complete five-target object; create/correct one history row | 201 / 200 |
| DELETE `/nutrition-goals/{effectiveDate}` | Remove history row; previous applicable goal takes effect | 204 |
| GET `/body-measurements?cursor=...` | Measurement history, newest first | 200 |
| POST `/body-measurements` | `{measuredAt, weightKg, heightCm?, bodyFatPct?, skeletalMuscleKg?, bmrKcal?, notes?}` | 201 |
| PATCH/DELETE `/body-measurements/{id}` | Correct entered fields / delete; version precondition | 200 / 204 |
| GET `/media/{id}` | Authenticated display/thumb bytes; outside `/api/v1` | 200 / 304 |

Body/goal create and update responses contain ID and version/ETag. The newest body record is the first history item. Profile timezone is operator-configured in v1. Derive ownership from the authenticated PAT. Date filters use local midnight through the next local midnight converted to UTC.

## Meal contract and idempotency

Meal fields: `id`, `capturedAt`, `mealType`, `notes`, `version`, `analysisRevision`, `processing`, `nutrition`, `media`, `createdAt`, `updatedAt`.

- `processing`: separate image/analysis states and current `jobId`; use these states to display processing progress.
- `nutrition`: null or `{source, revision, stale, recognized, foods, assumptions, model, caloriesKcal, carbsG, proteinG, fatG, fiberG}`. Model/recognized/assumptions may be null for imports.
- `media`: available variants only, each `{id, kind, url, width, height}`. Include thumbnail on lists; display URL on details.

Persist meal upload idempotency for the tombstone's lifetime. A repeated key and matching payload returns the existing receipt (200); a changed payload or deleted meal returns 409. Use the same key after timeout. Server receipt time is excluded from the hash. Accept uploads after both object and database persistence succeed.

Analysis requests use a unique `(mealId, requestKey)` on the first job in the pipeline. Check a replay before the version precondition and return the same job; new requests while processing is active return 409. Missing source returns 409 `IMAGE_REQUIRED`. Metadata edits that change notes or meal type cancel/fence the old analysis and enqueue a new revision. Capture-time changes only move daily aggregation. Photos are immutable in v1; replacing a photo means deleting and adding a meal. Worker-visible updates also increment the meal version; summary ETags include applicable goals and meal versions.

Keep the previous successful result visible with `stale=true` during reanalysis or failure; day summaries count it and report a stale count. An `unrecognized` result becomes current with null nutrients. Imported partial values remain distinguishable from pending jobs. Poll active jobs every 2 seconds, backing off to 10 seconds; pause hidden tabs and stop on terminal state. Refresh the meal/day after completion.

## Summary example

```json
{
  "date": "2026-09-28",
  "timeZone": "Asia/Taipei",
  "mealCount": 3,
  "pendingCount": 1,
  "failedCount": 0,
  "staleCount": 0,
  "nutrients": {
    "caloriesKcal": {
      "value": 2250.0,
      "knownCount": 2,
      "missingCount": 1,
      "target": 1800.0,
      "percent": 125.0,
      "excess": 450.0
    }
  }
}
```

The real response includes all five nutrients. Sum known values only; return null if none are known (including no meals). Calculate `percent`/`excess` only when value and positive target exist. Apply identical rules to dashboard, gallery and trends.
