<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Delivery Roadmap

A milestone is complete only when the behavior is implemented, tested, documented, secure for its intended deployment, and demonstrable. Screens, mocked responses, metadata-only records, and planned adapters do not count as completed runtime capabilities.

The sequence protects the current working foundation while moving toward the conversation-first, cloud-first hybrid product.

## M0 — Repository and runtime foundation

- [x] Apache 2.0 license, NOTICE, Python API package, and CI baseline.
- [x] Initial SQLAlchemy schema and Alembic migrations.
- [x] Docker Compose development environment.
- [ ] Supply-chain scanning, image hardening, and automated signed releases.

## M1 — Control-plane foundation (implemented baseline)

- [x] User registration/login with Argon2 password hashing and signed access tokens.
- [x] Workspaces, owner memberships, projects, and server-side workspace isolation.
- [x] Persistent jobs, event history, demonstration worker, and queued cancellation.
- [x] Resumable SSE job event stream.
- [x] Responsive browser Studio for account, workspace, project, jobs, and event monitoring.
- [x] Project artifact upload/list/download using bounded local storage and integrity hashes.
- [x] Project-scoped model identities and immutable metadata version records.
- [ ] Account verification, password recovery, MFA, refresh-token rotation/revocation, and rate limiting.
- [ ] Workspace invitations, scoped roles, and complete audit events.
- [ ] Production object storage, retention/deletion, and durable job scheduling.

**Exit criteria:** authenticated users can create a facility/project, submit a task, monitor events, cancel eligible work, and cannot access another user's workspace. The current demonstration worker remains explicitly limited to safe demo tasks.

## M2 — Conversation product and built-in intelligence

- [x] Replace the dashboard-first experience with one responsive conversation as the primary surface.
- [x] Add a compact non-human animated Core panel and inference connection status.
- [ ] Define conversation, message, attachment, tool-call, task, and citation records.
- [x] Implement an authenticated OpenAI-compatible inference gateway adapter.
- [ ] Implement first-party orchestration, streaming responses, persistent conversations, and tool calling.
- [ ] Provision a managed default inference route for first-run users.
- [ ] Add model gateway/provider interfaces and clear unavailable-provider behavior.
- [ ] Add conversation streaming, retry, stop/cancel, history, and reconnect behavior.
- [ ] Enforce user/facility isolation, retention policy, and provider consent.

**Exit criteria:** a new managed user can sign in and ask a question without supplying an API key; a task response streams; the Core accurately shows activity; self-hosted deployments clearly require a configured inference backend.

## M3 — Model import, connections, and provider registry

- [ ] Add provider and endpoint registries with secret references and health/capability metadata.
- [x] Inspect public Hugging Face repository URLs and register source/license/task metadata.
- [ ] Implement pinned-revision weight downloads and immutable model artifacts.
- [ ] Implement direct supported file URL and local file/folder upload adapters.
- [ ] Implement safe ZIP manifest inspection and isolated extraction.
- [ ] Implement hosted inference endpoint and paired local runtime connection adapters.
- [ ] Add model manifest validation, checksums, provenance, license metadata, and format inspection.
- [ ] Add runtime/device compatibility discovery and test-inference flow.
- [ ] Add clear import/connect states, retry/resume, and safe cleanup.

**Exit criteria:** a user can paste a supported repository URL, upload a supported archive, or connect a valid endpoint; Container correctly distinguishes import from connection and shows source, compatibility, and test results.

## M4 — Research, knowledge, and datasets

- [ ] Add permitted web/source search and source registry.
- [ ] Add source retrieval metadata, provenance, rate limits, and access/terms checks.
- [ ] Add sandboxed extraction, parsing, classification, deduplication, and content hashing.
- [ ] Add knowledge collections, full-text search, optional semantic/vector index, and citations.
- [ ] Add conversation/project/agent memory with retention and deletion controls.
- [ ] Add dataset manifests, immutable versions, quality reports, and lineage.
- [ ] Add research missions and recurring jobs with user-defined scope and budget.

**Exit criteria:** research produces inspectable source-backed results; permitted sources can become reproducible dataset/knowledge versions with complete lineage.

## M5 — Compute orchestration and model adaptation

- [ ] Add managed cloud compute integration and capability-aware worker registry.
- [ ] Add job resource profiles, cost estimation, quotas, and budget confirmation.
- [ ] Add optional external compute and user-owned desktop worker pairing.
- [ ] Add worker leases, heartbeats, isolation, bounded retries, and cancellation of actual work.
- [ ] Add first supported LoRA fine-tuning path.
- [ ] Add compatible QLoRA path after runtime/hardware validation.
- [ ] Add checkpoints, resumable runs, logs, experiment metadata, and cleanup.
- [ ] Add data/model/runtime/license preflight checks.

**Exit criteria:** a supported fine-tuning job runs on a compatible managed or explicitly connected worker, shows a clear cost estimate, can recover from interruption, and produces a versioned candidate.

## M6 — Evaluation, inference, and deployment

- [ ] Add versioned model and agent evaluation suites.
- [ ] Add baselines, regression thresholds, safety checks, and release gates.
- [ ] Add local and remote inference runtime adapters.
- [ ] Add authenticated gateway endpoints, streaming, batch requests, usage, rate limits, and health checks.
- [ ] Add deployment revisions, rollout/rollback, monitoring, and endpoint management.

**Exit criteria:** a registered candidate can be evaluated reproducibly and served through an authenticated compatible runtime; failed gates block promotion.

## M7 — Agents, workflows, and multimodal capabilities

- [ ] Add agent definitions, model selection, scoped tools, memory, budgets, and schedules.
- [ ] Add workflow validation, run history, retries, trace inspection, and approval steps.
- [ ] Add connector registry and per-tool permissions.
- [ ] Add multimodal integrations for supported image, audio, speech, video, and document workloads.
- [ ] Add agent evaluation for prompt injection, tool misuse, privacy, and recovery.

**Exit criteria:** users can create and operate bounded agents through conversation, inspect each tool/action, and approve consequential operations.

## M8 — Cross-device product distribution

- [x] Deliver responsive browser experience and installable PWA static shell.
- [ ] Deliver signed Android packages and store distribution.
- [ ] Deliver desktop installers for Windows, macOS, and Linux.
- [ ] Add shared conversation/project state and notifications across clients.
- [ ] Add optional desktop local-worker pairing.
- [ ] Test accessibility, older-device support, low-bandwidth operation, and interrupted uploads.

**Exit criteria:** users can start and monitor the same facility from mobile, desktop, and browser without different product data or workflows.

## M9 — Production readiness and ecosystem

- [ ] Threat model and independent security review.
- [ ] Backup, restore, disaster recovery, and retention drills.
- [ ] Metrics, tracing, alerting, audit export, and operational SLOs.
- [ ] Deployment automation, signed builds, upgrade/rollback, SBOM, and supply-chain provenance.
- [ ] Extension SDK and verified provider/runtime/data connectors.
- [ ] Operator/user documentation and support process.
- [ ] Cost, quota, privacy, and incident response operational controls.

**Exit criteria:** a reproducible signed release with reviewed security boundaries, tested recovery, support documentation, and transparent service limits.

## Release policy

Do not mark planned integrations as implemented. Keep experimental connectors behind capability flags. Pin dependency ranges and update through tested changes. Preserve model/data provenance. A model checkpoint, agent configuration, or research output is not an improvement until independent evaluation supports it.
