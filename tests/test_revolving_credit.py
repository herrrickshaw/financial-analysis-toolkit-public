"""finmodel.revolving_credit: daily-balance interest is checked against the real round-trip property that
annualizing the effective rate on a CONSTANT balance must reproduce the input annual rate exactly; the
credit-card minimum-payment schedule is checked for the real, defining comparative property (a lower minimum
percentage always takes longer and costs more total interest) and for an explicit negative-amortization
case where the minimum payment doesn't even cover accruing interest."""
import pytest

from finmodel import revolving_credit as RC


def test_daily_balance_interest_on_a_constant_balance_reproduces_the_annual_rate():
    out = RC.daily_balance_interest(daily_balances=[100_000.0] * 30, annual_rate=0.12)
    assert out["average_balance"] == pytest.approx(100_000.0)
    assert out["total_interest"] == pytest.approx(30 * 100_000.0 * 0.12 / 365)
    assert out["effective_annualized_rate_on_average_balance"] == pytest.approx(0.12)


def test_daily_balance_interest_with_a_fluctuating_balance_matches_hand_calc():
    balances = [100_000.0] * 15 + [50_000.0] * 15
    out = RC.daily_balance_interest(balances, annual_rate=0.12)
    expected = 15 * 100_000.0 * 0.12 / 365 + 15 * 50_000.0 * 0.12 / 365
    assert out["total_interest"] == pytest.approx(expected)
    assert out["average_balance"] == pytest.approx(75_000.0)


def test_lower_minimum_payment_percentage_takes_longer_and_costs_more_interest():
    kwargs = dict(balance=50_000.0, annual_rate=0.18, min_payment_floor=500.0)
    slow = RC.credit_card_minimum_payment_schedule(**kwargs, min_payment_pct=0.02)
    fast = RC.credit_card_minimum_payment_schedule(**kwargs, min_payment_pct=0.05)
    assert slow["paid_off"] and fast["paid_off"]
    assert slow["months_to_payoff"] > fast["months_to_payoff"]
    assert slow["total_interest_paid"] > fast["total_interest_paid"]


def test_minimum_payment_below_accruing_interest_causes_negative_amortization():
    out = RC.credit_card_minimum_payment_schedule(balance=1_000_000.0, annual_rate=0.42, min_payment_pct=0.01,
                                                  min_payment_floor=100.0, max_months=12)
    first = out["schedule"][0]
    assert first["interest"] == pytest.approx(1_000_000.0 * 0.42 / 12)
    assert first["payment"] == pytest.approx(10_000.0)
    assert first["closing_balance"] > first["opening_balance"]  # the balance GREW despite a payment being made
    assert out["paid_off"] is False
    assert out["months_to_payoff"] is None


def test_from_dict_bundles_everything():
    out = RC.from_dict({"daily_balance_interest": {"daily_balances": [1000.0, 2000.0], "annual_rate": 0.10}})
    assert out["daily_balance_interest"]["average_balance"] == pytest.approx(1500.0)
