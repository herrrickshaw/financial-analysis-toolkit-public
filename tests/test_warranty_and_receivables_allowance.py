"""finmodel.warranty_and_receivables_allowance: the warranty reserve roll-forward is checked against a hand
calculation, and the receivables aging-method allowance is checked against hand calculations plus the real,
well-known property that a small, high-risk bucket can contribute disproportionately more allowance than a
much larger, low-risk one."""
import pytest

from finmodel import warranty_and_receivables_allowance as WRA


def test_warranty_reserve_rollforward_matches_hand_calc():
    out = WRA.warranty_reserve_rollforward(beginning_reserve=100_000.0, units_sold=10_000.0, failure_rate=0.02,
                                           average_repair_cost=50.0, actual_warranty_costs_incurred=80_000.0)
    assert out["additions"] == pytest.approx(10_000.0 * 0.02 * 50.0)
    assert out["additions"] == pytest.approx(10_000.0)
    assert out["ending_reserve"] == pytest.approx(100_000.0 + 10_000.0 - 80_000.0)
    assert out["ending_reserve"] == pytest.approx(30_000.0)


def test_receivables_allowance_aging_method_matches_hand_calc():
    buckets = [
        {"bucket": "current", "balance": 500_000.0, "expected_loss_rate": 0.01},
        {"bucket": "31-60", "balance": 100_000.0, "expected_loss_rate": 0.05},
        {"bucket": "90+", "balance": 50_000.0, "expected_loss_rate": 0.50},
    ]
    out = WRA.receivables_allowance_aging_method(buckets)
    assert out["total_receivables"] == pytest.approx(650_000.0)
    assert out["total_allowance"] == pytest.approx(500_000.0 * 0.01 + 100_000.0 * 0.05 + 50_000.0 * 0.50)
    assert out["total_allowance"] == pytest.approx(35_000.0)
    assert out["net_realizable_receivables"] == pytest.approx(650_000.0 - 35_000.0)


def test_a_small_high_risk_bucket_can_out_contribute_a_much_larger_low_risk_one():
    buckets = [
        {"bucket": "current", "balance": 500_000.0, "expected_loss_rate": 0.01},
        {"bucket": "90+", "balance": 50_000.0, "expected_loss_rate": 0.50},
    ]
    out = WRA.receivables_allowance_aging_method(buckets)
    current_allowance = next(b["allowance"] for b in out["buckets"] if b["bucket"] == "current")
    overdue_allowance = next(b["allowance"] for b in out["buckets"] if b["bucket"] == "90+")
    assert overdue_allowance > current_allowance  # 10x smaller balance, but 50x the loss rate


def test_from_dict_bundles_everything():
    out = WRA.from_dict({"warranty_reserve_rollforward": {"beginning_reserve": 10.0, "units_sold": 100.0,
                                                           "failure_rate": 0.1, "average_repair_cost": 1.0,
                                                           "actual_warranty_costs_incurred": 5.0}})
    assert out["warranty_reserve_rollforward"]["ending_reserve"] == pytest.approx(15.0)
