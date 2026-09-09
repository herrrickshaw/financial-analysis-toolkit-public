"""finmodel.investment_incentives: every mechanic is checked against a hand calculation, plus the
net_tax_reimbursement_schedule's defining property -- the cumulative reimbursement across all years never
exceeds the scheme's overall cap, even though each individual year's own cap wasn't reached."""
import pytest

from finmodel import investment_incentives as INC


def test_capital_investment_subsidy_uncapped():
    out = INC.capital_investment_subsidy(eligible_investment=50.0, subsidy_rate=0.15, subsidy_cap=12.0)
    assert out["raw_entitlement"] == pytest.approx(7.5)
    assert out["subsidy_amount"] == pytest.approx(7.5)
    assert out["capped"] is False


def test_capital_investment_subsidy_capped():
    out = INC.capital_investment_subsidy(eligible_investment=100.0, subsidy_rate=0.15, subsidy_cap=12.0)
    assert out["raw_entitlement"] == pytest.approx(15.0)
    assert out["subsidy_amount"] == pytest.approx(12.0)
    assert out["capped"] is True


def test_interest_subsidy_schedule_matches_hand_calc_with_some_years_capped():
    out = INC.interest_subsidy_schedule(annual_interest_paid=[4.0, 4.0, 10.0, 10.0], subsidy_rate=0.05,
                                        annual_cap=0.3, tenure_years=4)
    subsidies = [row["subsidy_paid"] for row in out["schedule"]]
    assert subsidies == pytest.approx([0.2, 0.2, 0.3, 0.3])
    assert [row["capped"] for row in out["schedule"]] == [False, False, True, True]
    assert out["total_subsidy"] == pytest.approx(1.0)


def test_interest_subsidy_schedule_beyond_the_supplied_years_treats_interest_as_zero():
    out = INC.interest_subsidy_schedule(annual_interest_paid=[5.0], subsidy_rate=0.1, annual_cap=10.0, tenure_years=3)
    assert [row["interest_paid"] for row in out["schedule"]] == [5.0, 0.0, 0.0]
    assert out["total_subsidy"] == pytest.approx(0.5)


def test_net_tax_reimbursement_schedule_overall_cap_binds_in_the_final_year():
    out = INC.net_tax_reimbursement_schedule(annual_net_tax_paid=[100.0, 100.0, 100.0, 100.0], reimbursement_rate=0.5,
                                             annual_cap=1000.0, tenure_years=4, overall_cap=180.0)
    paid = [row["reimbursement_paid"] for row in out["schedule"]]
    assert paid == pytest.approx([50.0, 50.0, 50.0, 30.0])
    assert [row["overall_cap_binding"] for row in out["schedule"]] == [False, False, False, True]
    assert out["total_reimbursement"] == pytest.approx(180.0)
    assert out["overall_cap_exhausted"] is True
    # the defining property: cumulative reimbursement never exceeds the overall cap, year by year
    cumulative = 0.0
    for amount in paid:
        cumulative += amount
        assert cumulative <= out["overall_cap"] + 1e-9


def test_net_tax_reimbursement_schedule_annual_cap_alone_does_not_trip_overall_cap_binding():
    out = INC.net_tax_reimbursement_schedule(annual_net_tax_paid=[1000.0], reimbursement_rate=0.5, annual_cap=100.0,
                                             tenure_years=1, overall_cap=1000.0)
    assert out["schedule"][0]["reimbursement_paid"] == pytest.approx(100.0)
    assert out["schedule"][0]["overall_cap_binding"] is False
    assert out["overall_cap_exhausted"] is False


def test_employment_generation_subsidy_matches_hand_calc():
    uncapped = INC.employment_generation_subsidy(eligible_employees=10.0, per_employee_monthly_amount=2000.0,
                                                  months=12.0, scheme_cap=1_000_000.0)
    assert uncapped["raw_entitlement"] == pytest.approx(240_000.0)
    assert uncapped["subsidy_amount"] == pytest.approx(240_000.0)
    assert uncapped["capped"] is False

    capped = INC.employment_generation_subsidy(eligible_employees=50.0, per_employee_monthly_amount=2000.0,
                                                months=12.0, scheme_cap=1_000_000.0)
    assert capped["raw_entitlement"] == pytest.approx(1_200_000.0)
    assert capped["subsidy_amount"] == pytest.approx(1_000_000.0)
    assert capped["capped"] is True


def test_ad_valorem_duty_exemption_full_and_partial():
    full = INC.ad_valorem_duty_exemption(payable_amount=500_000.0, exemption_pct=1.0)
    assert full["exempted_amount"] == pytest.approx(500_000.0)
    assert full["net_payable"] == pytest.approx(0.0)

    partial = INC.ad_valorem_duty_exemption(payable_amount=200_000.0, exemption_pct=0.5)
    assert partial["exempted_amount"] == pytest.approx(100_000.0)
    assert partial["net_payable"] == pytest.approx(100_000.0)


def test_incremental_metric_linked_incentive_below_base_year_earns_nothing():
    out = INC.incremental_metric_linked_incentive(base_year_value=1000.0, current_year_value=800.0,
                                                   incentive_rate=0.05, cap=100.0)
    assert out["incremental_value"] == pytest.approx(0.0)
    assert out["incentive_amount"] == pytest.approx(0.0)


def test_incremental_metric_linked_incentive_capped_and_uncapped():
    uncapped = INC.incremental_metric_linked_incentive(base_year_value=1000.0, current_year_value=1500.0,
                                                        incentive_rate=0.05, cap=100.0)
    assert uncapped["incremental_value"] == pytest.approx(500.0)
    assert uncapped["incentive_amount"] == pytest.approx(25.0)
    assert uncapped["capped"] is False

    capped = INC.incremental_metric_linked_incentive(base_year_value=1000.0, current_year_value=5000.0,
                                                      incentive_rate=0.05, cap=100.0)
    assert capped["entitlement"] == pytest.approx(200.0)
    assert capped["incentive_amount"] == pytest.approx(100.0)
    assert capped["capped"] is True


def test_combined_incentive_package_aggregates_by_scheme_and_jurisdiction():
    components = [
        {"scheme_name": "MP BIPA", "jurisdiction": "state", "amount": 50.0},
        {"scheme_name": "PLI-Textiles", "jurisdiction": "central", "amount": 120.0},
        {"scheme_name": "MP BIPA", "jurisdiction": "state", "amount": 10.0},
    ]
    out = INC.combined_incentive_package(components)
    assert out["total_incentive_value"] == pytest.approx(180.0)
    assert out["by_scheme"] == pytest.approx({"MP BIPA": 60.0, "PLI-Textiles": 120.0})
    assert out["by_jurisdiction"] == pytest.approx({"state": 60.0, "central": 120.0})


def test_effective_capex_after_incentives():
    out = INC.effective_capex_after_incentives(gross_capex=1000.0, upfront_capital_subsidies=150.0)
    assert out["net_capex"] == pytest.approx(850.0)
    assert out["effective_subsidy_pct"] == pytest.approx(0.15)


def test_from_dict_bundles_everything():
    out = INC.from_dict({
        "capital_investment_subsidy": {"eligible_investment": 100.0, "subsidy_rate": 0.15, "subsidy_cap": 12.0},
        "combined_incentive_package": [
            {"scheme_name": "A", "jurisdiction": "state", "amount": 5.0},
            {"scheme_name": "B", "jurisdiction": "central", "amount": 7.0},
        ],
    })
    assert out["capital_investment_subsidy"]["subsidy_amount"] == pytest.approx(12.0)
    assert out["combined_incentive_package"]["total_incentive_value"] == pytest.approx(12.0)
