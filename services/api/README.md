<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container API

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

The FastAPI service owns accounts, workspaces, projects, model metadata, job records, artifact metadata, and job submission. The separate worker claims supported jobs from the database. There is no model, training loop, model-serving runtime, or real compute scheduler in this repository.

## Requirements

- Python 3.11 or newer.
- PostgreSQL for shared/deployed environments; SQLite is used for isolated unit tests.

## Install and run

From the repository root:

    python -m venv .venv
    . .venv/bin/activate
    python -m pip install -e "services/api[dev]"
    export CONTAINER_DATABASE_URL="sqlite:///./container.db"
    export CONTAINER_JWT_SECRET="replace-with-a-unique-secret-at-least-32-characters"
    alembic -c services/api/alembic.ini upgrade head
    uvicorn container_api.main:app --app-dir services/api/src --reload

In another terminal, start the worker from the repository root:

    PYTHONPATH=services/api/src python -m container_api.worker

API docs: http://127.0.0.1:8000/docs  
Browser Studio: http://127.0.0.1:8000/studio

## Test and lint

From services/api:

    python -m pip install -e ".[dev]"
    pytest
    ruff check . ../../eval
    node --check src/container_api/static/app.js

CI applies Alembic migrations to PostgreSQL before running tests.

## Job types

- demo.echo and demo.delay are harmless worker demonstrations.
- eval_run runs the frozen deterministic evaluation harness as a bounded subprocess and stores its result as a SHA-256-bearing JSON artifact.

The eval_run request requires a registered model_id belonging to the project, an eval_path inside the repository eval/ directory, and the expected eval_hash. The worker rechecks project ownership, constrains the path, verifies the pinned hash in the harness, enforces CONTAINER_EVAL_TIMEOUT_SECONDS, validates the result, and stores a report artifact.

The API and worker require the same operator-configured setting:

- CONTAINER_EVAL_PREDICTOR: trusted Python entry point in module.path:function_name form. It is deliberately blank by default. Do not let users supply this value per job.
- CONTAINER_EVAL_TIMEOUT_SECONDS: subprocess time limit, default 120 seconds.

For a local plumbing test only, set CONTAINER_EVAL_PREDICTOR=eval.stub_predictor:predict. That fixture returns fixed answers for the six frozen test questions. It is not a model, does not load model weights, and its score is not a model-quality result.

The adapter is trusted operator code, not a sandbox. Do not configure a module from an untrusted project or user upload. The evaluation subprocess receives a restricted environment and is not given the API process's inherited environment variables.

## Artifact handling

Artifacts use generated immutable storage keys, never user-provided paths. The API records project/workspace ownership, filename metadata, media type, byte size, and SHA-256. Uploads are bounded by CONTAINER_MAX_ARTIFACT_BYTES; download authorization is checked against workspace membership.

The local filesystem adapter is for development. Production requires private object storage, ingress body limits, retention/deletion policy, backups, and operational monitoring.

## Model registry and snapshots

The model registry stores project-scoped identities and metadata-only version records. It does not fetch model files, inspect tensors, perform inference, train, or serve weights.

Snapshots are immutable file copies addressed by their SHA-256 digest. The database record is created only after the stored copy has been re-read and verified. A snapshot hash identifies bytes; it does not prove model quality.

## Current operational boundaries

The worker is a single database-polling process. eval_run executes a trusted adapter on that worker host; this is not a GPU scheduler, worker fleet, isolated arbitrary-code service, or managed inference system. Job cancellation does not provide an independent process supervisor for an adapter that is already running; the configured subprocess timeout is the current execution bound.

No training or fine-tuning job type exists. Phase E must remain deferred until the frozen evaluation harness exists and passes its integrity and negative-control tests.
