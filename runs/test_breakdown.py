"""Diagnostics on the test set AFTER the single run. Nothing here changes the frozen settings."""
import numpy as np
from jev_rubric_judge.cli import jev_predictions, llm_predictions, part_items

items = part_items("test"); y = np.array([i.correct for i in items])
unanimous = np.array([len(set(i.labels)) == 1 for i in items]); number = np.array(["Number" in i.categories for i in items])
for name, preds, (ty, tn) in (("Jev noul-fewshot", jev_predictions("test", "noul-fewshot"), (0.83, 0.42)),
                              ("LLM instruction", llm_predictions("test", "instruction")[0], (0.69, -0.01))):
    p = np.array([preds[i.key] for i in items]); yes = p >= ty; no = p <= tn; taken = yes | no
    wrong = (yes & (y == 0)) | (no & (y == 1))
    print(f"{name}: took 'yes' {int(yes.sum())}, right {int((yes & (y == 1)).sum())} ({100 * (y[yes] == 1).mean():.1f}%)"
          + (f"; took 'no' {int(no.sum())}, right {int((no & (y == 0)).sum())} ({100 * (y[no] == 0).mean():.1f}%)" if no.any() else "; took no 'no' answers")
          + f"; wrong taken answers {int(wrong.sum())}: {int((wrong & ~unanimous).sum())} on questions where experts disagreed, {int((wrong & number).sum())} on Number questions"
          + f"; of {int((~unanimous).sum())} questions where experts disagreed, {int((~unanimous & ~taken).sum())} went to a human")
print("needed for 94.1% on Jev's 516 taken answers:", int(np.ceil(0.941 * 516)), "right; got 480")
