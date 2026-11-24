"""Cross-validation as in crossval.py, with stricter and stricter boundaries: what accuracy can
'model first, one expert on the rest' reach when the expert's pay matters less?"""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import FEWSHOT, jev_predictions, llm_predictions, part_items

shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
items = [i for part in ("dev", "test") for i in part_items(part) if i.key not in shown]
jev = {**jev_predictions("dev", "noul-fewshot"), **jev_predictions("test", "noul-fewshot")}
llm = {**llm_predictions("dev", "instruction")[0], **llm_predictions("test", "instruction")[0]}
Y = np.array([i.correct for i in items]); G = np.array([i.instruction_id for i in items]); L = np.array([i.labels for i in items])
ids = np.unique(G); N = len(Y); PRICE = 1416 / 3 / 1135; SEC = 1440 * 60 / 3 / 1135
alone = float(np.mean([(L[:, e] == Y).mean() for e in range(3)]))
print(f"{N} questions. One expert alone: {100 * alone:.1f}% right, ${N * PRICE:.0f}, {N * SEC / 3600:.1f} h. Three experts on everything: right by definition, ${3 * N * PRICE:.0f}, {3 * N * SEC / 3600:.1f} person-hours")
for name, preds in (("Jev", jev), ("LLM judge", llm)):
    P = np.array([preds[i.key] for i in items])
    for target in (0.96, 0.97, 0.98, 0.99, 0.995):
        rng = np.random.default_rng(0); out = []
        for rep in range(20):
            ty = np.zeros(N, bool); tn = np.zeros(N, bool)
            for fold in np.array_split(rng.permutation(ids), 10):
                te = np.isin(G, fold); r = metrics.pick_thresholds(P[~te], Y[~te], target)
                ty |= te & (P >= r.t_yes); tn |= te & (P <= r.t_no)
            taken = ty | tn; ans = np.where(ty, 1, 0)
            if not taken.any(): continue
            whole = np.mean([(np.where(taken, ans, L[:, e]) == Y).mean() for e in range(3)])
            whole3 = ((ans[taken] == Y[taken]).sum() + (~taken).sum()) / N  # three experts on the rest are right by definition
            out.append(((~taken).sum(), 100 * (ans[taken] == Y[taken]).mean(), 100 * np.mean([(L[taken, e] == Y[taken]).mean() for e in range(3)]), 100 * whole, 100 * whole3))
        if not out:
            print(f"{name}, {100 * target:.1f}%: no answers taken"); continue
        m = np.mean(out, axis=0); q = m[0]
        print(f"{name}, taken answers at least {100 * target:.1f}% right on the tuning questions: expert answers {q:.0f} of {N} ({100 * q / N:.0f} per 100), "
              f"${q * PRICE:.0f}, {q * SEC / 3600:.1f} h | taken answers right {m[1]:.1f}% | one expert on the same taken questions {m[2]:.1f}% | whole process with ONE expert on the rest {m[3]:.1f}% (one expert alone {100 * alone:.1f}%)"
              f" | with THREE experts on the rest: {m[4]:.1f}% right, ${3 * q * PRICE:.0f}, {3 * q * SEC / 3600:.1f} person-hours")
