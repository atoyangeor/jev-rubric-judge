import math

import numpy as np

from jev_rubric_judge.clients import p_yes_from_logprobs
from jev_rubric_judge.metrics import accuracy, calibration_error, pick_thresholds, route

# The ten invented questions from the chat example of 2026-11-23.
P = np.array([0.99, 0.97, 0.95, 0.03, 0.93, 0.08, 0.91, 0.62, 0.85, 0.40])
Y = np.array([1, 1, 1, 0, 1, 0, 1, 1, 0, 0])


def test_route_counts():
    r = route(P, Y, 0.90, 0.10)
    assert (r.n_human, r.n_taken, r.n_taken_correct) == (3, 7, 7)
    assert r.human_per_100 == 30
    wide = route(P, Y, 0.80, 0.20)
    assert (wide.n_human, wide.n_taken, wide.n_taken_correct) == (2, 8, 7)


def test_pick_thresholds_respects_condition():
    r = pick_thresholds(P, Y, min_accuracy=0.941)
    assert r.taken_accuracy >= 0.941
    assert r.n_human == 2  # question 8 (0.62, correct yes) can be taken; question 9 (0.85, correct no) cannot


def test_model_alone():
    assert accuracy(P, Y) == 0.9


def test_calibration_perfect_and_bad():
    assert calibration_error(np.array([0.0, 1.0]), np.array([0, 1]))[0] == 0
    assert math.isclose(calibration_error(np.array([0.95, 0.95]), np.array([0, 0]))[0], 0.95)


def test_p_yes_sums_spellings():
    lp = {"content": [{"top_logprobs": [{"token": "YES", "logprob": math.log(0.5)}, {"token": " yes", "logprob": math.log(0.25)},
                                         {"token": "NO", "logprob": math.log(0.25)}]}]}
    assert math.isclose(p_yes_from_logprobs(lp), 0.75)
    assert p_yes_from_logprobs(None) is None
