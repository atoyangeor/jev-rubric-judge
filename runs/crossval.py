"""Cross-validation over all 50 instructions (designed AFTER the single test run, so it is a second
analysis, not the pre-registered result). Every question is judged with boundaries that were chosen on
other instructions. Two ways to choose boundaries:
  joint    - one pair; at least 96% of all taken answers right on the training instructions;
  per side - the 'yes' boundary and the 'no' boundary are chosen separately, each side must be at least
             96% right on the training instructions (a side with fewer than 20 taken answers is not taken).
Also: the whole process (taken answers + ONE expert on the rest) against one expert alone."""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import FEWSHOT, jev_predictions, llm_predictions, part_items

shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
items = [i for part in ("dev", "test") for i in part_items(part) if i.key not in shown]
jev = {**jev_predictions("dev", "noul-fewshot"), **jev_predictions("test", "noul-fewshot")}
llm = {**llm_predictions("dev", "instruction")[0], **llm_predictions("test", "instruction")[0]}
Y = np.array([i.correct for i in items]); G = np.array([i.instruction_id for i in items]); L = np.array([i.labels for i in items])
ids = np.unique(G); TARGET = 0.96

def per_side(p, y, target=TARGET, min_n=20):
    grid_yes = np.round(np.arange(0.51, 1.001, 0.01), 2); grid_no = np.round(np.arange(0.49, -0.001, -0.01), 2)
    t_yes = next((float(t) for t in grid_yes if (p >= t).sum() >= min_n and (y[p >= t] == 1).mean() >= target), 1.01)
    t_no = next((float(t) for t in grid_no if (p <= t).sum() >= min_n and (y[p <= t] == 0).mean() >= target), -0.01)
    return t_yes, t_no

def joint(p, y):
    r = metrics.pick_thresholds(p, y, TARGET); return r.t_yes, r.t_no

expert_alone = float(np.mean([(L[:, e] == Y).mean() for e in range(3)]))
print(f"{len(Y)} questions, {len(ids)} instructions. One expert alone is right on {100 * expert_alone:.1f}% of them (mean of three).")
for name, preds in (("Jev noul-fewshot", jev), ("LLM judge with the instruction", llm)):
    P = np.array([preds[i.key] for i in items])
    for rule_name, rule in (("joint 96%", joint), ("per side 96%", per_side)):
        rng = np.random.default_rng(0); out = []
        for rep in range(20):
            take_yes = np.zeros(len(Y), bool); take_no = np.zeros(len(Y), bool)
            for fold in np.array_split(rng.permutation(ids), 10):
                te = np.isin(G, fold); t_yes, t_no = rule(P[~te], Y[~te])
                take_yes |= te & (P >= t_yes); take_no |= te & (P <= t_no)
            taken = take_yes | take_no; ans = np.where(take_yes, 1, 0)
            whole = np.mean([(np.where(taken, ans, L[:, e]) == Y).mean() for e in range(3)])
            exp_taken = np.mean([(L[taken, e] == Y[taken]).mean() for e in range(3)])
            out.append((100 * (~taken).mean(), 100 * (ans[taken] == Y[taken]).mean(), 100 * whole, 100 * exp_taken,
                        100 * (Y[take_yes] == 1).mean(), 100 * (Y[take_no] == 0).mean() if take_no.any() else float("nan"), int(take_no.sum())))
        o = np.array(out); m = np.nanmean(o, axis=0)
        print(f"{name} | {rule_name}: human {m[0]:.1f} per 100 ({o[:,0].min():.1f}-{o[:,0].max():.1f}); taken right {m[1]:.1f}% ({o[:,1].min():.1f}-{o[:,1].max():.1f}), "
              f"94.1% met in {int((o[:,1] >= 94.1).sum())} of 20; one expert on the same taken questions {m[3]:.1f}%; whole process {m[2]:.1f}% ({o[:,2].min():.1f}-{o[:,2].max():.1f}) "
              f"vs one expert alone {100 * expert_alone:.1f}%; taken 'yes' right {m[4]:.1f}%, taken 'no' right {m[5]:.1f}% (about {m[6]:.0f} 'no' answers)")
