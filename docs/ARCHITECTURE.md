<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — System Architecture

**Status:** target architecture and implementation direction. The shipped boundary is recorded in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## 1. Architectural definition

Container is an AI-powered facility with a conversation-first client. It is not a single model or a single inference endpoint. It combines a first-party intelligence layer, pluggable model/provider adapters, domain services, durable execution workers, storage, and client applications.

The user should experience one conversation and one Core activity panel. Internally, capabilities remain modular and independently testable.

The architecture is **cloud-first hybrid**: managed remote inference and compute are the default for users without capable hardware. Local and third-party compute are optional resource providers, not prerequisites.

## 2. System boundaries

### Client and experience layer

- Responsive browser application and installable web experience.
- Android application distributed through signed app packages/store publishing.
- Desktop application for Windows, macOS, and Linux.
- Optional self-hosted web/server deployment.
- One versioned API and one account/facility model across clients.
- Conversation shell, contextual task surfaces, upload/URL handling, and the interactive Core panel.

Clients are not training schedulers. They submit requests, display progress, collect approvals, and optionally bridge to user-owned hardware when explicitly configured.

### Container Intelligence layer

This is a first-party product capability and must be available in the managed experience from first use.

- **Conversation orchestrator:** maintains turns, context, attachments, task state, and streaming responses.
- **Model gateway and router:** selects the configured default model or an authorized alternate based on task, capability, availability, policy, and budget.
- **Planning and tool orchestration:** turns requests into typed task plans and invokes authorized Container capabilities.
- **Agent runtime:** runs policy-bound agents with explicit model, tools, memory, budgets, and approval requirements.
- **Memory and retrieval:** retrieves relevant conversation/project knowledge and records permitted user-approved memory.
- **Provider registry:** manages managed inference, user-supplied API providers, hosted endpoints, and local runtime adapters.
- **Policy and evaluation hooks:** validate tool permissions, enforce limits, record events, and evaluate outcomes.

The first-party intelligence feature includes a real configured inference backend. The orchestration code alone is not a reasoning model. Managed installations provision a Container-managed default inference service. Self-hosted installations must configure a compatible provider or local inference backend. External providers are optional for managed users and replaceable through the gateway.

### Control plane

Begin with a modular FastAPI application and independently running workers. Do not split into microservices until measured throughput, security boundaries, or deployment needs justify it.

- Versioned HTTP APIs and server-sent event streams.
- Identity, workspaces, ownership, permissions, and sessions.
- Conversation/task records, projects, registries, providers, sources, datasets, models, agents, evaluations, and deployments.
- Durable jobs, append-only events, idempotency, cancellation, approvals, quotas, and audit records.
- PostgreSQL as the source of truth for relational state.
- Alembic for schema migrations.

### Execution plane

Long-running or resource-intensive tasks run outside API request processes:
- Conversation/model inference workers.
- Provider and model import workers.
- Web research and permitted source-ingestion workers.
- Data preparation and quality workers.
- Training and fine-tuning workers.
- Evaluation and benchmark workers.
- Agent and workflow workers.
- Deployment and inference-serving workers.

The initial database-polling worker is for harmless demonstration jobs only. A broker, leases/heartbeats, retry policies, and durable workflow orchestration are staged additions.

### Compute plane

A capability-aware scheduler routes work among:
1. Container-managed cloud CPU/GPU workers (default).
2. Explicitly connected external cloud compute.
3. Optional user-owned desktop/server workers.
4. Compatible on-device execution for small supported workloads.

A phone is primarily a control surface. The system must not silently consume a user's battery, storage, mobile data, or device compute for heavy work.

### Storage plane

- PostgreSQL: users, ownership, job/task metadata, configuration, events, indexes, manifests, and lineage.
- Private object storage: imported files, model weights, adapters, datasets, checkpoints, logs, evaluation artifacts, and reports.
- Search indexes: full-text and, where useful, vector/semantic retrieval; indexes are rebuildable from authoritative source data.
- Local filesystem adapter: development and first vertical slice only.
- Git: source code, migrations, small configuration, and reproducible manifests—not model weights or datasets.

## 3. Logical topology

    Browser / Android / Desktop
              |
       HTTPS API + SSE
              |
      Conversation Experience
              |
       Container Intelligence
       |       |       |       |
     Model   Planner  Memory  Provider
     Gateway / Agents / Tools Registry
              |
        FastAPI Control Plane
       |       |        |       |
   Identity  Projects  Models  Jobs
       |       |        |       |
       +------ PostgreSQL -------+
              |
        Job Dispatcher
              |
     Capability-aware Scheduler
       |        |        |       |
    Research  Training  Eval   Inference
      Worker   Worker   Worker   Worker
       |        |        |       |
       +------ Private Artifact Store
              |
       Managed / External / Optional
       User-owned Compute Backends

All resource access remains authorized in the control plane. Workers receive short-lived, scoped job credentials rather than broad user credentials.

## 4. Domain model

### Personal facility and ownership

A user account owns a default personal facility/workspace. Projects organize related conversations, sources, datasets, models, agents, jobs, and deployments. Workspace and project IDs are never authorization by themselves; every operation checks membership and role server-side.

The schema should allow future team memberships and scoped roles, but the first-run UX is individual-first.

### Conversations and tasks

A conversation belongs to a user/facility and may be associated with a project. Turns reference attachment metadata, model/provider use, tool calls, citations, and task/job IDs. Sensitive content is not copied into general-purpose event logs. User-configurable retention and deletion apply to conversation data.

A task is a durable unit of requested work. It has a type, validated specification, creator, authorization context, state, progress events, cost/resource budget, cancellation behavior, and result/artifact references.

### Models and versions

A model is an identity and lineage record. An immutable version records its source, revision, license/provenance, architecture, tokenizer/config files, weights/artifact hashes, quantization, runtime compatibility, training run, and evaluation status. Imported, connected, adapted, and trained models share the registry abstraction but retain their source and lifecycle distinctions.

### Providers and endpoints

A provider record describes an inference or compute service, its capabilities, authentication reference, health, limits, routing policy, and terms. Secret values live in a dedicated secret store and are never returned in normal API responses. Hosted endpoints and local runtime endpoints have different connectivity and security requirements.

### Sources and datasets

Source records store canonical origin, source class, retrieval time, terms/license assessment, attribution, integrity hash, and ingestion configuration. Dataset versions are immutable manifests over artifacts and processing lineage.

### Jobs, events, and approvals

Job state transitions are validated and durable. Events are append-only and schema-versioned. Retries create auditable attempts; terminal results are not silently overwritten. Sensitive actions use explicit approval records linked to the exact proposed action and its authorization context.

### Agents and workflows

An agent is a policy-bound configuration: model/provider, instructions, allowed tools, data scopes, memory policy, budget, rate limits, and approval rules. A workflow is a versioned graph of typed nodes with validated inputs/outputs. Agent-generated plans do not grant permissions.

## 5. Primary flows

### Conversation request

1. Authenticate the user and resolve facility/project scope.
2. Load only permitted conversation and knowledge context.
3. Classify intent and determine whether a model response, tool, or durable job is required.
4. Build a typed plan and check permissions, budget, data scope, and required approval.
5. Route inference through the model gateway.
6. Execute tools/jobs in isolated workers.
7. Stream progress and cite results where source-backed.
8. Store required outputs and audit metadata; apply retention settings.

### Model connection/import

1. Classify input as repository, file URL, archive, local file, hosted endpoint, or local runtime endpoint.
2. Validate network destination or upload constraints.
3. Inspect metadata, format, files, licensing/provenance, and compatibility.
4. Estimate storage and execution requirements.
5. Ask before chargeable downloads, compute, or provider use.
6. Import to private storage or register an endpoint without downloading it.
7. Run a safe validation/test connection.
8. Register the result and show supported next actions.

### Research and knowledge acquisition

1. Search only allowed public or user-authorized sources.
2. Apply source-specific access, robots/terms, rate, privacy, and size policies.
3. Preserve URL, publisher/author when available, retrieval time, license/terms, and content hash.
4. Parse and classify in a sandbox; treat retrieved text as untrusted data.
5. Extract claims and relationships with links to original evidence.
6. Deduplicate and index approved material.
7. Expose uncertainty, disagreement, and source quality rather than treating search rank as truth.

### Training and evaluation

1. Select immutable model and dataset versions.
2. Validate license, data policy, architecture, runtime, and compute requirements.
3. Estimate price, duration range, storage, and accelerator needs.
4. Require user confirmation for chargeable resources.
5. Run an isolated training job with checkpoints and reproducible configuration.
6. Register a candidate version and evaluate against baseline suites.
7. Promote only after configured gates pass; retain rollback references.

## 6. Technology direction

| Layer | Direction | Boundary |
|---|---|---|
| API | FastAPI + Pydantic | Typed, versioned control plane. |
| Persistence | SQLAlchemy 2.x + Alembic | Explicit transactions and versioned schema. |
| Metadata | PostgreSQL | Ownership, configuration, state, manifests, indexes, and events. |
| Isolated tests | SQLite | Fast tests; production behavior also tested on PostgreSQL. |
| Initial jobs | Database-backed polling | Existing low-volume first step; not the final GPU scheduler. |
| Future task queue | Broker plus transactional outbox | Add when worker concurrency/throughput requires it. |
| Durable workflows | A durable workflow engine | Use for timers, approval pauses, retries, and recovery. |
| Inference | Adapter interface | Multiple managed, external, and local runtimes behind an authenticated gateway. |
| Training | PyTorch ecosystem adapters | Begin with supported fine-tuning; full pretraining requires separate capacity and design. |
| Evaluation | Versioned first-party suites | Portable definitions and reproducible results; tracking integrations remain optional. |
| Storage | Private S3-compatible object store | Filesystem adapter remains for development. |
| Observability | OpenTelemetry-compatible telemetry | Correlate request, conversation, task, job, tool, provider, and model operations. |
| Web | Shared responsive application | Same API and user experience across device sizes. |
| Mobile/Desktop | Native shells or validated cross-platform packaging | Choose after testing background tasks, secure storage, local-worker access, notifications, and store requirements. |

Do not add every available framework. Select an adapter only when a real use case, license review, maintenance plan, and integration test justify it.

## 7. Execution and scaling evolution

- **Foundation:** database-backed jobs, worker polling, persistent events, cancellation, and harmless demo handlers.
- **Scale step:** transactional outbox, queue broker, worker leases/heartbeats, bounded retries, idempotency keys, and capability-aware scheduling.
- **Long-running work:** durable workflow orchestration for approval pauses, timers, callbacks, and recovery.
- **Distributed compute:** isolated workers with resource profiles, scoped credentials, quotas, and checkpoint recovery.

## 8. Security boundaries

- Resource-level server authorization and tenant/facility isolation.
- Secret references rather than raw credentials in tasks or events.
- Sandboxed file parsing, model inspection, training, and tool execution.
- Egress controls and SSRF protections for all URL fetchers.
- CPU, RAM, disk, network, time, and GPU quotas per job.
- Untrusted-source handling for web content, archives, model files, and model outputs.
- Explicit approval for sensitive or irreversible actions.
- Provenance, audit, versioned evaluation, rollback, and backup/restore.
- No automatic production promotion based solely on model-generated claims.

See [SECURITY.md](SECURITY.md) for the detailed requirements.
