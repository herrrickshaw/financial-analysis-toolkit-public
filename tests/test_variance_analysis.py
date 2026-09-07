"""finmodel.variance_analysis: the volume/price decomposition and the multi-product mix/quantity decomposition
are each checked against the real, exact algebraic identity that must hold (their components sum to the total
variance being decomposed), and horizontal/vertical analysis are checked by hand."""
import pytest

from finmodel import variance_analysis as V


def test_budget_vs_actual_variance_matches_hand_calc_and_reconciles():
    out = V.budget_vs_actual_variance(budget_volume=10000, actual_volume=11000, budget_price=10.0, actual_price=9.5)
    assert out["volume_variance"] == pytest.approx(10000.0)   # (11000-10000)*10
    assert out["price_variance"] == pytest.approx(-5500.0)    # (9.5-10)*11000
    assert out["total_variance"] == pytest.approx(4500.0)
    assert out["reconciles"] is True


def test_budget_vs_actual_variance_pure_price_case():
    # volume unchanged -> volume variance must be exactly zero
    out = V.budget_vs_actual_variance(budget_volume=100, actual_volume=100, budget_price=10.0, actual_price=12.0)
    assert out["volume_variance"] == 0.0
    assert out["price_variance"] == pytest.approx(200.0)


def test_sales_mix_and_volume_variance_sums_to_the_real_total_volume_variance():
    products = [{"name": "A", "budget_units": 600, "actual_units": 500, "budget_contribution_margin_per_unit": 5.0},
                {"name": "B", "budget_units": 400, "actual_units": 600, "budget_contribution_margin_per_unit": 8.0}]
    out = V.sales_mix_and_volume_variance(products)
    manual_total = sum((p["actual_units"] - p["budget_units"]) * p["budget_contribution_margin_per_unit"] for p in products)
    assert out["total_volume_variance"] == pytest.approx(manual_total)
    assert out["total_sales_mix_variance"] + out["total_sales_quantity_variance"] == pytest.approx(manual_total)


def test_sales_mix_variance_is_zero_when_mix_is_unchanged():
    # same proportional split budget vs actual (just scaled up) -> mix variance should be zero, all quantity
    products = [{"name": "A", "budget_units": 600, "actual_units": 660, "budget_contribution_margin_per_unit": 5.0},
                {"name": "B", "budget_units": 400, "actual_units": 440, "budget_contribution_margin_per_unit": 8.0}]
    out = V.sales_mix_and_volume_variance(products)
    assert out["total_sales_mix_variance"] == pytest.approx(0.0, abs=1e-6)


def test_horizontal_analysis_first_period_is_none_and_pct_matches_hand_calc():
    out = V.horizontal_analysis({"Revenue": [1000000, 1150000, 1300000]})
    r = out["Revenue"]
    assert r["pct_change"][0] is None
    assert r["pct_change"][1] == pytest.approx(0.15)
    assert r["pct_change"][2] == pytest.approx(1300000 / 1150000 - 1)


def test_vertical_analysis_matches_hand_calc():
    out = V.vertical_analysis({"COGS": [400000, 450000]}, base_line_values=[1000000, 1150000])
    assert out["COGS"][0] == pytest.approx(0.40)
    assert out["COGS"][1] == pytest.approx(450000 / 1150000)


def test_from_dict_bundles_everything():
    d = {"budget_vs_actual_variance": {"budget_volume": 100.0, "actual_volume": 100.0, "budget_price": 10.0, "actual_price": 11.0},
         "horizontal_analysis": {"line_items_by_period": {"Revenue": [100.0, 110.0]}}}
    out = V.from_dict(d)
    assert out["budget_vs_actual_variance"]["total_variance"] == pytest.approx(100.0)
    assert out["horizontal_analysis"]["Revenue"]["pct_change"][1] == pytest.approx(0.10)
