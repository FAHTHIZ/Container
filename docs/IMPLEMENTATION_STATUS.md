<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-31.

A checked item means the implementation is present and has been exercised by
the indicated automated checks. It does not imply production security
certification, an operational SLA, or completion of the whole product. Product
direction must not be confused with shipped behavior.

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
- [x] Authenticated conversation-first browser Studio with a compact animated Core panel and persistent account-scoped conversation history.
- [x] OpenAI-compatible inference gateway with readiness reporting, bounded conversation history, and explicit unconfigured-provider errors.
- [x] Server-sent event streaming from a configured OpenAI-compatible inference endpoint, with browser token rendering and persisted completed replies.
- [x] Authenticated, conservative API-worker CPU, memory-limit, and visible-accelerator inventory for Core diagnostics.
- [x] Public Hugging Face model URL metadata inspection and source registration without downloading or executing model files.
- [x] Existing workspace/project/job/artifact/model catalogue control-plane views retained behind the conversation-first shell.
- [x] Studio JavaScript syntax validation and browser-Studio smoke tests are included in CI.
- [x] Installable browser PWA shell with a static-asset service worker that bypasses authenticated /api/ requests.
- [x] Bounded, immutable local artifact storage with SHA-256 digests.
- [x] Authenticated project-scoped artifact upload, listing, and download with size limits and workspace authorization.
- [x] Docker Compose development stack with PostgreSQL and a persistent artifact volume.
- [x] Project-scoped model identity and version metadata, including source/license/format/quantization fields and optional links to same-project artifacts.
- [x] Initial content-addressed snapshot capture that stores a SHA-256 digest; full snapshot verification requirements remain incomplete.
- [x] Frozen JSONL evaluation fixture, pinned SHA-256, deterministic exact-match scorer, predictor interface, negative-control implementation, and associated unit tests.

## Not implemented or incomplete

- [ ] Snapshot verification API, stored-file mutation detection, size_bytes metadata, and Checkpoint extension.
- [ ] Evaluation quarantine scan wired into CI and run against the repository's actual training-data directories.
- [ ] End-to-end eval_run job that stores the scored result as a SHA-256-bearing artifact.
- [ ] Provider capability registry, tested local-provider defaults, and adapt-don't-assume handling for supports_tools=false.
- [ ] Automatic local Ollama default in the current configurable inference gateway.
- [ ] SQLite-first standalone mobile profile, no-Docker phone startup, checkpoint-resume, retention, bounded retry, and job-size limits.
- [ ] Model weight download/import, safe ZIP extraction, file-format inspection, and runtime compatibility checks.
- [ ] S3-compatible production object storage, artifact deletion, retention policies, and signed object URLs.
- [ ] Source registry, permitted research ingestion, web search adapters, dataset manifests, and dataset lineage.
- [ ] Knowledge collections, semantic/vector indexing, memory policies, and retention/deletion controls.
- [ ] Account verification, password reset, MFA, refresh-token rotation/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and complete audit-event coverage.
- [ ] Broker-backed scheduling, transactional outbox, worker leases/heartbeats, retry policies, capability-aware scheduling, and durable workflow orchestration.
- [ ] Model training adapters, accelerator allocation, fine-tuning workflows, checkpoint recovery, and reproducible experiment tracking. Training remains blocked by the build contract's evaluation and job gates.
- [ ] Agent runtime, tool registry, permission engine, workflow builder, approval UI, and trace inspection. Harness behavior belongs in the separate OASIS repository.
- [ ] Android client, desktop packaging, and cross-device notifications.
- [ ] Multimodal integrations and extension/SDK ecosystem.
- [ ] Production observability, managed secrets, backup/restore, infrastructure hardening, and independent security review.

## Known limitations

- Access tokens are short-lived JWT bearer tokens; refresh and revocation endpoints do not exist yet.
- The initial worker is a low-volume database-polling demonstration runner, not a GPU training scheduler. The authenticated capability endpoint inventories the API host only; it is not a paired-worker registry, GPU allocator, benchmark, or compatibility certification.
- Only harmless demo jobs execute in the background worker. Chat can call an operator-configured OpenAI-compatible endpoint synchronously or through SSE streaming; the API does not yet train models or run arbitrary downloaded code.
- Artifact files currently use the local filesystem adapter. Production object storage and retention workflows are not implemented.
- Model registry entries store metadata only. Public Hugging Face repository metadata can be inspected and registered, but weights are not downloaded, inspected at the tensor level, trained, evaluated, or served.
- Upload size is bounded in the artifact storage layer. Production deployments must also enforce request-body limits at the ingress/reverse-proxy layer.
- Conversation history is persisted per account and restored by the browser client. Streaming is available when the configured provider supports the OpenAI-compatible SSE protocol.
- The inference gateway forwards to an operator-configured compatible endpoint. It is not a bundled model and does not yet choose a local Ollama provider automatically.
- The phone profile is a target, not a shipped feature. The current server development profile still uses Docker Compose/PostgreSQL by default.
- Docker Compose uses development defaults and must not be exposed publicly.
- The snapshot creator computes and verifies the digest while capturing the source, but there is no API to re-verify a stored snapshot after later mutation. It must not yet be described as a complete checkpoint-resume system.
- The eval runner checks the frozen file hash and has a negative control. The CI workflow does not yet call the quarantine checker; Phase C is therefore incomplete.
- Container does not contain Artemis or the OASIS harness. Those projects remain separate.

## Verification notes

- On 2026-10-31, GitHub Actions CI run 94 for main commit db4eac5e82de2c350454f6d650b513981998da64 failed at the Ruff lint step. The JavaScript syntax, migration, and test steps were skipped. The lint findings were two B904 findings and one E501 finding in services/api/src/container_api/snapshots.py, plus three E402 findings in services/api/tests/test_eval.py.
- Because CI did not complete, Phase A is not marked complete. Fix the lint findings, rerun the full workflow, and review the exception paths before closing the Phase A gate.
- Historical successful CI runs are not evidence that the current main commit passes.
