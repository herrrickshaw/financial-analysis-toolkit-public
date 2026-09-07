"""finmodel.inventory_costing: each method is checked against a hand-computed three-layer example with
rising purchase costs, verified against the universal cost-conservation identity (cogs + ending inventory
value equals total cost available, regardless of method), and against the real, well-known directional
property that FIFO reports the lowest cost of goods sold and LIFO the highest in a rising-cost environment,
with weighted average landing exactly between them."""
import pytest

from finmodel import inventory_costing as IC

PURCHASES = [{"quantity": 100.0, "unit_cost": 10.0}, {"quantity": 100.0, "unit_cost": 12.0}, {"quantity": 100.0, "unit_cost": 15.0}]
TOTAL_COST_AVAILABLE = 100 * 10.0 + 100 * 12.0 + 100 * 15.0  # 3,700


def test_fifo_matches_hand_calc():
    out = IC.fifo(PURCHASES, units_sold=150.0)
    assert out["cogs"] == pytest.approx(100 * 10.0 + 50 * 12.0)  # 1,600: oldest, cheapest layers sold first
    assert out["ending_inventory_value"] == pytest.approx(50 * 12.0 + 100 * 15.0)  # 2,100: newest layers remain
    assert out["cogs"] + out["ending_inventory_value"] == pytest.approx(TOTAL_COST_AVAILABLE)


def test_lifo_matches_hand_calc():
    out = IC.lifo(PURCHASES, units_sold=150.0)
    assert out["cogs"] == pytest.approx(100 * 15.0 + 50 * 12.0)  # 2,100: newest, priciest layers sold first
    assert out["ending_inventory_value"] == pytest.approx(50 * 12.0 + 100 * 10.0)  # 1,600: oldest layers remain
    assert out["cogs"] + out["ending_inventory_value"] == pytest.approx(TOTAL_COST_AVAILABLE)


def test_weighted_average_matches_hand_calc():
    out = IC.weighted_average(PURCHASES, units_sold=150.0)
    expected_avg = TOTAL_COST_AVAILABLE / 300.0
    assert out["average_cost_per_unit"] == pytest.approx(expected_avg)
    assert out["cogs"] == pytest.approx(150.0 * expected_avg)
    assert out["cogs"] + out["ending_inventory_value"] == pytest.approx(TOTAL_COST_AVAILABLE)


def test_fifo_gives_lowest_cogs_and_lifo_highest_in_a_rising_cost_environment():
    out = IC.compare_costing_methods(PURCHASES, units_sold=150.0)
    assert out["fifo"]["cogs"] < out["weighted_average"]["cogs"] < out["lifo"]["cogs"]
    # every method still conserves the same total cost available, just splits it differently
    for method in ("fifo", "lifo", "weighted_average"):
        assert out[method]["cogs"] + out[method]["ending_inventory_value"] == pytest.approx(out["total_cost_available"])


def test_rejects_selling_more_units_than_available():
    with pytest.raises(ValueError):
        IC.fifo(PURCHASES, units_sold=1000.0)
    with pytest.raises(ValueError):
        IC.weighted_average(PURCHASES, units_sold=1000.0)


def test_from_dict_bundles_everything():
    out = IC.from_dict({"compare_costing_methods": {"purchases": PURCHASES, "units_sold": 150.0}})
    assert out["compare_costing_methods"]["fifo"]["cogs"] < out["compare_costing_methods"]["lifo"]["cogs"]
