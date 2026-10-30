<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operations and Local Development

## Docker Compose

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and CONTAINER_JWT_SECRET with unique random values.
3. Start with docker compose up --build.
4. Open the API docs at http://localhost:8000/docs.
5. Stop with docker compose down. The named Postgres volume remains; docker compose down -v deletes that local development data.

Compose ports bind to loopback by default to avoid exposing development services on the LAN.

## Local Python setup

From services/api:
- Create a virtual environment with Python 3.11 or newer.
- Install with python -m pip install -e ".[dev]".
- Set CONTAINER_DATABASE_URL to SQLite or PostgreSQL.
- Set CONTAINER_JWT_SECRET to a unique secret of at least 32 characters.
- Run alembic upgrade head.
- Start uvicorn container_api.main:app --reload.
- In a second process, start python -m container_api.worker.

## First API workflow

1. Register through POST /api/v1/auth/register.
2. Use the returned bearer token.
3. Read the created workspace through GET /api/v1/workspaces.
4. Create a project through POST /api/v1/workspaces/{workspace_id}/projects.
5. Submit a demo job through POST /api/v1/projects/{project_id}/jobs.
6. Inspect it through GET /api/v1/jobs/{job_id} and GET /api/v1/jobs/{job_id}/events.

The worker must be running for a queued job to execute.

## Configuration

- CONTAINER_ENVIRONMENT: development or production.
- CONTAINER_DATABASE_URL: SQLAlchemy connection URL.
- CONTAINER_JWT_SECRET: unique signing key; the placeholder is rejected in production.
- CONTAINER_ALLOWED_ORIGINS: JSON array of browser origins permitted by CORS.
- CONTAINER_ACCESS_TOKEN_TTL_MINUTES: bearer-token lifetime.
- CONTAINER_WORKER_POLL_SECONDS: idle worker polling interval.

## Operational boundaries

- Back up PostgreSQL and test restoration before storing valuable project metadata.
- Put large model weights, checkpoints, and datasets in object storage, not the source repository/database.
- Keep API and worker credentials scoped separately when remote workers are introduced.
- Treat data files, downloaded content, model outputs, and tool outputs as untrusted.
- Do not expose interactive API docs or development ports publicly without a deployment-specific access policy.
- The current worker is a demonstration runner. Do not schedule training jobs or arbitrary downloaded code through it.
