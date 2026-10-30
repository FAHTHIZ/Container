<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container API

The API is the initial control plane for accounts, workspaces, projects, and persistent jobs.

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

## Test and lint

    pytest
    ruff check .

CI also applies the Alembic migration to a real PostgreSQL service before running tests.

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

Use the bearer token returned by registration/login. The only worker job types are demo.echo and demo.delay; these are safe demonstration tasks, not model training or external research.
