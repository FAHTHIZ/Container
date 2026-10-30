<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container

**A personal AI facility, operated through one conversation.**

Container gives individuals one place to connect models, create assistants and agents, research information, organize knowledge and datasets, train and evaluate models, and run AI workloads. Its interface is intentionally simple: one chat is the main workspace, while a small interactive Core reveals the facility's activity and system status.

Container includes its own first-party intelligence layer. In the managed experience, that layer is available immediately through Container-managed inference; users do not need to bring an API key just to begin. Users can also connect their own model providers, hosted endpoints, local model servers, and imported models.

> **Development status: early development.** The repository now includes the conversation-first browser shell, animated Core panel, authenticated OpenAI-compatible inference gateway, public Hugging Face repository metadata inspection/registration, PWA shell, authentication, artifacts, jobs and model metadata. Managed inference, actual weight imports, training, research automation, evaluation and production compute remain unfinished.

## Product principles

- **One conversation, not a maze of tabs.** People describe what they want to do. Container presents the relevant controls and evidence in context.
- **AI is built in.** Container has a first-party intelligence layer, model gateway, orchestration, memory, and agent runtime. External providers are optional integrations, not the product's only source of intelligence.
- **Cloud-first hybrid compute.** A user's phone or ordinary laptop is primarily a control surface. Larger workloads run on managed remote workers by default. Connecting personal or third-party compute is optional.
- **Start with a URL or a file.** Users can submit supported model repository URLs, direct file URLs, ZIP archives, local files, or hosted/local inference endpoints. Container inspects and validates the source before importing or connecting it.
- **Works across devices.** Browser, Android, and desktop clients share one account, facility, API, and project history.
- **Progressive disclosure.** Advanced training, routing, evaluation, data, and security controls exist without becoming permanent navigation clutter.
- **Inspectable and safe execution.** Long-running work is visible, cancellable where possible, resource-bounded, auditable, and evaluated before promotion.

## What people can do in Container

- **Use built-in intelligence:** ask questions, plan work, search permitted web sources, operate tools, and coordinate jobs.
- **Connect and import models:** inspect repositories and files, connect hosted endpoints, register local model servers, and organize model versions.
- **Build assistants and agents:** configure instructions, models, tools, memory, scopes, budgets, schedules, approvals, and reusable workflows.
- **Research and curate knowledge:** search the web, papers, repositories, and approved sources; retain provenance; create searchable knowledge collections.
- **Prepare datasets:** import, clean, deduplicate, classify, validate, version, and trace source lineage.
- **Train and adapt models:** run supported fine-tuning and other training jobs on compatible managed or connected compute.
- **Evaluate models and agents:** compare versions, run repeatable benchmarks, test regressions, and gate releases.
- **Run and deploy models:** use compatible local or remote inference runtimes, authenticated endpoints, monitoring, and rollback.
- **Work with multimodal systems:** connect supported image, audio, speech, video, document, and other modality-specific models and tools.
- **Manage the facility:** inspect jobs, resource usage, storage, provider health, credentials, permissions, events, and costs.

The capability catalog is internal architecture. It does not prescribe a separate page or tab for every capability. The primary experience remains the conversation and its contextual task views.

## The Core

A compact, non-human system visualization sits in a corner of the conversation. Opening it reveals a contextual activity panel: current jobs, research activity, model/provider health, compute state, recent events, and notifications. The visual direction is a restrained cinematic systems interface—concentric geometry, diagnostic rings, fine telemetry, and subtle blue/cyan light—not a human avatar.

## Compute model

Container is **cloud-first and hybrid**:

- Managed remote compute is the default for work that exceeds ordinary device capabilities.
- Phones can start work, upload files, follow progress, review results, and approve sensitive actions without acting as training servers.
- Desktop and user-owned machines may optionally connect as local workers for supported tasks.
- External compute providers can be connected through adapters.
- Work continues remotely when a mobile app closes or a device disconnects, subject to the job's lifecycle and service availability.

Remote GPU time, storage, networking, and managed inference have real costs. Container must show estimates and usage, enforce quotas, and require the user's consent for chargeable work. It must not imply unlimited free cloud compute.

## Clients and distribution

The target is one shared product available as:
- A responsive browser app and installable web experience.
- An Android app distributed as a signed APK for direct installation and through the appropriate store publishing format.
- Desktop installers for Windows, macOS, and Linux.
- An optional self-hosted/server deployment for users who want to operate their own infrastructure.

All clients use the same versioned backend APIs and account/facility model. Native packaging and local-worker integration are implementation choices to validate; they must not create divergent products.

## What works today

- FastAPI backend with versioned routes and a first-party browser Studio at `/studio`.
- Registration/login with Argon2 password hashing and signed bearer access tokens.
- Workspaces, owner memberships, projects, and server-side workspace authorization.
- Persistent job records, append-only job events, cancellation, and resumable SSE event streams.
- Separate database-polling worker for harmless demonstration job types.
- PostgreSQL configuration, isolated SQLite tests, and Alembic migrations.
- Bounded immutable local artifact storage with SHA-256 metadata and authenticated project-scoped upload/list/download.
- Project-scoped model identities and immutable version metadata; the registry is metadata-only.
- Docker Compose development stack and GitHub Actions checks.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for the exact committed boundary. A green CI run validates the checks in that workflow; it does not mean the full product is complete or production-ready.

## Documentation

- [Product vision and experience](docs/PRODUCT_VISION.md)
- [System architecture](docs/ARCHITECTURE.md)
- [Built-in intelligence and research](docs/INTELLIGENCE.md)
- [Model import and connection](docs/MODEL_IMPORT.md)
- [Compute and cost model](docs/COMPUTE.md)
- [Clients and distribution](docs/CLIENTS.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Delivery roadmap](docs/ROADMAP.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Operations and local development](docs/OPERATIONS.md)
- [Security principles](docs/SECURITY.md)
- [Repository security policy](SECURITY.md)

## Run locally for development

1. Copy `.env.example` to `.env`.
2. Replace development secrets with unique values.
3. Start with `docker compose up --build`.
4. Open the Studio at `http://localhost:8000/studio` or API documentation at `http://localhost:8000/docs`.

The current Studio opens into the chat-first experience. Configure an OpenAI-compatible inference endpoint to receive real model responses. Hugging Face URL inspection currently records repository metadata only; it does not download model weights. The legacy project/job/artifact tools remain available in the backend APIs. Compose is for local development only; do not expose development credentials or ports to the public internet.

## Run the API without Docker

Requirements: Python 3.11 or newer and a local database.

From `services/api`:
- Create and activate a virtual environment.
- Install with `python -m pip install -e ".[dev]"`.
- Set `CONTAINER_DATABASE_URL` and `CONTAINER_JWT_SECRET`.
- Run `alembic upgrade head`.
- Start `uvicorn container_api.main:app --reload`.

Run tests with `pytest` and static checks with `ruff check .`. See [API development instructions](services/api/README.md).

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Third-party model weights, datasets, providers, connectors, and runtime engines retain their own licenses and terms. Container's license does not relicense external materials.


## Current interactive build

After starting the API, open `/studio`, create an account, and use the conversation-first workspace. The chat gateway supports any configured OpenAI-compatible inference service. Public Hugging Face model URLs can be inspected and registered from the composer; this is metadata inspection, not a model-weight download.

For local Docker Compose, copy `.env.example` to `.env` and configure:

- `CONTAINER_INFERENCE_BASE_URL`
- `CONTAINER_INFERENCE_MODEL`
- `CONTAINER_INFERENCE_API_KEY` (only if required by the selected endpoint)

Then run `docker compose up --build`. Without an inference endpoint, account creation and the facility UI work, but chat correctly reports that intelligence is not connected. A managed default inference service is still required for a zero-configuration hosted product.

Hardware placement, sizing assumptions, and CPU/GPU scheduling principles are documented in [Hardware Strategy](docs/HARDWARE_STRATEGY.md).
