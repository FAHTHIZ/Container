"""Writes dummy files to test Container's checkpoint contract; does not train a model."""

from pathlib import Path


def run_training(
    *,
    dataset_path: Path,
    output_dir: Path,
    model_id: str,
    steps: int,
    loss_every: int,
    checkpoint_every: int,
) -> None:
    """Emit deterministic loss records and checkpoint-shaped test bytes."""
    if not dataset_path.is_file() or not dataset_path.read_bytes():
        raise ValueError("The fixture requires a non-empty training dataset.")

    for step in range(loss_every, steps + 1, loss_every):
        # This numeric value only exercises the output parser; it is not a measured loss.
        print(f"LOSS step={step} loss={1.0 / (step + 1):.8f}")

    for step in range(checkpoint_every, steps + 1, checkpoint_every):
        checkpoint = output_dir / f"checkpoint-step-{step:08d}.bin"
        checkpoint.write_bytes(
            f"TEST FIXTURE ONLY\nmodel={model_id}\nstep={step}\n".encode()
        )



def omit_one_loss_record(
    *,
    dataset_path: Path,
    output_dir: Path,
    model_id: str,
    steps: int,
    loss_every: int,
    checkpoint_every: int,
) -> None:
    """Negative fixture: create all checkpoints but omit the first required loss."""
    if not dataset_path.is_file():
        raise FileNotFoundError("The fixture dataset is missing.")

    for step in range(loss_every, steps + 1, loss_every):
        if step != loss_every:
            print(f"LOSS step={step} loss={1.0 / (step + 1):.8f}")

    for step in range(checkpoint_every, steps + 1, checkpoint_every):
        checkpoint = output_dir / f"checkpoint-step-{step:08d}.bin"
        checkpoint.write_bytes(f"INVALID TEST FIXTURE\n{model_id}\n{step}\n".encode())
