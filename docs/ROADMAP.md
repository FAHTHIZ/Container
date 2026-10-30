<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Delivery Roadmap

A milestone is complete only when the acceptance criteria are implemented, tested, documented, and demonstrable. The control plane comes first; research and model-development systems are larger workstreams.

## M0 — Repository and runtime foundation

- [x] Product boundary and architecture.
- [x] Apache 2.0 license and NOTICE.
- [x] Python API package and CI baseline.
- [x] Initial SQLAlchemy schema and Alembic migrations.
- [ ] Supply-chain scanning, image hardening, and automated releases.

## M1 — Control plane (in progress)

- [x] User registration and login.
- [x] Signed access tokens and Argon2 password hashing.
- [x] Workspaces, owner memberships, projects, and workspace isolation.
- [x] Persistent jobs, event history, demo worker, and queued cancellation.
- [x] Resumable SSE job event stream.
- [x] First-party browser Studio for authentication, workspaces, projects, and job monitoring.
- [ ] Account verification, password recovery, MFA, refresh-token rotation, revocation, and rate limiting.
- [ ] Workspace invitations, role administration, and audit events.
- [ ] Broker-backed scheduling, transactional outbox, worker leases, retry policies, and heartbeats.
- [ ] Expanded Studio job-monitor controls, filters, and reconnect UX.

**Exit criteria:** an authenticated user can create a workspace/project, submit a task, monitor state/events, cancel work, and cannot access another workspace.

## M2 — Artifact and data foundation (in progress)

- [x] Artifact storage contract and bounded local filesystem adapter.
- [x] Authenticated project-scoped artifact upload, listing, and download with SHA-256 metadata.
- [ ] S3-compatible production artifact adapter.
- [ ] Artifact deletion, retention, signed downloads, and object-level audit events.
- [ ] Source registry with provenance and access/terms metadata.
- [ ] Ingestion allowlists, rate limits, privacy checks, and sandboxing.
- [ ] Dataset manifests, immutable versions, deduplication, and quality reports.

**Exit criteria:** permitted sources produce reproducible dataset versions with inspectable provenance, processing lineage, and integrity hashes.

## M3 — Model registry and evaluation

- [ ] Imported model registry and exact model-version metadata.
- [ ] Weights/config/tokenizer/adapters as immutable artifact references.
- [ ] License, source, quantization, and compatibility metadata.
- [ ] Evaluation-suite definitions and repeatable workers.
- [ ] Baseline comparisons, regression gates, and rollback references.

**Exit criteria:** a candidate is evaluated against a versioned suite and a regression cannot be promoted.

## M4 — Model adaptation

- [ ] Resource-aware training job specifications.
- [ ] First supported LoRA fine-tuning path.
- [ ] QLoRA only for compatible software/hardware.
- [ ] Checkpoint recovery and experiment provenance.
- [ ] Evaluation and release gate integrated with training.

**Exit criteria:** a supported adaptation completes on a compatible worker and produces a reproducible, evaluable model version.

## M5 — Local and remote inference

- [ ] Runtime adapter contract.
- [ ] Local llama.cpp adapter for supported model/device combinations.
- [ ] Remote vLLM adapter behind authenticated gateway.
- [ ] Capability discovery and hardware compatibility checks.
- [ ] Streaming, usage telemetry, request limits, health, and rollback.

**Exit criteria:** a registered model is served by a compatible runtime through authenticated Container APIs.

## M6 — Agents and workflow builder

- [ ] Versioned agent definitions and explicit tool registry.
- [ ] Tool schemas, scoped permissions, and policy enforcement.
- [ ] Visual workflow graph, validator, and versioned execution plan.
- [ ] Durable run history and trace/event inspection.
- [ ] Human approval for sensitive operations.
- [ ] Prompt-injection, tool-abuse, and data-boundary evaluations.

**Exit criteria:** a safe bounded agent/workflow can complete a task, show each step, and pause for approvals.

## M7 — Product clients

- [x] Initial responsive browser Studio for core control-plane operations.
- [ ] Expanded Studio for data, model, training, evaluation, and deployment lifecycles.
- [ ] Android Kotlin + Jetpack Compose client.
- [ ] Real-time progress and approval notifications.
- [ ] Device capability reporting and low-bandwidth behavior.
- [ ] Accessibility and secure local credential storage.

**Exit criteria:** users can complete core lifecycle operations through the UI without direct database/terminal work.

## M8 — Production hardening and release

- [ ] Threat model and independent security review.
- [ ] Backup, restore, disaster recovery, and retention drills.
- [ ] Metrics, tracing, alerting, audit export, and SLOs.
- [ ] Deployment automation and upgrade/rollback process.
- [ ] SBOM, dependency/license scanning, signed releases, and provenance.
- [ ] Operator/user documentation and support process.

**Exit criteria:** reproducible release, documented operations, security review, and tested recovery.

## Release policy

Do not mark planned integrations as implemented. Keep experiments behind capability flags. Pin dependency ranges and update through tested changes. Preserve model/data provenance. A new checkpoint is not an improvement until measurable evaluations support it.
