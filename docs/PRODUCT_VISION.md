<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Product Vision

**Status:** product direction. Implementation status is tracked separately in [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

## 1. Product definition

Container is a personal AI facility for anyone who wants to use, connect, research, adapt, train, evaluate, and operate AI systems without having to assemble the infrastructure by hand.

The user-facing product is a single conversation. A person can ask for help, paste a model URL, upload an archive, connect an endpoint, or describe a task. Container interprets the request, identifies the relevant capability, explains important decisions, and carries out the work through its internal systems.

The facility is broad; the interface is deliberately narrow. The product must not expose its internal architecture as dozens of permanent tabs.

## 2. Audience

Container is for anyone, including:
- People who simply want to use an existing model.
- Creators who want a personal assistant or agent.
- Developers connecting APIs, tools, and workflows.
- Researchers collecting sources, comparing models, or preparing datasets.
- Advanced users training, evaluating, and deploying models.

The product should support beginners without hiding the evidence, controls, and reproducibility that advanced users need. Individual ownership is the first product priority. The data model should leave room for collaboration and team membership later without making team administration the first-run experience.

## 3. Core interaction

### Primary surface

The initial screen is a clean chat:
- Conversation history and a single message composer.
- Paste/drop affordances for model URLs, endpoint URLs, files, and archives.
- Contextual result cards for imports, research, jobs, evaluations, and approvals.
- Minimal global controls for account, facility, and conversation/project context.
- Responsive layouts across phone, tablet, and desktop.

There is no requirement to navigate through a separate page for each capability. When a task needs advanced configuration, Container opens a focused, contextual panel or step inside the current conversation. Completed objects remain accessible through search and conversation context.

### The Core panel

A compact interactive Core sits in one corner. It is an abstract system visualization, not a human or humanoid avatar. A tap/click opens a panel containing:
- Active and queued jobs.
- Current assistant/agent activity and tool calls.
- Research and ingestion status.
- Model and provider connectivity.
- Compute allocations and resource pressure.
- Recent events, warnings, and notifications.
- Approvals awaiting the user.

The visual language is cinematic but restrained: geometric rings, layered diagnostics, thin telemetry lines, and subtle blue/cyan illumination. It should communicate state, not distract from reading or conversation.

### Progressive disclosure

Container may have many internal capabilities, but only the controls relevant to the current task should appear. For example:
- Pasting a model repository link opens the import inspection flow.
- Asking to train a model opens dataset, training, resource, and budget choices.
- Asking for web research opens source scope, citations, and research progress.
- Creating an agent reveals model, tools, permissions, memory, and approval settings.
- A deployment request reveals endpoint access, scaling, usage, and rollback settings.

Advanced users can open detailed views when needed. These are contextual task views, not a large fixed tab bar.

## 4. First-run experience

A new user should be able to start without first learning model infrastructure.

1. Sign in or create an account.
2. Land directly in the conversation.
3. Use Container's first-party built-in intelligence immediately in the managed experience; no user API key is required for the default path.
4. Paste a supported model URL, upload a file, connect an endpoint, or simply ask a question.
5. Container classifies the request and explains any required storage, permission, compatibility, or cost decisions.
6. Container performs the task and streams meaningful progress.
7. The user receives a usable result and can continue the conversation.

A self-hosted installation must configure a default inference source or explicitly install/select a compatible local model. Documentation must not imply that a reasoning model is magically available without an inference backend.

## 5. Internal capability catalog

The following are product capabilities, not mandatory top-level screens:

1. **Conversation and built-in intelligence:** request understanding, planning, model routing, tool selection, streaming, context management, and task summaries.
2. **Model library:** imported/connected models, model lineage, versions, files, metadata, licenses, runtime compatibility, and lifecycle state.
3. **Model import:** repositories, direct URLs, archives, local files, model packages, hosted endpoints, and local runtime endpoints.
4. **Provider center:** managed default provider, external provider adapters, endpoint credentials, capability discovery, health, usage, limits, routing, and fallback policies.
5. **Agent workshop:** agent definitions, instructions, models, tools, permissions, memory, budgets, schedules, collaboration, templates, tests, and run history.
6. **Research center:** web search, permitted source ingestion, papers, repositories, source comparison, extraction, citations, research missions, and reports.
7. **Knowledge and memory:** document collections, full-text/semantic search, optional vector indexes, knowledge relationships, conversation memory, project memory, agent memory, retention, and deletion.
8. **Dataset workshop:** source tracking, import, parsing, cleaning, deduplication, language/format classification, quality checks, licensing/provenance, sensitive-data review, versioning, and lineage.
9. **Model foundry:** supported fine-tuning, adapter training, continued training where feasible, distillation workflows, quantization, checkpointing, experiment tracking, and resource estimates.
10. **Evaluation arena:** repeatable benchmarks, model/agent comparisons, factuality and tool-use tests, multilingual tests, safety checks, regression suites, and release gates.
11. **Inference and deployment:** local/remote serving adapters, authenticated APIs, compatible OpenAI-style endpoints where supported, streaming, batch execution, monitoring, scaling, rollback, and usage limits.
12. **Multimodal capabilities:** connected image, audio, speech, video, document, and other specialized model/tool integrations.
13. **Compute and facilities:** capability discovery, managed workers, optional user-owned workers, external compute adapters, queues, quotas, storage, cost estimates, and job recovery.
14. **Security and ecosystem:** identity, permissions, credentials, auditing, sandboxing, extension/provider registries, SDKs, connector templates, backups, and data export/deletion.

Capability support is adapter- and version-dependent. The user experience should explain what is currently supported rather than advertise universal compatibility.

## 6. Product modes

The product should remain one interface while supporting different deployment profiles:
- **Managed:** the default experience, with Container-managed intelligence and remote compute.
- **Connected:** users bring external model providers, endpoints, or compute.
- **Self-hosted:** users operate the API, storage, workers, and configured inference provider on their own infrastructure.
- **Hybrid:** any combination of managed, connected, and user-owned resources under explicit routing and policy.

Do not make users choose a complex installation profile before they understand the product. Offer advanced deployment choices when appropriate.

## 7. Product quality principles

- A beginner can complete the first model connection without reading infrastructure documentation.
- No silent chargeable compute, provider use, or external side effects.
- Every long task has a visible state, history, and useful failure explanation.
- User data and credentials are private by default; training on user data requires explicit policy and consent.
- Advanced controls are discoverable but do not clutter the conversation.
- All clients share the same facility state and permissions.
- The product is honest about unsupported formats, model limitations, costs, and incomplete capabilities.
