"""Second run of Jev noul-fewshot on all questions (2026-11-25), for two things the first run cannot show:
the wall-clock time with 8 parallel requests (the same as the LLM judge rerun), and whether Jev returns
the same probability for the same request. The first run's answers stay the ones every result uses.
Expected cost: 248 requests x ~1,550 input tokens at $0.042 per 1M = about $0.016."""
import json, os, time
import httpx
import numpy as np
from jev_rubric_judge.cli import FEWSHOT, JEV_MODEL, JEV_PRICE, ROOT, jev_predictions, load_env, part_items
from jev_rubric_judge.clients import JevClient
from jev_rubric_judge.cost import CostMeter
from jev_rubric_judge.runner import read_jsonl, run_jev

load_env(); shown = json.loads(FEWSHOT.read_text()); used = {e["key"] for e in shown}
examples = [{k: v for k, v in e.items() if k != "key"} for e in shown]
meter = CostMeter("Jev repeat", *JEV_PRICE, budget_usd=0.05); total = 0.0; diffs = []
with httpx.Client(timeout=60) as http:
    client = JevClient(os.environ["TYPESAFE_API_KEY"], JEV_MODEL, http, meter)
    for part in ("dev", "test"):
        items = [i for i in part_items(part) if i.key not in used]
        out = ROOT / "runs" / part / f"jev__{JEV_MODEL}__noul-fewshot__repeat.jsonl"
        if out.exists(): out.unlink()
        t = time.perf_counter(); run_jev(client, items, "noul-fewshot", out, workers=8, examples=examples); w = time.perf_counter() - t; total += w
        first = jev_predictions(part, "noul-fewshot"); again = {r["key"]: r["p_yes"] for r in read_jsonl(out)}
        diffs += [abs(first[k] - again[k]) for k in again]
        print(f"{part}: {len(again)} questions in {len({k.rsplit('|', 1)[0] for k in again})} requests, wall-clock {w:.1f} s with 8 parallel requests")
d = np.array(diffs)
print(meter.summary()); print(f"total wall-clock {total:.1f} s for {len(d)} questions")
print(f"same request twice: identical probability on {int((d == 0).sum())} of {len(d)} questions; differs by 0.05 or more on {int((d >= 0.05).sum())}, by 0.10 or more on {int((d >= 0.10).sum())}; largest difference {d.max():.2f}")
