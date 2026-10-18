# versions

Migration revisions. Each file has `upgrade()` and `downgrade()` and names its predecessor in `down_revision`.

| Revision | Change |
| --- | --- |
| `0001` | `meal` and `media_object` tables, the `meal_type` and `media_kind` enum types, and the `(user_id, captured_at, id)` index |

## Rules

- `downgrade()` reverses `upgrade()` completely, including Postgres enum types, which `drop_table` leaves behind.
- Every constraint and index has an explicit name wrapped in `op.f()`.

## Trade-offs

- **`0001` has been edited in place** while no environment holds data worth keeping (renames, constraint names). Once a real deployment has run a revision, it is frozen and changes go into a new revision.
- **Postgres native enums.** The database rejects invalid values itself, but adding a meal type or media kind needs a migration with `ALTER TYPE ... ADD VALUE`.
