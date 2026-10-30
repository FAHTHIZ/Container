# Container API

The first API milestone provides a minimal, typed HTTP application and health endpoints. Domain modules, persistence, authentication, and job orchestration will be added in later vertical slices.

## Requirements

- Python 3.11+

## Run locally

From this directory:

```bash
python -m venv .venv
. .venv/bin/activate
python -m pip install -e ".[dev]"
uvicorn container_api.main:app --reload
```

On Windows PowerShell, activate with `.venv\\Scripts\\Activate.ps1`.

- API docs: `http://127.0.0.1:8000/docs`
- Liveness: `http://127.0.0.1:8000/health/live`
- Readiness: `http://127.0.0.1:8000/health/ready`

## Test

```bash
pytest
ruff check .
```

The readiness endpoint currently reports that the API process is ready; dependency checks will be added when database and queue integrations are implemented.
