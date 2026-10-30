<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container API

The API is the initial control plane for accounts, workspaces, projects, and persistent jobs.

## Requirements

- Python 3.11+
- PostgreSQL for shared/deployed environments; SQLite is supported for local tests and evaluation only.

## Install and run

From services/api:

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e ".[dev]"
    export CONTAINER_DATABASE_URL="sqlite:///./container.db"
    export CONTAINER_JWT_SECRET="replace-with-a-unique-secret-at-least-32-characters"
    alembic upgrade head
    uvicorn container_api.main:app --reload

In a second terminal, start the worker:

    python -m container_api.worker

API documentation: http://127.0.0.1:8000/docs

## Test and lint

    pytest
    ruff check .

The CI workflow also verifies that Alembic can apply the initial migration to an empty local database.

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
- POST /api/v1/jobs/{job_id}/cancel

Use the bearer token returned by registration/login. The only executable worker kinds are demo.echo and demo.delay. These are test jobs, not model training or external research operations.
