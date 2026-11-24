"""Run a model over items and keep every answer in a JSONL file, so a rerun never pays twice."""
from __future__ import annotations

import json
from collections import defaultdict
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from .clients import JevClient, OpenAIJudge
from .data import Item
from .variants import build_request


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def _append(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "a", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def run_jev(client: JevClient, items: list[Item], variant: str, out: Path, workers: int = 4,
            examples: list[dict] | None = None, limit_responses: int | None = None) -> None:
    done = {r["key"] for r in read_jsonl(out)}
    by_response: dict[str, list[Item]] = defaultdict(list)
    for item in items:
        if item.key not in done:
            by_response[item.response_key].append(item)
    groups = list(by_response.values())[:limit_responses]

    def one(group: list[Item]) -> list[dict]:
        state, questions = build_request(group, variant, examples)
        answers, usage, seconds = client.ask(state, questions)
        return [{"key": i.key, "p_yes": answers[f"q{i.q_idx}"], "seconds_request": seconds,
                 "input_tokens_request": usage.get("input_tokens"), "questions_in_request": len(group)} for i in group]

    with ThreadPoolExecutor(workers) as pool:
        for rows in pool.map(one, groups):
            _append(out, rows)


def run_llm(judge: OpenAIJudge, items: list[Item], out: Path, repeats: int = 3, workers: int = 8,
            limit: int | None = None, with_instruction: bool = False, examples: list[dict] | None = None) -> None:
    done = {(r["key"], r["repeat"]) for r in read_jsonl(out)}
    todo = [(i, rep) for i in items for rep in range(repeats) if (i.key, rep) not in done][:limit]

    def one(job: tuple[Item, int]) -> dict:
        item, rep = job
        p_yes, answer, usage, seconds = judge.ask(item.input, item.response, item.question,
                                                 item.instruction if with_instruction else None, examples)
        return {"key": item.key, "repeat": rep, "p_yes": p_yes, "answer": answer, "seconds": seconds,
                "prompt_tokens": usage["prompt_tokens"], "completion_tokens": usage["completion_tokens"]}

    with ThreadPoolExecutor(workers) as pool:
        for row in pool.map(one, todo):
            _append(out, [row])
