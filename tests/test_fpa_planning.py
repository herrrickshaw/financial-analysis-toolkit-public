"""finmodel.fpa_planning: the headcount schedule is checked for its real, defining behavior (a role's cost
doesn't appear before its own start month), and the rolling forecast is checked for its defining mechanic
(it re-anchors off the LAST actual, not the first)."""
import pytest

from finmodel import fpa_planning as F


def test_headcount_cost_schedule_matches_hand_calc():
    roles = [{"title": "Engineer", "start_month": 0, "monthly_base_salary": 10000.0, "count": 3},
             {"title": "Sales", "start_month": 6, "monthly_base_salary": 8000.0, "count": 2}]
    out = F.headcount_cost_schedule(roles, months=12, benefits_load_pct=0.25)
    assert out["monthly_cost"][0] == pytest.approx(3 * 10000.0 * 1.25)
    assert out["monthly_cost"][5] == pytest.approx(3 * 10000.0 * 1.25)  # sales hasn't started yet
    assert out["monthly_cost"][6] == pytest.approx(3 * 10000.0 * 1.25 + 2 * 8000.0 * 1.25)
    assert out["total_cost"] == pytest.approx(sum(out["monthly_cost"]))


def test_headcount_cost_schedule_role_never_appears_before_its_start_month():
    roles = [{"title": "Late hire", "start_month": 11, "monthly_base_salary": 5000.0, "count": 1}]
    out = F.headcount_cost_schedule(roles, months=12, benefits_load_pct=0.0)
    assert out["monthly_cost"][:11] == [0.0] * 11
    assert out["monthly_cost"][11] == pytest.approx(5000.0)


def test_rolling_forecast_reanchors_off_the_last_actual():
    out = F.rolling_forecast(actuals_to_date=[100.0, 110.0, 121.0], driver_growth_rate=0.05, forecast_periods=2)
    assert out["forecast"][0] == pytest.approx(121.0 * 1.05)
    assert out["forecast"][1] == pytest.approx(121.0 * 1.05 ** 2)
    assert out["combined"] == out["actuals_to_date"] + out["forecast"]


def test_rolling_forecast_rejects_empty_actuals():
    with pytest.raises(ValueError):
        F.rolling_forecast(actuals_to_date=[], driver_growth_rate=0.05, forecast_periods=2)


def test_from_dict_bundles_everything():
    d = {"headcount_cost_schedule": {"roles": [{"title": "A", "start_month": 0, "monthly_base_salary": 1000.0, "count": 1}], "months": 3},
         "rolling_forecast": {"actuals_to_date": [10.0], "driver_growth_rate": 0.1, "forecast_periods": 1}}
    out = F.from_dict(d)
    assert out["headcount_cost_schedule"]["total_cost"] == pytest.approx(1000.0 * 1.25 * 3)
    assert out["rolling_forecast"]["forecast"][0] == pytest.approx(11.0)
