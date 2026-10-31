# MODEL STATUS

## Is there a model in this repo?
No. Container is infrastructure. The model is a separate, private project.

## What Container does
Schedules jobs, stores artifacts, tracks checkpoints by hash, runs evals.

## What Container does not do
Train, infer, reason, or claim any capability on its own.

## Verified by test
- [ ] Snapshot creation requires SHA-256
- [ ] Eval set hash is checked at startup
- [ ] Negative control scores worse than stub predictor
- [ ] Eval questions do not appear in training data (CI check)

## Aspirational (not yet verified)
- (empty — do not add anything here that isn't backed by a test)
