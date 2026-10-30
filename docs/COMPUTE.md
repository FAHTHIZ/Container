<!-- SPDX-License-Identifier: Apache-2.0 -->

# Container — Compute and Cost Model

**Status:** target architecture. Current jobs are demonstration tasks and do not schedule GPU workloads.

## 1. Cloud-first hybrid

Container is hybrid, but the default must be practical for people with ordinary phones and low-powered computers. A user should not need a GPU, large local storage, or technical knowledge of hardware to start using the managed product.

The default path uses Container-managed remote inference and remote workers. User-owned hardware is an optional resource source, not a requirement or a hidden dependency.

## 2. Resource roles

- **Phone/tablet:** chat, file selection/upload, approvals, notifications, job monitoring, previews, and compatible lightweight work only when the user opts in.
- **Desktop/laptop:** normal client use plus optional local inference, local data preparation, and a user-owned worker for compatible jobs.
- **Container-managed cloud:** default inference and remote CPU/GPU jobs, durable artifacts, research ingestion, and background work.
- **External cloud/compute provider:** optional adapter for users who have their own account, capacity, or billing relationship.

A mobile client must not silently train on-device, consume mobile data for large downloads, or keep a device awake for a long task.

## 3. Capability-aware scheduling

Every job declares a resource profile:
- CPU cores and memory.
- GPU/accelerator type and memory.
- System RAM and temporary disk.
- Persistent input/output storage.
- Expected network and data transfer.
- Runtime, model architecture, precision/quantization, and library compatibility.
- Estimated duration/cost range.
- Privacy region, data residency, and provider constraints.

The scheduler checks actual available capacity and runtime compatibility before dispatch. It may queue, recommend a smaller method, or report that no compatible resource is available. It must not claim that every model or training method can run on every worker.

Workload classes include interactive inference, batch inference, model import, research/ingestion, data processing, fine-tuning, evaluation, and deployment. Different classes require different priority, timeout, retry, and isolation policies.

## 4. Durable jobs

Long jobs run remotely and continue when a phone disconnects. Job state and events persist independently of the app session. Users can reconnect, inspect logs/progress, cancel where supported, and retrieve outputs later.

Workers use scoped credentials and isolated environments. Training jobs need checkpoints and recovery semantics. Cancellation must stop or safely terminate the actual worker process, not merely change a database status.

## 5. Cost transparency

Remote inference, GPU time, object storage, network transfer, and background jobs have real operating costs. Container must not promise unlimited free cloud resources.

The product should support:
- Included usage allowances or quotas for managed plans.
- Clear usage metering by inference, training, storage, and transfer.
- Preflight estimates and a user-visible maximum budget.
- Confirmation before a chargeable job begins or exceeds its approved budget.
- Per-project and per-job cost records.
- Usage limits, alerts, rate limits, and graceful queueing when limits are reached.
- Optional user-supplied provider/compute accounts, with the responsible billing party clearly shown.
- Cancellation and cleanup of abandoned resources.

Pricing and allowance values are product/business decisions and must not be hardcoded into this architecture document.

## 6. Data placement and privacy

Before dispatch, Container determines which data an operation needs and which provider/region may receive it. Private project data must not be sent to an external provider or user-owned worker unless the user policy and authorization allow it. Data transfer is recorded and minimized.

Storage and compute quotas are separate. Deleting a client app must not silently delete remote project data; account/facility deletion follows an explicit retention and confirmation flow.

## 7. Local worker pairing

An optional desktop/server connector may pair a user-owned machine with a facility:
- Explicit installation and pairing.
- Device identity and revocable credentials.
- Capability reporting and health heartbeat.
- Per-job sandbox and scope.
- User-defined availability and resource limits.
- No inbound public port requirement by default.
- Clear indicators when work runs on the user's own electricity, hardware, or network.

Disconnecting or revoking the worker stops new assignments and safely handles in-flight work according to the job's recovery policy.

## 8. Scaling direction

Start with the existing database-backed job model for small demonstration tasks. Add a queue broker, transactional outbox, worker leases, and capability-aware scheduler before real training or large research workloads. Add distributed training only after single-worker training, checkpointing, evaluation, cost controls, and recovery are reliable.


## Hardware strategy

See [HARDWARE_STRATEGY.md](HARDWARE_STRATEGY.md) for the current CPU/GPU discovery contract, workload placement, inference memory admission, training preflight, and remote-compute consent rules. Container is cloud-first by default: the mobile device is a control surface, not the default training worker.
