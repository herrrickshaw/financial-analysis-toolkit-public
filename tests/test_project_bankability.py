"""finmodel.project_bankability: annual_incentive_cashflow is checked against a hand calculation;
project_returns' IRR values are checked the rigorous way -- by reconstructing each cash-flow stream
independently in the test and confirming its NPV at the module's own returned IRR is ~0, which is the
literal definition of an internal rate of return, rather than trusting a hand-typed decimal; the simple ROI
and payback figures are checked by hand; rank_projects is checked for correct sorting and for correctly
flagging only the project that crosses the hurdle rate BECAUSE OF incentives, not before and not still
after."""
import pytest

from finmodel import project_bankability as PB


def test_annual_incentive_cashflow_sums_recurring_and_ignores_upfront():
    detail = [
        {"timing": "upfront", "nominal_total": 10.0},
        {"timing": "recurring", "annual_amounts": [1.0, 2.0, 3.0]},
    ]
    out = PB.annual_incentive_cashflow(detail, project_life_years=5)
    assert out == pytest.approx([1.0, 2.0, 3.0, 0.0, 0.0])


def test_annual_incentive_cashflow_sums_overlapping_recurring_components():
    detail = [
        {"timing": "recurring", "annual_amounts": [1.0, 1.0, 1.0]},
        {"timing": "recurring", "annual_amounts": [5.0, 5.0]},
    ]
    out = PB.annual_incentive_cashflow(detail, project_life_years=3)
    assert out == pytest.approx([6.0, 6.0, 1.0])


def test_project_returns_irr_values_solve_their_own_npv_to_zero():
    detail = [{"timing": "recurring", "annual_amounts": [5.0, 5.0, 5.0, 5.0, 5.0]}]
    out = PB.project_returns(total_capex=100.0, upfront_incentive_value=20.0, incentive_detail=detail,
                             annual_operating_cash_flow=15.0, project_life_years=5)

    cashflow_without = [-100.0] + [15.0] * 5
    npv_at_irr_without = sum(cf / (1 + out["irr_without_incentives"]) ** i for i, cf in enumerate(cashflow_without))
    assert npv_at_irr_without == pytest.approx(0.0, abs=1e-6)

    cashflow_with = [-80.0] + [20.0] * 5  # net day-0 investment 100-20=80; 15 opex cash flow + 5 recurring incentive
    npv_at_irr_with = sum(cf / (1 + out["irr_with_incentives"]) ** i for i, cf in enumerate(cashflow_with))
    assert npv_at_irr_with == pytest.approx(0.0, abs=1e-6)

    assert out["irr_uplift"] == pytest.approx(out["irr_with_incentives"] - out["irr_without_incentives"])
    # incentives reduce net day-0 investment and add to operating cash flow, so IRR-with must exceed IRR-without
    assert out["irr_with_incentives"] > out["irr_without_incentives"]


def test_project_returns_simple_roi_and_payback_match_hand_calc():
    detail = [{"timing": "recurring", "annual_amounts": [5.0, 5.0, 5.0, 5.0, 5.0]}]
    out = PB.project_returns(total_capex=100.0, upfront_incentive_value=20.0, incentive_detail=detail,
                             annual_operating_cash_flow=15.0, project_life_years=5)
    assert out["simple_roi_without_incentives"] == pytest.approx(15.0 / 100.0)
    assert out["simple_roi_with_incentives"] == pytest.approx(20.0 / 80.0)
    assert out["payback_years_without_incentives"] == pytest.approx(100.0 / 15.0)
    assert out["payback_years_with_incentives"] == pytest.approx(80.0 / 20.0)


def test_rank_projects_sorts_correctly_and_flags_only_the_incentive_enabled_project():
    entries = [
        {"state": "A", "sector": "S1", "total_capex": 100.0, "upfront_incentive_value": 0.0,
         "incentive_detail": [{"timing": "recurring", "annual_amounts": [22.0] * 5}],
         "annual_operating_cash_flow": 8.0, "project_life_years": 5},
        {"state": "B", "sector": "S2", "total_capex": 100.0, "upfront_incentive_value": 0.0,
         "incentive_detail": [], "annual_operating_cash_flow": 30.0, "project_life_years": 5},
        {"state": "C", "sector": "S3", "total_capex": 100.0, "upfront_incentive_value": 0.0,
         "incentive_detail": [{"timing": "recurring", "annual_amounts": [2.0] * 5}],
         "annual_operating_cash_flow": 8.0, "project_life_years": 5},
    ]
    hurdle_rate = 0.10
    out = PB.rank_projects(entries, hurdle_rate)

    expected = {e["state"]: PB.project_returns(total_capex=e["total_capex"],
                                               upfront_incentive_value=e["upfront_incentive_value"],
                                               incentive_detail=e["incentive_detail"],
                                               annual_operating_cash_flow=e["annual_operating_cash_flow"],
                                               project_life_years=e["project_life_years"]) for e in entries}

    # B (30/yr, no incentive) should be the top-ranked project on its own economics
    assert out["ranked_by_irr_without_incentives"][0]["state"] == "B"
    assert out["ranked_by_irr_without_incentives"][0]["irr_without_incentives"] == pytest.approx(
        expected["B"]["irr_without_incentives"])
    # sorted descending
    irrs_without = [p["irr_without_incentives"] for p in out["ranked_by_irr_without_incentives"]]
    assert irrs_without == sorted(irrs_without, reverse=True)
    irrs_with = [p["irr_with_incentives"] for p in out["ranked_by_irr_with_incentives"]]
    assert irrs_with == sorted(irrs_with, reverse=True)

    # A: without-incentive IRR is deeply negative (8/yr can't recoup a 100 capex in 5 yrs), with-incentive IRR
    # (8+22=30/yr) clears the 10% hurdle -> incentives make this project bankable
    assert expected["A"]["irr_without_incentives"] < hurdle_rate <= expected["A"]["irr_with_incentives"]
    # B: already clears the hurdle without any incentive at all -> not "enabled" (condition requires below hurdle first)
    assert expected["B"]["irr_without_incentives"] >= hurdle_rate
    # C: a small incentive nudges cash flow from 8/yr to 10/yr, nowhere near enough to clear a 10% hurdle either way
    assert expected["C"]["irr_with_incentives"] < hurdle_rate

    enabled_states = {p["state"] for p in out["incentive_enabled_projects"]}
    assert enabled_states == {"A"}


def test_debt_service_coverage_ratio_matches_independent_annuity_formula():
    r, n, loan = 0.10, 10, 100.0
    expected_annual_debt_service = loan * r / (1 - (1 + r) ** -n)
    out = PB.debt_service_coverage_ratio(annual_cash_flow=20.0, loan_amount=loan, interest_rate=r,
                                         tenure_years=n, min_dscr=1.2)
    assert out["annual_debt_service"] == pytest.approx(expected_annual_debt_service)
    assert out["dscr"] == pytest.approx(20.0 / expected_annual_debt_service)
    assert out["compliant"] is True  # dscr ~1.229 >= 1.2


def test_debt_service_coverage_ratio_flags_noncompliance_against_a_stricter_covenant():
    out = PB.debt_service_coverage_ratio(annual_cash_flow=20.0, loan_amount=100.0, interest_rate=0.10,
                                         tenure_years=10, min_dscr=1.3)
    assert out["dscr"] == pytest.approx(1.2289134211409374)
    assert out["compliant"] is False  # dscr ~1.229 < 1.3


def test_from_dict_bundles_everything():
    out = PB.from_dict({
        "project_returns": {"total_capex": 100.0, "upfront_incentive_value": 20.0,
                            "incentive_detail": [{"timing": "recurring", "annual_amounts": [5.0] * 5}],
                            "annual_operating_cash_flow": 15.0, "project_life_years": 5},
    })
    assert out["project_returns"]["simple_roi_without_incentives"] == pytest.approx(0.15)
