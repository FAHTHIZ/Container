# Container

**Container is an open-source platform for building, adapting, evaluating, running, and deploying AI systems.**

It is designed to connect research and data preparation, model development, inference, agents, workflows, and application delivery in one coherent workspace. It will support local devices and remote compute rather than pretending that every training workload can run on a phone.

> **Project status:** Foundation stage. This repository currently contains the initial product documentation and architecture plan. Features are not yet implemented or production-ready.

## Product goals

- Discover and manage trustworthy data sources with provenance and licensing metadata.
- Prepare datasets through repeatable cleaning, filtering, deduplication, and validation pipelines.
- Create model projects for fine-tuning, continued pretraining, and (eventually) training from scratch where compute allows.
- Run reproducible evaluations and compare model versions before release.
- Serve models locally or through remote inference workers.
- Compose assistants, tool-using agents, and visual workflows.
- Manage jobs, compute resources, artifacts, permissions, logs, and deployments from one workspace.
- Provide a mobile-friendly control surface while delegating resource-intensive work to suitable machines or cloud workers.

## Architecture at a glance

Container is planned as a modular monorepo:

- **Apps:** web studio first; mobile client as a first-class target.
- **API:** authentication, projects, model registry, datasets, jobs, artifacts, deployments, and events.
- **Workers:** research ingestion, data processing, evaluation, training, and inference.
- **Shared contracts:** typed API schemas, event definitions, and reusable domain models.
- **Infrastructure:** local development, database, queue, object storage, observability, and deployment templates.

See:
- [Product and system architecture](docs/ARCHITECTURE.md)
- [Delivery roadmap](docs/ROADMAP.md)
- [Security principles](docs/SECURITY.md)
- [Architecture decisions](docs/DECISIONS.md)

## Core engineering principles

1. **Evidence before claims:** every dataset, model run, evaluation, and release should have inspectable provenance.
2. **Reproducibility:** record configuration, code revision, input artifacts, environment, and output artifacts for jobs.
3. **Safe model evolution:** improvements are measured against fixed evaluations; regressions block promotion; releases can be rolled back.
4. **Least privilege:** workers receive scoped credentials and permissions; secrets are never committed to the repository.
5. **Hardware-aware execution:** choose local, remote, or cloud execution based on actual hardware and workload requirements.
6. **Modular by default:** start with a maintainable modular backend and separate workers; split into services only when scale or isolation justifies it.
7. **Honest status:** distinguish implemented, experimental, planned, and unavailable capabilities in both UI and docs.

## Development status

The current milestone is **M0 — Foundation**: define contracts, repository structure, local development, security boundaries, and the first vertical slice. The roadmap is the source of truth for implementation status.

## License

No license has been selected yet. Until one is added, do not assume the code is licensed for reuse or redistribution.
