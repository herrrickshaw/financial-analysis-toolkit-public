"""finmodel.percentage_of_completion: the single-period calculation is checked against hand-computed values
for both the over-billed and under-billed cases, and the multi-period schedule is checked against its own
self-verifying accounting identity -- once costs incurred reach exactly the total estimate, cumulative
recognized revenue must equal exactly the contract price, and the sum of every period's current-period
revenue must equal that same total."""
import pytest

from finmodel import percentage_of_completion as POC


def test_percentage_of_completion_under_billed_matches_hand_calc():
    out = POC.percentage_of_completion(costs_incurred_to_date=600_000.0, total_estimated_costs=1_000_000.0,
                                       contract_price=1_200_000.0, billings_to_date=700_000.0)
    assert out["pct_complete"] == pytest.approx(0.6)
    assert out["revenue_recognized_to_date"] == pytest.approx(720_000.0)
    assert out["gross_profit_to_date"] == pytest.approx(120_000.0)
    assert out["estimated_total_gross_profit"] == pytest.approx(200_000.0)
    assert out["classification"] == "costs_in_excess_of_billings_asset"
    assert out["net_billing_position"] == pytest.approx(20_000.0)


def test_percentage_of_completion_over_billed_matches_hand_calc():
    out = POC.percentage_of_completion(costs_incurred_to_date=600_000.0, total_estimated_costs=1_000_000.0,
                                       contract_price=1_200_000.0, billings_to_date=800_000.0)
    assert out["classification"] == "billings_in_excess_of_costs_liability"
    assert out["net_billing_position"] == pytest.approx(80_000.0)


def test_percentage_of_completion_rejects_non_positive_estimated_costs():
    with pytest.raises(ValueError):
        POC.percentage_of_completion(costs_incurred_to_date=1.0, total_estimated_costs=0.0, contract_price=10.0)


def test_completion_schedule_cumulative_revenue_equals_contract_price_at_100_pct_complete():
    out = POC.completion_schedule(cost_incurred_by_period=[300_000.0, 300_000.0, 400_000.0],
                                  total_estimated_costs=1_000_000.0, contract_price=1_200_000.0)
    assert out["total_costs_incurred"] == pytest.approx(1_000_000.0)
    assert out["total_revenue_recognized"] == pytest.approx(1_200_000.0)  # the self-verifying identity
    assert out["total_gross_profit"] == pytest.approx(200_000.0)
    assert sum(p["current_period_revenue"] for p in out["periods"]) == pytest.approx(1_200_000.0)
    assert out["periods"][-1]["pct_complete"] == pytest.approx(1.0)


def test_completion_schedule_tracks_billings_over_and_under_across_periods():
    out = POC.completion_schedule(cost_incurred_by_period=[500_000.0, 500_000.0],
                                  total_estimated_costs=1_000_000.0, contract_price=1_200_000.0,
                                  billings_by_period=[700_000.0, 500_000.0])
    p1, p2 = out["periods"]
    assert p1["classification"] == "billings_in_excess_of_costs_liability"  # billed 700k vs recognized 600k
    assert p2["revenue_recognized_to_date"] == pytest.approx(1_200_000.0)


def test_from_dict_bundles_everything():
    out = POC.from_dict({"percentage_of_completion": {"costs_incurred_to_date": 100.0, "total_estimated_costs": 200.0, "contract_price": 300.0}})
    assert out["percentage_of_completion"]["pct_complete"] == pytest.approx(0.5)
