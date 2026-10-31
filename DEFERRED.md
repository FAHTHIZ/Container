# DEFERRED

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

The following work is intentionally out of scope for this repository:

- Model architecture, pretraining, fine-tuning algorithms, and training loops before the frozen evaluation harness passes.
- Model inference, reasoning, or a bundled model runtime.
- The separate private model project and its internal architecture.
- OASIS agent/harness functionality.
- Non-tokenized input, novel sparse-memory mechanisms, continual learning, and multi-source model reasoning.
- Claims of general intelligence, frontier capability, or state-of-the-art performance.
- Unverified GPU scheduling, distributed training, or claims that the current demo worker is a production compute orchestrator.

Container may implement the ordinary infrastructure contracts around external systems: job records, subprocess boundaries, immutable artifact storage, SHA-256 provenance, resource metadata, and evaluation-result tracking. Each capability remains unchecked until its tests pass.
