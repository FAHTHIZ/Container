# DEFERRED

Container is an infrastructure control plane. It schedules, stores, tracks,
and evaluates. It is not the model and it is not the coding-agent harness.

The following work is intentionally out of scope or blocked until its phase
gate is satisfied:

- Artemis model architecture, pretraining, continual-learning algorithms,
  non-tokenized input, sparse-memory mechanisms, and model-internal snapshot
  tournaments. Artemis remains private and separate.
- OASIS agent/harness logic: tool execution, approval policy, context
  management, orchestration, and harness-specific provider behavior. Those
  changes belong in the separate OASIS repository. Container may expose the
  infrastructure job contracts OASIS calls.
- Training loops and training jobs until the frozen evaluation (Phase C) and
  eval-job path (Phase D) pass their gates.
- A bundled model or a claim that Container independently reasons, infers,
  thinks, or has model capabilities. The existing gateway is an adapter to
  configured providers, not a model.
- Managed cloud compute as the default or required deployment. Any managed
  compute integration must be optional, clearly labelled, and never required
  for the free local/on-device path.
- Paid APIs as a required dependency, expiring free tiers as a foundation,
  subscriptions, billing, payment collection, or "add a card" flows.
- Training on a phone. The mobile profile is for control-plane work and small
  deterministic eval jobs, not model training.
- Mobile profile implementation until Phases A–F are complete: SQLite
  selection, no-Docker startup, hash-verified checkpoint-resume, retention,
  bounded network retry, and job-size limits.
- Unverified GPU allocation, distributed training, remote worker scheduling,
  and claims that the current demonstration worker is a production compute
  orchestrator.
- Provider support claims for endpoints that have not passed capability
  tests. Untested providers must be labelled as untested.

Container may implement ordinary infrastructure contracts around external
systems: job records, subprocess boundaries, immutable artifact storage,
SHA-256 provenance, resource metadata, evaluation-result tracking, and
provider capability metadata. Each capability remains unverified until its
tests pass.
