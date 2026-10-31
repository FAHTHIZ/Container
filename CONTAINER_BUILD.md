# CONTAINER — BUILD SPEC

> This document is the implementation contract for Container. Read it before changing code. When it conflicts with a proposed implementation, this document wins.

## Identity

**Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.**

Container is a cloud control plane for accounts, workspaces, projects, jobs, artifacts, model metadata, and API keys. It is not a model, learning algorithm, inference engine, or reasoning system. OASIS is a separate harness.

Artemis is a private model project in a separate repository. Keep its architecture and model-specific learning logic out of Container.

## Honest baseline

The repository provides a FastAPI control plane, authentication, workspaces/projects/jobs/artifacts, upload SHA-256 hashing, Alembic migrations, Docker Compose, CI, frozen evaluation, evaluation jobs, and external trainer orchestration. Model records are metadata; checkpoint artifacts are produced only when a trusted external adapter is configured.

Container contains no model architecture or learning algorithm. The optional train_run job invokes operator-installed trusted code. The built-in test adapter writes dummy fixture bytes and is not a real trainer. The worker is a single database-polling process, not a production compute scheduler or security sandbox.

A checked status item means its implementation is committed and a test passes. It does not mean production-ready.

## Rules for changes

1. Never claim a capability that code and tests do not prove.
2. The frozen evaluation harness must pass its hash and negative-control tests before a training job can be accepted.
3. Fail closed: validation, filters, and guards reject on errors. Do not add silent exception handling or exception-driven filter bypasses.
4. A snapshot or checkpoint must include the SHA-256 of the exact stored bytes. No hash means no snapshot or checkpoint.
5. External trainer adapters must emit loss at a documented interval and provide hash-verified checkpoints at their requested save intervals. Container verifies these outputs and runs the frozen evaluation against the final checkpoint.
6. Explain non-trivial code in plain English. For code blocks longer than about 15 lines, add a 3–5 sentence explanation.
7. Prefer standard libraries, boring patterns, and minimal dependencies.
8. Keep evaluation and any future trainer adapter code heavily commented and reviewable line by line.

## Verified phases

### Phase A — Make the scaffold honest

- [x] Existing API features mapped to automated tests.
- [x] MODEL_STATUS.md and DEFERRED.md define the model boundary and deferred work.
- [x] Python exception handling reviewed for silent filter bypasses.
- [x] CI runs lint and tests.

### Phase B — Artifact and snapshot hashing

- [x] Snapshot database record requires SHA-256.
- [x] create_snapshot copies to content-addressed storage and re-verifies stored bytes.
- [x] Missing, unreadable, and symbolic-link sources cannot create a snapshot.

### Phase C — Frozen evaluation

- [x] Frozen task set and pinned SHA-256 file.
- [x] Hash verified before task parsing/scoring.
- [x] Deterministic exact-match scoring.
- [x] Negative control strictly worse than known-good test predictor.
- [x] Training-data quarantine check in CI.

The initial evaluation fixture is a plumbing test, not a general model benchmark. It is not evidence of model quality.

### Phase D — Evaluation jobs, no training

- [x] eval_run job accepts model_id, eval_path, and eval_hash.
- [x] Runs the frozen harness as a bounded subprocess using trusted operator-configured code.
- [x] Stores the evaluation result as a SHA-256-bearing artifact.
- [x] End-to-end submission, execution, download, and digest test passes.

### Phase E — External trainer orchestration, not model implementation

- [x] train_run accepts a same-project model and text dataset artifact, step budget, loss interval, checkpoint interval, and frozen-eval identity.
- [x] Only an operator-configured adapter can be selected; workspace job payloads cannot choose code or commands.
- [x] Frozen evaluation hash is verified before the trainer starts, and exact eval questions are rejected in the selected training dataset.
- [x] The worker requires a finite LOSS record at every requested interval.
- [x] The worker requires the exact checkpoint files at each save interval, hashes each source file, stores it as an artifact, and re-hashes the stored copy.
- [x] The final checkpoint path is passed to the frozen evaluation adapter.
- [x] The final checkpoint hash and evaluation score are persisted together in model-version metadata.
- [x] Tests cover successful orchestration, stored checkpoint digests, final-checkpoint handoff, eval-data leakage, and missing loss records.

Phase E verifies an infrastructure contract only. No model-specific learning algorithm is included. The test adapter emits artificial loss values and dummy file contents; it is not a trainer and its score is not evidence of model quality.

## Frozen evaluation requirements

The eval set is versioned, hashed, deterministic, and quarantined from training data. Changing it requires regenerating and reviewing the hash file. No random sampling and no model-as-judge scoring. The negative control must be strictly worse than the known-good stub predictor; otherwise the harness is not trusted.

## Deferred boundaries

This repository does not implement model architecture, learning algorithms, inference, non-tokenized input, memory-heavy sparsity, snapshot attribution tournaments, continual learning, or multi-source model reasoning. Those belong in the separate model project. No real external trainer package is included or enabled by default.

The generic job may invoke trusted operator-installed trainer code. That code is not sandboxed; never point the setting at user uploads or unreviewed code. A future production deployment still needs isolated workers, resource limits, durable scheduling, cancellation of child processes, and independent security review.

Do not make unsupported model-capability or state-of-the-art claims in code, docs, commits, or release notes.

## Definition of done

- Phase A: every checked status item has test coverage; model and deferred status files exist; CI passes.
- Phase B: a test proves a missing/unreadable source cannot produce a snapshot and every created snapshot has a digest.
- Phase C: startup hash verification passes; tampering is rejected; negative control scores strictly worse; training-data quarantine check is in CI.
- Phase D: a submitted job runs the harness and stores a hash-bearing score artifact, verified by test.
- Phase E: the external trainer orchestration test proves loss intervals, hash-bearing checkpoint artifacts, final-checkpoint evaluation, and database persistence. This does not certify the external trainer's learning algorithm or model quality.

A test must be capable of failing. A confident status message is not evidence.
