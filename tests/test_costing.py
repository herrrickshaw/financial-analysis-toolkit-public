import pytest
from finmodel.costing import resource_allocation, allocate_costs, CostObject, CostPool, full_cost_price, income_diversification, from_dict


def test_resource_allocation_sums_to_envelope():
    r = resource_allocation(1000, {"Arts": {"students": 600, "research": 20}, "Science": {"students": 400, "research": 80}}, {"students": 0.6, "research": 0.4}, top_slice_pct=0.1, strategic={"Science": 50})
    assert r["check"] and r["top_slice"] == 100 and r["formula_pool"] == 850
    assert r["units"]["Arts"]["formula_share"] == pytest.approx(0.6 * 0.6 + 0.4 * 0.2)
    assert r["units"]["Science"]["total"] == pytest.approx(850 * (0.6 * 0.4 + 0.4 * 0.8) + 50)


def test_costing_two_step_allocation_and_rates():
    objs = [CostObject("BSc Physics", "teaching", {"students": 300, "person_years": 20, "m2": 1000}, direct_costs=1200, direct_salary=800),
            CostObject("Physics research", "research", {"students": 0, "person_years": 30, "m2": 1500}, direct_costs=1500, direct_salary=1000)]
    pools = [CostPool("Student support", 300, "students"), CostPool("Library", 250, "person_years"), CostPool("Facilities", 500, "m2"), CostPool("Orphan", 100, "boats")]
    r = allocate_costs(objs, pools, salary_addon_rate=0.5)
    t, rs = r["objects"]
    assert t["indirect"] == pytest.approx(300 + 250 * 20 / 50 + 500 * 1000 / 2500)   # 600
    assert rs["indirect"] == pytest.approx(250 * 30 / 50 + 500 * 1500 / 2500)          # 450
    assert t["indirect_rate_on_salary"] == pytest.approx(600 / 1200)
    assert r["unallocated"] == {"Orphan": 100} and r["check"]
    assert r["by_activity"]["research"]["full_cost"] == pytest.approx(1950)
    p = full_cost_price(100, 200, indirect_rate_on_salary=0.9, salary_addon_rate=0.5, margin=0.1)
    assert p["full_cost"] == pytest.approx(100 + 100 + 300 * 0.9) and p["price"] == pytest.approx(p["full_cost"] * 1.1)


def test_income_diversification_hhi():
    r = income_diversification({"public": 700, "tuition": 200, "industry": 100}, stability={"public": 4, "tuition": 3, "industry": 2}, potential={"public": 1, "tuition": 3, "industry": 5})
    assert r["hhi"] == pytest.approx(0.49 + 0.04 + 0.01) and r["effective_sources"] == pytest.approx(1 / 0.54)
    assert r["ranking"][0] == "industry" and r["weighted_stability"] == pytest.approx(0.7 * 4 + 0.2 * 3 + 0.1 * 2)
    out = from_dict({"income": {"a": 1, "b": 1}})
    assert out["income_diversification"]["hhi"] == pytest.approx(0.5)
