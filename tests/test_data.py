from jev_rubric_judge.data import parse_labels


def test_three_label_formats():
    assert parse_labels("1. Yes\n2. No\n3. Yes") == [1, 0, 1]
    assert parse_labels("yes\nno\nyes") == [1, 0, 1]
    assert parse_labels("1.0.1") == [1, 0, 1]


def test_empty_and_unreadable():
    assert parse_labels("  ") is None
    assert parse_labels("1. Yes\n2. maybe") == [1, None]
