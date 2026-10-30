# Container — Architecture Decisions

This file records decisions that shape the product. Revisit a decision when evidence changes; do not silently contradict it in implementation.

## ADR-001 — Build a modular platform, not a single model

**Decision:** Container manages the lifecycle of multiple models and AI applications. It is not synonymous with any one model.

**Reason:** model architectures, providers, training methods, and inference runtimes will change independently of the platform.

## ADR-002 — Begin with a modular monolith and isolated workers

**Decision:** start with one well-structured API application and separate worker processes. Split modules into services only when scaling, deployment, or isolation requirements justify it.

**Reason:** a premature microservice fleet increases operational complexity before product boundaries are proven.

## ADR-003 — Use a hybrid compute model

**Decision:** support local, desktop, and remote/cloud execution through a common job contract. Validate hardware requirements before dispatch.

**Reason:** mobile devices are useful control surfaces and can run compatible small workloads, but are not suitable for every training job.

## ADR-004 — Separate Git source from large artifacts

**Decision:** Git stores code, schemas, small configs, and manifests. Large datasets, checkpoints, and model weights use an artifact/object store with immutable references and hashes.

**Reason:** repository history is not a scalable artifact registry.

## ADR-005 — Make evaluation a release gate

**Decision:** model changes must be evaluated against versioned suites and guardrails before promotion. Preserve baselines and rollback references.

**Reason:** an automated training loop must not treat every new checkpoint as an improvement.

## ADR-006 — Keep tool execution permissioned and observable

**Decision:** agents and workflows receive explicit tool permissions. Sensitive actions require approval and all calls are auditable.

**Reason:** model output is not a trusted authorization signal.
