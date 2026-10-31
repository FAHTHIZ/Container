<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container

**Container is a free, local-first infrastructure control plane.** It manages
jobs, artifacts, snapshots, and deterministic evaluations on infrastructure
you control. It contains **no model** and is not a coding-agent harness. The
primary product path is intended to run on a phone or laptop without paid
services. Local model runtimes such as Ollama, llama.cpp, and LM Studio are the
preferred integrations; hosted providers are optional and never required.

The repository is in early development. The current server profile uses a
locally operated FastAPI/PostgreSQL stack. The dedicated phone profile
(SQLite, no Docker, checkpoint-resume) is planned but is **not implemented
yet**. Do not confuse the intended local-first product direction with shipped
mobile support.

## Project boundaries

Container is one of three separate projects:

| Project | Responsibility | Location |
|---|---|---|
| **Container** | Infrastructure control plane: job scheduling, artifact storage, snapshot provenance, and evaluation execution | This repository |
| **OASIS** | Coding-agent harness: tools, approvals, context management, provider adapters, and agent workflows | Separate repository |
| **Artemis** | Model architecture and learning system | Private project, outside this repository |

Container does not implement Artemis's model architecture or duplicate OASIS
harness logic. It provides infrastructure contracts that those separate
projects may call.

## Product principles

- **Local first.** The free, self-operated path is the primary deployment.
- **No paid dependency.** No subscription, required payment method, expiring
  free tier, or paid API is required to use the infrastructure layer.
- **Local models first.** Ollama, llama.cpp, and LM Studio are the preferred
  provider integrations. Third-party free gateways are optional conveniences.
- **Fail closed.** If a required validation cannot run, the operation stops.
- **Verifiable artifacts.** A snapshot or checkpoint must have a SHA-256 digest.
- **Evaluation before training.** The frozen evaluation and its negative
  control gate all future training work.
- **Honest status.** A source file or UI is not evidence that a feature is
  complete. A verified status requires a passing test.

## What exists in this repository today

The current codebase includes:

- FastAPI backend with versioned routes.
- Registration and login using Argon2 password hashing and signed access
  tokens.
- Workspaces, owner memberships, projects, and server-side authorization.
- Persistent job records, append-only job events, cancellation, and resumable
  server-sent event streams.
- A database-polling worker for harmless demonstration jobs.
- PostgreSQL configuration, isolated SQLite test support, and Alembic
  migrations.
- Bounded local artifact storage with SHA-256 metadata and authenticated,
  project-scoped upload/list/download operations.
- Project-scoped model identities and version metadata. The registry stores
  metadata; it does not contain model weights.
- A configurable OpenAI-compatible inference gateway. It forwards requests to
  an endpoint configured by the operator; it is not a bundled model.
- An initial snapshot-capture implementation that writes a content-addressed
  copy and stores a SHA-256 digest.
- A frozen JSONL evaluation fixture, pinned SHA-256, deterministic exact-match
  scorer, predictor interface, and negative-control implementation.
- A GitHub Actions workflow for API linting, JavaScript syntax validation,
  migrations, and tests.

These items describe code that exists. They do not mean every related phase
gate has passed.

## What is not complete

The following work must not be described as finished:

- Snapshot verification API, stored-file mutation detection, size metadata,
  and the Checkpoint extension.
- Repository-wide evaluation-data quarantine scan wired into CI.
- End-to-end eval_run job and hash-bearing result artifact.
- Provider capability registry and tests that suppress tool calls when a
  provider does not support them.
- Default local-provider selection in the inference gateway.
- Standalone phone profile, SQLite-first startup, no-Docker operation,
  checkpoint-resume, retention, retry, and job-size limits.
- Model training, model-weight import, production compute scheduling, and
  production mobile packaging.

There is no model in this repository. No training loop should be added until
the frozen eval and eval-job phases pass their gates.

See [implementation status](docs/IMPLEMENTATION_STATUS.md) for the
implementation inventory and [MODEL_STATUS.md](MODEL_STATUS.md) for the
model boundary and test-verification checklist.

## Compute and provider policy

The default deployment path is local and free. The current laptop/server
development profile uses services that the operator runs locally; it is not
a managed cloud deployment.

The local model path is the intended default:

1. Run a local model server such as Ollama, llama.cpp, or LM Studio.
2. Configure Container's compatible inference endpoint to point to that
   server.
3. Keep model files and artifacts on storage you control.

The gateway currently accepts a configured OpenAI-compatible endpoint. It
does **not yet automatically select Ollama as its default provider**. That
provider-default change is still required; do not claim that it has shipped.

Hosted or managed endpoints, if added later, must be optional, clearly
labelled, and opt-in. They must not be necessary to run the infrastructure
layer. There is no billing, subscription, quota-payment, or card-entry flow.

## Development setup: current server profile

The current server profile is for local development on a laptop or desktop.
It uses Docker Compose and PostgreSQL running under the developer's control.
These are local development dependencies, not a paid managed service.

1. Copy the **.env.example** file to **.env**.
2. Replace development secrets with unique local values.
3. Start the server profile with **docker compose up --build**.
4. Open the Studio at **http://localhost:8000/studio** or the API docs at
   **http://localhost:8000/docs**.

The current inference gateway needs an operator-configured compatible
endpoint. Set **CONTAINER_INFERENCE_BASE_URL**,
**CONTAINER_INFERENCE_MODEL**, and, only when required by that endpoint,
**CONTAINER_INFERENCE_API_KEY**. Without a configured provider, account and
control-plane functions can still be used, but chat correctly reports that
inference is not connected.

Do not expose development credentials or development ports to the public
internet.

## Run the API without Docker

The API can also be started directly with Python and a locally available
database. This is a server-development path; it is **not yet** the standalone
phone profile.

From **services/api**:

- Create and activate a virtual environment.
- Install with **python -m pip install -e ".[dev]"**.
- Set **CONTAINER_DATABASE_URL** and **CONTAINER_JWT_SECRET**.
- Run **alembic upgrade head**.
- Start **uvicorn container_api.main:app --reload**.

Run API tests from **services/api** with **pytest** and static checks with
**ruff check .**.

The planned phone profile will use SQLite and no Docker. It has not been
implemented; its requirements are listed in CONTAINER_BUILD.md.

## Evaluation and snapshots

The frozen evaluation lives under **eval/**. The runner verifies the pinned
dataset hash before parsing or scoring and includes a deterministic negative
control. This fixture tests evaluation plumbing; it is not a general model
benchmark and its score is not evidence of model quality.

The quarantine checker exists, but the CI workflow must still invoke it
against the repository's actual training-data directories before Phase C is
complete.

The snapshot creator currently hashes and stores a content-addressed copy.
The verification API, stored-file mutation test, size metadata, and Checkpoint
extension remain Phase B work. Until those tests pass, do not claim verified
snapshot recovery or checkpoint-resume.

See [CONTAINER_BUILD.md](CONTAINER_BUILD.md) for phase gates and the rules
governing future changes.

## Documentation

- [Build contract](CONTAINER_BUILD.md)
- [Model status](MODEL_STATUS.md)
- [Deferred scope](DEFERRED.md)
- [Architecture decisions](docs/DECISIONS.md)
- [Implementation status](docs/IMPLEMENTATION_STATUS.md)
- [Operations and local development](docs/OPERATIONS.md)
- [Security principles](docs/SECURITY.md)

## License

Apache License 2.0. See [LICENSE](LICENSE) and [NOTICE](NOTICE). Third-party
model weights, datasets, providers, connectors, and runtime engines retain
their own licenses and terms. Container's license does not relicense
external materials.
