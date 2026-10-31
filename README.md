# Container

**Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.**

Container is a control plane for accounts, workspaces, projects, jobs, artifacts, model metadata, snapshots, and evaluation records. It is not a model, reasoning engine, learning algorithm, or inference runtime.

## What is in this repository

- FastAPI API with account registration and login.
- Workspaces, projects, owner authorization, and persistent job records.
- A limited worker for harmless demonstration jobs: demo.echo and demo.delay.
- An eval_run job that invokes the frozen deterministic evaluation harness through a bounded subprocess and stores a SHA-256-bearing JSON report artifact.
- A train_run job that orchestrates an operator-configured external trainer, verifies loss intervals and checkpoint hashes, evaluates the final checkpoint, and stores checkpoint/evaluation metadata.
- Append-only job events, cancellation requests, and resumable event streaming.
- Project-scoped artifact upload/list/download with size limits and SHA-256 digests.
- Hash-required immutable file snapshots.
- Project-scoped model identities and metadata-only version records.
- Docker Compose development stack, PostgreSQL migrations, and GitHub Actions CI.
- Browser Studio for account, project, conversation, and system status workflows.
- An optional API gateway that can forward requests to an operator-configured OpenAI-compatible endpoint. The external provider performs inference; no model is bundled here.

## What is not implemented

- No model or model architecture.
- No model-specific learning algorithm or real trainer package is included.
- No evaluation result for an actual trained model; the built-in fixture only verifies plumbing.
- No real GPU/CPU scheduler or worker fleet.
- No managed inference service, credential vault, or provider routing.
- No research ingestion, general dataset preparation, or production training-data pipeline.
- No production object storage, service SLA, or independent security certification.

The database-backed worker runs demo tasks, eval_run, and train_run. The train_run job invokes only an operator-configured trusted Python adapter; the job payload cannot select code. The adapter runs on the worker host and is not sandboxed. The included test adapter writes dummy bytes and fixed example loss values; it is not a model trainer. Hardware inventory is descriptive metadata, not a benchmark, compatibility check, allocator, or scheduler.

## Development

Requirements: Python 3.11+, Docker Compose (for the full local stack).

1. Copy .env.example to .env.
2. Replace the development secrets with unique local values.
3. Leave evaluation and trainer adapter settings blank unless you have reviewed the adapter code and installed it in the worker environment.
4. Run docker compose up --build.
5. Open http://localhost:8000/studio or http://localhost:8000/docs.

For API-only development, see services/api/README.md. Tests run with pytest from services/api. The frozen evaluation can be run from the repository root with:

    python -m eval.runner --negative-control
    python -m eval.check_quarantine

Read TRAINING.md for the external trainer contract, CONTAINER_BUILD.md for the implementation contract, MODEL_STATUS.md for model boundaries, DEFERRED.md for intentionally excluded work, and docs/IMPLEMENTATION_STATUS.md for the tested feature checklist.

## Security boundary

Compose is for local development and binds service ports to loopback. Do not expose it directly to the public internet. Treat uploaded files, external repositories, model metadata, provider output, and job payloads as untrusted. Trainer and evaluator adapters are trusted operator code, not a sandbox; never point them at user uploads or unreviewed modules. No imported model file is executed by the metadata registry.

## License

Apache License 2.0. See LICENSE and NOTICE. External models, datasets, providers, and runtime engines retain their own licenses and terms.
