"""Load the expert-annotated part of InFoBench into one flat list of items.

One item = one rubric question asked about one model response, with the answers of three experts.
"""
from __future__ import annotations

import csv
import json
import re
from dataclasses import dataclass
from pathlib import Path

RESPONSE_MODELS = ("gpt-3.5-turbo", "gpt-4", "claude-v1", "alpaca-7b", "vicuna-13b")
# Third expert's column has no "annotator3" suffix in the source files.
LABEL_COLUMNS = ("{m}-annotation-annotator1", "{m}-annotation-annotator2", "{m}-annotation")

csv.field_size_limit(10**9)


@dataclass(frozen=True)
class Item:
    subset: str  # "easy" | "hard"
    instruction_id: str
    response_model: str
    q_idx: int
    question: str
    categories: tuple[str, ...]
    input: str
    instruction: str
    response: str
    labels: tuple[int, int, int]  # 1 = yes, 0 = no, one per expert

    @property
    def correct(self) -> int:
        """The answer at least two of the three experts gave."""
        return int(sum(self.labels) >= 2)

    @property
    def key(self) -> str:
        return f"{self.instruction_id}|{self.response_model}|{self.q_idx}"

    @property
    def response_key(self) -> str:
        return f"{self.instruction_id}|{self.response_model}"


def parse_labels(cell: str) -> list[int | None] | None:
    """Parse one expert's cell. Three formats occur: '1. Yes\\n2. No', 'yes\\nno', '1.0.1'."""
    cell = cell.strip()
    if not cell:
        return None
    if re.fullmatch(r"[01](\.[01])*\.?", cell):
        return [int(x) for x in cell.strip(".").split(".")]
    out: list[int | None] = []
    for line in cell.splitlines():
        line = line.strip().lower()
        if not line:
            continue
        line = re.sub(r"^\d+\s*[\.\)]?\s*", "", line)
        out.append(1 if line.startswith("yes") else 0 if line.startswith("no") else None)
    return out


def _load_hf(path: Path) -> dict[str, dict]:
    raw = path.read_text(encoding="utf-8").strip()
    try:
        records = json.loads(raw)
    except json.JSONDecodeError:
        records = [json.loads(line) for line in raw.splitlines() if line.strip()]
    return {r["id"]: r for r in records}


def load_items(raw_dir: Path) -> tuple[list[Item], list[str]]:
    """Return (items with three readable labels, keys of responses dropped for unreadable labels)."""
    hf = _load_hf(raw_dir / "InfoBench.json")
    items: list[Item] = []
    dropped: list[str] = []
    for subset in ("easy", "hard"):
        with open(raw_dir / f"expert_{subset}.csv", encoding="utf-8") as f:
            rows = list(csv.DictReader(f))
        for row in rows:
            rid = (row.get("id") or "").strip()
            if not rid or rid not in hf:
                continue
            questions = hf[rid]["decomposed_questions"]
            categories = hf[rid]["question_label"]
            for model in RESPONSE_MODELS:
                parsed = [parse_labels(row.get(c.format(m=model), "") or "") for c in LABEL_COLUMNS]
                if all(p is None for p in parsed):
                    continue  # this instruction was not annotated by experts
                if any(p is None or len(p) != len(questions) or None in p for p in parsed):
                    dropped.append(f"{rid}|{model}")
                    continue
                for q_idx, question in enumerate(questions):
                    items.append(
                        Item(
                            subset=subset,
                            instruction_id=rid,
                            response_model=model,
                            q_idx=q_idx,
                            question=question,
                            categories=tuple(categories[q_idx]),
                            input=row["input"],
                            instruction=row["instruction"],
                            response=row[model],
                            labels=tuple(p[q_idx] for p in parsed),  # type: ignore[index,arg-type]
                        )
                    )
    return items, dropped
