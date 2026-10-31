# Container

**Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.**

Container is a control plane for accounts, workspaces, projects, jobs, artifacts, model metadata, and evaluation records. It is not a model, reasoning engine, training framework, or inference runtime.

## What is in this repository

- FastAPI API with account registration and login.
- Workspaces, projects, owner authorization, and persistent job records.
- A limited worker for harmless demonstration jobs: demo.echo and demo.delay.
- Append-only job events, cancellation requests, and resumable event streaming.
- Project-scoped artifact upload/list/download with size limits and SHA-256 digests.
- Project-scoped model identities and metadata-only version records.
- Docker Compose development stack, PostgreSQL migrations, and GitHub Actions CI.
- Browser Studio for account, project, conversation, and system status workflows.
- An optional API gateway that can forward requests to an operator-configured OpenAI-compatible endpoint. The external provider performs inference; no model is bundled here.
- Hash-required immutable file snapshots and a frozen deterministic evaluation fixture, both covered by CI tests.

## What is not implemented

- No model or model architecture.
- No training loop or fine-tuning implementation.
- No production evaluation of a trained model.
- No checkpointing of trained weights.
- No real GPU/CPU job scheduler or worker fleet.
- No managed inference service, credential vault, or provider routing.
- No research ingestion, dataset preparation, or training-data pipeline.
- No production object storage, service SLA, or independent security certification.

The database-backed worker currently runs only the two demo task types. Hardware inventory is descriptive metadata, not a benchmark, compatibility check, allocator, or scheduler. Model registry entries are metadata; they do not download, execute, train, or serve model files.

## Development

Requirements: Python 3.11+, Docker Compose (for the full local stack).

1. Copy .env.example to .env.
2. Replace the development secrets with unique local values.
3. Run docker compose up --build.
4. Open http://localhost:8000/studio or http://localhost:8000/docs.

For API-only development, see services/api/README.md. Tests run with pytest from services/api. The frozen evaluation can also be run from the repository root with:

    python -m eval.runner --negative-control
    python -m eval.check_quarantine

Read CONTAINER_BUILD.md for the implementation contract, MODEL_STATUS.md for model boundaries, DEFERRED.md for intentionally excluded work, and docs/IMPLEMENTATION_STATUS.md for the tested feature checklist.

## Security boundary

Compose is for local development and binds service ports to loopback. Do not expose it directly to the public internet. Treat uploaded files, external repositories, model metadata, provider output, and job payloads as untrusted. No imported model file is executed by the metadata registry.

## License

Apache License 2.0. See LICENSE and NOTICE. External models, datasets, providers, and runtime engines retain their own licenses and terms.
