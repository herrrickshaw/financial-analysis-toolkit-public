"""finmodel.breakeven: break-even units/revenue, margin of safety, and degree of operating leverage are each
checked against hand-computed values, plus the real, defining property that DOL is most extreme right at the
break-even point and falls as volume rises above it."""
import pytest

from finmodel import breakeven as B


def test_contribution_margin():
    out = B.contribution_margin(price_per_unit=50.0, variable_cost_per_unit=30.0)
    assert out["contribution_margin_per_unit"] == 20.0
    assert out["contribution_margin_ratio"] == pytest.approx(0.4)


def test_break_even_point_matches_hand_calc():
    out = B.break_even_point(fixed_costs=500000.0, price_per_unit=50.0, variable_cost_per_unit=30.0)
    assert out["break_even_units"] == pytest.approx(25000.0)
    assert out["break_even_revenue"] == pytest.approx(1250000.0)


def test_margin_of_safety_matches_hand_calc():
    out = B.margin_of_safety(actual_or_planned_units=30000.0, break_even_units=25000.0, price_per_unit=50.0)
    assert out["unit_cushion"] == 5000.0
    assert out["revenue_cushion"] == 250000.0
    assert out["margin_of_safety_pct"] == pytest.approx(5000.0 / 30000.0)


def test_degree_of_operating_leverage_matches_hand_calc():
    out = B.degree_of_operating_leverage(units=30000.0, price_per_unit=50.0, variable_cost_per_unit=30.0, fixed_costs=500000.0)
    assert out["total_contribution_margin"] == pytest.approx(600000.0)
    assert out["operating_profit"] == pytest.approx(100000.0)
    assert out["degree_of_operating_leverage"] == pytest.approx(6.0)


def test_dol_is_more_extreme_closer_to_the_break_even_point():
    near = B.degree_of_operating_leverage(units=26000.0, price_per_unit=50.0, variable_cost_per_unit=30.0, fixed_costs=500000.0)
    far = B.degree_of_operating_leverage(units=50000.0, price_per_unit=50.0, variable_cost_per_unit=30.0, fixed_costs=500000.0)
    assert near["degree_of_operating_leverage"] > far["degree_of_operating_leverage"] > 1.0


def test_from_dict_chains_break_even_units_into_margin_of_safety():
    d = {"break_even_point": {"fixed_costs": 500000.0, "price_per_unit": 50.0, "variable_cost_per_unit": 30.0},
         "margin_of_safety": {"actual_or_planned_units": 30000.0, "price_per_unit": 50.0}}
    out = B.from_dict(d)
    assert out["margin_of_safety"]["unit_cushion"] == pytest.approx(5000.0)
