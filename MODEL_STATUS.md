# MODEL STATUS

## Is there a model in this repo?

No. Container is infrastructure. The model is Artemis (private, separate repo).
The harness is OASIS (separate repo).

## What Container does

Schedules jobs, stores artifacts, and tracks infrastructure metadata. The
current branch also has preliminary snapshot-capture and frozen-eval plumbing.
Those components are not yet evidence that the complete phase gates pass.

## What Container does not do

Train a model, contain a bundled model, or reason on its own. The existing
inference gateway is a connection layer to a configured provider, not a model
inside Container.

## Verified by test

- [ ] Snapshot creation requires SHA-256
- [ ] Snapshot verification detects stored-file mutation
- [ ] Eval set hash is checked before scoring
- [ ] Negative control scores worse than the known-good stub
- [ ] Eval questions are excluded from training data by a CI check
- [ ] Provider with supports_tools=false receives no tool calls

## Current implementation gaps

- Snapshot capture code and tests exist, but there is no verify_snapshot API,
  stored-file mutation test, size_bytes field, or Checkpoint extension.
- The frozen eval dataset, hash check, exact-match runner, negative control,
  and unit tests exist. The CI workflow does not yet run the repository-wide
  quarantine scan against actual training-data directories.
- The eval_run job, provider capability registry, and no-tool-call capability
  test are not implemented.

These observations describe files present on the current branch. They are not
marked "Verified" until the corresponding tests pass in CI.

## Aspirational (not yet verified)

- (empty)

## Rule

If an item is not backed by a passing test, it does not go in "Verified."
Do not populate "Aspirational" with unmeasured marketing claims.
