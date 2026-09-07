"""finmodel.credit_card_abs: excess spread is checked against a hand calc; the early-amortization trigger is
checked against a hand-traced 3-month rolling average crossing zero, and against a series that never
triggers; the master-trust cash flow walk is checked for the real, defining revolving-vs-amortization
mechanic (a flat certificate balance and interest-only payments throughout the revolving period, then a full,
hand-computed paydown afterward) under both real amortization methods."""
import pytest

from finmodel import credit_card_abs as CCA


def test_excess_spread_matches_hand_calc():
    value = CCA.excess_spread(portfolio_yield=0.18, certificate_rate=0.05, servicing_fee_rate=0.02, charge_off_rate=0.06)
    assert value == pytest.approx(0.18 - 0.05 - 0.02 - 0.06)


def test_early_amortization_trigger_fires_when_the_3_month_average_turns_negative():
    spreads = [0.03, 0.025, 0.02, 0.01, -0.01, -0.02, -0.03]
    out = CCA.early_amortization_trigger(spreads, window=3)
    expected_averages = [sum(spreads[max(0, i - 2):i + 1]) / len(spreads[max(0, i - 2):i + 1]) for i in range(len(spreads))]
    assert out["rolling_averages"] == pytest.approx(expected_averages)
    assert out["triggered"] is True
    assert out["triggered_month"] == 6  # the first month whose trailing 3-month average is <= 0


def test_early_amortization_trigger_never_fires_on_healthy_spread():
    out = CCA.early_amortization_trigger([0.05, 0.04, 0.06, 0.05, 0.045], window=3)
    assert out["triggered"] is False
    assert out["triggered_month"] is None


def test_master_trust_pass_through_matches_hand_calc():
    out = CCA.master_trust_cash_flows(receivables_balance=100_000_000.0, monthly_payment_rate=0.15,
                                      revolving_period_months=24, certificate_balance=80_000_000.0,
                                      certificate_rate=0.05, amortization_method="pass_through")
    # revolving period: flat certificate balance, interest-only
    for row in out["schedule"][:24]:
        assert row["principal_paid"] == pytest.approx(0.0)
        assert row["closing_certificate_balance"] == pytest.approx(80_000_000.0)
        assert row["interest_paid"] == pytest.approx(80_000_000.0 * 0.05 / 12)
    # amortization: 15M/month collections pay down the 80M balance in 5 full months + one 5M remainder month
    month_25 = out["schedule"][24]
    assert month_25["principal_paid"] == pytest.approx(15_000_000.0)
    assert out["months_to_full_paydown"] == 30  # 24 revolving + 6 amortization months (5 full + 1 partial)
    assert out["schedule"][-1]["principal_paid"] == pytest.approx(5_000_000.0)
    assert out["fully_paid_down"] is True


def test_master_trust_controlled_amortization_pays_a_level_amount():
    out = CCA.master_trust_cash_flows(receivables_balance=100_000_000.0, monthly_payment_rate=0.15,
                                      revolving_period_months=24, certificate_balance=80_000_000.0,
                                      certificate_rate=0.05, amortization_method="controlled_amortization",
                                      controlled_amortization_months=10)
    amortization_rows = out["schedule"][24:]
    assert len(amortization_rows) == 10
    for row in amortization_rows:
        assert row["principal_paid"] == pytest.approx(8_000_000.0)
    assert out["months_to_full_paydown"] == 34
    assert out["schedule"][-1]["closing_certificate_balance"] == pytest.approx(0.0, abs=1.0)


def test_master_trust_rejects_bad_amortization_method_and_missing_controlled_months():
    with pytest.raises(ValueError):
        CCA.master_trust_cash_flows(100.0, 0.1, 1, 100.0, 0.05, amortization_method="bogus")
    with pytest.raises(ValueError):
        CCA.master_trust_cash_flows(100.0, 0.1, 1, 100.0, 0.05, amortization_method="controlled_amortization")


def test_from_dict_bundles_everything():
    out = CCA.from_dict({"excess_spread": {"portfolio_yield": 0.18, "certificate_rate": 0.05,
                                           "servicing_fee_rate": 0.02, "charge_off_rate": 0.06}})
    assert out["excess_spread"]["value"] == pytest.approx(0.05)
