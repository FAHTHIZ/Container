# CONTAINER — BUILD SPEC

> This document is the implementation contract for Container. Read it before changing code. When it conflicts with a proposed implementation, this document wins.

## Identity

**Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.**

Container is a cloud control plane for accounts, workspaces, projects, jobs, artifacts, model metadata, and API keys. It is not a model, training framework, inference engine, reasoning system, or replacement for the separate OASIS harness.

The private model project is separate from this repository. Keep model architecture and model-specific learning mechanisms out of Container.

## Honest baseline

The repository currently provides a FastAPI control plane, authentication, workspaces/projects/jobs/artifacts, upload SHA-256 hashing, Alembic migrations, Docker Compose, CI, and architecture/status documentation. The worker executes only harmless demonstration jobs. Model records are metadata.

There is no training loop, evaluation harness (until Phase C is implemented and verified), model checkpoint hashing/versioning, real compute orchestration, trained model, or evaluation result that supports a model capability claim.

A checked status item means its implementation is committed and a test passes. It does not mean production-ready.

## Rules for changes

1. Never claim a capability that code and tests do not prove.
2. Build a frozen evaluation harness before any training implementation. Refuse training work until Phase C passes.
3. Fail closed: validation, filters, and guards reject on errors. Do not add silent exception handling or exception-driven filter bypasses.
4. A snapshot or checkpoint must include the SHA-256 of the exact stored bytes. No hash means no snapshot.
5. Any future training loop must emit loss at a documented interval and save hash-verified checkpoint artifacts.
6. Explain non-trivial code in plain English. For code blocks longer than about 15 lines, add a 3–5 sentence explanation.
7. Prefer standard libraries, boring patterns, and minimal dependencies.
8. Keep evaluation and training code heavily commented and reviewable line by line.

## Phase order

### Phase A — Make the scaffold honest
- Add or extend tests for checked functionality.
- Add \`MODEL_STATUS.md\` and \`DEFERRED.md\`.
- Audit exception handling and fail-closed validation.
- CI must run tests and fail on lint errors.

### Phase B — Artifact and snapshot hashing
- Preserve the existing SHA-256 upload implementation.
- Add a database Snapshot record with ID, timestamp, digest, immutable stored path, and metadata.
- Add \`create_snapshot(path)\`; it must fail when the source is missing, unreadable, mutable during capture, or cannot be hashed and stored.
- Test that a missing file cannot produce a snapshot.

### Phase C — Frozen evaluation (before training)
- Store a frozen task set at \`eval/data/eval.jsonl\` and its SHA-256 at \`eval/data/eval.sha256\`.
- Verify the hash before reading or scoring tasks. A mismatch, missing file, malformed task, or unreadable input is a hard failure.
- Run a supplied prediction function and score deterministically (exact match; no LLM judge).
- Print the eval hash, model ID, score, task count, and UTC timestamp.
- Provide a negative control that returns deliberately incorrect predictions and proves its score is strictly below a known-good deterministic test predictor.
- CI must reject exact evaluation questions found in designated training-data directories.
- Document task additions and hash regeneration.

The initial evaluation fixture is a plumbing test, not a general model benchmark. It must not be presented as evidence of model quality.

### Phase D — Evaluation jobs, no training
- Add only the \`eval_run\` job type.
- Inputs: \`model_id\`, \`eval_path\`, and \`eval_hash\`.
- Run the verified evaluation harness as a subprocess.
- Return \`score\`, \`n_tasks\`, \`eval_hash\`, and \`model_id\`.
- Persist the result as an artifact with SHA-256.
- Test the complete submission-to-artifact path.
- Do not claim real compute orchestration beyond the execution path actually tested.

### Phase E — Training (only after Phase C passes)
- Training jobs must print loss every N steps.
- Each saved checkpoint must be accompanied by its SHA-256.
- Run the frozen evaluation harness against the resulting checkpoint.
- Persist checkpoint hash and evaluation score together.
- Do not make quality claims beyond measured evaluation results.
- Keep the training code heavily commented and explain it line by line when requested.

## Frozen evaluation requirements

The eval set is versioned, hashed, deterministic, and quarantined from training data. Changing it requires regenerating and reviewing the hash file. No random sampling and no model-as-judge scoring. The negative control must be strictly worse than the known-good stub predictor; otherwise the harness is not trusted.

## Deferred boundaries

This repository does not implement model architecture, novel learning algorithms, non-tokenized input, memory-heavy sparsity, snapshot attribution tournaments, continual learning, or multi-source model fact-checking. Those belong in the separate model project. Container may add the job, artifact, provenance, and evaluation plumbing that an external model runtime needs.

Do not use unsupported labels such as "AGI", "frontier-level", or "state of the art" in code, docs, commits, or release notes.

## Definition of done

- Phase A: every checked status item has test coverage; model and deferred status files exist; CI passes.
- Phase B: a test proves a missing/unreadable source cannot produce a snapshot and every created snapshot has a digest.
- Phase C: startup hash verification passes; tampering is rejected; negative control scores strictly worse; training-data quarantine check is in CI.
- Phase D: a submitted job runs the harness and stores a hash-bearing score artifact, verified by test.
- Phase E: a training job stores hash-bearing checkpoints and their corresponding evaluation results. No unsupported quality claims.

A test must be capable of failing. A confident status message is not evidence.
