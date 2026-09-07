"""finmodel.lease_accounting: lease classification is checked against each of the five real ASC 842
finance-lease triggers individually; initial measurement is checked against an independently-summed present
value; the finance-lease schedule is checked against the real, defining front-loaded-expense property (and
an exact first-period interest hand calc); the operating-lease schedule is checked against the real, defining
level-expense property using the clean special case of level payments, where straight-line expense equals
the payment exactly, plus the identity that the ROU-asset amortization "plug" sums to the initial ROU asset."""
import pytest

from finmodel import lease_accounting as LA


def test_classify_lease_no_triggers_is_operating():
    out = LA.classify_lease(lease_term_years=3, asset_economic_life_years=10, pv_lease_payments=50_000.0, asset_fair_value=200_000.0)
    assert out["classification"] == "operating"
    assert out["reasons"] == []


def test_classify_lease_ownership_transfer_triggers_finance():
    out = LA.classify_lease(lease_term_years=3, asset_economic_life_years=10, pv_lease_payments=50_000.0,
                            asset_fair_value=200_000.0, transfers_ownership=True)
    assert out["classification"] == "finance"


def test_classify_lease_bargain_purchase_option_triggers_finance():
    out = LA.classify_lease(lease_term_years=3, asset_economic_life_years=10, pv_lease_payments=50_000.0,
                            asset_fair_value=200_000.0, bargain_purchase_option=True)
    assert out["classification"] == "finance"


def test_classify_lease_economic_life_threshold_triggers_finance():
    out = LA.classify_lease(lease_term_years=8, asset_economic_life_years=10, pv_lease_payments=50_000.0, asset_fair_value=200_000.0)
    assert out["classification"] == "finance"
    assert out["economic_life_pct"] == pytest.approx(0.8)


def test_classify_lease_fair_value_threshold_triggers_finance():
    out = LA.classify_lease(lease_term_years=3, asset_economic_life_years=10, pv_lease_payments=190_000.0, asset_fair_value=200_000.0)
    assert out["classification"] == "finance"
    assert out["fair_value_pct"] == pytest.approx(0.95)


def test_classify_lease_specialized_asset_triggers_finance():
    out = LA.classify_lease(lease_term_years=3, asset_economic_life_years=10, pv_lease_payments=50_000.0,
                            asset_fair_value=200_000.0, specialized_asset_no_alternative_use=True)
    assert out["classification"] == "finance"


def test_initial_measurement_matches_independent_pv_sum():
    payments = [10_000.0] * 5
    rate = 0.06
    out = LA.initial_measurement(payments, rate, initial_direct_costs=500.0, prepaid_lease_payments=1_000.0, lease_incentives_received=2_000.0)
    expected_liability = sum(p / (1 + rate) ** (i + 1) for i, p in enumerate(payments))
    assert out["lease_liability"] == pytest.approx(expected_liability)
    assert out["rou_asset"] == pytest.approx(expected_liability + 500.0 + 1_000.0 - 2_000.0)


def test_finance_lease_first_period_interest_matches_hand_calc_and_expense_is_front_loaded():
    out = LA.finance_lease_schedule([10_000.0] * 5, 0.06)
    assert out["schedule"][0]["interest_expense"] == pytest.approx(out["initial_liability"] * 0.06)
    assert out["schedule"][0]["total_expense"] > out["schedule"][-1]["total_expense"]
    assert out["schedule"][-1]["liability_balance"] == pytest.approx(0.0, abs=1e-2)


def test_operating_lease_with_level_payments_recognizes_a_flat_expense_equal_to_the_payment():
    out = LA.operating_lease_schedule([10_000.0] * 5, 0.06)
    assert out["straight_line_expense"] == pytest.approx(10_000.0)
    for row in out["schedule"]:
        assert row["straight_line_expense"] == pytest.approx(10_000.0)
    assert out["schedule"][-1]["liability_balance"] == pytest.approx(0.0, abs=1e-2)
    assert out["schedule"][-1]["rou_asset_balance"] == pytest.approx(0.0, abs=1e-2)


def test_operating_lease_rou_amortization_plug_sums_to_the_initial_rou_asset():
    out = LA.operating_lease_schedule([10_000.0, 12_000.0, 8_000.0, 15_000.0], 0.07)
    assert sum(row["rou_amortization"] for row in out["schedule"]) == pytest.approx(out["initial_rou_asset"], abs=1e-2)


def test_from_dict_bundles_everything():
    out = LA.from_dict({"initial_measurement": {"lease_payments": [1000.0, 1000.0], "discount_rate": 0.05}})
    assert out["initial_measurement"]["lease_liability"] > 0
