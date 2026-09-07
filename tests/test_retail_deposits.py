"""finmodel.retail_deposits: FD maturity is checked against the plain compound-interest formula computed
independently in the test; RD maturity is checked against an independent re-simulation of the same
per-installment compounding, plus the defining edge property that the LAST installment (deposited right at
maturity) earns exactly zero interest; TDS is checked for the real, easy-to-miss rule that once interest
crosses the threshold, the FULL amount is withheld, not just the excess."""
import pytest

from finmodel import retail_deposits as RD


def test_fixed_deposit_maturity_matches_compound_interest_formula():
    out = RD.fixed_deposit_maturity(principal=100_000.0, annual_rate=0.07, tenure_years=3, compounding_frequency=4)
    expected = 100_000.0 * (1 + 0.07 / 4) ** (4 * 3)
    assert out["maturity_value"] == pytest.approx(expected)
    assert out["interest_earned"] == pytest.approx(expected - 100_000.0)


def test_recurring_deposit_maturity_matches_independent_resimulation():
    installment, rate, months = 5000.0, 0.065, 24
    out = RD.recurring_deposit_maturity(installment, rate, months, compounding_frequency=4)
    expected_total = sum(installment * (1 + rate / 4) ** (4 * (months - k) / 12.0) for k in range(1, months + 1))
    assert out["maturity_value"] == pytest.approx(expected_total)
    assert out["total_deposited"] == pytest.approx(installment * months)
    assert out["interest_earned"] == pytest.approx(expected_total - installment * months)


def test_recurring_deposit_last_installment_earns_zero_interest():
    out = RD.recurring_deposit_maturity(5000.0, 0.065, 24)
    last = out["installments"][-1]
    assert last["years_to_maturity"] == pytest.approx(0.0)
    assert last["future_value"] == pytest.approx(5000.0)  # deposited right at maturity -> no time to compound
    first = out["installments"][0]
    assert first["future_value"] > last["future_value"]  # the earliest installment compounds the longest


def test_recurring_deposit_premature_value_uses_the_applicable_rate_only_up_to_closure():
    out = RD.recurring_deposit_premature_value(monthly_installment=5000.0, installments_made=12, applicable_rate=0.05)
    assert out["total_deposited"] == pytest.approx(5000.0 * 12)
    assert out["premature_value"] > out["total_deposited"]  # still earns some interest, just at the lower rate


def test_tds_full_amount_withheld_once_the_threshold_is_crossed():
    below = RD.tds_on_interest(interest_earned=35_000.0)
    assert below["tds_applicable"] is False and below["tds_amount"] == pytest.approx(0.0)

    above = RD.tds_on_interest(interest_earned=45_000.0)
    assert above["tds_applicable"] is True
    assert above["tds_amount"] == pytest.approx(45_000.0 * 0.10)  # the FULL interest, not (45000-40000)
    assert above["net_interest"] == pytest.approx(45_000.0 - 4_500.0)


def test_from_dict_bundles_everything():
    out = RD.from_dict({"fixed_deposit_maturity": {"principal": 1000.0, "annual_rate": 0.05, "tenure_years": 1}})
    assert out["fixed_deposit_maturity"]["interest_earned"] > 0
