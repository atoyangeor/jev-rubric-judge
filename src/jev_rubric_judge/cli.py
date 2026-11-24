"""Entry point: prepare the split, run Jev, run the LLM judge, print the report.

    uv run python -m jev_rubric_judge.cli prepare
    uv run python -m jev_rubric_judge.cli run-jev --part dev --variant noul-plain
    uv run python -m jev_rubric_judge.cli run-llm --part dev
    uv run python -m jev_rubric_judge.cli report --part dev
"""
from __future__ import annotations

import argparse
import json
import os
from collections import defaultdict
from pathlib import Path

import httpx
import numpy as np

from . import metrics
from .clients import JevClient, OpenAIJudge
from .cost import CostMeter
from .data import Item, load_items
from .runner import read_jsonl, run_jev, run_llm
from .split import load_split, make_split, select

ROOT = Path(__file__).resolve().parents[2]
RAW = ROOT / "data" / "raw"
SPLIT = ROOT / "data" / "split.json"
RUNS = ROOT / "runs"

JEV_MODEL = "jev-1.14.0"
LLM_MODEL = "gpt-6-luna"
# Prices per 1M tokens. Jev: docs.typesafe.ai, read 2026-11-22 (output is free).
# gpt-6-luna: developers.openai.com/api/docs/pricing, "Standard", read 2026-11-24.
JEV_PRICE = (0.042, 0.0)
LLM_PRICE = (0.10, 0.50)
# Paper, Table 4: three experts cost $1,416 for 1,135 questions -> one expert answer costs $0.4159.
USD_PER_EXPERT_ANSWER = 1416 / 3 / 1135


def load_env() -> None:
    env = ROOT / ".env"
    if env.exists():
        for line in env.read_text(encoding="utf-8").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and key.strip() not in os.environ:
                os.environ[key.strip()] = value.strip()


def part_items(part: str) -> list[Item]:
    items, _ = load_items(RAW)
    return select(items, load_split(SPLIT), part)


FEWSHOT = ROOT / "data" / "fewshot_examples.json"


def fewshot_examples() -> list[dict]:
    """Eight dev set questions shown to Jev as examples: 4 with the correct answer yes, 4 with no,
    all three experts agree, short responses. Written to a file once; these questions are left out
    of the metric of the few-shot variant."""
    if FEWSHOT.exists():
        return json.loads(FEWSHOT.read_text(encoding="utf-8"))
    import random
    pool = [i for i in part_items("dev") if len(set(i.labels)) == 1 and len(i.response) < 600 and len(i.input) < 600]
    random.Random(20261124).shuffle(pool)
    chosen, used_instructions = [], set()
    for want in (1, 0) * 4:
        item = next(i for i in pool if i.correct == want and i.instruction_id not in used_instructions)
        used_instructions.add(item.instruction_id)
        ex = {"key": item.key, "generated_text": item.response, "question": item.question, "answer": "yes" if want else "no"}
        if item.input.strip():
            ex["input"] = item.input
        chosen.append(ex)
    FEWSHOT.write_text(json.dumps(chosen, indent=1, ensure_ascii=False), encoding="utf-8")
    return chosen


def guard_test(part: str, confirmed: bool) -> None:
    if part == "test" and not confirmed:
        raise SystemExit("The test set is run once, after the variant and the boundaries are fixed. Add --final-test-run.")


def jev_path(part: str, variant: str) -> Path:
    return RUNS / part / f"jev__{JEV_MODEL}__{variant}.jsonl"


LLM_VARIANTS = ("paper", "instruction", "fewshot")


def llm_path(part: str, variant: str = "paper") -> Path:
    suffix = "" if variant == "paper" else f"__{variant}"
    return RUNS / part / f"llm__{LLM_MODEL}{suffix}.jsonl"


def cmd_prepare(args) -> None:
    items, dropped = load_items(RAW)
    print(f"questions with three readable expert answers: {len(items)}; responses dropped: {dropped}")
    if SPLIT.exists():
        print(f"{SPLIT} already exists, not overwritten")
    else:
        SPLIT.write_text(json.dumps(make_split(items), indent=1), encoding="utf-8")
    split = load_split(SPLIT)
    for part in ("dev", "test"):
        sel = select(items, split, part)
        yes = sum(i.correct for i in sel)
        print(f"{part}: {len(split[part])} instructions, {len({i.response_key for i in sel})} responses, "
              f"{len(sel)} questions, correct answer 'yes' in {yes} ({100 * yes / len(sel):.1f}%)")


def cmd_run_jev(args) -> None:
    guard_test(args.part, args.final_test_run)
    load_env()
    # Expected: ~100 requests x ~700 input tokens at $0.042 per 1M = about $0.003 for the dev set.
    meter = CostMeter("Jev", *JEV_PRICE, budget_usd=args.budget)
    with httpx.Client(timeout=120) as http:
        client = JevClient(os.environ["TYPESAFE_API_KEY"], JEV_MODEL, http, meter)
        items, examples = part_items(args.part), None
        if args.variant == "noul-fewshot":
            shown = fewshot_examples()
            used = {e["key"] for e in shown}
            items = [i for i in items if i.key not in used]
            examples = [{k: v for k, v in e.items() if k != "key"} for e in shown]
        try:
            run_jev(client, items, args.variant, jev_path(args.part, args.variant),
                    limit_responses=args.limit, examples=examples)
        finally:
            print(meter.summary())


def cmd_run_llm(args) -> None:
    guard_test(args.part, args.final_test_run)
    load_env()
    # Expected: ~450 questions x 3 repeats x ~700 input tokens at $0.10 per 1M + 4 output tokens at $0.50 per 1M
    # = about $0.10 for the dev set. The dry run (--limit 30) checks the tokens per call before the full run.
    meter = CostMeter("LLM judge", *LLM_PRICE, budget_usd=args.budget)
    with httpx.Client(timeout=120) as http:
        judge = OpenAIJudge(os.environ["OPENAI_API_KEY"], LLM_MODEL, http, meter)
        items, examples = part_items(args.part), None
        if args.variant == "fewshot":
            shown = fewshot_examples()
            used = {e["key"] for e in shown}
            items = [i for i in items if i.key not in used]
            examples = [{k: v for k, v in e.items() if k != "key"} for e in shown]
        try:
            run_llm(judge, items, llm_path(args.part, args.variant), repeats=args.repeats, limit=args.limit,
                    with_instruction=args.variant == "instruction", examples=examples)
        finally:
            print(meter.summary())


def jev_predictions(part: str, variant: str) -> dict[str, float]:
    return {r["key"]: r["p_yes"] for r in read_jsonl(jev_path(part, variant))}


def llm_predictions(part: str, variant: str = "paper") -> tuple[dict[str, float], dict]:
    by_key: dict[str, list[float]] = defaultdict(list)
    no_probability = 0
    for r in read_jsonl(llm_path(part, variant)):
        p = r["p_yes"]
        if p is None:  # no yes/no among the first-token alternatives: fall back to the answer text
            no_probability += 1
            p = 1.0 if r["answer"].strip().lower().startswith("yes") else 0.0
        by_key[r["key"]].append(p)
    spread = [max(v) - min(v) for v in by_key.values() if len(v) > 1]
    info = {"calls_without_probability": no_probability,
            "questions_where_repeats_differ_by_0.10_or_more": int(sum(s >= 0.10 for s in spread)),
            "questions_with_repeats": len(spread)}
    return {k: float(np.mean(v)) for k, v in by_key.items()}, info


def describe(name: str, items: list[Item], preds: dict[str, float], min_accuracy: float, thresholds=None) -> dict:
    """All numbers for one system on one part. thresholds=None -> pick them on this part (dev set only)."""
    sel = [i for i in items if i.key in preds]
    p = np.array([preds[i.key] for i in sel])
    y = np.array([i.correct for i in sel])
    groups = np.array([i.instruction_id for i in sel])
    r = metrics.pick_thresholds(p, y, min_accuracy) if thresholds is None else metrics.route(p, y, *thresholds)
    ece, _ = metrics.calibration_error(p, y)
    acc = metrics.accuracy(p, y)
    acc_ci = metrics.bootstrap_interval(groups, lambda idx: metrics.accuracy(p[idx], y[idx]))
    human_ci = metrics.bootstrap_interval(groups, lambda idx: metrics.route(p[idx], y[idx], r.t_yes, r.t_no).human_per_100)
    taken_ci = metrics.bootstrap_interval(groups, lambda idx: metrics.route(p[idx], y[idx], r.t_yes, r.t_no).taken_accuracy)
    return {"system": name, "questions": len(sel), "questions_missing": len(items) - len(sel),
            "alone_correct": int(round(acc * len(sel))), "alone_accuracy": acc, "alone_accuracy_ci95": acc_ci,
            "t_yes": r.t_yes, "t_no": r.t_no, "human_questions": r.n_human, "human_per_100": r.human_per_100,
            "human_per_100_ci95": human_ci, "taken": r.n_taken, "taken_correct": r.n_taken_correct,
            "taken_accuracy": r.taken_accuracy, "taken_accuracy_ci95": taken_ci, "calibration_error": ece,
            "usd_one_expert_all": USD_PER_EXPERT_ANSWER * len(sel), "usd_one_expert_left": USD_PER_EXPERT_ANSWER * r.n_human}


def cmd_report(args) -> None:
    items = part_items(args.part)
    y = np.array([i.correct for i in items])
    print(f"{args.part}: {len(items)} questions; all-'yes' baseline is right in {int(y.sum())} ({100 * y.mean():.1f}%)")
    systems: list[tuple[str, dict[str, float]]] = []
    for variant in args.variants:
        preds = jev_predictions(args.part, variant)
        if preds:
            systems.append((f"Jev {variant}", preds))
    for variant in LLM_VARIANTS:
        llm, info = llm_predictions(args.part, variant)
        if llm:
            systems.append((f"LLM judge {LLM_MODEL} {variant}", llm))
            print(f"LLM judge {variant}:", info)
    fixed = json.loads(args.thresholds) if args.thresholds else {}
    rows = [describe(name, items, preds, args.min_accuracy, tuple(fixed[name]) if name in fixed else None) for name, preds in systems]
    out = RUNS / args.part / "report.json"
    out.write_text(json.dumps(rows, indent=1), encoding="utf-8")
    for r in rows:
        print(f"\n{r['system']}  ({r['questions']} questions, {r['questions_missing']} missing)")
        print(f"  alone: {r['alone_correct']} of {r['questions']} right = {100 * r['alone_accuracy']:.1f}% "
              f"(95% interval {100 * r['alone_accuracy_ci95'][0]:.1f}-{100 * r['alone_accuracy_ci95'][1]:.1f})")
        print(f"  boundaries t_yes={r['t_yes']:.2f} t_no={r['t_no']:.2f}: human gets {r['human_questions']} of {r['questions']} "
              f"= {r['human_per_100']:.1f} per 100 (95% interval {r['human_per_100_ci95'][0]:.1f}-{r['human_per_100_ci95'][1]:.1f})")
        print(f"  answers taken from the model: {r['taken_correct']} of {r['taken']} right = {100 * r['taken_accuracy']:.1f}% "
              f"(95% interval {100 * r['taken_accuracy_ci95'][0]:.1f}-{100 * r['taken_accuracy_ci95'][1]:.1f})")
        print(f"  calibration error {r['calibration_error']:.3f}; one expert: ${r['usd_one_expert_all']:.0f} for all, "
              f"${r['usd_one_expert_left']:.0f} for the questions left")


def main() -> None:
    parser = argparse.ArgumentParser()
    sub = parser.add_subparsers(required=True)
    sub.add_parser("prepare").set_defaults(fn=cmd_prepare)
    for name, fn in (("run-jev", cmd_run_jev), ("run-llm", cmd_run_llm)):
        p = sub.add_parser(name)
        p.add_argument("--part", choices=("dev", "test"), required=True)
        p.add_argument("--final-test-run", action="store_true")
        p.add_argument("--limit", type=int, default=None, help="dry run: only this many requests")
        p.add_argument("--budget", type=float, default=1.0, help="stop when the run has cost this many USD")
        if name == "run-jev":
            p.add_argument("--variant", default="noul-plain")
        else:
            p.add_argument("--repeats", type=int, default=3)
            p.add_argument("--variant", choices=LLM_VARIANTS, default="paper")
        p.set_defaults(fn=fn)
    p = sub.add_parser("report")
    p.add_argument("--part", choices=("dev", "test"), required=True)
    p.add_argument("--variants", nargs="*", default=["noul-plain", "noul-criteria", "noul-instruction", "noul-fewshot"])
    p.add_argument("--min-accuracy", type=float, default=metrics.ONE_EXPERT_ACCURACY)
    p.add_argument("--thresholds", default=None, help='JSON {"system name": [t_yes, t_no]} fixed on the dev set')
    p.set_defaults(fn=cmd_report)
    args = parser.parse_args()
    args.fn(args)


if __name__ == "__main__":
    main()
