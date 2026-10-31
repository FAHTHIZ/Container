"""Deterministic trainer-contract fixture; this does not train or create model weights."""

from pathlib import Path
from typing import Callable


def run_training(
    *,
    dataset_path: Path,
    output_dir: Path,
    model_id: str,
    steps: int,
    loss_every: int,
    checkpoint_every: int,
    save_checkpoint: Callable[[int, Path], None],
) -> None:
    """Emit fixed loss records and dummy checkpoint bytes for infrastructure tests."""
    if not dataset_path.is_file():
        raise FileNotFoundError("Test dataset artifact is missing.")

    for step in range(1, steps + 1):
        if step % loss_every == 0:
            print(f"LOSS step={step} loss={1.0 / step:.8f}")

        if step % checkpoint_every == 0:
            checkpoint_path = output_dir / f"fixture-step-{step:08d}.bin"
            checkpoint_path.write_bytes(
                f"TEST FIXTURE ONLY\nmodel={model_id}\nstep={step}\n".encode("utf-8")
            )
            save_checkpoint(step, checkpoint_path)
