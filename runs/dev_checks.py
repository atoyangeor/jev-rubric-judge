"""Extra dev set checks: same-question comparison, the Number rule, and how boundaries picked on half
of the dev instructions hold on the other half."""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import jev_predictions, llm_predictions, part_items, FEWSHOT

items = part_items("dev")
shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
common = [i for i in items if i.key not in shown]
systems = {f"Jev {v}": jev_predictions("dev", v) for v in ("noul-plain", "noul-criteria", "noul-instruction", "noul-fewshot")}
systems["LLM judge gpt-6-luna"] = llm_predictions("dev")[0]
y = np.array([i.correct for i in common]); groups = np.array([i.instruction_id for i in common])
number = np.array(["Number" in i.categories for i in common])
print(f"same {len(common)} questions for every system; Number questions: {int(number.sum())}")
rng = np.random.default_rng(0); ids = np.unique(groups)
for name, preds in systems.items():
    p = np.array([preds[i.key] for i in common])
    r = metrics.pick_thresholds(p, y)
    # Number rule: Number questions always go to a human, boundaries picked on the rest
    r2 = metrics.pick_thresholds(p[~number], y[~number]); human2 = r2.n_human + int(number.sum())
    acc_num = metrics.accuracy(p[number], y[number]); acc_rest = metrics.accuracy(p[~number], y[~number])
    held, human = [], []
    for _ in range(200):
        half = set(rng.choice(ids, size=len(ids) // 2, replace=False)); a = np.array([g in half for g in groups])
        ra = metrics.pick_thresholds(p[a], y[a]); rb = metrics.route(p[~a], y[~a], ra.t_yes, ra.t_no)
        if rb.n_taken: held.append(rb.taken_accuracy); human.append(rb.human_per_100)
    held = np.array(held)
    print(f"{name}: human {r.n_human} of {len(common)} = {r.human_per_100:.1f} per 100, taken right {r.n_taken_correct}/{r.n_taken} = {100*r.taken_accuracy:.1f}%"
          f" | with Number rule: human {human2} = {100*human2/len(common):.1f} per 100"
          f" | alone on Number {100*acc_num:.1f}%, on the rest {100*acc_rest:.1f}%"
          f" | boundaries from 10 instructions checked on the other 10, 200 random halves: taken answers right {100*held.mean():.1f}% on average,"
          f" condition 94.1% met in {int((held >= 0.941).sum())} of {len(held)} halves, human {np.mean(human):.1f} per 100")
