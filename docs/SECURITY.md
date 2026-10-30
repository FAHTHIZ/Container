<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Security Principles

## Reporting

Do not publish exploitable security details in a public issue. Use GitHub private vulnerability reporting when available, or contact the repository owner privately through GitHub. Include affected version/commit, impact, and a minimal reproduction. Do not include user secrets or private datasets.

## Current posture

The repository is an early development foundation, not a production security certification. Implemented controls include Argon2 password hashing, signed short-lived bearer tokens, production rejection of the default development signing key, server-side workspace membership checks, bounded artifact storage, and loopback-only Compose port bindings.

Important controls still missing include verified account recovery, MFA, refresh-token rotation/revocation, authentication throttling, complete audit logs, advanced role management, worker sandboxing, managed secret storage, production object-store policies, and a formal threat-model review.

## Identity, ownership, and credentials

- Authorize every resource operation server-side; a user-supplied workspace/project ID is never proof of access.
- Use short-lived scoped service credentials for workers and connectors.
- Store provider credentials in a dedicated secret store or encrypted credential service. Never expose raw secrets in API responses, chat history, job specs, logs, or events.
- Rotate and revoke credentials; provide clear provider disconnect behavior.
- Keep personal facility data isolated by owner and workspace.
- Support explicit retention, export, and deletion policies for conversations, artifacts, datasets, and provider connections.
- Do not train on user conversations or uploaded files by default. Any opt-in use requires clear, scoped, revocable consent.

## Model and archive import

- Treat repositories, model files, tokenizer/config files, checkpoints, archives, and model cards as untrusted.
- Validate file size, content type, expected structure, checksum, and format before registering or loading.
- Use generated storage keys; do not trust user filenames or archive paths.
- Defend ZIP extraction against traversal, symlinks, duplicate paths, file-count abuse, and decompression bombs.
- Do not execute scripts or custom model code during import.
- Isolate any explicitly supported custom-code loading path and require an informed opt-in.
- Avoid unsafe deserialization of pickle-based checkpoints in privileged services.

## Network access and research

All URL-fetching components require strict SSRF protection:
- Allow only explicitly supported schemes and destinations.
- Reject loopback, private, link-local, multicast, reserved, and cloud metadata addresses for public-source import.
- Revalidate DNS resolution and every redirect; defend against DNS rebinding.
- Set connection/read timeouts, body-size limits, redirect limits, concurrency caps, and per-user quotas.
- Never forward internal credentials, cookies, authorization headers, or service identity to arbitrary origins.
- Treat fetched pages and repository content as untrusted text; embedded instructions cannot override system policy or user permissions.
- Respect source terms, robots policies, privacy, rate limits, copyright, and authentication boundaries. Do not bypass paywalls or private access controls.

A local endpoint is a separate trust path and must require explicit pairing, a user-authorized connector, or narrowly configured private-network access. Do not weaken public URL protections to support local devices.

## Agents, tools, and execution

- Tool definitions use typed schemas and explicit allowlists.
- Apply least privilege and per-job network/data scopes.
- Limit worker CPU, memory, disk, GPU, execution time, and outbound network.
- Keep untrusted tool output separate from instructions and authorization policy.
- Require user approval for purchases/charges, external writes, destructive changes, deployment promotion, credential changes, permission expansion, and other consequential actions.
- Record tool invocations, approvals, resource use, and result status in audit events.
- Support cancellation and cleanup of actual running processes and resources.

## Research, training, and evaluation

- Preserve source provenance, data lineage, licensing/terms metadata, and model lineage.
- Check datasets and model licenses for the intended use and redistribution.
- Separate retrieved knowledge from training data and from model weights.
- Use independent evaluation, holdout data, regression checks, and rollback before promotion.
- Do not accept a candidate based solely on model-generated claims or self-evaluation.
- Keep experiment artifacts and logs private to their authorized facility/project.

## Production requirements

Before public production use:
- TLS termination, secure cookie/session settings, CORS allowlists, rate limits, and abuse monitoring.
- Managed secrets and key rotation.
- Worker sandboxing, egress policy, quotas, and resource accounting.
- Private object storage with lifecycle, retention, and signed-access policies.
- Backup/restore and disaster-recovery drills.
- Security logging, alerts, and audit review.
- Threat model and independent security assessment.
- Incident response and data breach procedures.

## Deployment warning

Docker Compose is for local development only. Its default values are placeholders. Do not expose it directly to the public internet. Production requires managed secrets, TLS, database backups, network restrictions, observability, and a reviewed authentication/authorization design.
