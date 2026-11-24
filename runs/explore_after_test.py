"""Exploration AFTER the single test run. Not a result: the test set was already seen.
A: what other boundaries would have given on the test set. B: cross-validation over all 50 instructions.
C: Jev alone against the LLM judge alone. D: seconds per question."""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import FEWSHOT, jev_predictions, llm_predictions, part_items
from jev_rubric_judge.runner import read_jsonl

shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
def load(part):
    items = [i for i in part_items(part) if i.key not in shown]
    jev = jev_predictions(part, "noul-fewshot"); llm = llm_predictions(part, "instruction")[0]
    return items, np.array([i.correct for i in items]), np.array([i.instruction_id for i in items]), np.array([jev[i.key] for i in items]), np.array([llm[i.key] for i in items])

items, y, g, pj, pl = load("test")
print("A. Jev noul-fewshot on the test set under other boundaries (frozen pair first)")
for ty, tn in ((0.83, 0.42), (0.83, 0.30), (0.83, 0.20), (0.83, 0.10), (0.83, -0.01), (0.90, 0.42), (0.90, 0.10), (0.90, -0.01), (0.95, -0.01)):
    r = metrics.route(pj, y, ty, tn)
    print(f"  t_yes {ty:.2f} t_no {'none' if tn < 0 else f'{tn:.2f}'}: human {r.n_human} of {r.n} = {r.human_per_100:.1f} per 100; taken right {r.n_taken_correct}/{r.n_taken} = {100*r.taken_accuracy:.1f}%")
for name, p in (("Jev", pj), ("LLM", pl)):
    r = metrics.pick_thresholds(p, y, 0.941)
    print(f"  best possible on the test set itself for {name} (boundaries chosen on the test set, optimistic): t_yes {r.t_yes:.2f} t_no {r.t_no:.2f}, human {r.n_human} = {r.human_per_100:.1f} per 100, taken right {r.n_taken_correct}/{r.n_taken} = {100*r.taken_accuracy:.1f}%")

di, dy, dg, dpj, dpl = load("dev")
Y = np.concatenate([dy, y]); G = np.concatenate([dg, g]); PJ = np.concatenate([dpj, pj]); PL = np.concatenate([dpl, pl])
print(f"\nB. Cross-validation over all {len(np.unique(G))} instructions, {len(Y)} questions: boundaries chosen on 9 tenths of the instructions, applied to the remaining tenth; 20 random ways to cut into tenths")
rng = np.random.default_rng(0); ids = np.unique(G)
for name, P in (("Jev noul-fewshot", PJ), ("LLM judge instruction", PL)):
    for target in (0.941, 0.96):
        hum, acc, taken_n = [], [], []
        for rep in range(20):
            perm = rng.permutation(ids); human = taken = right = 0
            for fold in np.array_split(perm, 10):
                test = np.isin(G, fold); r0 = metrics.pick_thresholds(P[~test], Y[~test], target); r = metrics.route(P[test], Y[test], r0.t_yes, r0.t_no)
                human += r.n_human; taken += r.n_taken; right += r.n_taken_correct
            hum.append(100 * human / len(Y)); acc.append(100 * right / taken); taken_n.append(taken)
        print(f"  {name}, rule {100*target:.1f}%: human {np.mean(hum):.1f} per 100 (from {min(hum):.1f} to {max(hum):.1f} across the 20 cuts); taken answers right {np.mean(acc):.1f}% (from {min(acc):.1f} to {max(acc):.1f}); 94.1% met in {sum(a >= 94.1 for a in acc)} of 20 cuts")

print("\nC. Alone, no human")
for label, yy, gg, a, b in (("test 644", y, g, pj, pl), (f"all {len(Y)}", Y, G, PJ, PL)):
    ca, cb = (a > .5).astype(int) == yy, (b > .5).astype(int) == yy
    rng = np.random.default_rng(1); u = np.unique(gg); mem = {k: np.flatnonzero(gg == k) for k in u}; d = []
    for _ in range(2000):
        idx = np.concatenate([mem[k] for k in rng.choice(u, size=len(u), replace=True)]); d.append(100 * (ca[idx].mean() - cb[idx].mean()))
    print(f"  {label}: Jev {int(ca.sum())}/{len(yy)} = {100*ca.mean():.1f}%, LLM {int(cb.sum())}/{len(yy)} = {100*cb.mean():.1f}%, difference {100*(ca.mean()-cb.mean()):.1f} points, 95% interval {np.percentile(d,[2.5,97.5]).round(1)}; calibration error Jev {metrics.calibration_error(a, yy)[0]:.3f}, LLM {metrics.calibration_error(b, yy)[0]:.3f}")

print("\nD. Seconds (one laptop, 4 parallel requests to Jev, 8 to OpenAI)")
jr = read_jsonl(__import__("pathlib").Path("runs/test/jev__jev-1.14.0__noul-fewshot.jsonl")); req = {r["key"].rsplit("|", 1)[0]: r["seconds_request"] for r in jr}
lr = read_jsonl(__import__("pathlib").Path("runs/test/llm__gpt-6-luna__instruction.jsonl")); ls = np.array([r["seconds"] for r in lr])
print(f"  Jev: {len(req)} requests for {len(jr)} questions, sum of request seconds {sum(req.values()):.1f} -> {sum(req.values())/len(jr):.3f} s per question; median request {np.median(list(req.values())):.2f} s")
print(f"  LLM: {len(ls)} calls, median {np.median(ls):.2f} s per call, mean {ls.mean():.2f} s; one call per question -> {ls.mean():.2f} s per question, three repeats -> {3*ls.mean():.2f} s")
print("  expert (paper): 1,440 minutes for 3 experts x 1,135 questions ->", round(1440 * 60 / 3 / 1135, 1), "s per answer")
print("\nE. seven real dev questions for the worked example")
pick = sorted(zip(dpj, dy, [i.question[:70] for i in di]), key=lambda t: -t[0])
for k in (0, 60, 300, 345, 400, 440, 465): print("  ", round(float(pick[k][0]), 2), "correct:", "yes" if pick[k][1] else "no", "|", pick[k][2])
