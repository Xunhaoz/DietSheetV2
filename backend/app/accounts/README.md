# accounts

Identifies the caller. Today this is a single owner authenticated by one static token.

| Module | Responsibility |
| --- | --- |
| `auth.py` | `current_owner` dependency: checks `Authorization: Bearer <token>` and returns the owner ID |

## Behaviour

The token from the request is compared with `API_TOKEN` in constant time (`secrets.compare_digest`), so response timing does not leak how much of a guess was right. A match returns the configured `OWNER_ID`; a missing or wrong token gets 401 with `WWW-Authenticate: Bearer`. Every record created by a request belongs to that owner.

## Trade-offs

- **Static token instead of the designed sessions.** The iPhone Shortcut can send a header but cannot run a login and CSRF flow. Anyone holding the token acts as the owner, so treat it like a password and rotate it by changing `API_TOKEN` and the Shortcut together.
- **No `app_user` table yet.** The owner exists only as a UUID in configuration. Adding accounts means adding the table, a foreign key from `meal.user_id`, and per-user credentials.
- **Raises `HTTPException` directly.** Unlike services, this module belongs to the HTTP layer.
