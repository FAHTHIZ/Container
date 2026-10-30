<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Architecture Decisions

Architecture decisions are durable product/engineering constraints. Revisit them when evidence changes; document replacements rather than silently contradicting them.

## ADR-001 — Container is the facility, not one model

**Decision:** Container is an AI-powered platform for model use, import, adaptation, evaluation, inference, research, data, agents, and operations. It does not depend on a single foundation model.

**Reason:** model families, providers, runtimes, and training methods evolve independently. The product must remain useful while any one model or provider changes.

## ADR-002 — Modular monolith first

**Decision:** start with a modular FastAPI application and isolated worker processes. Split domains into services only when scale, security boundaries, or operational constraints justify it.

**Reason:** premature microservices add complexity before domain boundaries are proven.

## ADR-003 — PostgreSQL is the control-plane source of truth

**Decision:** store identity, ownership, configuration, job state, events, model/provider metadata, and relational lineage in PostgreSQL. Store large datasets, checkpoints, and model weights in private object storage.

**Reason:** ownership and state transitions need transactions; Git and relational rows are not large artifact registries.

## ADR-004 — Durable jobs evolve in stages

**Decision:** begin with durable database job rows and a separate polling worker. Introduce a broker, transactional outbox, leases, and bounded retries when throughput and worker count justify them. Add durable workflow orchestration for long-running approval/recovery processes.

**Reason:** verify job contracts before adding infrastructure. Worker handlers must be idempotent because queues can retry or redeliver work.

## ADR-005 — Cloud-first hybrid compute

**Decision:** managed remote inference and compute are the default in the managed experience. External cloud resources and user-owned local workers are optional. Phones are primarily control clients.

**Reason:** the product must work for people without powerful hardware while still allowing advanced users to use their own resources.

## ADR-006 — Evaluation gates model releases

**Decision:** candidate model changes require versioned evaluation against baselines and guardrails before promotion. Preserve release history and rollback references.

**Reason:** a new checkpoint is not automatically a better model.

## ADR-007 — Agents get explicit tool permissions

**Decision:** agent tools are schema-defined, allowlisted, scoped, rate-limited, and audited. Sensitive or irreversible actions require approval.

**Reason:** model-generated text is not an authorization decision.

## ADR-008 — Conversation is the primary interface

**Decision:** the main user experience is a single conversation with contextual task surfaces and a compact interactive Core panel. Capabilities are progressively disclosed rather than exposed as dozens of permanent tabs.

**Reason:** Container must be approachable to beginners while retaining advanced capabilities behind the same interaction model.

## ADR-009 — Built-in intelligence is first-party

**Decision:** Container includes a first-party intelligence layer and a default managed inference route. Users do not need to provide an API key to use the managed first-run experience. The provider gateway also supports optional external and user-owned models.

**Reason:** orchestration without a reasoning backend is not a useful built-in AI experience. Provider independence prevents lock-in.

## ADR-010 — Model import is multi-source and inspect-before-use

**Decision:** model repositories, direct files, ZIP archives, local uploads, hosted endpoints, and local runtime endpoints have distinct adapters and validation paths. No import source is trusted by default.

**Reason:** endpoints should not be downloaded like files, archives have security risks, and model formats require runtime-specific compatibility checks.

## ADR-011 — One facility across clients

**Decision:** browser, Android, and desktop clients use the same identity, versioned APIs, data model, and job system. Self-hosting uses the same product contracts.

**Reason:** device packaging must not fragment the user experience or state.

## ADR-012 — Research preserves provenance and permission

**Decision:** public and user-authorized sources are acquired under access, terms, privacy, rate, and copyright constraints. Research records provenance, retrieval time, and links to evidence. Retrieved content is untrusted input.

**Reason:** internet access is not permission to ignore access controls or train on every retrieved document.

## ADR-013 — Capability-based resource scheduling

**Decision:** every workload declares compute, memory, storage, runtime, network, privacy, and budget needs. The scheduler dispatches only to compatible authorized workers.

**Reason:** device and model capabilities vary; silent best-effort execution creates cost and reliability failures.

## ADR-014 — Advanced capability does not require advanced navigation

**Decision:** model training, data, evaluation, deployment, provider, security, and research systems remain modular internally but are surfaced contextually through conversation and focused panels.

**Reason:** product simplicity is achieved by progressive disclosure, not by removing technical capability.
