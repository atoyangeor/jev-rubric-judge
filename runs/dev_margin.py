"""What if boundaries are picked on the dev set with a stricter condition than 94.1%?"""
import json
import numpy as np
from jev_rubric_judge import metrics
from jev_rubric_judge.cli import jev_predictions, llm_predictions, part_items, FEWSHOT

items = part_items("dev"); shown = {e["key"] for e in json.loads(FEWSHOT.read_text())}
common = [i for i in items if i.key not in shown]
y = np.array([i.correct for i in common]); groups = np.array([i.instruction_id for i in common]); ids = np.unique(groups)
systems = {f"Jev {v}": jev_predictions("dev", v) for v in ("noul-fewshot", "noul-instruction", "noul-plain", "noul-criteria")}
systems |= {"LLM judge paper": llm_predictions("dev")[0], "LLM judge instruction": llm_predictions("dev", "instruction")[0], "LLM judge fewshot": llm_predictions("dev", "fewshot")[0]}
for name, preds in systems.items():
    p = np.array([preds[i.key] for i in common])
    print(f"{name} | alone {int(round(metrics.accuracy(p, y) * len(y)))} of {len(y)} = {100 * metrics.accuracy(p, y):.1f}% | calibration error {metrics.calibration_error(p, y)[0]:.3f}")
    for target in (0.941, 0.96):
        r = metrics.pick_thresholds(p, y, target)
        rng = np.random.default_rng(0); held, human = [], []
        for _ in range(200):
            half = set(rng.choice(ids, size=len(ids) // 2, replace=False)); a = np.array([g in half for g in groups])
            ra = metrics.pick_thresholds(p[a], y[a], target); rb = metrics.route(p[~a], y[~a], ra.t_yes, ra.t_no)
            if rb.n_taken: held.append(rb.taken_accuracy); human.append(rb.human_per_100)
        held = np.array(held)
        print(f"{name} | condition on dev {100*target:.1f}% | t_yes {r.t_yes:.2f} t_no {r.t_no:.2f} | human {r.n_human} of {len(common)} = {r.human_per_100:.1f} per 100 | taken right {r.n_taken_correct}/{r.n_taken} = {100*r.taken_accuracy:.1f}%"
              f" | on unseen halves: {100*held.mean():.1f}% right on average, 94.1% met in {int((held>=0.941).sum())} of {len(held)}, human {np.mean(human):.1f} per 100")
