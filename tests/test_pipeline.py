"""finmodel.pipeline: a single-step pipeline is checked against the same hand-known example used elsewhere
in this suite; a two-step pipeline is checked for both real placeholder-resolution paths (a dict-key lookup
and a list-index lookup) into an earlier step's actual output; and the pipeline's own error handling is
checked for a duplicate step name, a module with no `from_dict()`, and a bad reference path."""
import pytest

from finmodel import pipeline as PL


def test_single_step_pipeline_matches_the_known_breakeven_example():
    out = PL.run_pipeline([
        {"name": "a", "module": "breakeven",
         "inputs": {"break_even_point": {"fixed_costs": 500000.0, "price_per_unit": 50.0, "variable_cost_per_unit": 30.0}}},
    ])
    assert out["order"] == ["a"]
    assert out["steps"]["a"]["break_even_point"]["break_even_units"] == pytest.approx(25000.0)


def test_two_step_pipeline_resolves_a_dict_key_and_a_list_index_placeholder():
    out = PL.run_pipeline([
        {"name": "forecast", "module": "fpa_planning",
         "inputs": {"rolling_forecast": {"actuals_to_date": [100.0], "driver_growth_rate": 0.10, "forecast_periods": 1}}},
        {"name": "safety", "module": "breakeven",
         "inputs": {"margin_of_safety": {"actual_or_planned_units": "${forecast.rolling_forecast.forecast.0}",
                                         "break_even_units": 25.0, "price_per_unit": 10.0}}},
    ])
    # step 1's forecast[0] = 100 * 1.10 = 110 -- both a dict-key lookup (rolling_forecast) and a list-index
    # lookup (forecast.0) had to resolve correctly for step 2 to see this exact number
    assert out["steps"]["forecast"]["rolling_forecast"]["forecast"][0] == pytest.approx(110.0)
    safety = out["steps"]["safety"]["margin_of_safety"]
    assert safety["unit_cushion"] == pytest.approx(110.0 - 25.0)
    assert safety["revenue_cushion"] == pytest.approx((110.0 - 25.0) * 10.0)


def test_realistic_retail_lending_pipeline_end_to_end():
    out = PL.run_pipeline([
        {"name": "eligibility", "module": "retail_loans",
         "inputs": {"loan_eligibility_foir": {"monthly_gross_income": 150000.0, "existing_emis": 20000.0,
                                              "annual_rate": 0.09, "tenure_months": 240, "foir_limit": 0.5}}},
        {"name": "schedule", "module": "retail_loans",
         "inputs": {"amortization_schedule": {"principal": "${eligibility.loan_eligibility_foir.max_eligible_principal}",
                                              "annual_rate": 0.09, "tenure_months": 240}}},
        {"name": "delinquency", "module": "npa_classification",
         "inputs": {"npa_provisioning": {"days_past_due": 120, "npa_age_days": 30,
                                         "outstanding_amount": "${schedule.amortization_schedule.schedule.23.closing_balance}"}}},
    ])
    principal = out["steps"]["eligibility"]["loan_eligibility_foir"]["max_eligible_principal"]
    outstanding_after_24_months = out["steps"]["schedule"]["amortization_schedule"]["schedule"][23]["closing_balance"]
    assert outstanding_after_24_months < principal  # the balance has amortized down after 2 years of EMIs
    provisioning = out["steps"]["delinquency"]["npa_provisioning"]
    assert provisioning["classification"] == "Sub-standard"
    assert provisioning["provision_required"] == pytest.approx(outstanding_after_24_months * 0.15)  # fully secured by default


def test_duplicate_step_name_rejected():
    with pytest.raises(ValueError, match="duplicate"):
        PL.run_pipeline([
            {"name": "a", "module": "breakeven", "inputs": {}},
            {"name": "a", "module": "breakeven", "inputs": {}},
        ])


def test_module_without_from_dict_rejected():
    with pytest.raises(ValueError, match="from_dict"):
        PL.run_pipeline([{"name": "a", "module": "fin", "inputs": {}}])


def test_bad_reference_path_raises_keyerror():
    with pytest.raises(KeyError):
        PL.run_pipeline([
            {"name": "a", "module": "breakeven",
             "inputs": {"break_even_point": {"fixed_costs": 1.0, "price_per_unit": 2.0, "variable_cost_per_unit": 1.0}}},
            {"name": "b", "module": "breakeven",
             "inputs": {"break_even_point": {"fixed_costs": "${a.break_even_point.nonexistent_field}",
                                             "price_per_unit": 2.0, "variable_cost_per_unit": 1.0}}},
        ])


def test_from_dict_wraps_run_pipeline():
    out = PL.from_dict({"steps": [
        {"name": "a", "module": "breakeven",
         "inputs": {"break_even_point": {"fixed_costs": 500000.0, "price_per_unit": 50.0, "variable_cost_per_unit": 30.0}}},
    ]})
    assert out["steps"]["a"]["break_even_point"]["break_even_units"] == pytest.approx(25000.0)
