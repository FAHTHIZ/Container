<!-- SPDX-License-Identifier: Apache-2.0 -->

# Contributing to Container

Thanks for considering a contribution.

## Before opening a pull request

- Open or find an issue describing the change.
- Keep pull requests focused and explain user impact.
- Add or update tests for behavior changes.
- Update architecture, operations, roadmap, and implementation-status docs when behavior or scope changes.
- Do not commit credentials, private datasets, model weights, generated artifacts, or personal data.
- Preserve upstream license and NOTICE files for third-party dependencies or assets.
- Do not mark mock screens or placeholder endpoints as implemented features.

## Development checks

From services/api:

    python -m pip install -e ".[dev]"
    ruff check .
    alembic upgrade head
    pytest

## Design expectations

- Use typed request/response schemas and validate inputs at API boundaries.
- Enforce workspace/project authorization on the server for every resource.
- Keep API requests short; long-running work belongs in worker processes.
- Make worker effects idempotent and record state transitions.
- Never place secrets in logs, events, test fixtures, or committed configuration.
- Document external service and compute requirements.

## Licensing

By submitting a contribution, you agree that it is offered under the repository's Apache License, Version 2.0, unless a separate written agreement says otherwise. Keep existing third-party attribution notices intact.
