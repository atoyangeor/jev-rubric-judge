"""More diagnostics on the test set after the single run. Nothing here changes the frozen settings."""
import csv
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import jev_predictions, llm_predictions, part_items

items = part_items("test"); y = np.array([i.correct for i in items]); groups = np.array([i.instruction_id for i in items])
labels = np.array([i.labels for i in items])
pj = np.array([jev_predictions("test", "noul-fewshot")[i.key] for i in items]); pl = np.array([llm_predictions("test", "instruction")[0][i.key] for i in items])
tj = (pj >= 0.83) | (pj <= 0.42); tl = pl >= 0.69; yes_j = pj >= 0.83
def expert_level(mask):
    per = [(labels[mask][:, e] == y[mask]).mean() for e in range(3)]
    return [round(100 * x, 1) for x in per], round(100 * float(np.mean(per)), 1)
print("one expert vs the answer of two of three, all 644 test questions:", expert_level(np.ones(len(y), bool)))
print("  on the 516 questions taken from Jev:", expert_level(tj), "| on the 128 left to a human:", expert_level(~tj))
print("  on the 482 questions taken from the LLM:", expert_level(tl), "| on the 162 left to a human:", expert_level(~tl))
print("  on the 450 'yes' taken from Jev:", expert_level(yes_j))
# paired bootstrap over instructions
rng = np.random.default_rng(0); ids = np.unique(groups); members = {g: np.flatnonzero(groups == g) for g in ids}
d_h, d_a, yo = [], [], []
for _ in range(2000):
    idx = np.concatenate([members[g] for g in rng.choice(ids, size=len(ids), replace=True)])
    rj = metrics.route(pj[idx], y[idx], 0.83, 0.42); rl = metrics.route(pl[idx], y[idx], 0.69, -0.01); ry = metrics.route(pj[idx], y[idx], 0.83, -0.01)
    d_h.append(rj.human_per_100 - rl.human_per_100); d_a.append(100 * (rj.taken_accuracy - rl.taken_accuracy)); yo.append(100 * ry.taken_accuracy)
print("difference Jev minus LLM, questions per 100 left to a human:", round(19.9 - 25.2, 1), "95% interval", np.percentile(d_h, [2.5, 97.5]).round(1))
print("difference Jev minus LLM, share of taken answers right, points:", round(93.0 - 95.6, 1), "95% interval", np.percentile(d_a, [2.5, 97.5]).round(1))
ry = metrics.route(pj, y, 0.83, -0.01)
print(f"Jev taking only 'yes': human {ry.n_human} of 644 = {ry.human_per_100:.1f} per 100, right {ry.n_taken_correct}/{ry.n_taken} = {100*ry.taken_accuracy:.1f}%, interval", np.percentile(yo, [2.5, 97.5]).round(1))
csv.field_size_limit(10**9)
for r in csv.DictReader(open("data/raw/expert_hard.csv", encoding="utf-8")):
    if r["id"] in ("domain_oriented_task_153", "domain_oriented_task_139"):
        print(r["id"], "alpaca-7b cells:", [repr(r[c][:40]) for c in ("alpaca-7b-annotation-annotator1", "alpaca-7b-annotation-annotator2", "alpaca-7b-annotation")], "| questions:", len([l for l in r["decomposed_questions"].splitlines() if l.strip()]), "| response empty:", not r["alpaca-7b"].strip())
