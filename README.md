# step-ca-webui
step-ca-webui
## PKI Web Platform (Step CA + Keycloak + FastAPI + React)

Production-oriented scaffold for a web-based PKI management platform with:

- `React + Vite + Tailwind` frontend
- `FastAPI` backend API
- `Redis + Celery` async job system
- isolated worker executing `step` CLI safely
- `step-ca` server
- `Keycloak` OIDC and role-based access
- PostgreSQL metadata storage

## Services

- `frontend` - UI (`http://localhost:5173`)
- `api` - FastAPI (`http://localhost:8000`)
- `worker` - Celery worker
- `step-ca` - certificate authority (`https://localhost:9000`)
- `postgres` - metadata DB
- `redis` - queue backend
- `keycloak` - IdP (`http://localhost:8080`)

## Implemented now

- OIDC-based authentication in UI via Keycloak (`keycloak-js`)
- JWT validation in FastAPI using Keycloak JWKS
- Role checks (`pki-admin`, `pki-operator`, `pki-auditor`, `pki-user`)
- Certificate issue flow (async job):
  - UI submits issue request
  - API enqueues Celery task and stores job record
  - Worker validates input and runs `step ca certificate` via subprocess (`shell=False`)
  - Job status and certificate metadata persisted in PostgreSQL
- API scaffolds for:
  - `/api/auth`
  - `/api/certificates`
  - `/api/provisioners`
  - `/api/acme`
  - `/api/ca/health`
  - `/api/audit-logs`
  - `/api/users`
  - `/api/settings`
  - `/scim/v2/Users`, `/scim/v2/Groups` (scaffold)

## Authentication note (SPA + API)

The UI uses Keycloak’s public client (`pki-frontend`). Access tokens often have `aud=account` (or `pki-frontend`), not `pki-api`. The API validates the JWT signature and issuer and does **not** require a strict `aud=pki-api` match, so `/api/auth/me` works without extra Keycloak audience mappers.

## CA setup in the UI

Use **CA Setup** in the app (`/ca-setup`) for:

- Manual initialization workflow and commands
- Live reachability and root fingerprint (when OpenSSL is available in the API image)
- **Download** `roots.pem` (and optional intermediate) through authenticated API proxies

Provisioner listing uses the worker (`STEP_CA_PASSWORD` must match the password you set during `step ca init`).

## Manual step-ca initialization (you control parameters)

This project now runs in **manual CA mode**. `step-ca` does not auto-init.

1. Initialize once with your own params:

```bash
cd infra
docker compose run --rm step-ca-init
```

You can change the init flags in `infra/docker-compose.yml` under `step-ca-init` (or run your own custom command).

2. Set worker password (for provisioner/admin operations):

```bash
export STEP_CA_PASSWORD='your-step-ca-password'
```

3. Start the full stack:

```bash
docker compose up --build
```

## Quick start

From repo root:

```bash
cd infra
docker compose up --build
```

Open:

- Frontend: `http://localhost:5173`
- Keycloak: `http://localhost:8080`
- API docs: `http://localhost:8000/docs`

## Default Keycloak bootstrap

Realm import at `infra/keycloak/realm-export.json` is **copied into the Keycloak image** at build time (`infra/keycloak/Dockerfile`). That avoids Docker Desktop macOS bind-mount bugs (`mkdir /host_mnt/.../realm-export.json: file exists`). After you edit `realm-export.json`, rebuild Keycloak: `docker compose build keycloak --no-cache` (or `docker-compose build keycloak`).

Realm contents:

- Realm: `pki`
- Clients:
  - `pki-frontend` (public + PKCE)
  - `pki-api` (confidential + service account)
- Roles:
  - `pki-admin`
  - `pki-operator`
  - `pki-auditor`
  - `pki-user`
- Test user:
  - username: `operator`
  - password: `operator123`

## Example API calls

Issue certificate:

```bash
curl -X POST http://localhost:8000/api/certificates/issue \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"common_name":"example.internal","sans":["www.example.internal"]}'
```

Fetch job status:

```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:8000/api/jobs/1
```

## Security notes

- Step CLI execution is isolated in the worker container
- No shell command strings, no `shell=True`
- CN/SAN inputs are validated in API and worker
- Mutating actions are audit logged
- Keep real secrets in secure environment stores before production