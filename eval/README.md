# Frozen Evaluation

Container is infrastructure. It schedules, stores, and tracks. It does not think.

This directory contains a small, deterministic plumbing fixture for verifying the evaluation runner. It is **not** a general language-model benchmark and its score is not evidence of model quality.

## Run it

From the repository root:

    python -m eval.runner --model-id deterministic-stub
    python -m eval.runner --negative-control
    python eval/check_quarantine.py

The runner verifies the evaluation JSONL against its SHA-256 pin before parsing or scoring tasks. A missing file, invalid digest, changed file, malformed task, or predictor error stops the run.

A prediction function is a trusted Python callable exposed as module.path:function_name:

    python -m eval.runner --model-id example --predictor my_adapter:predict

The function receives one question string and must return one answer string. It is loaded only because the operator explicitly selected it; do not point it at untrusted code.

## Add a task

1. Add one JSON object per line to eval/data/eval.jsonl.
2. Each object must contain exactly three non-empty string fields: id, question, and expected.
3. Give every task a unique ID. Keep prompts stable and deterministic.
4. Review the question for suitability and make sure it is not copied into any training dataset.
5. Regenerate the hash only after reviewing the change.

For example:

    {"id":"example-unique-id","question":"What is 3 + 5?","expected":"8"}

## Re-freeze the dataset

From the repository root, regenerate the digest after an intentional eval edit:

    sha256sum eval/data/eval.jsonl | cut -d ' ' -f 1 > eval/data/eval.sha256

On PowerShell:

    (Get-FileHash eval/data/eval.jsonl -Algorithm SHA256).Hash.ToLower() | Set-Content eval/data/eval.sha256 -NoNewline

Review the diff to both files and commit them together. Do not update the hash merely to silence a failed check.

## Negative control

The negative-control flag replaces every prediction with a fixed no-op answer. It calculates the known-good deterministic stub score and asserts the no-op score is strictly lower. The stub is a test fixture, not an AI model. A failed negative control invalidates the evaluation harness.

## Training-data quarantine

CI scans directories named train, training, train_data, training_data, train-data, or training-data. Files must use an inspected text format. Unknown/binary files, symlinks, unreadable files, and exact occurrences of any eval question fail closed. Keep future training corpora in one of these designated directories so CI can inspect them.
