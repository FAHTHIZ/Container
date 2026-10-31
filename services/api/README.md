<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container API

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

The FastAPI service owns accounts, workspaces, projects, model metadata, job records, artifact metadata, and job submission. The separate worker claims supported jobs from the database. No model architecture or learning algorithm is bundled here.

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
- train_run orchestrates a separately supplied trainer adapter. It verifies data/eval separation, loss output intervals, checkpoint artifacts and hashes, then evaluates the final checkpoint.

The train_run request requires a model_id and dataset_artifact_id in the same project, steps, loss_every, checkpoint_every, eval_path, and eval_hash. The dataset must be a supported UTF-8 text artifact. The worker verifies that it does not contain any exact frozen-evaluation question before the trainer starts.

The operator, not the job submitter, configures the external adapter:

- CONTAINER_TRAIN_RUNNER: trusted Python entry point in module.path:function_name form. Blank by default.
- CONTAINER_TRAIN_ADAPTER_PATH: optional operator-provided directory containing the adapter package. Leave blank when the package is installed in the worker's Python environment. Mount adapter code read-only in container deployments.
- CONTAINER_TRAIN_TIMEOUT_SECONDS: trainer subprocess time limit, default 3,600 seconds.
- CONTAINER_EVAL_PREDICTOR: trusted evaluation entry point, required for train_run and eval_run.
- CONTAINER_EVAL_TIMEOUT_SECONDS: evaluation subprocess time limit, default 120 seconds.

The adapter must print one finite LOSS line at every requested loss interval. It must create a non-empty regular checkpoint file named checkpoint-step-00000100.bin at every requested checkpoint interval. Container stores each file with a SHA-256 digest and verifies the stored copy again. The final checkpoint is passed to the evaluation adapter through CONTAINER_EVAL_CHECKPOINT_PATH. Model-version metadata stores the final checkpoint hash and evaluation score together.

A local test can use the test-only adapter package from services/api/tests/training_fixtures and the checkpoint stub predictor in eval/. They emit fake values and dummy bytes; they are not models and their score is not evidence of model quality.

Trainer and evaluator adapters are trusted operator code, not a sandbox. A workspace member cannot select an adapter or command in a job payload. Never point the settings at user uploads or unreviewed modules. The current worker is a single host process; it is not a GPU scheduler or an isolated remote execution fleet. See TRAINING.md for the exact adapter contract and limitations.

## Artifact handling

Artifacts use generated immutable storage keys, never user-provided paths. The API records project/workspace ownership, filename metadata, media type, byte size, and SHA-256. Uploads are bounded by CONTAINER_MAX_ARTIFACT_BYTES; download authorization is checked against workspace membership.

The local filesystem adapter is for development. Production requires private object storage, ingress body limits, retention/deletion policy, backups, and operational monitoring.

## Model registry and snapshots

The model registry stores project-scoped identities and version metadata. It does not fetch model files, inspect tensors, perform inference, or include a learning algorithm. The train_run job may create a model version that points to the final checkpoint artifact and stores its SHA-256 plus frozen-evaluation score; this records external outputs, not a quality guarantee.

Snapshots are immutable file copies addressed by their SHA-256 digest. The database record is created only after the stored copy has been re-read and verified. A snapshot hash identifies bytes; it does not prove model quality.

## Current operational boundaries

The worker is a single database-polling process. eval_run and train_run execute trusted configured adapters on that worker host; this is not a GPU scheduler, worker fleet, or sandbox. Cancellation does not independently terminate an active child process; configured subprocess timeouts are the current execution bounds. The test trainer creates dummy checkpoint files only.

No bundled training loop, model-specific algorithm, automatic checkpoint resume, real GPU allocation, or production compute scheduler exists in this repository.
