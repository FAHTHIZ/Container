# Container — System Architecture

**Status:** Proposed architecture, to be validated as implementation begins.

## 1. Product boundary

Container is the platform that manages the lifecycle around AI systems. It is not itself a single foundation model. A model can be developed inside Container, imported from an external source, evaluated, adapted, served, and used by agents or applications.

The platform owns:
- Projects and workspaces
- Data-source and dataset records
- Model registry and model versions
- Job orchestration and execution history
- Artifact metadata and storage references
- Evaluation suites and results
- Agent and workflow definitions
- Deployments, endpoints, and audit events

Execution engines are replaceable components. Container should not hard-code itself to one model family, training library, inference runtime, or cloud provider.

## 2. Architecture shape

Start with a **modular monolith API plus isolated workers**, not a large microservice fleet. This keeps the first version understandable and testable while preserving clear module boundaries.

```text
Web Studio / Android Client
          |
       API Gateway
          |
   Container API (modular)
   |       |        |       |
Projects  Data    Models   Jobs
   |       |        |       |
   +-------+--------+-------+
                   |
            Job Orchestrator
                   |
        Queue / Event Backbone
          /       |        \
   Research   Training   Evaluation
    Worker     Worker      Worker
          \       |        /
             Artifact Store
                   |
       Local / Remote Inference
                   |
        Agents / Workflows / Apps
```

This diagram is conceptual. It does not imply that these components already exist.

## 3. Recommended technology direction

| Area | Initial direction | Reason |
|---|---|---|
| Web studio | React + TypeScript | Broad ecosystem and reusable UI contracts |
| Mobile | Android-first client; Kotlin + Jetpack Compose is the native target | Reliable device integration and mobile UX |
| API | Python + FastAPI | Strong AI/ML ecosystem and typed HTTP APIs |
| Domain validation | Pydantic models and explicit service boundaries | Shared validation and clear contracts |
| Primary database | PostgreSQL | Durable relational records and transactions |
| Job queue | Redis-backed queue for the first implementation | Simple asynchronous execution |
| Long-running orchestration | Add Temporal when durable multi-step workflows justify it | Retries, timers, recovery, and workflow history |
| Artifact storage | S3-compatible object storage, with local filesystem adapter for development | Large datasets, checkpoints, and model artifacts |
| Model adaptation | PyTorch + Hugging Face ecosystem; adapters/LoRA first | Practical fine-tuning without full-model retraining |
| Local inference | llama.cpp where model format and device support fit | CPU-oriented and quantized local execution |
| Remote inference | Pluggable serving backend; vLLM for compatible GPU workloads | Efficient batched serving |
| Observability | Structured logs, metrics, traces, and job events | Debuggability and operational visibility |

These are starting choices, not irreversible commitments. Pin versions and validate Android, CPU, GPU, and deployment compatibility before adopting dependencies.

## 4. Core domain modules

### Identity and access
Users, workspaces, memberships, roles, API tokens, device sessions, and audit events. All credentials are stored in a secrets facility or encrypted configuration—not in source control or plain job logs.

### Projects
A project is the top-level container for related datasets, models, evaluations, jobs, agents, workflows, and deployments. Each resource belongs to a workspace and has explicit ownership.

### Research and data
A source record captures origin, access method, retrieval time, license/terms, attribution, and integrity metadata. A dataset version is immutable once finalized and points to content-addressed artifacts plus a manifest. Processing steps are recorded as lineage.

### Models
A model record identifies architecture/family and origin. A model version identifies exact weights or adapter artifacts, tokenizer/configuration, quantization, source revision, and evaluation status. Imported models and Container-trained models use the same registry.

### Jobs and orchestration
Every long-running operation is a job with:
- A typed job kind and validated configuration
- Queued/running/succeeded/failed/cancelled states
- Owner, project, worker assignment, and resource request
- Start/end times, progress events, logs, and cancellation state
- Input/output artifact references
- Retry policy and idempotency key where appropriate

Workers execute jobs; the API does not perform long training or ingestion work inside request handlers.

### Evaluation and releases
Evaluation suites are versioned. Results record the exact model version, dataset/suite version, runtime configuration, metrics, and report artifact. Promotion rules compare a candidate against a baseline and guardrails. A failed or regressed candidate is not automatically promoted.

### Agents and workflows
An agent is a configured runtime identity with a model/provider, instructions, permitted tools, and resource/permission scope. A workflow is a versioned graph of typed steps. Each run creates a job and emits inspectable events. Human approval is required for sensitive or irreversible actions.

### Inference and deployment
Inference endpoints refer to an immutable model version and serving configuration. Deployments track target, health, version, rollout state, and rollback target. Local inference is a device capability, not a promise that every model will fit on every phone.

## 5. Data and artifact lifecycle

1. Register a source and record its provenance and terms.
2. Ingest only data the project is allowed to use.
3. Normalize, filter, deduplicate, and validate in a worker.
4. Produce an immutable dataset version and manifest.
5. Link a training/evaluation job to exact dataset and code revisions.
6. Store checkpoints, adapters, logs, and reports as artifacts.
7. Register a model version with its artifact hashes and configuration.
8. Evaluate against fixed suites and compare to a baseline.
9. Promote only if required checks pass; preserve rollback history.

Large datasets and model weights should not be stored as ordinary Git blobs. Git stores code, small configuration, schemas, and reproducible manifests; object storage stores large artifacts.

## 6. Compute strategy

Container must be **hardware-aware and hybrid**:
- Phone: project control, monitoring, lightweight preprocessing, and compatible small-model inference.
- Laptop/desktop: local development, smaller inference, and workloads supported by available RAM/CPU/GPU.
- Remote worker: larger training and inference workloads when the user has access to suitable compute.

Before a job starts, validate resource requirements and explain why a selected target is incompatible. Do not imply that a phone can train frontier-scale models.

## 7. API and event contracts

Use versioned HTTP endpoints for durable resource operations and a streaming channel (SSE initially; WebSocket only where bidirectional interaction is required) for live job events.

Initial resource families:
- `/api/v1/workspaces`
- `/api/v1/projects`
- `/api/v1/sources`
- `/api/v1/datasets`
- `/api/v1/models`
- `/api/v1/evaluations`
- `/api/v1/jobs`
- `/api/v1/agents`
- `/api/v1/workflows`
- `/api/v1/deployments`

Event envelopes should include `event_id`, `event_type`, `occurred_at`, `workspace_id`, `project_id`, `job_id` when relevant, and a schema-versioned payload. Never put secrets or raw sensitive data in event payloads.

## 8. Quality gates

Every module should have:
- Unit tests for domain logic
- Integration tests for database/queue/storage boundaries
- API contract tests
- Authorization tests (including cross-workspace isolation)
- Failure/retry/cancellation tests for workers
- Migrations tested from an empty database and previous schema
- Security checks and dependency scanning in CI

## 9. Initial vertical slice

The first end-to-end slice should be deliberately small:
1. Create a workspace and project.
2. Submit a lightweight background job.
3. Observe queued/running/succeeded events in the UI.
4. Persist logs and a small output artifact.
5. Cancel a running job and verify the state transition.
6. Enforce project/workspace authorization at every API boundary.

This proves the platform's central control plane before expensive model training is introduced.
