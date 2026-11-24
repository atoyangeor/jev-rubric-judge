"""All numbers of the experiment are computed here, from two arrays: p_yes and the correct answer."""
from __future__ import annotations

from dataclasses import dataclass

import numpy as np

ONE_EXPERT_ACCURACY = 0.941  # share of questions where one expert gave the answer of two of three experts
GRID_STEP = 0.01


@dataclass(frozen=True)
class Routing:
    t_yes: float
    t_no: float
    n: int
    n_human: int  # questions left to a human
    n_taken: int  # answers taken from the model
    n_taken_correct: int

    @property
    def human_per_100(self) -> float:
        return 100 * self.n_human / self.n

    @property
    def taken_accuracy(self) -> float:
        return self.n_taken_correct / self.n_taken if self.n_taken else float("nan")


def accuracy(p_yes: np.ndarray, correct: np.ndarray, threshold: float = 0.5) -> float:
    """Model alone, no human: 'yes' when p_yes is above the threshold."""
    return float(((p_yes > threshold).astype(int) == correct).mean())


def route(p_yes: np.ndarray, correct: np.ndarray, t_yes: float, t_no: float) -> Routing:
    take_yes = p_yes >= t_yes
    take_no = p_yes <= t_no
    taken = take_yes | take_no
    taken_correct = (take_yes & (correct == 1)) | (take_no & (correct == 0))
    return Routing(t_yes, t_no, len(p_yes), int((~taken).sum()), int(taken.sum()), int(taken_correct.sum()))


def pick_thresholds(p_yes: np.ndarray, correct: np.ndarray, min_accuracy: float = ONE_EXPERT_ACCURACY) -> Routing:
    """Among pairs (t_yes, t_no) on a 0.01 grid where the taken answers are right at least min_accuracy
    of the time, return the pair that leaves the fewest questions to a human.
    Ties: higher accuracy of taken answers, then the wider pair."""
    best: Routing | None = None
    grid_yes = np.round(np.arange(0.5 + GRID_STEP, 1.0 + GRID_STEP / 2, GRID_STEP), 2)
    grid_no = np.round(np.arange(0.0, 0.5, GRID_STEP), 2)
    for t_yes in list(grid_yes) + [1.01]:  # 1.01 = never take 'yes'
        for t_no in [-0.01] + list(grid_no):  # -0.01 = never take 'no'
            r = route(p_yes, correct, float(t_yes), float(t_no))
            if r.n_taken and r.taken_accuracy < min_accuracy:
                continue
            key = (r.n_human, -(r.taken_accuracy if r.n_taken else 0.0), -(r.t_yes - r.t_no))
            if best is None or key < (best.n_human, -(best.taken_accuracy if best.n_taken else 0.0), -(best.t_yes - best.t_no)):
                best = r
    assert best is not None  # the pair (1.01, -0.01) takes nothing and always qualifies
    return best


def calibration_error(p_yes: np.ndarray, correct: np.ndarray, bins: int = 10) -> tuple[float, list[dict]]:
    """Split questions into 10 groups by p_yes. In each: mean p_yes vs the real share of 'yes'.
    Return the mean gap weighted by group size (textbook name: expected calibration error), and the groups."""
    edges = np.linspace(0, 1, bins + 1)
    idx = np.clip(np.digitize(p_yes, edges[1:-1]), 0, bins - 1)
    rows, total = [], 0.0
    for b in range(bins):
        mask = idx == b
        if not mask.any():
            continue
        mean_p, share_yes = float(p_yes[mask].mean()), float(correct[mask].mean())
        total += mask.sum() / len(p_yes) * abs(mean_p - share_yes)
        rows.append({"from": float(edges[b]), "to": float(edges[b + 1]), "n": int(mask.sum()), "mean_p_yes": mean_p, "share_yes": share_yes})
    return float(total), rows


def bootstrap_interval(groups: np.ndarray, fn, n_resamples: int = 2000, seed: int = 0) -> tuple[float, float]:
    """95% interval: resample whole instructions with replacement and recompute fn(index array)."""
    rng = np.random.default_rng(seed)
    unique = np.unique(groups)
    members = {g: np.flatnonzero(groups == g) for g in unique}
    values = []
    for _ in range(n_resamples):
        chosen = rng.choice(unique, size=len(unique), replace=True)
        values.append(fn(np.concatenate([members[g] for g in chosen])))
    values = np.array(values, dtype=float)
    values = values[~np.isnan(values)]
    return float(np.percentile(values, 2.5)), float(np.percentile(values, 97.5))
