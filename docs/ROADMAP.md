# Container — Delivery Roadmap

**Status:** Planning baseline. A milestone is complete only when its acceptance criteria are implemented and verified.

## M0 — Foundation

- [ ] Establish monorepo layout and development conventions.
- [ ] Add license decision, contribution guide, code of conduct, and security policy.
- [ ] Define typed API and event contracts.
- [ ] Add formatting, linting, type checking, tests, and CI.
- [ ] Add local development environment for API, PostgreSQL, queue, and object storage.
- [ ] Document threat model, secrets handling, and supported deployment modes.

**Exit criteria:** a clean checkout can start the API and dependencies, run migrations, and pass CI.

## M1 — Platform control plane

- [ ] Workspace and project CRUD.
- [ ] Authentication and workspace-scoped authorization.
- [ ] PostgreSQL schema and migration strategy.
- [ ] Job model, queue integration, worker registration, and job history.
- [ ] Structured logs, progress events, cancellation, retries, and idempotency.
- [ ] Minimal web studio for projects and job monitoring.

**Exit criteria:** user can create a project, launch a demo job, monitor it, cancel it, and inspect its result.

## M2 — Data and research pipeline

- [ ] Source registry with provenance and terms metadata.
- [ ] Ingestion adapters with explicit allowlists and rate limits.
- [ ] Dataset manifests and immutable versions.
- [ ] Cleaning, filtering, deduplication, and validation workers.
- [ ] Dataset preview, lineage, and quality reports.

**Exit criteria:** a permitted source can be processed reproducibly into a versioned dataset with inspectable lineage.

## M3 — Model registry and evaluation

- [ ] Register imported models and local model artifacts.
- [ ] Track model versions, tokenizer/config, hashes, and license metadata.
- [ ] Evaluation-suite definitions and reproducible evaluation jobs.
- [ ] Baseline comparison and regression gates.
- [ ] Model release history and rollback metadata.

**Exit criteria:** a candidate model can be evaluated against a fixed suite and cannot be promoted when required guardrails fail.

## M4 — Training and adaptation

- [ ] Training job specification and resource validation.
- [ ] First supported fine-tuning path using adapters/LoRA.
- [ ] Checkpoint and artifact management.
- [ ] Training telemetry and failure recovery.
- [ ] Reproducibility metadata and run comparison.
- [ ] Clear hardware compatibility reporting.

**Exit criteria:** one documented, supported adaptation workflow completes on a compatible worker and produces a registered, evaluable model version.

## M5 — Inference and deployment

- [ ] Pluggable inference backend interface.
- [ ] Local inference adapter for supported model formats/devices.
- [ ] Remote inference worker and authenticated endpoint.
- [ ] Deployment health, rollout state, and rollback.
- [ ] Usage and resource telemetry.

**Exit criteria:** a registered model can be served through a documented endpoint and rolled back to a previous version.

## M6 — Agents and visual workflows

- [ ] Agent definitions with scoped tool permissions.
- [ ] Tool registry and approval boundaries.
- [ ] Versioned workflow graph and validator.
- [ ] Workflow run history and event stream.
- [ ] Human approval for sensitive actions.
- [ ] Audit trail for tool execution.

**Exit criteria:** a workflow can execute a safe sample task, show each step, and stop for approval when required.

## M7 — Mobile client and product hardening

- [ ] Android client for project creation and job monitoring.
- [ ] Device capability reporting and local model compatibility checks.
- [ ] Secure device/session management.
- [ ] Accessibility, offline states, and low-bandwidth behavior.
- [ ] Backup/restore, observability, performance, and security review.
- [ ] Deployment and operator documentation.

**Exit criteria:** the mobile client can safely control the platform and report device capabilities without pretending to perform unsupported workloads.

## Release policy

- Never mark a feature complete because a screen or mock API exists.
- Every milestone requires tests, documentation, and a demonstrable end-to-end path.
- Keep experimental integrations behind explicit capability flags.
- Maintain a changelog and migration notes for user-visible changes.
