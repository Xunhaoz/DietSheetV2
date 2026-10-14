# Data and migration

## Relational model

The domain and identity ER diagrams below cover all proposed tables, including personal access tokens and Alembic version metadata. Beat uses a static schedule; PostgreSQL job rows hold outcomes.

```plantuml
@startuml
!pragma layout smetana
skinparam monochrome true
skinparam shadowing false
skinparam linetype ortho
hide circle
title DietSheet - Domain ER (see identity ER for accounts)
entity "app_user\n(identity ER)" as user {
  * id : uuid <<PK>>
}
entity meal {
  * id : uuid <<PK>>
  * user_id : uuid <<FK>>
  {field} * request_id : varchar(80)
  {field} * request_hash : char(64)
  captured_at : timestamptz ?
  meal_type : enum ?
  notes : text ?
  current_result_id : uuid ? <<FK>>
  * analysis_revision : int
  * version : int
  * created_at : timestamptz
  * updated_at : timestamptz
  deleted_at : timestamptz ?
  --
  UNIQUE(user_id, request_id)
  captured_at/type required for live meals
}
entity media_object {
  * id : uuid <<PK>>
  * meal_id : uuid <<FK>>
  * kind : source | display | ai | thumb
  * processor_version : int
  * object_key : text <<UNIQUE>>
  {field} * sha256 : char(64)
  * content_type : varchar
  * byte_size : bigint
  * width : int
  * height : int
  * created_at : timestamptz
  --
  UNIQUE(meal_id, kind, processor_version)
}
entity job {
  * id : uuid <<PK>>
  * meal_id : uuid <<FK>>
  * kind : image | analysis | purge
  * revision : int
  {field} request_key : varchar(80) ?
  * input_snapshot : jsonb
  * state : enum
  * attempts : int
  next_attempt_at : timestamptz ?
  lease_token : uuid ?
  lease_expires_at : timestamptz ?
  error_code : varchar ?
  * created_at : timestamptz
  * updated_at : timestamptz
  --
  UNIQUE(meal_id, kind, revision)
  UNIQUE(meal_id, request_key) when non-null
}
entity outbox_event {
  * id : uuid <<PK>>
  * job_id : uuid <<FK, UNIQUE>>
  * available_at : timestamptz
  published_at : timestamptz ?
  * created_at : timestamptz
}
entity nutrition_result {
  * id : uuid <<PK>>
  * meal_id : uuid <<FK>>
  job_id : uuid ? <<FK, UNIQUE>>
  * revision : int
  * source : ai | import
  recognized : boolean ?
  {field} calories_kcal : numeric(10,1) ?
  {field} carbs_g : numeric(10,1) ?
  {field} protein_g : numeric(10,1) ?
  {field} fat_g : numeric(10,1) ?
  {field} fiber_g : numeric(10,1) ?
  * foods : text
  assumptions : text ?
  model : varchar ?
  prompt_version : varchar ?
  * created_at : timestamptz
  --
  UNIQUE(meal_id, id)
}
entity nutrition_goal {
  * id : uuid <<PK>>
  * user_id : uuid <<FK>>
  * effective_date : date
  {field} calories_kcal : numeric(10,1) ?
  {field} carbs_g : numeric(10,1) ?
  {field} protein_g : numeric(10,1) ?
  {field} fat_g : numeric(10,1) ?
  {field} fiber_g : numeric(10,1) ?
  * version : int
  * created_at : timestamptz
  * updated_at : timestamptz
  --
  UNIQUE(user_id, effective_date)
}
entity body_measurement {
  * id : uuid <<PK>>
  * user_id : uuid <<FK>>
  * measured_at : timestamptz
  {field} * weight_kg : numeric(8,2)
  {field} height_cm : numeric(8,2) ?
  {field} body_fat_pct : numeric(5,2) ?
  {field} skeletal_muscle_kg : numeric(8,2) ?
  {field} bmr_kcal : numeric(8,1) ?
  * notes : text
  * version : int
  * created_at : timestamptz
  * updated_at : timestamptz
}
user ||--o{ meal : owns
user ||--o{ nutrition_goal : owns
user ||--o{ body_measurement : owns
meal ||--o{ media_object : stores
meal ||--o{ job : schedules
job ||--o| outbox_event : dispatches
meal ||--o{ nutrition_result : history
job |o--o| nutrition_result : produces
meal |o--o| nutrition_result : selects current
note bottom of nutrition_result
  Current selection uses a same-meal composite FK.
  AI jobs/results must share meal ownership.
  Imported results allow a null job reference and partial nutrients.
end note
legend bottom
  * = NOT NULL; ? = nullable; PK = primary key; FK = foreign key
  Crow's foot = many; circle = optional; bar = one
  Files live in object storage; media_object stores metadata.
endlegend
@enduml
```

Application IDs are UUIDs. `?` denotes nullable. Timestamps use UTC `timestamptz`; effective goal dates use the user's IANA timezone, initially `Asia/Taipei`. Keep that reporting timezone fixed in v1. Nutrients are `numeric(10,1)`; physical measurements are `numeric(8,2)` unless indicated.

| Constraint / index | Rule |
| --- | --- |
| Meal ownership | All queries and media requests resolve through authenticated `user_id` |
| Upload deduplication | Unique `(user_id, request_id)`; SHA-256 over normalized submitted metadata and source bytes; conflicts return 409 |
| Meal lookup | Index `(user_id, captured_at, id)` for live meals; partial index on `deleted_at IS NULL` |
| Result selection | Composite FK `(meal.id, current_result_id)` references unique `(result.meal_id, result.id)`; selected result must belong to this meal |
| Result validation | Nullable nutrients represent unknown values; non-null values >= 0; fiber <= carbs when both known; recognized AI output requires all five values, unrecognized output requires all null |
| Job/result relationship | Nullable unique `result.job_id`; AI results require an analysis job belonging to the same meal; imported results use `job_id=null` |
| Jobs and outbox | Unique `(meal_id, kind, revision)` and `outbox.job_id`; index job `(state, next_attempt_at)`, outbox `(published_at, available_at)` |
| Media | Unique `(meal_id, kind, processor_version)` and object key; positive size/dimensions; original source is version 1 |
| Goal history | Unique `(user_id, effective_date)`; each target is positive or null (disabled); latest effective date <= viewed date wins |
| Measurements | Index `(user_id, measured_at, id)`; positive weight/height, body fat percentage 0..100, other measurements nonnegative; weight required |

Foreign keys restrict accidental physical deletion. Purge explicitly clears `current_result_id`, removes results/outbox/prior jobs/media, then strips meal content while retaining `id`, owner, request ID/hash and deletion timestamps. Retain the completed purge job with an empty input snapshot for status polling. Updates use a `version` counter; serialize competing writes under row locks. Goals and body records reference their owner independently.

BMI and body-fat mass are derived from a measurement's weight/height/fat percentage when available. Store skeletal muscle mass and BMR as entered measurements. Import body measurements after owner confirmation.

```plantuml
@startuml
!pragma layout smetana
skinparam monochrome true
skinparam shadowing false
hide circle
title DietSheet - Identity and infrastructure ER
entity app_user {
  * id : uuid <<PK>>
  {field} * username : varchar(100) <<UNIQUE>>
  {field} * time_zone : varchar(64)
  * is_active : boolean
  * created_at : timestamptz
  * updated_at : timestamptz
}
entity personal_access_token {
  * id : uuid <<PK>>
  * user_id : uuid <<FK>>
  {field} * token_digest : char(64) <<UNIQUE>>
  * created_at : timestamptz
  revoked_at : timestamptz ?
}
entity rate_limit_bucket {
  {field} * key_digest : char(64) <<PK>>
  * scope : varchar
  * window_started_at : timestamptz
  * count : int
  * expires_at : timestamptz <<INDEX>>
}
entity alembic_version {
  {field} * version_num : varchar(32) <<PK>>
}
app_user ||--o{ personal_access_token : owns
note bottom of personal_access_token
  Store SHA-256 digests of random PATs.
  V1 frontend and shortcut share a provisioned PAT.
  Revocation disables subsequent API authentication.
end note
note bottom of rate_limit_bucket
  Shared atomic counters for failed authentication/upload throttling.
  Key includes scope and hashed client/account identity.
  Expired counters are periodically removed.
end note
note bottom of alembic_version
  Alembic-managed revision metadata.
  Enforce a single migration head in CI.
end note
legend bottom
  * = NOT NULL; ? = nullable
  All domain owner foreign keys reference app_user.id.
endlegend
@enduml
```

Generate cryptographically random PATs and store only their SHA-256 digests in PostgreSQL. Each token belongs to one active owner and remains valid until revoked in v1. Embed the provisioned plaintext application PAT in the frontend configuration and the iPhone shortcut as explicitly accepted for this single-owner version. Rotation provisions a replacement, updates both clients and revokes the old token. No password hashes, sessions or CSRF records are required. Alembic owns `alembic_version`.

## Object storage

Use a private `diet-media` bucket with immutable keys `users/{userId}/meals/{mealId}/{processorVersion}/{variant}/{uuid}.{ext}`. PostgreSQL holds object keys, checksums, dimensions and content types. Browser access goes through authenticated `/media/{id}`; the API streams the object and supports private conditional caching. Backend services use host-mounted credentials to access source and AI variants through private object storage.

Persist objects first, then commit metadata in a database transaction; orphan sweeping handles interrupted writes. Backups must cover both PostgreSQL and S3 data plus SeaweedFS metadata/configuration.

## Google Sheets cutover

1. Back up the Sheet and disable writes and its minute trigger for a final consistent snapshot. Keep it read-only until reconciliation passes.
2. Export all pages with `photos=none`, following `nextAfter`; fetch `photos=data&id=...` per record. Save a local manifest, checksum and import checkpoint.
3. Preserve original `requestId` as a string (legacy IDs support 16–80 alphanumeric, underscore or hyphen characters). Map the six legacy labels to `breakfast`, `lunch`, `dinner`, `snack`, `late_snack`, `drink`. Preserve timestamps, all five nullable nutrients, notes and food descriptions.
4. The current export omits status, assumptions, model, received/updated timestamps and retry history. Extract those columns in a one-time read-only exporter or mark them unknown. Invalid timestamps/values and missing photos enter a reconciliation report for review.
5. Create `source=import` results, retaining partial/null values. Import JPEG bytes as sources and generate derivatives with `analyzeAfter=false`. If a legacy ratio differs, pad the derivatives to the nearer allowed ratio; preserve source bytes and record the transformation. Create media jobs for records with image bytes.
6. Upsert by owner + legacy request ID; skip unchanged hashes and report changed snapshots for review. Compare IDs, row counts, timezone/day totals, null counts and photo checksums. Resume safely after interruption.
7. Offer an explicit one-time import of browser-local goals with an effective date. Body report values require owner confirmation. Switch the frontend only after reconciliation, then revoke legacy tokens and remove the embedded connection URL during implementation.

Freeze Sheet writes during cutover. Before new-system writes start, rollback can return to the frozen Sheet. After new writes start, use a new-system backup/restore or an explicit reverse export to preserve subsequent records.
