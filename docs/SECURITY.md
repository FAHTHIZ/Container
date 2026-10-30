<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Security Principles

## Reporting

Do not publish exploitable security details in a public issue. Use GitHub private vulnerability reporting when available, or contact the repository owner privately through GitHub. Include affected version/commit, impact, and a minimal reproduction. Do not include user secrets or private datasets.

## Current posture

The current repository is an early development foundation, not a production security certification. Implemented controls include Argon2 password hashing, signed short-lived bearer tokens, production rejection of the default development signing key, server-side workspace membership checks, and loopback-only Compose port bindings.

Important controls still missing include verified account recovery, MFA, refresh-token rotation/revocation, authentication throttling, administrative audit logs, advanced role management, worker sandboxing, object-store policies, and a formal threat-model review.

## Requirements before production

- Authorize every project/resource operation server-side.
- Never trust a client-supplied workspace/project ID without checking membership.
- Store only password hashes; never log passwords, tokens, or secret values.
- Use unique secrets and rotate them.
- Keep credentials out of Git, artifacts, application logs, and event payloads.
- Limit worker CPU, memory, disk, execution time, and network access.
- Treat downloaded documents, datasets, repositories, model files, tool outputs, and model responses as untrusted data.
- Use explicit tool allowlists and scoped permissions for agents.
- Require confirmation for sensitive or irreversible actions.
- Record privileged changes and external tool execution in audit events.
- Validate artifacts by expected type, size, and digest before loading.
- Configure TLS, CORS allowlists, rate limits, backups, and monitoring at the deployment boundary.

## Deployment warning

Docker Compose is for local development only. Its default values are placeholders. Do not expose it directly to the public internet. Production requires managed secrets, TLS termination, database backups, network restrictions, observability, and a reviewed authentication/authorization design.
