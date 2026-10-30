<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Built-in Intelligence and Research

**Status:** target capability specification. This document does not claim these services are already implemented.

## 1. Built-in intelligence is part of Container

Container must be useful as an AI product from first launch. It therefore includes a first-party **Container Intelligence layer**: an inference connection, model gateway, conversation orchestrator, planning, memory, tool execution, agent runtime, and evaluation hooks.

This is more than a static prompt or a set of buttons. The managed experience must have an actual default reasoning/inference backend provisioned by Container. A user should not need to find an API key, install a model, or own a GPU to begin using the default assistant.

For self-hosted deployments, the operator must configure a compatible default inference provider or explicitly install a supported local model. Container must report a missing inference backend clearly rather than pretending that orchestration code alone is intelligent.

## 2. Intelligence components

- **Conversation orchestrator:** understands messages, attachments, conversation context, and task outcomes; streams responses and progress.
- **Model gateway:** provides a stable Container interface to managed inference, user-connected providers, imported models, and local runtime endpoints.
- **Task planner:** turns requests into validated typed plans, identifies capabilities, estimates requirements, and requests approval where needed.
- **Tool catalog:** exposes registered capabilities with schemas, descriptions, data scopes, and permission requirements.
- **Agent runtime:** executes bounded agents with explicit model, instructions, tools, memory, budgets, schedules, and approval policy.
- **Memory/retrieval:** retrieves relevant user-approved conversation, project, and knowledge context. It distinguishes temporary context, durable memory, source documents, and derived summaries.
- **Policy layer:** enforces workspace access, provider restrictions, network rules, budgets, data boundaries, and approval requirements.
- **Evaluation hooks:** record task outcomes, tool correctness, source quality, latency, cost, and user feedback without treating a fluent response as proof of correctness.

## 3. Provider independence

The managed product starts with a Container-managed default model route. Users may additionally connect:
- Commercial or hosted inference APIs.
- OpenAI-compatible or other supported model endpoints.
- Their own hosted model deployments.
- Local model servers on a connected desktop/server.
- Models imported into Container and deployed through supported runtimes.

Providers are adapters behind one gateway. The user-facing experience should not be coupled to a single provider's API, identity system, or proprietary agent format. Provider health, capabilities, limitations, rate limits, and usage should be inspectable.

Routing can consider task type, context length, modality, latency, availability, quality requirements, privacy policy, and price. It must not silently send private data to a different provider. Cross-provider fallback is allowed only when the routing policy and user consent permit it.

## 4. Research capabilities

Research should support web search and user-authorized sources such as public documentation, papers, public repositories, and permitted datasets. It should provide:
- Search and discovery.
- Source inspection and extraction.
- Citation and retrieval-time records.
- Cross-source comparison and disagreement detection.
- Research notes, reports, and saved collections.
- Reusable knowledge indexes.
- Recurring or long-running research tasks where explicitly configured.

Source access must respect applicable terms, robots policies, rate limits, privacy requirements, copyright restrictions, and authentication boundaries. Do not bypass paywalls, access controls, or private accounts. Do not treat every search result as licensed training material.

## 5. Knowledge, memory, and learning are different

Container must make these distinctions explicit:

| Mechanism | Purpose | Does it change model weights? |
|---|---|---|
| Conversation context | Supplies relevant recent turns to the current response. | No |
| Retrieval | Finds relevant documents and evidence when needed. | No |
| Persistent memory | Retains approved facts, preferences, or project state. | No |
| Skill acquisition | Adds tested procedures, tool definitions, or reusable workflows. | Usually no |
| Fine-tuning | Adjusts a model using an approved training dataset. | Yes |
| Distillation | Trains a smaller candidate using validated teacher outputs/data. | Yes |
| Architecture/model research | Tests alternative model structures and learning methods. | Potentially |

Browsing a web page does not automatically update model weights. Container must preserve source material and retrieval references separately from any training dataset. A training run is a separate, budgeted, reproducible operation.

## 6. Continuous research and improvement cycle

Container should provide reusable workflows for an authorized learning/research system:

1. **Observe:** discover information through permitted sources and user-approved data.
2. **Acquire:** record provenance, retrieval time, terms, hashes, and access scope.
3. **Organize:** parse, classify, deduplicate, index, and link claims to their evidence.
4. **Identify gaps:** compare current tested capabilities and knowledge against defined objectives.
5. **Research:** formulate questions and collect additional evidence.
6. **Propose:** create candidate datasets, skills, experiments, or model changes.
7. **Execute:** run approved processing, training, or evaluation jobs on compatible compute.
8. **Evaluate independently:** compare against baselines, holdout data, adversarial cases, and regression suites.
9. **Retain or reject:** preserve validated artifacts and lineage; quarantine or discard failed candidates according to retention policy.
10. **Repeat:** use evaluation results to prioritize the next research cycle.

This is an engineering framework for continuous improvement. It does not guarantee general intelligence, autonomous scientific discovery, or that more internet data necessarily produces a better model.

## 7. Training and adaptation lifecycle

Training capabilities should be exposed only when a compatible method and worker are available. Planned methods may include:
- LoRA/QLoRA fine-tuning for compatible models.
- Continued training where licenses, data, architecture, and resources permit.
- Supervised fine-tuning and preference optimization.
- Distillation into smaller candidate models.
- Quantization and format conversion for deployment.
- Multimodal adaptation where model/tool support exists.

Full foundation-model pretraining is a distinct high-cost workstream and must not be implied by a basic fine-tuning feature.

Every run references immutable model, dataset, code, configuration, and environment revisions; stores logs/checkpoints; records compute cost; and produces a candidate version for evaluation.

## 8. Trust and safety controls

- Treat web pages, documents, repositories, tool results, model outputs, and uploaded archives as untrusted data.
- Retrieved instructions never override system policy or user permissions.
- Separate source evidence from generated summaries and hypotheses.
- Record citations and uncertainty for source-based claims.
- Do not train on user conversations/files by default. Any opt-in use needs explicit, revocable consent and clear data scope.
- Do not silently expand agent permissions, export private data, spend beyond budget, or perform irreversible external actions.
- Research and experiment jobs can be bounded and autonomous within configured permissions; deployment promotion, credential changes, permission expansion, and consequential external actions require approval.
- Keep immutable experiment history and rollback paths.

## 9. Success measures

Measure useful behavior rather than anthropomorphic claims:
- Task completion and verified tool-result rate.
- Citation coverage and source correctness.
- Retrieval relevance and stale/contradictory evidence rate.
- Model/agent benchmark performance and regression rate.
- Cost, latency, availability, and provider fallback success.
- Data provenance completeness and policy violations.
- Human approval rate, rejected actions, and recovery success.

No release should claim a capability based only on a model's self-assessment.
