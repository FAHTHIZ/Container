# DEFERRED

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

The following work is intentionally out of scope for this repository:

- Model architecture, pretraining, fine-tuning algorithms, and model-specific training loops. Container has no approved external trainer adapter contract yet; it must not invent a learning algorithm or pretend that a fixture is real training.
- Model inference, reasoning, or a bundled model runtime.
- The separate private model project and its internal architecture.
- OASIS agent/harness functionality.
- Non-tokenized input, novel sparse-memory mechanisms, continual learning, and multi-source model reasoning.
- Claims of general intelligence, frontier capability, or state-of-the-art performance.
- Unverified GPU scheduling, distributed training, or claims that the current database-polling worker is a production compute orchestrator.

Container may implement the ordinary infrastructure contracts around external systems: job records, reviewed adapter interfaces, subprocess timeouts, immutable artifact storage, SHA-256 provenance, resource metadata, and evaluation-result tracking. A training adapter can be considered only when its input/output contract is reviewed and its loss, checkpoint, hash, and evaluation behavior can be tested. Until then, Phase E remains deferred.
