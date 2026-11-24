"""How one model response and its rubric questions become one Jev request."""
from __future__ import annotations

from .data import Item

VARIANTS = ("noul-plain", "noul-criteria", "noul-instruction", "noul-fewshot")

# The YES / NO rules of the InFoBench judge prompt, shortened to one line each.
CRITERIA = {
    "true": "The generated text entirely fulfills the condition in the question. Even a minor inaccuracy means the answer is not yes.",
    "false": "The generated text fails the condition, or gives no information that could be used to answer the question.",
}


def build_request(items: list[Item], variant: str, examples: list[dict] | None = None) -> tuple[dict, dict[str, dict]]:
    """items = all questions about ONE model response. Returns (state, questions keyed by 'q<idx>')."""
    first = items[0]
    assert all(i.response_key == first.response_key for i in items)
    state: dict = {}
    if variant == "noul-instruction":
        state["instruction"] = first.instruction
    if first.input.strip():
        state["input"] = first.input
    state["generated_text"] = first.response
    if variant == "noul-fewshot":
        state["examples_of_judged_questions"] = examples or []
    questions: dict[str, dict] = {}
    for item in items:
        q: dict = {"type": "noul", "instructions": item.question}
        if variant == "noul-criteria":
            q["criteria"] = CRITERIA
        questions[f"q{item.q_idx}"] = q
    return state, questions
