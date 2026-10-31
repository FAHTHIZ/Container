# MODEL STATUS

## Is there a model in this repo?
No. Container is infrastructure. The model is Artemis (private, separate repo).

## What Container does
Schedules jobs, stores artifacts, tracks checkpoints by hash, runs evals.

## What Container does not do
Train, infer, reason, or claim any capability on its own.

## Verified by test
- [x] Snapshot creation requires SHA-256
- [x] Eval set hash is checked at startup
- [x] Negative control scores worse than stub predictor
- [x] Eval questions do not appear in training data (CI check)

## Aspirational (not yet verified)
- (empty — do not add anything here that isn't backed by a test)
