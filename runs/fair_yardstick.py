"""Fair yardstick. In the main analysis an expert is graded against the vote of three experts, one of
which is his own; a model has no vote. Here everyone is graded the same way: against two experts, on the
questions where those two agree. The third expert is then 'the person' being compared with the model.
Each of the three experts takes that role in turn; numbers are the mean over the three.
Computed after the test run. Boundaries are NOT retuned: check 1 uses the frozen pair, check 2 the same
cross-validation as runs/crossval.py (tuning labels on the training instructions = vote of three)."""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import FEWSHOT, jev_predictions, llm_predictions, part_items

shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
items = [i for part in ("dev", "test") for i in part_items(part) if i.key not in shown]
is_test = np.array([i.instruction_id in {j.instruction_id for j in part_items("test")} for i in items])
jev = {**jev_predictions("dev", "noul-fewshot"), **jev_predictions("test", "noul-fewshot")}
llm = {**llm_predictions("dev", "instruction")[0], **llm_predictions("test", "instruction")[0]}
Y = np.array([i.correct for i in items]); G = np.array([i.instruction_id for i in items]); L = np.array([i.labels for i in items]); N = len(Y)
PAIRS = [(e, [k for k in range(3) if k != e]) for e in range(3)]
REF = [(L[:, o[0]] == L[:, o[1]], L[:, o[0]]) for _, o in PAIRS]  # (the two agree, their answer)
ids = np.unique(G); mem = {g: np.flatnonzero(G == g) for g in ids}

def fair(answer, subset):
    """Share of `subset` questions (where the two reference experts agree) on which `answer` equals them; mean over the three roles."""
    return float(np.mean([(answer(e)[m & subset] == ref[m & subset]).mean() for (e, _), (m, ref) in zip(PAIRS, REF)]))

def interval(fn, n=2000, seed=0):
    rng = np.random.default_rng(seed); vals = []
    for _ in range(n):
        idx = np.concatenate([mem[g] for g in rng.choice(ids, size=len(ids), replace=True)]); w = np.bincount(idx, minlength=N).astype(float)
        vals.append(fn(w))
    return np.percentile(vals, [2.5, 97.5])

def wfair(answer, subset, w):
    return float(np.mean([np.average((answer(e) == ref)[m & subset], weights=w[m & subset]) for (e, _), (m, ref) in zip(PAIRS, REF) if w[m & subset].sum() > 0]))

ALL = np.ones(N, bool); expert = lambda e: L[:, e]
print(f"{N} questions. The two reference experts agree on {[int(m.sum()) for m, _ in REF]} of them (one number per role).")
print(f"\nA. Alone, all questions: one expert {100 * fair(expert, ALL):.1f}%")
def cv_cutoff(P, reps=20):
    rng = np.random.default_rng(0); out = np.zeros((reps, N), int)
    for r in range(reps):
        for fold in np.array_split(rng.permutation(ids), 10):
            te = np.isin(G, fold); cs = np.unique(np.round(np.concatenate([[0.5], P[~te]]), 3))
            c = max(cs, key=lambda c: ((P[~te] > c).astype(int) == Y[~te]).mean()); out[r, te] = (P[te] > c).astype(int)
    return out
for name, preds in (("Jev", jev), ("LLM judge", llm)):
    P = np.array([preds[i.key] for i in items]); a05 = (P > .5).astype(int); tuned = cv_cutoff(P)
    d = interval(lambda w: 100 * (wfair(lambda e: a05, ALL, w) - wfair(expert, ALL, w)))
    t_acc = np.mean([fair(lambda e, a=a: a, ALL) for a in tuned])
    dt = interval(lambda w: 100 * (wfair(lambda e: tuned[0], ALL, w) - wfair(expert, ALL, w)))
    print(f"   {name}: 0.5 rule {100 * fair(lambda e: a05, ALL):.1f}% (minus the expert: {100 * (fair(lambda e: a05, ALL) - fair(expert, ALL)):+.1f}, interval {d.round(1)}); "
          f"cut-off tuned on other instructions {100 * t_acc:.1f}% (minus the expert: {100 * (t_acc - fair(expert, ALL)):+.1f}, interval {dt.round(1)})")

def report(label, name, taken, ans, subset):
    T = taken & subset
    model_t, exp_t = fair(lambda e: ans, T), fair(expert, T)
    whole = fair(lambda e: np.where(taken, ans, L[:, e]), subset); alone = fair(expert, subset)
    d = interval(lambda w: 100 * (wfair(lambda e: ans, T, w) - wfair(expert, T, w)))
    dw = interval(lambda w: 100 * (wfair(lambda e: np.where(taken, ans, L[:, e]), subset, w) - wfair(expert, subset, w)))
    print(f"   {label} {name}: left to the person {100 * (~taken & subset).sum() / subset.sum():.1f} per 100 | on the questions taken from the model: model {100 * model_t:.1f}%, the person {100 * exp_t:.1f}% "
          f"(model minus person {100 * (model_t - exp_t):+.1f}, interval {d.round(1)}) | whole process {100 * whole:.1f}%, the person alone {100 * alone:.1f}% (difference {100 * (whole - alone):+.1f}, interval {dw.round(1)})")

print("\nB. Check 1: the frozen boundaries on the 644 test questions")
for name, preds, (ty, tn) in (("Jev", jev, (0.83, 0.42)), ("LLM judge", llm, (0.69, -0.01))):
    P = np.array([preds[i.key] for i in items]); report("check 1", name, (P >= ty) | (P <= tn), (P >= ty).astype(int), is_test)

print("\nC. Check 2: cross-validation over all instructions (first of the 20 cuts for the intervals; the means over 20 cuts follow)")
for name, preds in (("Jev", jev), ("LLM judge", llm)):
    P = np.array([preds[i.key] for i in items]); rng = np.random.default_rng(0); rows = []
    for rep in range(20):
        ty_ = np.zeros(N, bool); tn_ = np.zeros(N, bool)
        for fold in np.array_split(rng.permutation(ids), 10):
            te = np.isin(G, fold); r = metrics.pick_thresholds(P[~te], Y[~te], 0.96); ty_ |= te & (P >= r.t_yes); tn_ |= te & (P <= r.t_no)
        taken = ty_ | tn_; ans = ty_.astype(int)
        if rep == 0: report("check 2", name, taken, ans, ALL)
        rows.append((100 * (~taken).mean(), 100 * fair(lambda e: ans, taken), 100 * fair(expert, taken), 100 * fair(lambda e: np.where(taken, ans, L[:, e]), ALL)))
    m = np.mean(rows, axis=0)
    print(f"   check 2 {name}, mean of 20 cuts: left {m[0]:.1f} per 100 | taken: model {m[1]:.1f}%, the person {m[2]:.1f}% | whole process {m[3]:.1f}%, the person alone {100 * fair(expert, ALL):.1f}%")
