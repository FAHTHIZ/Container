<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contributing to Container

Thanks for considering a contribution.

## Before proposing a change

- Open or find an issue describing the behavior and user impact.
- Keep changes focused and explain how they fit the product and architecture.
- Add or update tests for behavior changes.
- Update architecture, product, operations, roadmap, security, and implementation-status docs when scope or behavior changes.
- Do not commit credentials, private datasets, model weights, generated artifacts, or personal data.
- Preserve upstream license and NOTICE files for third-party dependencies or assets.
- Do not mark mock screens, metadata-only records, or placeholder endpoints as implemented features.

## Development checks

From `services/api`:

    python -m pip install -e ".[dev]"
    ruff check .
    alembic upgrade head
    pytest
    node --check src/container_api/static/app.js

## Product expectations

- Keep the primary experience conversation-first; avoid adding permanent navigation for every internal capability.
- Use focused contextual panels and progressive disclosure for advanced operations.
- Keep the Core panel informative and non-human; respect reduced-motion and accessibility settings.
- Make managed inference and compute behavior explicit; never imply that a local device must supply heavy resources.
- Distinguish imported model files from hosted/local endpoint connections.
- Enforce source provenance, licensing checks, network restrictions, and safe artifact handling.
- Show users cost and permission decisions before chargeable or consequential work.
- Ensure browser, Android, and desktop clients share API contracts and authorization semantics.

## Engineering expectations

- Use typed request/response schemas and validate inputs at API boundaries.
- Enforce workspace/project authorization on the server for every resource.
- Keep API requests short; long-running work belongs in worker processes.
- Make worker effects idempotent and record state transitions.
- Scope worker/provider credentials; never put secrets in logs, events, test fixtures, or committed configuration.
- Treat imported files, web results, model outputs, and tool results as untrusted.
- Document compute, storage, network, provider, licensing, and operational requirements.
- Add migrations and update tests for persistent model changes.

## Licensing

By submitting a contribution, you agree that it is offered under the repository's Apache License, Version 2.0, unless a separate written agreement says otherwise. Keep existing third-party attribution notices intact.
