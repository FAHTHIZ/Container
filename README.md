<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container

**An open-source platform for building, adapting, evaluating, running, and deploying AI systems.**

Container brings research and data preparation, model development, inference, agents, workflows, and application delivery into one coherent workspace. It uses hybrid execution: a phone can control projects and run compatible small workloads, while larger jobs are delegated to suitable local or remote workers.

> **Status: early development.** The current repository contains a working backend foundation and a first authenticated project/job workflow. It is not yet a complete or production-ready AI development platform.

## What Container is

Container is the platform and lifecycle manager, not one specific AI model. It will support importing models, adapting compatible models, evaluating model versions, serving them on compatible devices or remote infrastructure, and composing assistants, agents, workflows, and applications.

## Working today

- FastAPI backend with a versioned API and a first-party browser Studio at /studio.
- User registration and login using Argon2 password hashing and signed bearer access tokens.
- Workspaces, owner memberships, and projects with server-side membership checks.
- Persistent job records, resumable job event history, and project-scoped artifact uploads/downloads.
- Project-scoped model identities and version metadata with optional links to uploaded assets.
- Project-scoped model registry records and immutable version metadata linked to project assets.
- A separate worker process for the first demo job types, with cancellation.
- PostgreSQL support, SQLite for local tests, and Alembic migrations.
- Docker Compose development stack and GitHub Actions checks.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for the verified feature boundary.

## Product modules

- **Research and data:** source registry, permitted ingestion, provenance, dataset versioning, quality checks, and repeatable preparation.
- **Model lifecycle:** initial project-scoped model registry and version metadata are implemented; fine-tuning, evaluation suites, release gates, and inference are planned.
- **Inference:** pluggable local and remote runtimes, hardware compatibility checks, authenticated endpoints, and monitoring.
- **Agents and workflows:** scoped tools, workflow graphs, visible execution events, approval gates, and audit records.
- **Clients:** responsive web studio and Android-first client for control, monitoring, and compatible on-device workloads.

## Architecture

The first implementation is a modular monolith API with independently running workers. PostgreSQL is the source of truth for platform metadata and job state. Large datasets, checkpoints, and weights belong in object storage—not Git history.

Read:
- [System architecture](docs/ARCHITECTURE.md)
- [Delivery roadmap](docs/ROADMAP.md)
- [Security policy](SECURITY.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Operations and local development](docs/OPERATIONS.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)

## Run locally with Docker

1. Copy .env.example to .env.
2. Replace the development secrets with unique values.
3. Start with docker compose up --build.
4. Open the Studio at http://localhost:8000/studio or the API documentation at http://localhost:8000/docs.

The Studio currently supports sign-in, workspace/project management, demo jobs, live job-event monitoring, artifact upload/download, and a metadata-only model catalogue with version records. The Compose stack is for local development only. Do not expose its sample credentials or development configuration to the public internet.

## Run the API without Docker

Requirements: Python 3.11 or newer and a local database.

From services/api:
- Create and activate a virtual environment.
- Install with python -m pip install -e ".[dev]".
- Set CONTAINER_DATABASE_URL and CONTAINER_JWT_SECRET.
- Run alembic upgrade head.
- Start uvicorn with container_api.main:app --reload.

Run tests with pytest and static checks with ruff check ..

## Worker

Run the API and a separate worker process. From services/api, invoke python -m container_api.worker. Jobs are persisted in the database and claimed transactionally. The first worker handles demonstration jobs only; research, training, evaluation, and inference workers will be separate modules.

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Third-party model weights, datasets, connectors, and runtime engines retain their own licenses and terms; Container's license does not relicense external materials.
