# Container — Security Principles

**Status:** Initial policy baseline; expand into a threat model before public production deployment.

## Security objectives

- Protect user accounts, workspace data, source credentials, datasets, model artifacts, and deployment endpoints.
- Prevent one workspace or project from accessing another project's resources.
- Keep untrusted research content and model outputs from becoming executable instructions.
- Make worker activity and privileged operations auditable.
- Fail closed when authorization, signature, integrity, or resource validation fails.

## Required controls

### Identity and authorization
- Enforce authorization server-side on every resource read and write.
- Scope resources to a workspace and project; do not trust client-supplied ownership IDs.
- Use least-privilege roles and short-lived credentials where possible.
- Rate-limit authentication and sensitive API operations.
- Record security-relevant events without recording secrets.

### Secrets
- Never commit API keys, tokens, passwords, private keys, or production environment files.
- Use environment-based secrets only for local development; use a dedicated secrets manager for deployed environments.
- Redact credentials from exceptions, traces, job logs, and event payloads.
- Support credential rotation and revocation.

### Worker isolation
- Treat dataset files, model files, downloaded repositories, and tool output as untrusted input.
- Run jobs with bounded CPU, memory, disk, time, and network access.
- Use separate worker identities and scoped credentials.
- Do not execute arbitrary downloaded code as part of ingestion or training.
- Require explicit policy and approval before a workflow can perform privileged or destructive operations.

### Data integrity and provenance
- Record source, retrieval time, terms/license metadata, processing configuration, and artifact hashes.
- Keep finalized dataset and model versions immutable.
- Verify artifact integrity before loading or deploying.
- Provide deletion and retention policies appropriate to the data source and user obligations.

### API and application
- Validate input at API boundaries.
- Use TLS for network traffic in deployed environments.
- Apply secure session and token handling.
- Protect against CSRF where cookie-based authentication is used.
- Use restrictive CORS policies; do not use wildcard origins with credentials.
- Avoid exposing internal worker or storage services directly to clients.

### Model and agent safety
- Treat model output as untrusted.
- Separate instructions from retrieved content and tool results.
- Give tools explicit schemas, allowlists, and scoped permissions.
- Require confirmation for sensitive or irreversible actions.
- Keep a complete audit trail of agent tool calls and approvals.
- Evaluate prompt-injection and data-exfiltration risks before enabling external tools.

## Release checklist

- [ ] Threat model reviewed.
- [ ] Authorization and cross-workspace isolation tests pass.
- [ ] Secrets scanning and dependency scanning enabled in CI.
- [ ] Worker resource limits and network policy documented.
- [ ] Backup, restore, and retention behavior tested.
- [ ] Audit events cover privileged operations.
- [ ] Security contact and vulnerability-reporting process published.

This document is a baseline, not a claim that the current repository already implements these controls.
