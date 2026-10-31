<!-- SPDX-License-Identifier: Apache-2.0 -->

# Implementation Status

Last reviewed: 2026-10-31.

A checked item means the implementation is present and a relevant automated check passes. It does not imply production security certification, an operational SLA, or completion of the whole product. Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

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
- [x] Authenticated conversation-first browser Studio with persistent account-scoped conversation history.
- [x] Optional OpenAI-compatible inference gateway with readiness reporting, bounded conversation history, explicit unconfigured-provider errors, and SSE streaming. The configured external provider performs inference; Container does not.
- [x] Authenticated, conservative API-worker CPU, memory-limit, and visible-accelerator inventory for Core diagnostics. This is inventory only, not a scheduler or benchmark.
- [x] Public Hugging Face model URL metadata inspection and source registration without downloading or executing model files.
- [x] Studio JavaScript syntax validation and browser-Studio smoke tests are included in CI.
- [x] Installable browser PWA shell with a static-asset service worker that bypasses authenticated /api/ requests.
- [x] Bounded, immutable local artifact storage with SHA-256 digests.
- [x] Authenticated project-scoped artifact upload, listing, and download with size limits and workspace authorization.
- [x] Docker Compose development stack with PostgreSQL and a persistent artifact volume.
- [x] Project-scoped model identity and metadata-only version records.
- [x] Initial content-addressed snapshot capture that stores a SHA-256 digest and re-verifies the stored copy immediately after capture.
- [x] Frozen JSONL evaluation fixture, pinned SHA-256, deterministic exact-match scorer, predictor interface, negative-control implementation, and associated unit tests.
- [x] Training-data quarantine checker in CI. It scans designated training-data directories and fails on exact frozen-eval question leakage, symlinks, unknown file formats, or unreadable text files.
- [x] eval_run job submission for project-registered model metadata, using a trusted operator-configured adapter.
- [x] Bounded evaluation subprocess with project, path, expected-hash, output, and timeout checks.
- [x] Evaluation JSON report artifact with its SHA-256 recorded in artifact metadata and job result.
- [x] train_run job accepts project-scoped model and dataset records plus bounded step/loss/checkpoint intervals.
- [x] Trainer and evaluator adapters are selected only by operator configuration, never by workspace job payloads.
- [x] The worker verifies frozen-eval hash and rejects exact evaluation questions in the training dataset before starting the adapter.
- [x] Loss records are checked for every requested interval and must contain finite numeric values.
- [x] Checkpoint files are required at each save interval, stored as project artifacts, and re-hashed from their stored copies.
- [x] The final checkpoint is evaluated with the frozen harness and its hash/evaluation score are saved together in model-version metadata.

## Phase A, B, and C — verified

- [x] Existing API capabilities have an automated test map.
- [x] MODEL_STATUS.md and DEFERRED.md define the model boundary and deferred work.
- [x] Snapshot database record requires a SHA-256 value.
- [x] Content-addressed snapshot copy is re-hashed after storage.
- [x] Tests prove that missing, unreadable, and symbolic-link snapshot sources cannot create a snapshot.
- [x] Frozen evaluation file has a pinned SHA-256 digest, checked before task parsing/scoring.
- [x] Deterministic exact-match scorer and known-good test predictor are covered by tests.
- [x] Negative control is strictly worse than the known-good predictor.
- [x] CI checks exact frozen evaluation questions against designated training-data directories.
- [x] Ruff lint and API tests pass in the current reviewed CI run.

## Phase D — verified

- [x] Evaluation job accepts model_id, eval_path, and eval_hash.
- [x] API rejects an unconfigured adapter and a model from another project.
- [x] Worker runs the frozen harness as a bounded subprocess using trusted operator-configured code.
- [x] Worker constrains the evaluation path to eval/, verifies the expected hash, and validates the returned model identity, digest, score, task count, and timestamp.
- [x] Worker stores the JSON result as an artifact with SHA-256.
- [x] End-to-end test submits an evaluation job, runs it, downloads the report, and verifies the digest.

## Phase E — verified external trainer orchestration

- [x] train_run accepts model_id, dataset_artifact_id, steps, loss_every, checkpoint_every, eval_path, and eval_hash.
- [x] The API requires both trusted adapters to be configured and validates that model and dataset belong to the project.
- [x] The worker verifies the frozen evaluation hash and checks the dataset for exact frozen-eval question leakage.
- [x] The adapter must print one finite LOSS record at every requested interval.
- [x] The adapter must create the exact checkpoint files at every requested save interval; missing, extra, malformed, or symbolic-link outputs fail the job.
- [x] Each checkpoint is hashed, stored as a project artifact, and re-hashed from the stored copy.
- [x] The final checkpoint path is passed to the frozen evaluation adapter.
- [x] The final checkpoint hash and evaluation score are recorded together in model-version metadata.
- [x] Tests cover successful submission-to-result execution, stored checkpoint hashing, final-checkpoint handoff, eval leakage rejection, and missing loss records.

Phase E verifies infrastructure orchestration only. The test adapter writes dummy bytes and fixed example loss values. It is not a model trainer, and its output is not evidence of model quality.

## Not implemented or incomplete

- [ ] Stored-snapshot verification API, later mutation detection, explicit snapshot size metadata, checkpoint extension, and checkpoint-resume workflow.
- [ ] Provider capability registry, tested local-provider defaults, and adapt-don't-assume behavior for providers that do not support tools.
- [ ] Automatic local Ollama default in the configurable inference gateway.
- [ ] SQLite-first standalone mobile profile and no-Docker phone startup.
- [ ] Model weight download/import, safe ZIP extraction, file-format inspection, hosted endpoint connection, and runtime compatibility checks.
- [ ] S3-compatible production object storage, artifact deletion, retention policies, and signed object URLs.
- [ ] Source registry, permitted research ingestion, web search adapters, dataset manifests, and dataset lineage.
- [ ] Knowledge collections, semantic/vector indexing, memory policies, and retention/deletion controls.
- [ ] Account verification, password reset, MFA, refresh-token rotation/revocation, and authentication throttling.
- [ ] Workspace invitations, role administration, and complete audit-event coverage.
- [ ] Broker-backed scheduling, transactional outbox, worker leases/heartbeats, retry policies, capability-aware scheduling, durable workflow orchestration, and GPU allocation.
- [ ] Model-specific learning algorithms or a real external trainer package. The generic adapter contract is implemented, but no actual model-training adapter is included or enabled by default.
- [ ] Agent runtime, tool registry, permission engine, workflow builder, approval UI, and trace inspection. Harness behavior belongs in the separate OASIS repository.
- [ ] Android client, desktop packaging, and cross-device notifications.
- [ ] Multimodal integrations and extension/SDK ecosystem.
- [ ] Production observability, managed secrets, backup/restore, infrastructure hardening, and independent security review.

## Known limitations

- Access tokens are short-lived JWT bearer tokens; refresh and revocation endpoints do not exist yet.
- The initial worker is a low-volume database-polling process, not a GPU training scheduler. The authenticated capability endpoint inventories the API host only; it is not a paired-worker registry, GPU allocator, benchmark, or compatibility certification.
- Only harmless demo jobs and eval_run execute in the worker. The eval_run type runs one bounded, operator-configured Python adapter on the worker host.
- The eval adapter is trusted code, not sandboxed. Users cannot choose an adapter in a job payload. The default is unconfigured.
- The built-in eval.stub_predictor returns fixed answers for six plumbing tasks. It is not a model, does not load model weights, and its score is not a model-quality result.
- Evaluation quarantine CI scanned zero text files in designated training-data directories in this repository. Fixture tests separately prove that leakage and uninspectable files are rejected.
- A snapshot digest identifies the captured bytes. The creation function verifies the stored copy at capture time, but there is no later API to re-verify a snapshot after external mutation. A snapshot hash does not prove model quality.
- File upload and report SHA-256 hashes identify stored bytes. They are not, by themselves, model quality or model version evidence.
- The inference gateway forwards to an operator-configured compatible endpoint. It is not a bundled model, managed inference service, or automatic local Ollama setup.
- The phone profile is a target, not a shipped feature. The current server development profile uses Docker Compose/PostgreSQL by default.
- Production deployment requires managed secrets, TLS, rate limits, private object storage, backups, resource limits, observability, and independent security review.
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
| eval_run submission, project isolation, subprocess execution, report hash | services/api/tests/test_eval_jobs.py |
| train_run adapter, loss intervals, checkpoint hashes, final evaluation, model-version metadata | services/api/tests/test_train_jobs.py |

## CI verification

The latest completed workflow on the feature branch passed:
- Ruff lint.
- Studio JavaScript syntax checks.
- PostgreSQL Alembic migrations.
- API and evaluation tests: 51 passed, 3 warnings.
- Frozen evaluation hash and training-data quarantine check: passed.

No model has been trained or evaluated by this repository. This status applies to the verified feature branch; the latest successful run and commit are linked in the build history.
