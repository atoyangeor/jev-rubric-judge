"""Jev against the LLM judge after the fair rerun (runs/llm_rerun_v2.py: one call per question, raw logprobs).
Two ways to turn the LLM's logprobs into P(yes):
  old - yes / (yes + no) over the returned alternatives. The API returns only ONE alternative on most
        calls, so this gives exactly 1.0 or 0.0 there.
  new - the same when both 'yes' and 'no' are returned; when only one is returned, its own probability:
        exp(logprob) for 'yes', 1 - exp(logprob) for 'no'. Fixed before looking at any result.
Everything else as in runs/fair_yardstick.py and runs/crossval_strict.py."""
import json, math, re
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import FEWSHOT, ROOT, jev_predictions, part_items
from jev_rubric_judge.runner import read_jsonl

shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
items = [i for part in ("dev", "test") for i in part_items(part) if i.key not in shown]
rows = {r["key"]: r for part in ("dev", "test") for r in read_jsonl(ROOT / "runs" / part / "llm__gpt-6-luna__instruction_v2.jsonl")}

def masses(top):
    yes = no = 0.0
    for a in top:
        w = re.sub(r"[^a-z]", "", a["token"].lower())
        if w == "yes": yes += math.exp(min(a["logprob"], 0.0))
        elif w == "no": no += math.exp(min(a["logprob"], 0.0))
    return yes, no
def p_old(top):
    y, n = masses(top); return y / (y + n)
def p_new(top):
    y, n = masses(top)
    return y / (y + n) if y > 0 and n > 0 else (y if y > 0 else 1 - n)

Y = np.array([i.correct for i in items]); G = np.array([i.instruction_id for i in items]); L = np.array([i.labels for i in items]); N = len(Y)
systems = {"Jev": np.array([{**jev_predictions("dev", "noul-fewshot"), **jev_predictions("test", "noul-fewshot")}[i.key] for i in items]),
           "LLM, one call, old formula": np.array([p_old(rows[i.key]["top"]) for i in items]),
           "LLM, one call, new formula": np.array([p_new(rows[i.key]["top"]) for i in items])}
ids = np.unique(G); mem = {g: np.flatnonzero(G == g) for g in ids}
PAIRS = [(e, [k for k in range(3) if k != e]) for e in range(3)]; REF = [(L[:, o[0]] == L[:, o[1]], L[:, o[0]]) for _, o in PAIRS]
def fair(answer, subset, w=None):
    w = np.ones(N) if w is None else w
    return float(np.mean([np.average((answer(e) == ref)[m & subset], weights=w[m & subset]) for (e, _), (m, ref) in zip(PAIRS, REF)]))
def interval(fn, n=2000):
    rng = np.random.default_rng(0)
    return np.percentile([fn(np.bincount(np.concatenate([mem[g] for g in rng.choice(ids, size=len(ids), replace=True)]), minlength=N).astype(float)) for _ in range(n)], [2.5, 97.5]).round(1)
expert = lambda e: L[:, e]; ALL = np.ones(N, bool)
def cv(P, target, reps=20, tune_cut=False):
    rng = np.random.default_rng(0); out = []
    for _ in range(reps):
        ty = np.zeros(N, bool); tn = np.zeros(N, bool); ans05 = np.zeros(N, int)
        for fold in np.array_split(rng.permutation(ids), 10):
            te = np.isin(G, fold)
            if tune_cut:
                cs = np.unique(np.round(np.concatenate([[0.5], P[~te]]), 6)); c = max(cs, key=lambda c: ((P[~te] > c).astype(int) == Y[~te]).mean()); ans05[te] = (P[te] > c).astype(int)
            else:
                r = metrics.pick_thresholds(P[~te], Y[~te], target); ty |= te & (P >= r.t_yes); tn |= te & (P <= r.t_no)
        out.append(ans05 if tune_cut else (ty, tn))
    return out

print(f"{N} questions. One person, graded by the other two experts where they agree: {100 * fair(expert, ALL):.1f}%\n")
for name, P in systems.items():
    a05 = (P > .5).astype(int); tuned = cv(P, None, tune_cut=True)
    print(f"== {name}: {len(np.unique(P))} distinct values; exactly 1.0 on {int((P == 1).sum())}, exactly 0.0 on {int((P == 0).sum())}; calibration error {metrics.calibration_error(P, Y)[0]:.3f}")
    print(f"   alone: 0.5 rule {100 * fair(lambda e: a05, ALL):.1f}%; cut-off tuned on other instructions {100 * np.mean([fair(lambda e, a=a: a, ALL) for a in tuned]):.1f}% "
          f"(minus the person {100 * (np.mean([fair(lambda e, a=a: a, ALL) for a in tuned]) - fair(expert, ALL)):+.1f}, interval {interval(lambda w: 100 * (fair(lambda e: tuned[0], ALL, w) - fair(expert, ALL, w)))})")
    for target in (0.96, 0.97, 0.98):
        res = cv(P, target); rws = []
        for ty, tn in res:
            taken = ty | tn; ans = ty.astype(int)
            if not taken.any(): rws.append((100.0, np.nan, np.nan, 100 * fair(expert, ALL), np.nan)); continue
            rws.append((100 * (~taken).mean(), 100 * fair(lambda e: ans, taken), 100 * fair(expert, taken), 100 * fair(lambda e: np.where(taken, ans, L[:, e]), ALL), 100 * (ans[taken] == Y[taken]).mean()))
        m = np.nanmean(np.array(rws), axis=0); ty, tn = res[0]; taken = ty | tn; ans = ty.astype(int)
        iv = interval(lambda w: 100 * (fair(lambda e: np.where(taken, ans, L[:, e]), ALL, w) - fair(expert, ALL, w))) if taken.any() else "n/a"
        print(f"   rule {int(100 * target)}%: left to the person {m[0]:.1f} per 100 | taken answers: model {m[1]:.1f}%, the person on the same {m[2]:.1f}% | whole process {m[3]:.1f}% (minus the person alone {m[3] - 100 * fair(expert, ALL):+.1f}, interval {iv}) | taken answers that match the vote of three {m[4]:.1f}%")
# direct comparison Jev vs the LLM (new formula), rule 96%, first cut
(jy, jn), (ly, ln) = cv(systems["Jev"], 0.96, reps=1)[0], cv(systems["LLM, one call, new formula"], 0.96, reps=1)[0]
jt, lt = jy | jn, ly | ln
print("\nJev minus LLM (new formula), rule 96%, first cut: questions left per 100", round(100 * ((~jt).mean() - (~lt).mean()), 1), "interval",
      interval(lambda w: 100 * (np.average(~jt, weights=w) - np.average(~lt, weights=w))),
      "| whole process, points", round(100 * (fair(lambda e: np.where(jt, jy.astype(int), L[:, e]), ALL) - fair(lambda e: np.where(lt, ly.astype(int), L[:, e]), ALL)), 1), "interval",
      interval(lambda w: 100 * (fair(lambda e: np.where(jt, jy.astype(int), L[:, e]), ALL, w) - fair(lambda e: np.where(lt, ly.astype(int), L[:, e]), ALL, w))))
secs = np.array([r["seconds"] for r in rows.values()])
print(f"LLM rerun: {len(rows)} calls, sum of request times {secs.sum():.0f} s, mean {secs.mean():.2f} s, median {np.median(secs):.2f} s; wall-clock with 8 parallel calls: 3 + 46 + 66 = 115 s; cost $0.064 (dry run $0.0015 + dev $0.0268 + test $0.0371, rounded)")
