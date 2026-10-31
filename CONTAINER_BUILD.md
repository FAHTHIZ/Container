# CONTAINER — BUILD CONTRACT

> **READ THIS FILE BEFORE EVERY CODE CHANGE.**
> This file is the single source of truth for what Container is, what it is
> not, what has already gone wrong, and the rules that prevent it from going
> wrong again. It supersedes any instruction given in chat. If a chat message
> conflicts with this file, **this file wins** and you must say so.
>
> If you are an AI assistant and you are about to generate code, stop and
> re-read §2 (Hard Constraints) and §3 (The Drift). Most mistakes happen
> because those two sections were skipped.

---

## 0. HOW TO USE THIS FILE

- You are helping a **solo developer** build **Container**.
- The developer is a **vibe coder**: strong product instincts, fast iteration,
  limited deep ML/systems background. You must **explain every non-trivial
  line you generate in plain English**, in the same message. Assume the
  reader will read the explanation, not the code.
- The developer is building **three separate things**. Do not conflate them
  (see §1).
- The developer has **no budget for paid services**. This is not a preference.
  It is a hard constraint (§2).
- The developer values **honest documentation over impressive documentation**.
  A file that says "not implemented" is worth more than a file that implies
  capability. Never optimize for how the repo *looks*.

---

## 1. THE THREE PROJECTS (DO NOT CONFLATE)

| Project | What it is | Where it lives | Who owns it |
|---|---|---|---|
| **Container** | Infrastructure control plane. Schedules jobs, stores artifacts, hashes snapshots, runs evals. **Contains no model.** | This repo | You are building this |
| **OASIS** | The coding agent harness. Tools, approvals, context management, provider adapters, eval fixtures. | Separate repo (**FAHTHIZ/oasis**) | Already exists; do not duplicate here |
| **Artemis** | The model. Novel architecture, non-tokenized input, memory-heavy sparsity, continual learning. | Private, not in any public repo | The developer is building this separately |

**Rules:**
- Container **does not train**. It runs jobs that *could* be training jobs, once Artemis exists.
- Container **does not reason**. It schedules, stores, tracks, and evaluates.
- Container **does not implement** the Artemis architecture, the 70/30 memory split, the snapshot tournament, or multi-source fact-checking. Those are Artemis concerns.
- OASIS **does not live here**. If the developer asks for a harness feature, say: *"That belongs in OASIS. I can help you build the Container job type that OASIS will call, but the harness logic stays in the OASIS repo."*

**If the developer asks Container to "think," "reason," "be AGI," or "train itself":** refuse, explain the separation, and offer the infrastructure equivalent (a job type, an artifact schema, an eval runner).

---

## 2. HARD CONSTRAINTS (NON-NEGOTIABLE)

These are not preferences. Code that violates them must not be merged.

### 2.1 No paid services, ever
- No managed cloud compute as a default path.
- No paid API required for the tool to work.
- No "free tier that expires" as a core dependency.
- No subscriptions, no billing, no "add your card to continue."

### 2.2 Free and on-device is the primary path
- The default deployment target is **a phone or a laptop with no paid services**.
- The default model path is **local models via Ollama / llama.cpp / LM Studio**.
- Free gateways (OmniRoute, FreeLLMAPI) are **convenience**, not foundation.
- If a feature only works with a paid service, it is **optional and clearly labelled**, never the default.

### 2.3 Fail closed
- Every filter, validator, guard, or check must **reject on error**, never pass on error.
- No silent exception handling that lets an operation proceed.
- No bare except/pass. No exception-driven filter bypasses. No "if the check fails, skip it."
- If a validation cannot run (missing file, network error, timeout), the operation **fails**, it does not proceed.

### 2.4 Hash everything that claims to be a snapshot
- Any artifact called a "snapshot," "checkpoint," or "version" **must** carry a SHA-256 of its contents, stored alongside it.
- No hash = not a snapshot. It is a file with an aspirational name.
- Snapshot creation must **refuse** if the hash cannot be computed.

### 2.5 Print the loss
- Any training code (Phase E and later) must print loss every N steps.
- If a training loop is generated without a loss print, it is incomplete.

### 2.6 The eval is frozen and quarantined
- The eval set is stored as a file with a hash.
- Re-running without changing the file produces the same hash.
- The eval set must never appear in any training data, in any snapshot, in any teacher-model dialogue, or in any user feedback log.
- A CI check must scan designated training data for eval questions and fail if any are found.

### 2.7 No capability claims without a test
- Claims such as "frontier-level," "competitive with a named model," "state of the art," "AGI," and "extremely powerful" are **forbidden** in code, docs, commit messages, and UI copy unless a test and an eval number back them.
- An empty MODEL_STATUS.md "Aspirational" section is correct. A populated one without tests is a lie.

---

## 3. THE DRIFT (WHAT WENT WRONG, AND HOW TO NOT REPEAT IT)

### 3.1 What happened

A previous build session produced a polished, coherent Container. It has:
- FastAPI backend
- Argon2 auth
- Workspaces, memberships
- Persistent job records
- Bounded artifact storage with SHA-256 on uploads
- A model registry (metadata only)
- A Studio UI and PWA shell
- An inference gateway

All real. All reusable. **None of it is the problem.**

The problem was the **framing** in the README:

> "Container is **cloud-first and hybrid**: Managed remote compute is the default for work that exceeds ordinary device capabilities."

> "Remote GPU time, storage, networking, and managed inference have real costs. Container must show estimates and usage, enforce quotas, and require the user's consent for chargeable work."

That is a **paid-managed-compute product**. It contradicts §2.1 and §2.2 directly. It was not a code bug — it was a **scope drift**.

### 3.2 The original gap list and the current audit

The original gap list was written before the latest merge. The current main
branch now contains **partial implementations** of snapshot creation and the
frozen eval runner. Do not rebuild those modules. Their remaining gaps are
listed in §4.3 and must be closed by tests. The presence of code is not proof
that a phase gate has passed.

The following are still missing or incomplete:
- Snapshot verification and mutation-detection for stored snapshot files.
- Snapshot size metadata and the required Checkpoint extension.
- Invocation of the eval quarantine scan in CI against actual training-data directories.
- The eval_run job type and its end-to-end artifact test.
- Provider capability metadata and the adapt-don't-assume test.
- The documented free mobile profile and its SQLite/no-Docker/resume work.
- Local-first README framing and status/documentation alignment.

### 3.3 The rule that prevents a repeat

**This file and the other three guardrail documents must be committed before
any further code change.** Every subsequent change must cite the section it
satisfies. If a change cannot cite a section, it needs a docs/DECISIONS.md
entry explaining why it is in scope.

**When scope drifts toward "bigger product":**
Stop. Ask: *"Does this satisfy Phase A, B, or C? If not, it is Phase Z and
it waits."* The foundation phases come first. Always.

---

## 4. WHAT EXISTS TODAY (AUDIT BEFORE BUILDING)

Do not delete working code. Do not rebuild what works. Audit, then adjust.

### 4.1 Keep (real, reusable; tests still determine verified status)
- Auth (Argon2, sessions, registration/login)
- Workspaces and memberships
- Job records (persistent, scoped)
- Artifact storage with SHA-256 on uploads
- Database migrations (Alembic)
- Docker Compose (for the **server** profile — see §10)
- CI pipeline

### 4.2 Demote (change framing, keep code)
- **Managed remote compute**: remove as default. Move it to an optional, clearly-labelled, non-default profile. The default becomes local/on-device.
- **Cloud-first README framing**: rewrite to local-first. The README opening must describe the free, on-device path first, and the optional managed path second (or not at all).
- **Inference gateway**: keep the code, but make the default provider **local (Ollama)**. Free gateways are secondary. Paid providers are tertiary and opt-in. A gateway is not a bundled model.

### 4.3 Add or complete (the actual remaining gaps)
- Replace the older, incomplete root build contract with this file.
- Align MODEL_STATUS.md and DEFERRED.md with the actual code and these gates.
- Record the local-first decision in docs/DECISIONS.md and retire conflicting defaults.
- docs/MOBILE_PROFILE.md — document the free on-device profile.
- Snapshot completion: size_bytes, verify_snapshot(id), mutation detection, and a Checkpoint model extending Snapshot with job/eval metadata.
- Eval completion: wire the existing quarantine checker into CI so the repository-wide scan runs and fails closed.
- Phase D: the eval_run job type and a hash-bearing result artifact.
- Provider capability schema and the no-tool-calls test for providers that declare supports_tools=false.
- Mobile implementation after Phases A–F: SQLite adapter, no-Docker startup, checkpoint-resume, retention, retry, and job-size cap.

**Important audit distinction:** the repository already has services/api/src/container_api/snapshots.py,
eval/runner.py, eval/check_quarantine.py, and associated tests. These are
partial implementations to finish and verify, not missing files to recreate.

### 4.4 The documented state is not the test result

The current branch contains source files and tests for some Phase B/C behavior,
but no passing CI status was available for the current merge commit during
this audit. Therefore this contract does **not** mark those gates complete.
A test file existing is not the same thing as a passing test run.

---

## 5. GROUND RULES FOR THE ASSISTANT

1. **Read this file before generating code.** Cite the section you are satisfying in your response.
2. **Never claim a capability the repo does not have.** If asked to add unsupported intelligence features, respond with the separation (§1) and offer the infrastructure equivalent.
3. **Eval before training.** Do not generate a training loop until §7 (the eval) exists and passes its negative-control test. If asked for training code first, refuse and offer the eval harness.
4. **Fail closed.** (§2.3) Every guard rejects on error.
5. **Hash snapshots.** (§2.4) No hash, no snapshot.
6. **Print the loss.** (§2.5) Any training code.
7. **Explain in plain English.** For any code block longer than about 15 lines, add a 3–5 sentence plain-English explanation.
8. **Prefer boring.** Standard libraries, standard patterns, minimal dependencies. No custom frameworks. No "clever" abstractions.
9. **Do not vibe-code the eval or the training loop.** These are the two files the developer must read line by line. Generate them with heavy comments and offer to walk through them.
10. **Update status files with every change.** If you add a feature, update docs/IMPLEMENTATION_STATUS.md. If you add a test, mark the corresponding item in MODEL_STATUS.md only after the test has passed. Never let the status files lag behind the code.

---

## 6. PHASE PLAN (IN ORDER, WITH GATES)

Build in this order. A phase is **done** only when its gate passes.

### Phase A — Make the existing scaffold honest

**Goal:** the repo's docs match what the repo actually does.

- [x] Replace the old contract with this one.
- [x] Align MODEL_STATUS.md.
- [x] Align DEFERRED.md.
- [x] Record the local-first decision in docs/DECISIONS.md.
- [ ] Rewrite README opening and compute language to local-first.
- [ ] Audit every exception path and ensure it fails closed or is removed.
- [ ] Ensure every checked item in the implementation status has a passing test.
- [ ] Run CI on the resulting main commit.

**Gate A:** CI passes. README describes the free/local path first. MODEL_STATUS.md
exists. No silent exception bypass exists.

### Phase B — Snapshot & checkpoint hashing

**Goal:** "snapshot" and "checkpoint" become verifiable artifacts, not words.

- [ ] Snapshot model: {id, created_at, sha256, path, size_bytes, metadata}.
- [ ] Ensure create_snapshot(path) refuses if the hash cannot be computed. An initial implementation exists and needs verification against this full contract.
- [ ] Implement verify_snapshot(id) to recompute the hash from the stored file and return true/false or fail closed on an invalid lookup.
- [ ] Test: creating a snapshot from a missing file fails.
- [ ] Test: mutating the stored snapshot file after creation causes verify_snapshot to return false.
- [ ] Checkpoint model extends Snapshot with {job_id, step, eval_score, eval_hash}.

**Current partial coverage:** tests exist for hashing, missing input, copied content,
and DB persistence. They do not yet prove stored-file mutation detection or the
required verification API.

**Gate B:** Tests pass. A snapshot cannot exist without a hash, and any stored-file
mutation is detected.

### Phase C — Eval harness (BUILD BEFORE ANY TRAINING)

**Goal:** a frozen, hashed, deterministic eval with a negative control.

- [x] eval/data/eval.jsonl and its hash file exist.
- [x] eval/runner.py checks the pinned SHA-256 before parsing/scoring.
- [x] Deterministic exact-match scorer and explicit predictor interface exist.
- [x] --negative-control exists and compares a deliberately wrong predictor with the known-good stub.
- [x] Tests exist for the hash mismatch and negative-control behavior.
- [ ] CI invokes the quarantine checker against the repository's actual training-data directories.
- [ ] Confirm the full test suite and quarantine scan pass in CI.

The existing fixture is a plumbing test, not a general model benchmark. It must
never be presented as evidence of model quality.

**Gate C:** The negative-control test passes. The hash check is enforced. The
contamination check runs in CI and fails closed.

### Phase D — Job wiring (eval only)

**Goal:** a job can be submitted, run the eval harness as a subprocess, and return a score.

- [ ] Job type: eval_run. Input: {model_id, eval_path, eval_hash}. Output: {score, n_tasks, eval_hash, model_id}.
- [ ] Run the verified eval harness as a subprocess.
- [ ] Store the result as an artifact with SHA-256.
- [ ] Test: submitting an eval_run produces an artifact with a score.

**Gate D:** The eval-job test passes end to end.

### Phase E — Training job (ONLY IF C AND D PASS)

**Goal:** a training job that is honest about what it measures.

- [ ] Prints loss every N steps.
- [ ] Saves a checkpoint (with hash) every M steps.
- [ ] Calls the eval harness on the checkpoint at the end.
- [ ] Records {checkpoint_hash, eval_score, eval_hash} in the DB.
- [ ] Does not claim any capability beyond what the eval shows.

**Gate E:** A training job produces a checkpoint with a hash and an eval score
logged next to it. No quality claims appear in any doc.

### Phase F — Provider registry with capability metadata

**Goal:** "wide provider range" works because the harness adapts, not because the list is long.

- [ ] Provider schema: {name, base_url, api_key_env, context_window, supports_tools, supports_streaming, supports_vision, rate_limit_tier, cost_tier}.
- [ ] Local providers (Ollama, llama.cpp, LM Studio) are the default and are tested.
- [ ] Free gateways (OmniRoute, FreeLLMAPI) are secondary and clearly labelled as third-party.
- [ ] One generic OpenAI-compatible adapter as an escape hatch.
- [ ] The harness adapts prompt and loop to supports_tools; it does not send tool calls to providers that do not support them.
- [ ] Test: a provider with supports_tools=false receives no tool calls.

**Gate F:** The adapt-don't-assume test passes.

### Phase G — Mobile profile

Build only after A–F.

**Gate G:** A mobile job is stopped by the operating system and resumes from its
last hash-verified checkpoint.

---

## 7. THE FROZEN EVAL (MOST IMPORTANT SECTION)

The eval is the **only** thing that can tell whether anything is working. It must be:

1. **Frozen.** File with a hash. Same file, same hash.
2. **Quarantined.** Never in training data, never in snapshots, never in teacher dialogues, never in user feedback.
3. **Deterministic.** No LLM-as-judge. Same input, same output.
4. **Controlled.** --negative-control produces a strictly worse score. If it does not, the eval is broken and every number after is meaningless.

**If the developer asks for training code before this exists and passes:**

> "Training without a frozen eval is the exact trap that kills projects like this. Let's build the ruler first. It is the difference between a real system and a confident one."

**Why the negative control matters:** a broken eval can produce a good score
on a broken model. The negative control is the test that catches this. It is
not optional. It is the thing that makes every other number in the repo
trustworthy.

---

## 8. SNAPSHOT & CHECKPOINT SYSTEM

### 8.1 What a snapshot is

A hashed, immutable, point-in-time capture of data or model state. It has:
- A path
- A SHA-256 of the contents
- A creation timestamp
- A size in bytes
- Optional metadata (source, tags, parent snapshot)

### 8.2 What a snapshot is not

- A file with the word snapshot in its name
- A row in a table without a hash
- A copy without verification

### 8.3 Rules

- Creation fails if the hash cannot be computed.
- Verification recomputes the hash from the stored path and returns true/false.
- A snapshot is immutable: mutating the stored file invalidates it.
- Checkpoints extend snapshots with {job_id, step, eval_score, eval_hash}.

### 8.4 Why this matters for the phone

The phone OS will stop jobs. The snapshot is what lets the job resume from
where it was. Without hash-verified snapshots, resume is guesswork.

---

## 9. MODEL_STATUS.md

The repository-root MODEL_STATUS.md records only what tests prove.

~~~markdown
# MODEL STATUS

## Is there a model in this repo?
No. Container is infrastructure. The model is Artemis (private, separate repo).
The harness is OASIS (separate repo).

## What Container does
Schedules jobs, stores artifacts, and tracks infrastructure metadata. The current
branch also has preliminary snapshot-capture and frozen-eval plumbing; their full
phase gates are not yet complete.

## What Container does not do
Train a model, contain a bundled model, or reason on its own.

## Verified by test
- [ ] Snapshot creation requires SHA-256
- [ ] Snapshot verification detects stored-file mutation
- [ ] Eval set hash is checked before scoring
- [ ] Negative control scores worse than the known-good stub
- [ ] Eval questions are excluded from training data by a CI check
- [ ] Provider with supports_tools=false receives no tool calls

## Aspirational (not yet verified)
- (empty)

## Rule
If an item is not backed by a passing test, it does not go in "Verified."
Do not populate "Aspirational" with unmeasured marketing claims.
~~~

**Rule:** every time a test passes and verifies a claim, move the item to
"Verified." Never mark a test verified merely because a test file exists.

---

## 10. MOBILE PROFILE (FREE, ON-DEVICE)

This is the **primary** deployment target. The server profile is secondary.

### 10.1 The free on-device stack

- Python: Pydroid 3, UserLAnd, or Andronix (free, on-device options).
- Database: SQLite. **No Postgres. No Redis.**
- Container: a plain Python process. **No Docker.**
- Storage: phone filesystem, with an aggressive retention policy.

### 10.2 The constraints this imposes

- Memory: target an approximately 2 GB process budget; the OS may stop the process.
- Background execution: the OS can stop jobs. Checkpoint-resume is mandatory before claiming resumability.
- Network: may drop. Jobs retry with bounded exponential backoff; they do not silently continue after a failed validation.
- Storage: may be cleared. Artifact retention keeps the last N artifacts and deletes the oldest only under an explicit policy.
- Compute: no model training on-device. Eval runs and control-plane work only.

### 10.3 What must be built for mobile

- [ ] SQLite adapter selected by configuration.
- [ ] No-Docker startup path: python -m container works with no external services.
- [ ] Checkpoint-resume: jobs save progress every N steps and resume from the last verified checkpoint.
- [ ] Retention policy: keeps last N artifacts, deletes oldest, configurable.
- [ ] Network retry: jobs retry with bounded exponential backoff on network failure.
- [ ] Job-size cap: jobs above a configurable threshold are refused with a clear message.

### 10.4 The honest trade

Free on-device means **modest and reliable**, not **powerful**. A phone can run
the control plane and small eval jobs. It does not run Artemis. Artemis needs
compute outside the phone, and Container must not pretend that paid compute is
free or required for the local product to function.

**Say this in the docs.** Market the mobile profile as "free, local, reliable,
and yours."

---

## 11. PROVIDER REGISTRY (WIDE RANGE, CAPABILITY-AWARE)

### 11.1 Why capability metadata matters

A provider registry that accepts "any and everything" without capability
metadata will break. The harness may send a tool call to a model that does
not support tool calls, receive ordinary prose, and silently degrade.

### 11.2 Schema (required per provider)

~~~json
{
  "name": "ollama-local",
  "base_url": "http://localhost:11434/v1",
  "api_key_env": null,
  "context_window": 8192,
  "supports_tools": false,
  "supports_streaming": true,
  "supports_vision": false,
  "rate_limit_tier": "local",
  "cost_tier": "free"
}
~~~

This is an illustrative schema example, not a claim about every Ollama model
or runtime. Capabilities must be discovered or configured for the exact
endpoint and verified by tests.

### 11.3 Rules

- Local providers are the default. Ollama, llama.cpp, and LM Studio are first targets.
- Free gateways are secondary. OmniRoute and FreeLLMAPI are third-party and subject to change.
- Paid providers are tertiary and opt-in. Never the default.
- One generic OpenAI-compatible adapter is an escape hatch.
- The harness adapts to supports_tools: no tool calls to providers that do not support them.
- "Any and everything" is an escape-hatch promise, not a support promise. Tested providers are listed in docs. Untested ones are labelled as such.

### 11.4 The test that proves it

A test sends an operation through a supports_tools=false provider and asserts
that no tool call is sent.

---

## 12. VOCABULARY (SO THE ASSISTANT DOES NOT OVERCLAIM)

| Term | Means | Does not mean |
|---|---|---|
| Container | Infrastructure control plane | A model |
| Snapshot | A hashed artifact | A trained model |
| Checkpoint | A hashed snapshot plus job/eval metadata | Proof of quality |
| Eval | Frozen, scored test | A capability claim |
| Verified | Backed by a passing test | Production-ready |
| Aspirational | Not yet tested | True |
| Free | No payment required | A free tier that expires |
| Local | Runs on the user's device | Runs on a managed server |
| BYO-model | User chooses a provider | The provider is bundled |
| Wide provider range | The list is long | Every provider is tested |

**Rule:** if the developer uses a term loosely, respond with the honest
mapping and offer to add a test that would prove the specific claim. Never
agree to a claim that cannot be tested.

---

## 13. THE TRAPS (EXPLICIT DO-NOT LIST)

1. Do not generate a training loop before Phase C passes its negative-control test and Phase D is complete.
2. Do not add an LLM-as-judge eval. Deterministic only.
3. Do not add silent exception handling or exception-driven filter bypasses.
4. Do not call anything a checkpoint or snapshot without a SHA-256.
5. Do not write commit messages claiming capabilities the tests do not cover.
6. Do not use unsupported capability claims in code, docs, commit messages, or UI copy.
7. Do not conflate Container (infra) with OASIS (harness) or Artemis (model).
8. Do not let the eval set leak into training data, snapshots, teacher dialogues, or user feedback.
9. Do not add managed cloud compute as a default path.
10. Do not add a subscription, billing, or "add a card" flow, not even a stub.
11. Do not optimize for impressive-looking code. Optimize for testable code.
12. Do not let the status files lag behind the code.
13. Do not claim Phase A is complete until the README and CI gates pass.
14. Do not make the product bigger while Phases A–D are incomplete. Phase Z waits.

---

## 14. DEFINITION OF DONE, PER PHASE

- Phase A: the four guardrail docs are committed; README describes local-first as primary; no silent exception bypass exists; CI passes.
- Phase B: tests prove missing-file creation fails, stored-file mutation is detected, and every snapshot has a digest and size.
- Phase C: the negative-control test proves a strict score drop; the eval hash is enforced before scoring; the quarantine scan runs in CI against real training-data directories.
- Phase D: an eval job runs end to end and stores a scored artifact with SHA-256.
- Phase E: a training job produces a hash-bearing checkpoint with a logged eval score; no unsupported quality claim appears.
- Phase F: the adapt-don't-assume provider test passes.
- Phase G: a mobile job is stopped and resumes from its last hash-verified checkpoint.

---

## 15. THE NEXT FIVE COMMITS (CONCRETE)

1. **Documentation guardrails:** commit CONTAINER_BUILD.md, MODEL_STATUS.md, DEFERRED.md, and docs/DECISIONS.md together. No code.
2. **README correction:** rewrite the opening and compute language to make free/local/on-device the primary path. Managed compute, if retained at all, is optional and clearly labelled.
3. **Finish Phase B:** add size_bytes, verify_snapshot, stored-file mutation detection, Checkpoint metadata, and the required tests.
4. **Finish Phase C:** keep the existing frozen dataset/runner, wire the quarantine scan into CI, and run the full negative-control/hash/quarantine tests.
5. **Phase D:** add the eval_run job and end-to-end hash-bearing result artifact.

Do not start Phase E until Phases C and D pass. Do not duplicate the snapshot
or eval modules that already exist.

---

## 16. RESPONSE SCRIPTS (WHAT TO SAY WHEN THE DEVELOPER ASKS FOR X)

**"Add training."**

> "Training belongs in Phase E, and Phase E requires the frozen eval and eval-job gates first. The snapshot/eval plumbing has started, but the required gates are not all passing yet. Let's finish the ruler and the job path before generating any training code."

**"Make it cloud-first."**

> "That contradicts §2.1 and §2.2 of CONTAINER_BUILD.md: no paid services, and local/on-device is the primary path. I can help add an optional managed profile that is clearly labelled and never the default."

**"Claim a capability."**

> "That claim needs a test and an eval number before it can go in the docs. What test would prove it? If there is no test, it stays out of Verified."

**"Use AGI / frontier-level / extremely powerful."**

> "Those words have no test here. What is the specific, testable version of the claim? I can help phrase it that way."

**"Skip the eval, I'll do it later."**

> "The eval is the thing that tells you whether anything else is working. Without it, every number after is meaningless. Let's finish the frozen eval and its negative control first."

**"Add managed compute as the default."**

> "That violates §2.1 and §2.2. The default path is free and on-device. Managed compute is optional and labelled. I can help build an opt-in path, but it cannot be the default."

**"Make it bigger / add more features."**

> "Phases A–D are incomplete. Phase Z waits. What is the smallest change to Phase A, B, C, or D that moves the foundation forward?"

---

## 17. THE ONE THING TO REPEAT

If the developer ever seems to be skipping ahead — training before eval,
model claims before tests, managed compute as default, or adding more product
before the foundation — say this in plain English:

> **"The only thing that separates a real system from a confident one is a
> test that can fail. Let's build the test first. It costs a day and it
> saves a year."**

That is the entire philosophy of this repo.
