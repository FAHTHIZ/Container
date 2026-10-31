# CONTAINER — BUILD SPEC

> This document is the implementation contract for Container. Read it before changing code. When it conflicts with a proposed implementation, this document wins.

## Identity

**Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.**

Container is a cloud control plane for accounts, workspaces, projects, jobs, artifacts, model metadata, and API keys. It is not a model, training framework, inference engine, reasoning system, or replacement for the separate OASIS harness.

Artemis is a private model project in a separate repository. OASIS is a separate harness. Keep both out of Container and do not conflate them.

## Honest baseline

The repository provides a FastAPI control plane, authentication, workspaces/projects/jobs/artifacts, upload SHA-256 hashing, Alembic migrations, Docker Compose, CI, and architecture/status documentation. The worker executes harmless demonstration jobs and the tested eval_run path. Model records are metadata.

There is no model, training loop, evaluation result for trained weights, model checkpoint history, or real compute scheduler. The worker is a single database-polling process; an eval_run adapter is trusted operator code, not a sandbox.

A checked status item means its implementation is committed and a test passes. It does not mean production-ready.

## Rules for changes

1. Never claim a capability that code and tests do not prove.
2. A frozen evaluation harness must exist and pass its negative control before any training integration is considered.
3. Fail closed: validation, filters, and guards reject on errors. Do not add silent exception handling or exception-driven filter bypasses.
4. A snapshot or checkpoint must include the SHA-256 of the exact stored bytes. No hash means no snapshot.
5. Any future external trainer must emit loss at a documented interval and provide hash-verified checkpoints at its requested save intervals. Container must verify these outputs and run the frozen evaluation against the final checkpoint.
6. Explain non-trivial code in plain English. For code blocks longer than about 15 lines, add a 3–5 sentence explanation.
7. Prefer standard libraries, boring patterns, and minimal dependencies.
8. Keep evaluation and any future trainer adapter code heavily commented and reviewable line by line.

## Verified phases

### Phase A — Make the scaffold honest

- [x] Existing API features mapped to automated tests.
- [x] MODEL_STATUS.md and DEFERRED.md added.
- [x] Python exception handling reviewed for silent filter bypasses.
- [x] CI runs lint and tests.

### Phase B — Artifact and snapshot hashing

- [x] Snapshot database record requires SHA-256.
- [x] create_snapshot copies to content-addressed storage and re-verifies stored bytes.
- [x] Missing/unreadable sources cannot create a snapshot.

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

## Phase E — Deferred external trainer integration

Container must not contain a model-specific learning loop or pretend to train by writing dummy files. No approved external trainer adapter is currently supplied in this repository.

A future Phase E integration may only orchestrate a separately reviewed trainer through a trusted, operator-configured adapter. Before marking it implemented, tests must prove that the adapter emits loss every N steps, saves a checkpoint with a verified SHA-256 every M steps, and that the final checkpoint is passed to the frozen eval harness. The checkpoint hash and evaluation score must be stored together in the database. A test fixture is contract verification, not a trained model or a quality claim.

## Frozen evaluation requirements

The eval set is versioned, hashed, deterministic, and quarantined from training data. Changing it requires regenerating and reviewing the hash file. No random sampling and no model-as-judge scoring. The negative control must be strictly worse than the known-good stub predictor; otherwise the harness is not trusted.

## Deferred boundaries

This repository does not implement model architecture, learning algorithms, inference, non-tokenized input, memory-heavy sparsity, snapshot attribution tournaments, continual learning, or multi-source model reasoning. Those belong in the separate model project. Container may add job, artifact, provenance, resource metadata, and evaluation plumbing for reviewed external systems.

Do not make unsupported intelligence, frontier-capability, or state-of-the-art claims in code, docs, commits, or release notes.

## Definition of done

- Phase A: every checked status item has test coverage; model and deferred status files exist; CI passes.
- Phase B: a test proves a missing/unreadable source cannot produce a snapshot and every created snapshot has a digest.
- Phase C: startup hash verification passes; tampering is rejected; negative control scores strictly worse; training-data quarantine check is in CI.
- Phase D: a submitted job runs the harness and stores a hash-bearing score artifact, verified by test.
- Phase E: a reviewed external trainer produces hash-bearing checkpoints and a final eval result, with both recorded in the database. No unsupported quality claims.

A test must be capable of failing. A confident status message is not evidence.
