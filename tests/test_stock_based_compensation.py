"""finmodel.stock_based_compensation: RSU fair value is checked against a hand calc; the option-grant fair
value is checked to match finmodel.options.black_scholes directly (not a reimplementation); the two expense-
attribution methods are checked against the real, defining property that graded vesting front-loads more
expense into early periods than straight-line does, while both expense EXACTLY the same total by the end."""
import pytest

from finmodel import stock_based_compensation as SBC
from finmodel.options import black_scholes


def test_rsu_grant_fair_value_matches_hand_calc():
    assert SBC.rsu_grant_fair_value(shares_granted=10_000.0, grant_date_share_price=45.0) == pytest.approx(450_000.0)


def test_stock_option_grant_fair_value_matches_black_scholes_directly():
    kwargs = dict(spot=100.0, strike=100.0, rate=0.05, vol=0.30, time=4.0)
    out = SBC.stock_option_grant_fair_value(shares_granted=50_000.0, **kwargs)
    expected_per_share = black_scholes(**kwargs, option_type="call")["price"]
    assert out["fair_value_per_share"] == pytest.approx(expected_per_share)
    assert out["total_fair_value"] == pytest.approx(50_000.0 * expected_per_share)


def test_straight_line_expense_schedule_is_level_and_sums_to_the_total():
    out = SBC.straight_line_expense_schedule(total_fair_value=1_000_000.0, vesting_periods=48)
    assert out["period_expense"] == pytest.approx(1_000_000.0 / 48)
    assert all(row["expense"] == pytest.approx(out["period_expense"]) for row in out["schedule"])
    assert out["schedule"][-1]["cumulative_expense"] == pytest.approx(1_000_000.0)


def test_graded_vesting_matches_hand_traced_four_tranche_example():
    # a standard 4-year graded-vesting award: 25% vesting at each of 12/24/36/48 months
    tranches = [{"pct_of_award": 0.25, "vesting_periods": 12}, {"pct_of_award": 0.25, "vesting_periods": 24},
                {"pct_of_award": 0.25, "vesting_periods": 36}, {"pct_of_award": 0.25, "vesting_periods": 48}]
    out = SBC.graded_vesting_expense_schedule(1_000_000.0, tranches)
    tranche_period_expenses = [250_000.0 / 12, 250_000.0 / 24, 250_000.0 / 36, 250_000.0 / 48]
    # month 1: all four tranches are still actively vesting
    assert out["schedule"][0]["expense"] == pytest.approx(sum(tranche_period_expenses))
    # month 13: the 12-month tranche has finished, only the other three remain active
    assert out["schedule"][12]["expense"] == pytest.approx(sum(tranche_period_expenses[1:]))
    # month 48 (the last): only the 48-month tranche is still active
    assert out["schedule"][-1]["expense"] == pytest.approx(tranche_period_expenses[3])
    assert out["schedule"][-1]["cumulative_expense"] == pytest.approx(1_000_000.0)  # same total as straight-line


def test_graded_vesting_front_loads_more_expense_than_straight_line():
    tranches = [{"pct_of_award": 0.25, "vesting_periods": 12}, {"pct_of_award": 0.25, "vesting_periods": 24},
                {"pct_of_award": 0.25, "vesting_periods": 36}, {"pct_of_award": 0.25, "vesting_periods": 48}]
    graded = SBC.graded_vesting_expense_schedule(1_000_000.0, tranches)
    straight = SBC.straight_line_expense_schedule(1_000_000.0, 48)
    assert graded["schedule"][11]["cumulative_expense"] > straight["schedule"][11]["cumulative_expense"]
    # both methods expense exactly the same total by the end of the full vesting period
    assert graded["schedule"][-1]["cumulative_expense"] == pytest.approx(straight["schedule"][-1]["cumulative_expense"])


def test_graded_vesting_rejects_percentages_not_summing_to_one():
    with pytest.raises(ValueError):
        SBC.graded_vesting_expense_schedule(1_000_000.0, [{"pct_of_award": 0.5, "vesting_periods": 12}])


def test_from_dict_bundles_everything():
    out = SBC.from_dict({"rsu_grant_fair_value": {"shares_granted": 100.0, "grant_date_share_price": 10.0}})
    assert out["rsu_grant_fair_value"]["value"] == pytest.approx(1000.0)
