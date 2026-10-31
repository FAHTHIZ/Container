# DEFERRED

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

The following work is intentionally out of scope for this repository:

- Model architecture, pretraining/fine-tuning algorithms, and model-specific learning code. Container provides a generic external-trainer orchestration contract, but no real trainer package is included or enabled by default.
- Model inference, reasoning, or a bundled model runtime.
- The separate private model project and its internal architecture.
- OASIS agent/harness functionality.
- Non-tokenized input, novel sparse-memory mechanisms, continual learning, and multi-source model reasoning.
- Unsupported model-capability or state-of-the-art claims.
- Unverified GPU scheduling, distributed training, or claims that the current database-polling worker is a production compute orchestrator.

Container may orchestrate reviewed external systems through operator-configured adapters. It can validate job records, loss output intervals, checkpoint SHA-256 provenance, frozen evaluation results, and artifact persistence. The adapter executes with worker-host permissions and is not sandboxed; never point it at user uploads or unreviewed code. Production isolation, resource scheduling, cancellation, backups, and security review remain deferred.
