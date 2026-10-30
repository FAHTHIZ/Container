<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-30.

A checked item means code is committed. It does not imply production security certification, a managed-service deployment, or an operational SLA. Product direction is described in [PRODUCT_VISION.md](PRODUCT_VISION.md); do not confuse target capabilities with shipped behavior.

## Implemented

- [x] Apache License 2.0, root LICENSE, NOTICE, and Python package license metadata.
- [x] FastAPI application with versioned API routes.
- [x] SQLAlchemy domain models and Alembic migrations.
- [x] PostgreSQL configuration and isolated SQLite test support.
- [x] User registration/login with Argon2 password hashes and signed access tokens.
- [x] Workspace creation/listing, owner memberships, project management, and server-side workspace isolation.
- [x] Persistent jobs, append-only job events, queued/running cancellation, and resumable Server-Sent Events.
- [x] Separate database-polling worker for harmless demo.echo and demo.delay tasks.
- [x] Database-aware liveness/readiness endpoints.
- [x] Authenticated conversation-first browser Studio with a compact animated Core panel.\n- [x] OpenAI-compatible inference gateway with readiness reporting, bounded conversation history, and explicit unconfigured-provider errors.\n- [x] Public Hugging Face model URL metadata inspection and source registration without downloading or executing model files.\n- [x] Existing workspace/project/job/artifact/model catalogue control-plane views retained behind the conversation-first shell.
- [x] Studio JavaScript syntax validation and browser-Studio smoke tests in CI.
- [x] Bounded, immutable local artifact storage with SHA-256 digests.
- [x] Authenticated project-scoped artifact upload, listing, and download with size limits and workspace authorization.
- [x] Docker Compose development stack with PostgreSQL and a persistent artifact volume.
- [x] Project-scoped model identity and version metadata, including source/license/format/quantization fields and optional links to same-project artifacts.
- [x] CI run for the current reviewed main commit completed successfully before this documentation update.

## Not implemented


- [ ] First-party Container Intelligence service, managed default inference, model gateway, routing, and conversation orchestration.
- [ ] Provider registry, provider credential vault, capability discovery, usage metering, and fallback routing.
- [ ] Model weight download/import, safe ZIP extraction, file-format inspection, hosted endpoint connections, and runtime compatibility checks.
- [ ] S3-compatible production object storage, artifact deletion, retention policies, and signed object URLs.
- [ ] Source registry, permitted research ingestion, web search adapters, dataset manifests, and dataset lineage.
- [ ] Knowledge collections, semantic/vector indexing, memory policies, and retention/deletion controls.
- [ ] Account verification, password reset, MFA, refresh-token rotation/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and complete audit-event coverage.
- [ ] Broker-backed scheduling, transactional outbox, worker leases/heartbeats, retry policies, capability-aware scheduling, and durable workflow orchestration.
- [ ] Model training adapters, accelerator allocation, fine-tuning workflows, checkpoint recovery, and reproducible experiment tracking.
- [ ] Evaluation suites, baseline comparisons, regression gates, and model release controls.
- [ ] Local/remote inference adapters, authenticated model gateway, deployment management, and usage monitoring.
- [ ] Agent runtime, tool registry, permission engine, workflow builder, approval UI, and trace inspection.
- [ ] Android client, desktop packaging, PWA/offline shell, and cross-device notifications.
- [ ] Multimodal integrations and extension/SDK ecosystem.
- [ ] Production observability, managed secrets, backup/restore, infrastructure hardening, and independent security review.

## Known limitations

- Access tokens are short-lived JWT bearer tokens; refresh and revocation endpoints do not exist yet.
- The initial worker is a low-volume database-polling demonstration runner, not a GPU training scheduler.
- Only harmless demo jobs execute in the background worker. The chat API can call an operator-configured OpenAI-compatible inference endpoint synchronously; the API does not yet train models or run arbitrary downloaded code.
- Artifact files currently use the local filesystem adapter. Production object storage and retention workflows are not implemented.
- Model registry entries store metadata only. Public Hugging Face repository metadata can be inspected and registered, but weights are not downloaded, inspected at the tensor level, trained, evaluated, or served.
- Upload size is bounded in the artifact storage layer. Production deployments must also enforce request-body limits at the ingress/reverse-proxy layer.
- The conversation-first shell is implemented, but chat history is held only in the current browser session and responses are currently non-streaming.
- There is no managed Container inference deployment in this repository yet. The default managed intelligence route is a product requirement, not a currently available service.
- Docker Compose uses development defaults and must not be exposed publicly.

## Verification notes

- The latest CI run observed before this documentation commit was run 29 for main commit 364c75d66590dfa6e91d6e33c2c5d9966b20a628; it completed with conclusion success.
- CI for this documentation commit must be checked separately after the push.
