<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container API

The API is the control plane for accounts, workspaces, projects, jobs, and project artifacts.

## Requirements

- Python 3.11 or newer.
- PostgreSQL for shared/deployed environments; SQLite is used for isolated unit tests.

## Install and run

From services/api:

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev]"
    export CONTAINER_DATABASE_URL="sqlite:///./container.db"
    export CONTAINER_JWT_SECRET="replace-with-a-unique-secret-at-least-32-characters"
    alembic upgrade head
    uvicorn container_api.main:app --reload

In another terminal, start the worker:

    python -m container_api.worker

API docs: http://127.0.0.1:8000/docs
Browser Studio: http://127.0.0.1:8000/studio

## Test and lint

    pytest
    ruff check .
    node --check src/container_api/static/app.js

CI also applies the Alembic migrations to a real PostgreSQL service before running tests.

## Initial endpoints

- POST /api/v1/auth/register
- POST /api/v1/auth/login
- GET /api/v1/auth/me
- GET and POST /api/v1/workspaces
- GET and POST /api/v1/workspaces/{workspace_id}/projects
- GET /api/v1/projects/{project_id}
- POST /api/v1/projects/{project_id}/jobs
- GET /api/v1/projects/{project_id}/jobs
- GET /api/v1/jobs/{job_id}
- GET /api/v1/jobs/{job_id}/events
- GET /api/v1/jobs/{job_id}/events/stream
- POST /api/v1/jobs/{job_id}/cancel
- GET and POST /api/v1/projects/{project_id}/artifacts
- GET /api/v1/artifacts/{artifact_id}/download
- GET and POST /api/v1/projects/{project_id}/models
- GET /api/v1/models/{model_id}
- GET and POST /api/v1/models/{model_id}/versions
- GET /api/v1/models/{model_id}/versions/{version_id}

Use the bearer token returned by registration/login. The only worker job types are demo.echo and demo.delay; these are harmless demonstration tasks, not model training or external research.

## Artifact handling

Artifacts are stored using generated immutable storage keys, not user-provided filenames. The API records project/workspace ownership, filename metadata, declared media type, byte size, and SHA-256 digest. Uploads are bounded by CONTAINER_MAX_ARTIFACT_BYTES. Download authorization is checked against workspace membership.

The local filesystem adapter is for development. Production needs private object storage, ingress request-body limits, retention/deletion policy, backups, and operational monitoring.

## Model registry

The initial registry stores project-scoped model identities and immutable version metadata. A version may reference one artifact already uploaded to the same project. Source URI and license ID are metadata only; the API does not fetch external model files, inspect weight contents, perform compatibility checks, train, evaluate, or serve models. Those capabilities have separate roadmap milestones.
