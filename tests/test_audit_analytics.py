"""finmodel.audit_analytics: Benford's Law is checked against a synthetic dataset built to exactly match (and
one built to badly violate) the expected first-digit distribution, so the MAD statistic and its real Nigrini
conformity thresholds are exercised at both ends; journal-entry testing is checked flag by flag."""
import math

import pytest

from finmodel import audit_analytics as AA


def test_first_digit_extraction():
    assert AA.first_digit(4567.89) == 4
    assert AA.first_digit(0.0034) == 3
    assert AA.first_digit(-812) == 8
    assert AA.first_digit(0) is None


def test_benford_expected_distribution_sums_to_one_and_is_decreasing():
    assert sum(AA.BENFORD_FIRST_DIGIT.values()) == pytest.approx(1.0)
    vals = [AA.BENFORD_FIRST_DIGIT[d] for d in range(1, 10)]
    assert vals == sorted(vals, reverse=True)  # digit 1 most common, digit 9 least -- Benford's defining shape


def test_benford_close_conformity_on_a_dataset_built_to_match_the_expected_distribution():
    n = 9000
    values = []
    for d in range(1, 10):
        values += [float(d)] * round(AA.BENFORD_FIRST_DIGIT[d] * n)
    out = AA.benford_first_digit_test(values)
    assert out["mad"] < 0.006
    assert out["conformity"] == "close conformity"


def test_benford_nonconformity_on_a_uniform_digit_dataset():
    # a real, uniform 1/9-per-digit population is exactly the kind of dataset Benford's Law does NOT describe --
    # confirms the test correctly flags a genuinely non-Benford-shaped population, not just a noisy small sample.
    values = []
    for d in range(1, 10):
        values += [float(d)] * 50
    out = AA.benford_first_digit_test(values)
    assert out["mad"] > 0.015
    assert out["conformity"] == "nonconformity"


def test_benford_raises_on_all_zero_input():
    with pytest.raises(ValueError):
        AA.benford_first_digit_test([0, 0, 0])


def test_journal_entry_round_dollar_flag():
    out = AA.journal_entry_test([{"id": "a", "amount": 5000}], round_dollar_threshold=1000)
    assert out["n_flagged"] == 1
    assert out["flagged"][0]["flags"] == ["round_dollar_amount"]


def test_journal_entry_weekend_and_after_hours_flags():
    out = AA.journal_entry_test([{"id": "a", "amount": 123.45, "is_weekend": True, "hour": 23}])
    assert set(out["flagged"][0]["flags"]) == {"weekend_posting", "after_hours_posting"}


def test_journal_entry_just_under_approval_threshold():
    out = AA.journal_entry_test([{"id": "a", "amount": 9800}], approval_threshold=10000)
    assert out["flagged"][0]["flags"] == ["just_under_approval_threshold"]
    # comfortably below the threshold (not "just under") should NOT flag
    out2 = AA.journal_entry_test([{"id": "b", "amount": 5000.5}], approval_threshold=10000)
    assert out2["n_flagged"] == 0


def test_journal_entry_clean_entry_is_not_flagged():
    out = AA.journal_entry_test([{"id": "a", "amount": 1234.56, "is_weekend": False, "hour": 11}], approval_threshold=10000)
    assert out["n_flagged"] == 0


def test_from_dict_bundles_benford_and_journal_entries():
    d = {"benford": {"values": [1.0] * 30 + [9.0] * 5}, "journal_entries": {"entries": [{"id": "a", "amount": 2000}], "round_dollar_threshold": 1000}}
    out = AA.from_dict(d)
    assert out["benford"]["n"] == 35
    assert out["journal_entries"]["n_flagged"] == 1
