<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — System Architecture

**Status:** implementation direction. Shipped components are distinguished from planned modules in the implementation-status document.

## 1. Product boundary

Container manages the lifecycle around AI systems. It is not itself a single foundation model. It is intended to import models, adapt compatible models, prepare and version data, evaluate model changes, run inference, orchestrate agents/workflows, and package applications.

The core product is the control plane: identity, workspaces, projects, registries, durable jobs, artifacts, permissions, events, and deployments. Expensive computation belongs in isolated workers and serving runtimes.

## 2. System topology

Start with a modular monolith API plus independently running worker processes. Do not split into microservices until scale, security, or operational constraints make a separate service necessary.

Clients:
- Web Studio: responsive project and lifecycle workspace.
- Android client: account/project control, job monitoring, approvals, and compatible local inference.
- CLI: automation and reproducible developer workflows.

Control plane:
- FastAPI application with versioned APIs.
- Domain modules: identity/access, workspaces/projects, data, models, jobs, evaluation, agents, workflows, deployments.
- PostgreSQL: metadata, ownership, job state, event history, and transactional records.
- Alembic: versioned database changes.
- Server-sent events (SSE) initially for job progress and events.

Execution plane:
- Research worker: source adapters, acquisition policy, provenance, and rate limits.
- Data worker: parsing, cleaning, deduplication, filtering, validation, and dataset manifests.
- Training worker: resource checks, fine-tuning, checkpoints, logs, and adapter artifacts.
- Evaluation worker: repeatable benchmark suites, comparisons, and regression gates.
- Inference runtimes: local and remote adapters.
- Agent/workflow workers: typed tools, scoped permissions, approvals, and audit events.

Storage:
- PostgreSQL for relational metadata and small control records.
- S3-compatible object storage for dataset files, model weights, adapters, checkpoints, evaluation reports, and build artifacts.
- Local filesystem adapter for development only.
- Git for code, schemas, small config, and reproducible manifests—not large datasets or model weights.

## 3. High-level data flow

    Android / Web / CLI
             |
       HTTPS API + SSE
             |
      FastAPI Control Plane
       |      |       |
    Identity Projects Jobs ---- PostgreSQL
       |      |       |
       +--- domain services ---+
                    |
              Job Dispatcher
                    |
       +------------+------------+
       |            |            |
    Research      Training    Evaluation
     Worker        Worker       Worker
       |            |            |
       +-------- Artifact Store -+
                    |
        Runtime Adapter Interface
              /             \
       llama.cpp             vLLM
       local/device        GPU serving
              \             /
          Agents / Workflows / Apps

The first committed worker uses database polling and handles demo tasks only. A dedicated broker, transactional outbox, multi-worker scheduler, and distributed workflow engine are later scale steps—not hidden assumptions.

## 4. Technology choices and boundaries

| Layer | Direction | Boundary / rationale |
|---|---|---|
| API | FastAPI + Pydantic | Typed Python HTTP control plane and request validation. |
| ORM | SQLAlchemy 2.x | Explicit transactions and relational mapping; each request/worker unit gets its own session. |
| Migrations | Alembic | Versioned schema evolution; no ORM auto-create in deployed environments. |
| Metadata DB | PostgreSQL | Transactional source of truth for identity, ownership, job state, and event records. |
| Local tests | SQLite | Fast isolated tests; production-specific behavior must also be checked on PostgreSQL. |
| Initial jobs | Database-backed polling worker | Simple, inspectable first vertical slice with conditional claims. |
| Later task delivery | Celery with Redis or RabbitMQ | Consider after measuring queue volume and worker requirements. Handlers must be idempotent; retry and acknowledgement semantics must be explicit. |
| Long workflows | Temporal or LangGraph | Temporal for durable business processes; LangGraph for stateful agent flows. They solve different orchestration problems. |
| Training | PyTorch + Hugging Face Transformers/PEFT/TRL | Begin with supported LoRA/QLoRA fine-tuning; full pretraining is a separate compute-intensive undertaking. |
| Evaluation | Versioned first-party suites; consider MLflow for tracking | Keep evaluation definitions, datasets, baselines, and release gates portable. |
| Local inference | llama.cpp adapter | GGUF and supported CPU/GPU/hybrid backends, gated by device capability. |
| GPU inference | vLLM adapter | High-throughput serving for supported accelerators/models; always place behind Container's authenticated gateway. |
| Artifacts | S3-compatible store + development filesystem adapter | Durable large objects and hashes; never store weights in normal Git history. |
| Observability | OpenTelemetry traces, metrics, and logs | Correlate API request, job, worker attempt, tool call, and model operation. |
| Web | React + TypeScript | Main cross-device Studio. |
| Android | Kotlin + Jetpack Compose | Native mobile client with secure device storage and lifecycle-aware controls. |

External projects are adapters, not the domain model. Their licenses, model licenses, data terms, and supported platform constraints must be checked independently before bundling or redistributing anything.

## 5. Domain model

### Identity and access
Users, workspaces, workspace memberships, roles, sessions, scoped API credentials, and audit records. Authorization is server-side and resource-scoped. A caller-supplied workspace ID never grants access on its own.

### Projects
Projects group sources, dataset versions, models, evaluations, jobs, workflows, and deployments. Each resource carries workspace ownership. Deletion and archival follow an explicit retention policy.

### Sources and datasets
A source record stores canonical origin, source type, access method, retrieval timestamp, terms/license assessment, attribution, integrity hash, and acquisition configuration. Dataset versions are immutable manifests over artifacts and processing lineage. Ingestion is limited to permitted sources and governed by terms, privacy, rate limits, and deletion obligations.

### Models and versions
A model is an identity/lineage record. A model version points to immutable weights/adapter/tokenizer/config artifacts, hashes, source revision, license metadata, quantization, training run, and evaluation status. Imported and adapted models share the registry abstraction.

### Jobs and events
A job has a type, validated specification, workspace/project, submitter, status, attempt count, resource request, cancellation state, timestamps, and artifact references. Events are append-only and contain schema version, timestamp, identifiers, and safe payloads. Secrets and sensitive raw inputs are excluded from logs/events.

Initial state transitions:
- queued -> running or cancelled
- running -> succeeded, failed, or cancelled
- retry is an explicit operation with an auditable attempt
- terminal states are immutable except through an explicit retry relation

Workers are separate processes. They validate job type, claim work transactionally, enforce resource limits, and make effects idempotent. The first demo runner does not execute arbitrary code.

### Evaluation and release
Evaluation suites are versioned with exact data, prompts/configuration, metric definitions, and scoring code. Results attach to immutable model versions. Release rules compare against a baseline and apply regression thresholds; an experiment is not an improvement until measured. Failed candidates are not automatically promoted.

### Agents and workflows
An agent is a policy-bound runtime configuration: model/provider, instructions, tool allowlist, scopes, budgets, and approval rules. A workflow is a versioned graph of typed nodes with validated inputs/outputs. Tool execution is server-authorized, audited, rate-limited, and subject to approval for sensitive or irreversible effects.

### Inference and deployments
A runtime adapter exposes a stable Container interface while translating to local llama.cpp or remote vLLM (or another compatible provider). Deployments reference immutable model versions/config. A trusted gateway handles authentication, rate limits, request limits, network isolation, and audit. Do not assume a serving engine's own API key protects every endpoint; validate each runtime's security surface.

## 6. Job execution evolution

Phase 1: database-backed jobs with worker polling, conditional state claims, persistent events, cancellation, and demo handlers.

Phase 2: introduce a broker when queue volume, worker count, or scheduling pressure justifies it. Use a transactional outbox so database commit and message publication cannot diverge. Use idempotency keys and bounded retries. Acknowledgement/re-delivery behavior must be explicit.

Phase 3: add a durable workflow engine for jobs involving timers, human approvals, external callbacks, compensation, or multi-step recovery. Keep agent state graphs distinct from general business process orchestration.

## 7. Data and model lifecycle

1. Register a source and record terms, provenance, and retrieval configuration.
2. Ingest through an approved adapter with bounded network access and rate limits.
3. Scan, parse, normalize, deduplicate, filter, and validate in isolated workers.
4. Publish an immutable dataset manifest with content hashes and lineage.
5. Start a training/evaluation job referencing exact dataset and code revisions.
6. Store logs/checkpoints/adapters/reports in object storage and record hashes.
7. Register the candidate model version.
8. Evaluate against versioned suites and guardrails.
9. Promote only if required checks pass; keep baseline and rollback history.

## 8. Compute strategy

Container is hybrid:
- Phone: control client, monitoring, approvals, light preprocessing, and inference only when model/runtime/hardware checks pass.
- Laptop/desktop: development, local inference, quantization, and modest adaptation supported by available CPU/GPU/RAM.
- Remote worker: larger training and high-throughput inference on suitable accelerators.

Every compute request needs a resource profile: device class, runtime/backend, CPU/GPU memory, system RAM, disk, accelerator, estimated artifact size, and compatibility constraints. Container must explain a mismatch rather than silently attempting an unsupported workload. A phone is not presented as capable of training frontier-scale models.

## 9. Security architecture

- Least-privilege service identities and per-job worker scopes.
- Strict workspace isolation tests for every resource family.
- Secret manager/encrypted secret storage; never secrets in source, logs, or events.
- Sandboxed workers with CPU, memory, disk, time, and network limits.
- Treat datasets, downloaded files, model outputs, and tool output as untrusted data, not privileged instructions.
- Verify artifact hashes and expected type/size before loading.
- Human approval for tools with write, delete, account, deployment, or other sensitive side effects.
- TLS, CORS allowlists, rate limiting, secure sessions, and audit coverage.
- Security review and backup/restore drills before production.

## 10. API families

- /api/v1/auth
- /api/v1/workspaces
- /api/v1/projects
- /api/v1/jobs
- /api/v1/sources
- /api/v1/datasets
- /api/v1/models
- /api/v1/evaluations
- /api/v1/agents
- /api/v1/workflows
- /api/v1/deployments

Stable REST endpoints manage resources. SSE streams job/workflow events. WebSockets are reserved for genuinely bidirectional interactions.

## 11. Reference documentation

- FastAPI security: https://fastapi.tiangolo.com/tutorial/security/oauth2-jwt/
- SQLAlchemy sessions and transactions: https://docs.sqlalchemy.org/en/20/orm/session_basics.html
- Celery task semantics/idempotency: https://docs.celeryq.dev/en/stable/userguide/tasks.html
- Hugging Face PEFT: https://huggingface.co/docs/peft/index
- vLLM serving: https://docs.vllm.ai/en/latest/serving/openai_compatible_server/
- llama.cpp: https://github.com/ggml-org/llama.cpp
- Apache License application guidance: https://www.apache.org/legal/apply-license

## 12. Quality gates

Every module needs unit tests, adapter integration tests, API contract tests, authorization/isolation tests, cancellation/retry/failure tests, migration verification, dependency checks, and operator documentation. A feature is not complete because its screen exists or an endpoint returns mocked data.
