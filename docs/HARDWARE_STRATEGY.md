<!-- SPDX-License-Identifier: Apache-2.0 -->

# Hardware and Compute Strategy

Last reviewed: 2026-10-30.

## Product rule: cloud-first, device-light

Container is a control surface and orchestration facility. A phone, tablet, or ordinary laptop must be able to use the product without being treated as the training cluster. The default hosted experience uses managed inference and remote workers. Local hardware is an optional execution location, not a prerequisite.

- Mobile clients handle chat, approvals, uploads, status, and monitoring.
- The API/control plane handles identity, policy, routing, metadata, and job orchestration.
- CPU workers handle I/O, parsing, indexing, tokenization, data preparation, and lightweight jobs.
- GPU workers handle compatible inference, fine-tuning, embeddings, and multimodal acceleration.
- Storage is independent of compute so a job can move between workers without losing its artifacts.
- A paired desktop worker is opt-in and reports capabilities; it never silently consumes the user's battery, bandwidth, or GPU.

## Resource discovery contract

Every worker should report a normalized, timestamped capability record:

| Resource | Required fields |
|---|---|
| CPU | vendor, model, architecture, physical/logical cores, instruction flags, current load |
| Memory | total/available RAM, swap, NUMA topology where relevant |
| GPU | vendor, model, device ID, driver/runtime, total/free VRAM, compute capability, supported precisions |
| Storage | available bytes, throughput class, filesystem and temporary-space budget |
| Network | reachable control-plane region, measured throughput/latency, transfer quota |
| Runtime | OS, container support, CUDA/ROCm/Metal/Vulkan/DirectML/CPU backends and versions |

The scheduler must use measured free memory and supported kernels, not just a GPU marketing name. A worker capability snapshot expires and must be refreshed before scheduling expensive work.

## Implemented discovery baseline

The API currently exposes an authenticated `GET /api/v1/system/capabilities` inventory for the host running the API process. It reports architecture, logical and effective CPU capacity (including visible cgroup limits), host memory when discoverable, cgroup memory limit, and best-effort accelerator visibility.

- NVIDIA devices are queried through `nvidia-smi` for model, reported memory, driver version, and compute capability.
- AMD accelerator architecture is best-effort through `rocminfo`.
- Apple Silicon is identified as an integrated-GPU candidate; Linux render-device nodes are reported generically when vendor tools are unavailable.
- The endpoint is authenticated and explicitly labels the result as inventory-only.

This is not yet a full worker capability record. It does not measure free VRAM, utilization, CPU instruction flags, memory bandwidth, storage throughput, network performance, runtime/kernel compatibility, or inference/training benchmarks. A detected device is not proof that a usable runtime is installed. Paired workers must later send signed, timestamped heartbeats and fresh measurements before scheduling.

## Workload placement

| Workload | Default placement | Why |
|---|---|---|
| Chat/inference | Managed hosted inference; optional paired local runtime | No local hardware burden for first-run users |
| Search/research | Managed CPU workers | Network and parsing dominate; GPU usually unnecessary |
| Document extraction | CPU workers, optional accelerator for supported vision models | Keep accelerator capacity for jobs that need it |
| Embeddings | CPU for small batches; GPU worker for large batches | Schedule by throughput and queue/cost |
| LoRA/QLoRA | Remote GPU worker | Memory and kernel requirements vary by architecture |
| Full fine-tuning | Dedicated multi-GPU/cloud cluster | High memory, interconnect and recovery requirements |
| Evaluation | CPU by default; GPU when target model requires it | Avoid reserving accelerators for ordinary scoring |
| Local inference | User-paired worker, explicitly enabled | Respect local power, temperature, and user policy |

## Memory estimation and admission

Model weights are only one part of inference memory. The admission estimator must include:

- Weight representation and quantization metadata.
- Runtime/kernel workspaces and temporary buffers.
- KV cache, which grows with context length, batch size, layers, hidden dimensions, and precision.
- Activations and multimodal inputs where applicable.
- Driver/runtime reservation and a safety margin.

A rough lower-bound for raw weights is:

`weight_bytes ≈ parameter_count × bits_per_weight / 8`

This is not a safe deployment estimate. The UI must show a range, identify assumptions, and reject a job when free memory is insufficient. Do not infer that a 4-bit checkpoint fits merely because its raw weights fit in VRAM.

For training, estimate base weights, gradients, optimizer states, activations, temporary buffers, sequence length, batch size, checkpoint space, and dataloader RAM separately. Require a preflight run before a paid or long-running job.

## CPU strategy

CPU is a first-class compute target, but it is not a universal substitute for a GPU.

- Detect architecture and vector instruction support (for example AVX2/AVX-512 on x86 and NEON/SVE on ARM).
- Use CPU inference backends for compatible quantized models and low-throughput tasks.
- Reserve cores for API, scheduler, tokenization, data loaders, and OS services.
- Bound thread pools; oversubscription can make performance worse.
- Separate latency-sensitive control-plane processes from long CPU-bound work.
- Use memory bandwidth, not core count alone, when estimating CPU inference throughput.

The vLLM deployment guidance notes that its multi-process GPU architecture has a CPU scheduling floor of at least `2 + N` physical cores for one API server, one engine core and N GPU workers; real deployments need headroom for the OS, tokenization and data loading. This is a vLLM deployment rule, not a universal minimum for every inference engine.

## GPU strategy

- NVIDIA: CUDA-compatible workers and validated driver/runtime combinations.
- AMD: ROCm-compatible workers; validate exact GPU, OS, ROCm, PyTorch and kernel support.
- Apple: Metal/MPS or MLX-compatible local workers where the chosen model/runtime supports them.
- Intel and other accelerators: capability adapters only after hardware/runtime compatibility tests.
- Never assume all GPUs from one vendor support the same precision, memory features, or model kernels.
- Schedule by actual free VRAM, supported precision, interconnect and tested runtime profile.
- Multi-GPU jobs must declare topology and interconnect requirements; do not promise linear scaling.

Kubernetes can expose NVIDIA and AMD accelerators through vendor device plugins. This is a possible future cluster backend, not a requirement for the initial single-node worker.

## Training policy

Parameter-efficient adaptation is the default first training path:

1. Retrieval/knowledge augmentation when the goal is new factual knowledge.
2. Prompting or tool/agent configuration when behavior can be changed without training.
3. LoRA when the base model and available GPU support it.
4. QLoRA only when the chosen quantization and kernel stack is validated.
5. Full fine-tuning only when justified by the objective and provisioned compute.

Do not publish universal VRAM minimums. Hardware demand depends on architecture, sequence length, batch size, optimizer, precision, checkpointing, runtime and data pipeline. A vendor's playbook may describe a specific hardware/software combination; present those numbers as that tested configuration only.

## Cost and user-consent rules

- Estimate cost before starting a remote GPU job and require explicit confirmation.
- Enforce per-user budgets, maximum runtime, storage quotas and concurrency limits.
- Provide pause, cancel, checkpoint/resume and automatic idle shutdown where supported.
- Never silently upload a local model or dataset to a cloud worker.
- Show region, data-transfer implications, retention, and whether the worker is shared or dedicated.
- If managed compute is unavailable, explain the limitation instead of falling back to the user's phone.

## Research references

- [Kubernetes: Schedule GPUs](https://kubernetes.io/docs/tasks/manage-gpus/scheduling-gpus/) — NVIDIA/AMD device-plugin resource scheduling.
- [Kubernetes: Device Plugins](https://kubernetes.io/docs/concepts/extend-kubernetes/compute-storage-net/device-plugins/) — accelerator discovery and device registration.
- [vLLM: Optimization and CPU resources](https://github.com/vllm-project/vllm/blob/main/docs/configuration/optimization.md) — CPU contention in multi-process GPU serving.
- [Hugging Face PEFT](https://huggingface.co/docs/peft/index) — parameter-efficient fine-tuning and adapter methods.
- [Hugging Face PEFT repository](https://github.com/huggingface/peft) — measured examples of memory trade-offs for LoRA and CPU offload.
- [AMD AI Playbooks: PyTorch fine-tuning on ROCm](https://developer.amd.com/playbooks/pytorch-finetuning/) — hardware-specific ROCm examples and cautions.

These references inform the architecture; they are not guarantees that a particular model runs on every listed device.
