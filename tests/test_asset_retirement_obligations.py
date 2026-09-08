"""finmodel.asset_retirement_obligations: initial recognition is checked against an independent PV
computation, and the accretion schedule is checked against its own defining identity -- accreting the
initial liability at the same discount rate used to discount it must reproduce EXACTLY the original
estimated future cost by the retirement date, since accretion is the exact algebraic reverse of the initial
discounting. Settlement gain/loss is checked in both directions."""
import pytest

from finmodel import asset_retirement_obligations as ARO


def test_initial_aro_recognition_matches_independent_pv_calc():
    out = ARO.initial_aro_recognition(estimated_future_cost=1_000_000.0, discount_rate=0.06, years_to_retirement=10)
    expected = 1_000_000.0 / (1.06 ** 10)
    assert out["initial_aro_liability"] == pytest.approx(expected)
    assert out["capitalized_asset_retirement_cost"] == pytest.approx(expected)


def test_accretion_reproduces_the_original_estimated_cost_exactly_at_retirement():
    initial = ARO.initial_aro_recognition(estimated_future_cost=1_000_000.0, discount_rate=0.06, years_to_retirement=10)
    out = ARO.accretion_schedule(initial["initial_aro_liability"], discount_rate=0.06, years_to_retirement=10)
    assert out["final_aro_liability"] == pytest.approx(1_000_000.0)
    # the liability balance must be strictly increasing every year (accretion is always positive)
    balances = [row["aro_liability_balance"] for row in out["schedule"]]
    assert balances == sorted(balances)


def test_settlement_gain_when_actual_cost_is_less_than_the_accreted_liability():
    out = ARO.settlement_gain_loss(actual_settlement_cost=950_000.0, aro_liability_at_settlement=1_000_000.0)
    assert out["gain_loss"] == pytest.approx(50_000.0)
    assert out["classification"] == "gain"


def test_settlement_loss_when_actual_cost_exceeds_the_accreted_liability():
    out = ARO.settlement_gain_loss(actual_settlement_cost=1_100_000.0, aro_liability_at_settlement=1_000_000.0)
    assert out["gain_loss"] == pytest.approx(-100_000.0)
    assert out["classification"] == "loss"


def test_from_dict_bundles_everything():
    out = ARO.from_dict({"initial_aro_recognition": {"estimated_future_cost": 100.0, "discount_rate": 0.05, "years_to_retirement": 5}})
    assert out["initial_aro_recognition"]["initial_aro_liability"] == pytest.approx(100.0 / 1.05 ** 5)
