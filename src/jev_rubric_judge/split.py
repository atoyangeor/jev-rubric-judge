"""Split instructions into dev set and test set. All questions of one instruction stay together."""
from __future__ import annotations

import json
import random
from pathlib import Path

from .data import Item

SEED = 20261124
DEV_PER_SUBSET = 10


def make_split(items: list[Item], seed: int = SEED, dev_per_subset: int = DEV_PER_SUBSET) -> dict:
    split: dict = {"seed": seed, "dev": [], "test": []}
    for subset in ("easy", "hard"):
        ids = sorted({i.instruction_id for i in items if i.subset == subset})
        random.Random(f"{seed}-{subset}").shuffle(ids)
        split["dev"] += sorted(ids[:dev_per_subset])
        split["test"] += sorted(ids[dev_per_subset:])
    return split


def load_split(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def select(items: list[Item], split: dict, part: str) -> list[Item]:
    ids = set(split[part])
    return [i for i in items if i.instruction_id in ids]
