<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-31.

A checked item means its implementation is committed and a relevant automated test passes. It does not mean production-ready, independently audited, or covered by an SLA. Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

## Implemented baseline

- [x] Apache License 2.0, NOTICE, and Python package license metadata.
- [x] FastAPI application with versioned API routes.
- [x] SQLAlchemy domain models and Alembic migrations.
- [x] PostgreSQL configuration and isolated SQLite test support.
- [x] User registration/login with Argon2 password hashing and signed access tokens.
- [x] Workspaces, owner memberships, projects, and server-side workspace isolation.
- [x] Persistent job records, append-only job events, and queued/running cancellation handling.
- [x] Database-polling worker for harmless demo.echo and demo.delay tasks only.
- [x] Database-aware liveness/readiness endpoints.
- [x] Authenticated browser Studio and installable PWA static shell.
- [x] Persistent account-scoped conversation records and history.
- [x] Optional OpenAI-compatible provider pass-through; actual inference runs outside this repository.
- [x] Hardware inventory endpoint with conservative, explicitly unverified device metadata.
- [x] Public Hugging Face metadata inspection without downloading or executing model files.
- [x] Bounded, immutable local artifact storage with SHA-256 digests.
- [x] Authenticated project-scoped artifact upload, listing, and download.
- [x] Project-scoped model identity and metadata-only version records.
- [x] Docker Compose development stack and GitHub Actions checks.

## Current branch additions — pending CI confirmation

- [ ] Snapshot database record with a mandatory SHA-256 value.
- [ ] Content-addressed snapshot copy with post-write digest verification.
- [ ] Test proving a missing source file cannot create a snapshot.
- [ ] Frozen evaluation file with a pinned SHA-256 digest.
- [ ] Startup verification of the frozen evaluation digest.
- [ ] Deterministic exact-match scorer and known-good test predictor.
- [ ] Negative control that must score strictly below the known-good predictor.
- [ ] CI check for exact frozen evaluation questions in designated training-data directories.

Do not check these boxes until the branch CI run that contains the implementation and tests has completed successfully.

## Not implemented

- [ ] Training loop, fine-tuning, pretraining, or training adapters.
- [ ] Evaluation of an actual trained model or claims about model quality.
- [ ] Model checkpoint creation/versioning for trained weights.
- [ ] Real compute orchestration, scheduler, worker heartbeats/leases, or GPU allocation.
- [ ] Evaluation job submission and score-artifact production (Phase D).
- [ ] Managed inference, model runtime deployment, provider registry, or credential vault.
- [ ] Model weight download/import, safe archive extraction, or tensor-format inspection.
- [ ] Research ingestion, dataset manifests, lineage, data preparation, or vector indexing.
- [ ] Account verification, password reset, MFA, token refresh/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and complete audit-event coverage.
- [ ] Production object storage, retention/deletion, backup/restore, and observability.
- [ ] Android client, desktop packaging, and cross-device notifications.
- [ ] Independent security review and production hardening.

## Known limitations

- Access tokens are short-lived bearer JWTs; refresh and revocation endpoints do not exist.
- The demonstration worker does not execute model training, inference, external research, or arbitrary downloaded code.
- Hardware inventory describes what the API process can see. It does not prove runtime availability, model compatibility, benchmark performance, or scheduling capacity.
- File upload SHA-256 hashes identify uploaded bytes. They are not, by themselves, model quality or model version evidence.
- Snapshot records are content-addressed file references; they do not prove model quality.
- The initial frozen evaluation fixture verifies the evaluation plumbing only. Its deterministic stub score is not a model benchmark.
- Production deployment requires managed secrets, TLS, rate limits, private object storage, backups, resource limits, observability, and an independent security review.
- Docker Compose defaults are for local development only.

## Test map

| Capability | Automated evidence |
|---|---|
| Auth, workspace isolation, project/job CRUD, job events, cancellation | services/api/tests/test_control_plane.py |
| Artifact SHA-256, upload bounds, immutable storage, download authorization | services/api/tests/test_control_plane.py and test_storage.py |
| Model metadata versions and project scoping | services/api/tests/test_control_plane.py |
| Conversation ownership, persistence, configured-provider gateway, streaming | services/api/tests/test_chat.py |
| Model source URL validation and metadata inspection | services/api/tests/test_model_sources.py |
| API health, capability inventory, Studio and PWA shell | test_health.py, test_capabilities.py, and test_studio.py |
| Snapshot hashing and missing-file rejection | services/api/tests/test_snapshots.py |
| Frozen evaluation hash, negative control, training-data quarantine | services/api/tests/test_eval.py |

## Verification policy

CI must run linting, API tests, migrations against PostgreSQL, JavaScript syntax checks, and the frozen-eval quarantine scan. A successful workflow verifies only the checks it actually ran. No model has been trained or evaluated by this repository.
