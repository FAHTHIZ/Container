<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-30.

A checked item means code is committed. It does not imply production security certification or an operational SLA.

## Implemented

- [x] Apache License 2.0, root LICENSE, NOTICE, and Python package license metadata.
- [x] FastAPI application and versioned API prefix.
- [x] SQLAlchemy domain models and initial Alembic migration.
- [x] PostgreSQL configuration and SQLite test support.
- [x] User registration/login with Argon2 password hashes and signed access tokens.
- [x] Workspace creation/listing and owner membership.
- [x] Project creation/listing and workspace isolation checks.
- [x] Persistent job records, append-only job event records, cancellation, and resumable Server-Sent Events (SSE).
- [x] Separate database-polling demo worker for demo.echo and demo.delay only.
- [x] Database-aware readiness endpoint.\n- [x] Authenticated project artifact upload, listing, and download with size limits and SHA-256 integrity metadata.
- [x] Docker Compose development stack.
- [x] First-party responsive browser Studio for authentication, workspaces, projects, demo jobs, and event streaming.\n- [x] CI verifies the Studio JavaScript syntax.
- [x] CI lint, migration, and API tests.

## Not implemented

- [ ] Account verification, password reset, MFA, refresh-token rotation/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and full audit-event coverage.
- [ ] Broker-backed scheduling, transactional outbox, worker leases/heartbeats, and retry policies.
- [x] Resumable SSE job event stream.\n- [ ] Expanded Studio job-monitor controls and filters.
- [x] Artifact storage contract and immutable, bounded local filesystem adapter for development/tests.\n- [ ] S3-compatible production object storage, artifact metadata API, source registry, permitted ingestion, and dataset lineage.
- [ ] Model registry, training adapters, accelerator scheduling, evaluations, and release gates.
- [ ] Local/remote inference adapters and deployment management.
- [ ] Agent runtime, workflow builder, connector permissions, and approval UI.
- [ ] Android client and expanded Studio views for data/model lifecycle.
- [ ] Production observability, backup/restore, infrastructure hardening, and security review.

## Known limitations

- Access tokens are short-lived JWT bearer tokens; no refresh or revocation endpoint exists yet.
- The initial worker uses the database as a simple queue. It is for a low-volume first slice, not a final GPU training scheduler.
- Only harmless demo jobs execute. The API does not train models, crawl external sources, or run arbitrary downloaded code.
- The Compose configuration uses development defaults and must not be exposed publicly.
