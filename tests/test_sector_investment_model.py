"""finmodel.sector_investment_model: land cost and capex assembly are checked against hand calculations;
incentive_present_value is checked against an independently-written NPV expression (not the module's own
npv() call) so the discounting logic is verified from outside, and against the real property that a
recurring stream's PRESENT value is always less than its NOMINAL (undiscounted) sum at any positive discount
rate -- the exact overstatement this module exists to avoid."""
import pytest

from finmodel import sector_investment_model as SIM


def test_industrial_land_cost():
    out = SIM.industrial_land_cost(area_acres=10.0, rate_per_acre=2.0)
    assert out["land_cost"] == pytest.approx(20.0)


def test_project_capex_stack_sums_all_components():
    out = SIM.project_capex_stack({"land": 20.0, "plant_and_machinery": 40.0, "building_and_infrastructure": 10.0})
    assert out["total_capex"] == pytest.approx(70.0)


def test_leasehold_land_cost_applies_the_discount_schedule_by_year():
    schedule = [{"through_year": 3, "rent_discount_pct": 0.50}, {"through_year": 5, "rent_discount_pct": 0.25}]
    out = SIM.leasehold_land_cost(area_acres=10.0, base_annual_rent_per_acre=1.0, lease_term_years=7,
                                  discount_rate=0.10, discount_schedule=schedule)
    # years 1-3 at 50% off, years 4-5 at 25% off, years 6-7 at full rate -- each year's rent = base * area * (1-discount)
    expected_rents = [5.0, 5.0, 5.0, 7.5, 7.5, 10.0, 10.0]
    assert out["annual_rent_schedule"] == pytest.approx(expected_rents)
    assert out["nominal_total_rent"] == pytest.approx(sum(expected_rents))
    assert out["land_cost"] == out["capitalized_cost"]  # aliased for drop-in use in project_capex_stack


def test_leasehold_land_cost_capitalized_value_matches_independent_npv_expression():
    schedule = [{"through_year": 3, "rent_discount_pct": 0.50}, {"through_year": 5, "rent_discount_pct": 0.25}]
    out = SIM.leasehold_land_cost(area_acres=10.0, base_annual_rent_per_acre=1.0, lease_term_years=7,
                                  discount_rate=0.10, discount_schedule=schedule)
    expected_rents = [5.0, 5.0, 5.0, 7.5, 7.5, 10.0, 10.0]
    expected_pv = sum(cf / (1.10 ** year) for year, cf in enumerate(expected_rents, start=1))
    assert out["capitalized_cost"] == pytest.approx(expected_pv)


def test_leasehold_land_cost_with_no_discount_schedule_pays_full_rent_every_year():
    out = SIM.leasehold_land_cost(area_acres=5.0, base_annual_rent_per_acre=2.0, lease_term_years=4,
                                  discount_rate=0.10, discount_schedule=())
    assert out["annual_rent_schedule"] == pytest.approx([10.0, 10.0, 10.0, 10.0])
    # a capitalized rent stream must always be worth less than its own nominal (undiscounted) sum
    assert out["capitalized_cost"] < out["nominal_total_rent"]


def test_incentive_present_value_matches_independent_npv_expression():
    components = [
        {"scheme_name": "State Capital Subsidy", "jurisdiction": "state", "timing": "upfront", "amount": 8.0},
        {"scheme_name": "Central PLI", "jurisdiction": "central", "timing": "recurring",
         "annual_amounts": [2.0, 2.0, 2.0, 2.0, 2.0]},
    ]
    out = SIM.incentive_present_value(components, discount_rate=0.10)
    expected_pv_of_recurring = sum(2.0 / (1.10 ** year) for year in range(1, 6))
    assert out["pv_of_recurring"] == pytest.approx(expected_pv_of_recurring)
    assert out["upfront_value"] == pytest.approx(8.0)
    assert out["total_present_value"] == pytest.approx(8.0 + expected_pv_of_recurring)
    assert out["nominal_total"] == pytest.approx(18.0)
    assert out["by_jurisdiction_nominal"] == pytest.approx({"state": 8.0, "central": 10.0})


def test_recurring_incentive_present_value_is_always_less_than_its_nominal_sum():
    components = [{"scheme_name": "Net-tax reimbursement", "jurisdiction": "state", "timing": "recurring",
                  "annual_amounts": [5.0, 5.0, 5.0, 5.0, 5.0, 5.0, 5.0]}]
    out = SIM.incentive_present_value(components, discount_rate=0.08)
    assert out["pv_of_recurring"] < out["nominal_total"]
    assert out["total_present_value"] == pytest.approx(out["pv_of_recurring"])


def test_sample_project_model_end_to_end_matches_hand_calc():
    land = SIM.industrial_land_cost(area_acres=10.0, rate_per_acre=2.0)
    components = [
        {"scheme_name": "State Capital Subsidy", "jurisdiction": "state", "timing": "upfront", "amount": 8.0},
        {"scheme_name": "Central PLI", "jurisdiction": "central", "timing": "recurring",
         "annual_amounts": [2.0, 2.0, 2.0, 2.0, 2.0]},
    ]
    out = SIM.sample_project_model(state="Telangana", sector="Pharmaceuticals", land=land,
                                   capex_components={"plant_and_machinery": 40.0, "building_and_infrastructure": 10.0},
                                   incentive_components=components, discount_rate=0.10)
    assert out["capex"]["total_capex"] == pytest.approx(70.0)
    expected_pv = 8.0 + sum(2.0 / (1.10 ** year) for year in range(1, 6))
    assert out["incentives"]["total_present_value"] == pytest.approx(expected_pv)
    assert out["net_effective_investment"] == pytest.approx(70.0 - expected_pv)
    assert out["effective_subsidy_pct_pv_basis"] == pytest.approx(expected_pv / 70.0)


def test_sample_project_matrix_sums_across_entries_and_carries_notes_through():
    entries = [
        {"state": "Telangana", "sector": "Pharmaceuticals", "land": {"area_acres": 10.0, "rate_per_acre": 2.0},
         "capex_components": {"plant_and_machinery": 40.0, "building_and_infrastructure": 10.0},
         "incentive_components": [{"scheme_name": "State Capital Subsidy", "jurisdiction": "state",
                                   "timing": "upfront", "amount": 8.0}],
         "discount_rate": 0.10},
        {"state": "Odisha", "sector": "Metals", "land": {"area_acres": 5.0, "rate_per_acre": 0.75},
         "capex_components": {"plant_and_machinery": 15.0},
         "incentive_components": [{"scheme_name": "Odisha Net-SGST Reimbursement", "jurisdiction": "state",
                                   "timing": "upfront", "amount": 3.0}],
         "discount_rate": 0.10, "note": "illustrative placeholder land rate"},
    ]
    out = SIM.sample_project_matrix(entries)
    assert len(out["projects"]) == 2
    expected_capex = (10.0 * 2.0 + 40.0 + 10.0) + (5.0 * 0.75 + 15.0)
    expected_incentive_pv = 8.0 + 3.0
    assert out["total_capex_across_projects"] == pytest.approx(expected_capex)
    assert out["total_incentive_present_value_across_projects"] == pytest.approx(expected_incentive_pv)
    assert "note" not in out["projects"][0]
    assert out["projects"][1]["note"] == "illustrative placeholder land rate"


def test_sample_project_matrix_dispatches_leasehold_land_alongside_purchase_land():
    entries = [
        {"state": "Andaman & Nicobar Islands", "sector": "General Manufacturing",
         "land": {"land_type": "leasehold", "area_acres": 10.0, "base_annual_rent_per_acre": 1.0,
                  "lease_term_years": 4, "discount_rate": 0.10, "discount_schedule": []},
         "capex_components": {"plant_and_machinery": 20.0},
         "incentive_components": [], "discount_rate": 0.10},
        {"state": "Telangana", "sector": "Pharmaceuticals", "land": {"area_acres": 10.0, "rate_per_acre": 2.0},
         "capex_components": {"plant_and_machinery": 40.0, "building_and_infrastructure": 10.0},
         "incentive_components": [], "discount_rate": 0.10},
    ]
    out = SIM.sample_project_matrix(entries)
    # leasehold entry: capitalized cost of Rs10/yr for 4yrs @10% + 20 capex
    expected_leasehold_land = sum(10.0 / (1.10 ** year) for year in range(1, 5))
    an_project = out["projects"][0]
    assert an_project["land"]["land_cost"] == pytest.approx(expected_leasehold_land)
    assert an_project["capex"]["total_capex"] == pytest.approx(expected_leasehold_land + 20.0)
    # purchase entry unaffected, still a plain one-time cost
    assert out["projects"][1]["land"]["land_cost"] == pytest.approx(20.0)


def test_from_dict_bundles_everything():
    out = SIM.from_dict({
        "sample_project_model": {
            "state": "Odisha", "sector": "Food Processing",
            "land": {"area_acres": 5.0, "rate_per_acre": 1.0},
            "capex_components": {"plant_and_machinery": 15.0},
            "incentive_components": [{"scheme_name": "X", "jurisdiction": "state", "timing": "upfront", "amount": 3.0}],
            "discount_rate": 0.10,
        }
    })
    r = out["sample_project_model"]
    assert r["capex"]["total_capex"] == pytest.approx(5.0 + 15.0)
    assert r["net_effective_investment"] == pytest.approx(20.0 - 3.0)
