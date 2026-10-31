"""Known-good deterministic test predictor; not a model or capability claim."""

_ANSWERS = {
    "What is 2 + 2?": "4",
    "What is 9 * 7?": "63",
    "What is 144 / 12?": "12",
    "What is 15 - 8?": "7",
    "Reverse the word 'container'.": "reniatnoc",
    "What is the capital of France?": "Paris",
}


def predict(question: str) -> str:
    """Return the fixture answer for a known task, or a fixed wrong answer."""
    return _ANSWERS.get(question, "NO_STUB_ANSWER")
