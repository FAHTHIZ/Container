# External Trainer Contract

Container is the infrastructure layer. It schedules, stores, and tracks. It does not think.

This document describes the Phase E `train_run` job. Container does not contain a learning algorithm or model architecture. The actual trainer must be supplied separately as trusted operator-installed code.

## Safety and ownership boundary

- A workspace member may submit a training job, but cannot choose its adapter or command.
- The operator configures `CONTAINER_TRAIN_RUNNER` as `module.path:function_name` on both the API and worker.
- The setting is blank by default. The API rejects training submissions until a trainer and evaluation adapter are configured.
- If the module is not installed in the worker Python environment, set CONTAINER_TRAIN_ADAPTER_PATH to an operator-provided directory containing the package. The directory must exist and cannot be a symbolic link. Mount it read-only in container deployments; the base Compose file does not mount external adapter code.
- The adapter runs on the worker host with that process's operating-system permissions. It is trusted code, not a sandbox. Never point it at a module from a user upload, an unreviewed repository, or a dataset artifact.
- The current worker is a single database-polling process. This is not a distributed scheduler, GPU allocator, process-isolation boundary, or production training service.

## Adapter interface

The selected Python function receives keyword arguments:

- `dataset_path`: a temporary, read-only copy of the same-project text dataset artifact.
- `output_dir`: a new, empty temporary directory for checkpoint outputs.
- `model_id`: the project-scoped model metadata ID.
- `steps`: the requested step budget.
- `loss_every` and `checkpoint_every`: reporting and save intervals.

The adapter owns all model-specific training. It must not expect Container to implement a learning algorithm. A successful process exit is not enough: Container validates the required records and files before storing anything.

## Required loss output

At every positive multiple of `loss_every` up to `steps`, print one line in this exact format:

    LOSS step=20 loss=0.12345678

The step must be the correct integer. The loss must parse as a finite number. Duplicate, missing, malformed, mistimed, or non-finite loss records fail the job. Other non-LOSS diagnostic lines are allowed within the bounded output size.

## Required checkpoint files

At every positive multiple of `checkpoint_every` up to `steps`, create one non-empty regular file in `output_dir` named:

    checkpoint-step-00000100.bin

The number is the zero-padded checkpoint step. Container rejects symbolic links, directories, unexpected files, missing checkpoints, empty files, files over the artifact limit, and a mismatch between the checkpoint schedule and the actual files.

Container calculates SHA-256 for each checkpoint, copies each checkpoint into immutable artifact storage, then re-reads the stored copy and calculates SHA-256 again. If the stored digest or size differs, the job fails. Each accepted checkpoint becomes a project artifact with its own SHA-256 value.

## Frozen evaluation at the end

After checkpoint verification, Container runs the already-frozen `eval_run` harness against the final checkpoint file. The configured evaluation adapter receives the path in `CONTAINER_EVAL_CHECKPOINT_PATH`. The evaluation adapter is also trusted operator code and must load that exact file when performing real evaluation.

The final checkpoint hash and frozen-evaluation score are recorded together in the model-version metadata, and in the job result. The evaluation JSON report is stored as a separate SHA-256-bearing artifact.

The included test adapters write deliberately artificial fixture data and return fixed answers. They verify the orchestration contract only. They are not models, do not perform learning, and their scores are not evidence of model quality.

## Training-data quarantine

Before the trainer starts, Container verifies the pinned eval hash and checks the selected text dataset artifact for every exact frozen evaluation question. A detected question stops the job. Binary, unsupported, unreadable, or tampered dataset artifacts are rejected. The dataset artifact must belong to the same project as the model.

CI separately scans designated repository training-data directories for eval-question leakage.

## Submit a job

The authenticated API accepts the following fields for a `train_run` job:

    {
      "kind": "train_run",
      "model_id": "project-model-id",
      "dataset_artifact_id": "project-dataset-artifact-id",
      "steps": 1000,
      "loss_every": 10,
      "checkpoint_every": 100,
      "eval_path": "eval/data/eval.jsonl",
      "eval_hash": "the-64-character-pinned-sha256"
    }

The model and dataset artifact must both belong to the requested project. `eval_path` must resolve to a JSONL file under the repository's `eval/` directory, and `eval_hash` must match its pinned hash.

Limits are enforced to keep logs and checkpoint counts bounded: at most 100,000 requested steps, 2,000 loss records, and 200 checkpoints. The adapter subprocess is bounded by `CONTAINER_TRAIN_TIMEOUT_SECONDS` (default 3,600 seconds). The evaluation subprocess is bounded separately by `CONTAINER_EVAL_TIMEOUT_SECONDS`.

## Verification meaning

A passing test proves that Container checks and records the adapter contract. It does not prove the adapter's internal learning algorithm is correct, that the checkpoint contains useful weights, or that a model has any particular capability. Real model results must come from an independently reviewed trainer and the frozen evaluation—not from the test fixture.
