<!-- SPDX-License-Identifier: Apache-2.0 -->

# Operations and Local Development

This guide describes the current development stack. It is not a production deployment guide for managed inference or compute.

## Docker Compose

1. Copy .env.example to .env.
2. Replace POSTGRES_PASSWORD and CONTAINER_JWT_SECRET with unique random values.
3. Leave CONTAINER_EVAL_PREDICTOR blank unless a trusted operator has reviewed an adapter. The eval.stub_predictor:predict adapter is for plumbing tests only.
4. Start with docker compose up --build.
5. Open API docs at http://localhost:8000/docs and Studio at http://localhost:8000/studio.
6. Stop with docker compose down. The named Postgres volume remains; docker compose down -v deletes that local development data.

Compose ports bind to loopback by default to avoid exposing development services on the LAN.

## Local Python setup

From the repository root:
- Create a virtual environment with Python 3.11 or newer.
- Install with python -m pip install -e "services/api[dev]".
- Set CONTAINER_DATABASE_URL to SQLite or PostgreSQL.
- Set CONTAINER_JWT_SECRET to a unique secret of at least 32 characters.
- Run alembic -c services/api/alembic.ini upgrade head.
- Start uvicorn container_api.main:app --app-dir services/api/src --reload.
- In a second process, start PYTHONPATH=services/api/src python -m container_api.worker.

## First API workflow

1. Register through POST /api/v1/auth/register.
2. Use the returned bearer token.
3. Read the created workspace through GET /api/v1/workspaces.
4. Create a project through POST /api/v1/workspaces/{workspace_id}/projects.
5. Submit a demo job through POST /api/v1/projects/{project_id}/jobs.
6. Inspect it through GET /api/v1/jobs/{job_id} and GET /api/v1/jobs/{job_id}/events.
7. Upload project assets through POST /api/v1/projects/{project_id}/artifacts and list them through GET /api/v1/projects/{project_id}/artifacts.
8. Download an artifact through GET /api/v1/artifacts/{artifact_id}/download.

The worker must be running for a queued job to execute.

## Frozen evaluation job

The optional eval_run job accepts a registered model ID, a repository-relative JSONL path under eval/, and the exact SHA-256 pin for that file. The worker rechecks project ownership and path restrictions, then executes eval.runner as a bounded subprocess. The result is stored in a JSON artifact whose SHA-256 is recorded in artifact metadata and the job result.

The API and worker must share these settings:

- CONTAINER_EVAL_PREDICTOR: trusted operator Python entry point, module.path:function_name. Blank by default; users cannot supply it in a job.
- CONTAINER_EVAL_TIMEOUT_SECONDS: maximum subprocess runtime in seconds (default 120).
- CONTAINER_ARTIFACTS_PATH: shared artifact directory; Compose mounts a shared volume.
- CONTAINER_MAX_ARTIFACT_BYTES: maximum report or upload size (default 100 MiB).

For local plumbing tests only, CONTAINER_EVAL_PREDICTOR=eval.stub_predictor:predict uses six fixed test answers. This is not a model adapter and its score is not evidence of model quality. A real adapter is trusted operator code, not a sandbox. Do not configure an adapter from an untrusted repository or user upload.

## Configuration

- CONTAINER_ENVIRONMENT: development or production.
- CONTAINER_DATABASE_URL: SQLAlchemy connection URL.
- CONTAINER_JWT_SECRET: unique signing key; the placeholder is rejected in production.
- CONTAINER_ALLOWED_ORIGINS: JSON array of browser origins permitted by CORS.
- CONTAINER_ACCESS_TOKEN_TTL_MINUTES: bearer-token lifetime.
- CONTAINER_WORKER_POLL_SECONDS: idle worker polling interval.
- CONTAINER_ARTIFACTS_PATH: local artifact directory; Compose mounts a persistent shared volume.
- CONTAINER_MAX_ARTIFACT_BYTES: maximum accepted artifact size per upload (default 100 MiB).
- CONTAINER_EVAL_PREDICTOR: operator-configured trusted evaluation adapter; blank by default.
- CONTAINER_EVAL_TIMEOUT_SECONDS: evaluation subprocess timeout (default 120 seconds).

## Current operational boundaries

- Back up PostgreSQL and test restoration before storing valuable project metadata.
- Local development stores artifacts in the configured persistent volume. Production should use durable private object storage; do not rely on a container's writable layer or put large weights/datasets in Git or relational rows.
- Keep API and worker credentials scoped separately when remote workers are introduced.
- Treat data files, downloaded content, model outputs, and tool outputs as untrusted.
- Do not expose interactive API docs or development ports publicly without a deployment-specific access policy.
- The worker is a single database-polling process. It runs harmless demo jobs and the bounded eval_run subprocess only.
- Eval adapter code is operator-trusted code; it is not sandboxed. Current cancellation does not independently terminate an active adapter; its configured timeout is the execution bound.
- No training loop, evaluation of trained weights, real GPU scheduling, managed inference deployment, or production compute scheduler exists in this repository.
- Docker Compose is a local development stack, not a production topology.

## Managed-service operations to add

Before managed users are onboarded, operators need documented procedures for inference-provider availability, capacity and queue management, model rollout/rollback, GPU worker provisioning, cost/quota enforcement, object-store lifecycle, incident response, data deletion, and regional privacy/data-residency requirements.
