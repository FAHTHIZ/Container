<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-30.

A checked item means code is committed. It does not imply production security certification or an operational SLA.

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
- [x] First-party responsive browser Studio for authentication, workspaces, projects, demo jobs, and event monitoring.
- [x] Studio JavaScript syntax validation and browser-Studio smoke tests in CI.
- [x] Bounded, immutable local artifact storage with SHA-256 digests.
- [x] Authenticated project-scoped artifact upload, listing, and download with size limits and workspace authorization.
- [x] Docker Compose development stack with PostgreSQL and a persistent artifact volume.
- [x] Project-scoped model identity and version metadata, including source/license/format/quantization fields and optional links to same-project artifacts.

## Not implemented

- [ ] S3-compatible production object storage, artifact deletion, retention policies, and signed object URLs.
- [ ] Source registry, permitted research ingestion, dataset manifests, and dataset lineage.
- [ ] Account verification, password reset, MFA, refresh-token rotation/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and complete audit-event coverage.
- [ ] Broker-backed scheduling, transactional outbox, worker leases/heartbeats, retry policies, and durable workflow orchestration.
- [ ] Model-file inspection/manifest validation, training adapters, accelerator scheduling, evaluation suites, and release gates.
- [ ] Local/remote inference adapters and deployment management.
- [ ] Agent runtime, workflow builder, connector permissions, and approval UI.
- [ ] Android client and expanded Studio views for data/model lifecycle.
- [ ] Production observability, backup/restore, infrastructure hardening, and independent security review.

## Known limitations

- Access tokens are short-lived JWT bearer tokens; refresh and revocation endpoints do not exist yet.
- The initial worker is a low-volume database-polling demonstration runner, not a GPU training scheduler.
- Only harmless demo jobs execute. The API does not train models, crawl external sources, or run arbitrary downloaded code.
- Artifact files currently use the local filesystem adapter. Production object storage and retention workflows are not implemented.
- Model registry entries currently store metadata only. Source URIs are not fetched, model contents are not inspected, and no model is trained, evaluated, or served by the registry.
- Upload size is bounded in the artifact storage layer. Production deployments must also enforce request-body limits at the ingress/reverse-proxy layer.
- Docker Compose uses development defaults and must not be exposed publicly.
