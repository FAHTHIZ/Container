<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Architecture Decisions

## ADR-001 — Container manages multiple models

**Decision:** Container is the platform/control plane around models, datasets, inference, agents, and applications. It is not the same product as ARTEMUS or any other model.

**Reason:** model families, training methods, runtimes, and providers evolve independently.

## ADR-002 — Modular monolith first

**Decision:** start with a modular FastAPI application and isolated worker processes. Split domains into services only when scale, deployment, or isolation requirements justify it.

**Reason:** premature microservices add operational complexity before the actual domain boundaries are proven.

## ADR-003 — PostgreSQL is the control-plane source of truth

**Decision:** store users, workspaces, projects, job state, event history, and registry metadata in PostgreSQL. Store large datasets/checkpoints/model weights in object storage.

**Reason:** ownership and state transitions need transactions; Git and relational rows are not large artifact registries.

## ADR-004 — Worker queue evolves in stages

**Decision:** begin with durable database job rows and a separate polling worker. Introduce a broker and transactional outbox when throughput/concurrency justifies it. Add a durable workflow engine for long-running multi-step processes.

**Reason:** verify job contracts and state transitions before adding infrastructure. Worker handlers must be idempotent because delivery systems may retry or redeliver work.

## ADR-005 — Hybrid compute is a product requirement

**Decision:** support phone, desktop, and remote workers through a common job/runtime capability interface.

**Reason:** phones are useful control surfaces and can run compatible small workloads, but cannot be assumed to have the resources for every training task.

## ADR-006 — Evaluation gates model releases

**Decision:** model changes require versioned evaluation against baselines and guardrails before promotion. Preserve release history and rollback references.

**Reason:** a new checkpoint is not automatically a better model.

## ADR-007 — Agents get explicit tool permissions

**Decision:** agent tools are schema-defined, allowlisted, scoped, rate-limited, and audited. Sensitive actions require human approval.

**Reason:** model-generated text is not an authorization decision.
