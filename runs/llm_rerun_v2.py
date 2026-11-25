"""Second run of the LLM judge, made after the independent review (2026-11-24).
Differences from the first run: ONE call per question (the review showed three add nothing), the raw
logprob alternatives are saved, and only the tokens "yes" / "no" (any case, any spacing) are counted.
Same model, same prompt with the instruction. The review suggested asking for 20 alternatives: the API
refuses ("Invalid value for 'top_logprobs': must be less than or equal to 5"), so 5 it stays.

    uv run python runs/llm_rerun_v2.py dev --limit 20     # dry run
    uv run python runs/llm_rerun_v2.py dev
    uv run python runs/llm_rerun_v2.py test

Expected cost: about 1,123 calls x ~600 input tokens at $0.10 per 1M = $0.07 in total."""
import argparse, json, math, os, re, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import httpx

from jev_rubric_judge.cli import LLM_MODEL, LLM_PRICE, ROOT, load_env, part_items
from jev_rubric_judge.clients import OpenAIJudge, _post
from jev_rubric_judge.cost import CostMeter


def p_yes(top: list[dict]) -> float | None:
    yes = no = 0.0
    for alt in top:
        word = re.sub(r"[^a-z]", "", alt["token"].lower())
        if word == "yes": yes += math.exp(alt["logprob"])
        elif word == "no": no += math.exp(alt["logprob"])
    return yes / (yes + no) if yes + no > 0 else None


def main() -> None:
    ap = argparse.ArgumentParser(); ap.add_argument("part", choices=("dev", "test")); ap.add_argument("--limit", type=int); ap.add_argument("--budget", type=float, default=0.15)
    args = ap.parse_args(); load_env()
    out = ROOT / "runs" / args.part / f"llm__{LLM_MODEL}__instruction_v2.jsonl"
    done = {json.loads(l)["key"] for l in out.read_text().splitlines()} if out.exists() else set()
    todo = [i for i in part_items(args.part) if i.key not in done][: args.limit]
    meter = CostMeter("LLM judge v2", *LLM_PRICE, budget_usd=args.budget)

    def one(item):
        body = {"model": LLM_MODEL, "logprobs": True, "top_logprobs": 5, "reasoning_effort": "none", "max_completion_tokens": 32,
                "messages": [{"role": "user", "content": OpenAIJudge.build_prompt(item.input, item.response, item.question, item.instruction)}]}
        data, seconds = _post(http, "https://api.openai.com/v1/chat/completions", {"Authorization": f"Bearer {os.environ['OPENAI_API_KEY']}"}, body, attempts=3)
        u = data["usage"]; meter.add(u["prompt_tokens"], u["completion_tokens"], (u.get("completion_tokens_details") or {}).get("reasoning_tokens") or 0)
        ch = data["choices"][0]; content = (ch.get("logprobs") or {}).get("content") or []
        top = [{"token": a["token"], "logprob": a["logprob"]} for a in content[0]["top_logprobs"]] if content else []
        return {"key": item.key, "p_yes": p_yes(top), "answer": ch["message"]["content"] or "", "top": top, "seconds": seconds,
                "prompt_tokens": u["prompt_tokens"], "completion_tokens": u["completion_tokens"]}

    started = time.perf_counter(); failed = 0
    # Each request may wait 30 s at most; answers are written as they arrive, so one stuck call cannot block the rest.
    with httpx.Client(timeout=30) as http, ThreadPoolExecutor(8) as pool, open(out, "a", encoding="utf-8") as f:
        try:
            for fut in as_completed([pool.submit(one, i) for i in todo]):
                try:
                    f.write(json.dumps(fut.result(), ensure_ascii=False) + "\n"); f.flush()
                except Exception as e:  # the question stays out of the file and is retried on the next run
                    failed += 1; print("failed:", type(e).__name__, str(e)[:120])
        finally:
            print(meter.summary(), f"| wall-clock {time.perf_counter() - started:.0f} s for {len(todo)} calls, 8 in parallel, {failed} failed")


if __name__ == "__main__":
    main()
