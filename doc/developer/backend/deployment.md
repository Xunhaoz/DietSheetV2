# Deploy to a host

How to run the current backend on a Linux host (commands assume Ubuntu) and reach it from the iPhone Shortcut over HTTPS. This covers the minimal slice in [Implementation status](README.md#implementation-status); the full release process is planned in [Delivery](../delivery.md).

## What runs

`compose.yaml` starts PostgreSQL, SeaweedFS, a one-shot `migrate` job and the API on port 8000. Only the API needs to be reachable; the database and object storage stay on the stack's private network. The API serves `POST /api/v1/meals` and `GET /health/live`, protected by one Bearer token.

## Prepare the host

Check the CPU architecture with `uname -m`; both `x86_64` and `aarch64` work. Install [Docker Engine](https://docs.docker.com/engine/install/ubuntu/) with Compose 2.24.4 or later, then add yourself to the `docker` group and log in again:

```bash
sudo usermod -aG docker $USER
```

To clone a private repository, give the host its own key with `ssh-keygen -t ed25519` and add the public key as a read-only **Deploy key** in the repository settings.

## Install

```bash
git clone <repository-url> DietSheet && cd DietSheet
cp .env.example .env && chmod 600 .env
```

Fill in every value in `.env`. Generate secrets and the token with `openssl rand -hex 32`, and `OWNER_ID` with `cat /proc/sys/kernel/random/uuid`. The API refuses to start with an `API_TOKEN` shorter than 32 characters. Keep a copy of `.env` in a password manager: the database and object storage cannot be opened without it.

```bash
docker compose up --build -d --wait
docker compose ps -a        # db, objects and api running; migrate exited (0)
curl http://localhost:8000/health/live
```

## Expose it through a reverse proxy

Uvicorn speaks plain HTTP and the token travels in a header, so expose the API only through a proxy that terminates HTTPS. These steps use Nginx Proxy Manager running in its own Compose project; any proxy on a shared Docker network works the same way.

1. Point a DNS A record, e.g. `diet.example.com`, at the host's public IP and forward TCP 80 and 443 on the router to the proxy. Do not forward 8000.
2. Put the proxy container on an external network, e.g. `nginx_network` (`docker network create nginx_network` if it does not exist yet).
3. Create `compose.override.yaml` next to `compose.yaml`. Compose reads it automatically, and it is gitignored so `git pull` never touches it:

   ```yaml
   services:
     api:
       ports: !override
         - 127.0.0.1:8000:8000   # host-only, for curl checks
       networks:
         default: {}
         nginx_network:
           aliases: [dietsheet-api]

   networks:
     nginx_network:
       external: true
   ```

   `!override` replaces the `8000:8000` binding from `compose.yaml`; a plain `ports:` would be appended to it and fail with a port conflict. Ports published by Docker bypass `ufw`, so binding to `127.0.0.1` is what keeps 8000 off the network. The `dietsheet-api` alias avoids clashing with other stacks' `api` services on the shared network.

4. Apply it and check that the proxy can reach the API:

   ```bash
   docker compose up -d --wait
   docker exec <proxy-container> curl -s http://dietsheet-api:8000/health/live
   ```

5. Add a proxy host for `diet.example.com`: scheme `http`, forward host `dietsheet-api`, port `8000`, *Block Common Exploits* on. Request a Let's Encrypt certificate and enable *Force SSL*. In the advanced configuration:

   ```nginx
   # API docs are not needed from outside.
   location ~ ^/(docs|redoc|openapi\.json) { return 404; }
   # The API rejects bodies over about 2 MiB; stop larger ones at the edge.
   client_max_body_size 3m;
   ```

   Keep request buffering on (the default): the API answers 411 to a body without `Content-Length`, and nginx adds it after buffering.

6. From outside the LAN, for example a phone on mobile data:

   ```bash
   curl https://diet.example.com/health/live
   ```

Then configure the Shortcut as in the [user guide](../../user/README.md#iphone-shortcut), using `https://diet.example.com/api/v1/meals`. iPhone photos are HEIC by default, so convert them to JPEG (without metadata) and resize the longest edge to 1024 before uploading; their 4:3 shape then meets the ratio rule.

## Test an upload

The photo must be a JPEG with a long edge of at most 1024 px and a 3:4 or 4:3 ratio. ImageMagick (`sudo apt install imagemagick`) makes a synthetic one:

```bash
convert -size 1024x768 xc:orange ~/meal.jpg
set -a && . ./.env && set +a
curl -i -H "Authorization: Bearer $API_TOKEN" -H "Idempotency-Key: test-upload-0000000001" \
  -F photo=@$HOME/meal.jpg -F capturedAt=2026-10-20T12:30:00+08:00 -F mealType=lunch \
  https://diet.example.com/api/v1/meals
```

The first request returns 201 and repeating it returns 200 with the same meal. Keep test files outside the checkout so `git status` stays clean.

## Update

```bash
git pull && docker compose up --build -d --wait
```

`migrate` runs before the API starts, so schema changes apply on every update. Back up first when an update contains a migration (see [Delivery](../delivery.md#recovery-and-operating-targets)). Change only `.env` and `compose.override.yaml` on the host: editing tracked files such as `compose.yaml` makes `git pull` conflict.

| Task | Command |
| --- | --- |
| Follow API logs | `docker compose logs -f api` |
| Rotate the token | Change `API_TOKEN` in `.env`, run `docker compose up -d`, update the Shortcut |
| Stop, keeping data | `docker compose down` |
| Delete all data | `docker compose down -v` (removes the database and photo volumes) |

## Before going public

- The token is the only protection and there is no rate limiting. Use a generated token, never share a Shortcut that contains it, and rotate it if it leaks. Add `limit_req` in the proxy if abuse becomes a concern.
- Source IP allowlists do not fit a phone on mobile data; rely on the token and HTTPS.
