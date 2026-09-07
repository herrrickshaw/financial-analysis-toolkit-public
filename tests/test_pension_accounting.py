"""finmodel.pension_accounting: the PBO and plan-asset roll-forwards, funded status, and net periodic cost
are each checked against hand calculations, then combined into one coherent end-to-end period using the same
underlying numbers to confirm the pieces fit together; asset_gain_loss is checked against the real, defining
gap between actual and expected returns that the net periodic cost calculation deliberately smooths over."""
import pytest

from finmodel import pension_accounting as PA


def test_pbo_rollforward_matches_hand_calc():
    out = PA.pbo_rollforward(beginning_pbo=1_000_000.0, service_cost=80_000.0, discount_rate=0.05,
                             benefits_paid=60_000.0, actuarial_gain_loss=20_000.0)
    assert out["interest_cost"] == pytest.approx(50_000.0)
    assert out["ending_pbo"] == pytest.approx(1_000_000.0 + 80_000.0 + 50_000.0 - 60_000.0 + 20_000.0)


def test_plan_assets_rollforward_matches_hand_calc():
    out = PA.plan_assets_rollforward(beginning_plan_assets=900_000.0, actual_return_on_assets=70_000.0,
                                     employer_contributions=50_000.0, benefits_paid=60_000.0)
    assert out["ending_plan_assets"] == pytest.approx(900_000.0 + 70_000.0 + 50_000.0 - 60_000.0)


def test_funded_status_classifies_underfunded_and_overfunded():
    under = PA.funded_status(ending_plan_assets=960_000.0, ending_pbo=1_090_000.0)
    assert under["funded_status"] == pytest.approx(-130_000.0)
    assert under["classification"] == "underfunded"
    over = PA.funded_status(ending_plan_assets=1_200_000.0, ending_pbo=1_090_000.0)
    assert over["classification"] == "overfunded"


def test_net_periodic_pension_cost_matches_hand_calc():
    out = PA.net_periodic_pension_cost(service_cost=80_000.0, beginning_pbo=1_000_000.0, discount_rate=0.05,
                                       beginning_plan_assets=900_000.0, expected_return_rate=0.07)
    assert out["interest_cost"] == pytest.approx(50_000.0)
    assert out["expected_return_on_assets"] == pytest.approx(63_000.0)
    assert out["net_periodic_pension_cost"] == pytest.approx(80_000.0 + 50_000.0 - 63_000.0)


def test_asset_gain_loss_is_the_gap_between_actual_and_expected_return():
    assert PA.asset_gain_loss(actual_return_on_assets=70_000.0, expected_return_on_assets=63_000.0) == pytest.approx(7_000.0)
    assert PA.asset_gain_loss(actual_return_on_assets=40_000.0, expected_return_on_assets=63_000.0) == pytest.approx(-23_000.0)


def test_full_period_roll_forward_is_internally_consistent():
    pbo = PA.pbo_rollforward(beginning_pbo=1_000_000.0, service_cost=80_000.0, discount_rate=0.05, benefits_paid=60_000.0)
    assets = PA.plan_assets_rollforward(beginning_plan_assets=900_000.0, actual_return_on_assets=70_000.0,
                                        employer_contributions=50_000.0, benefits_paid=60_000.0)
    status = PA.funded_status(assets["ending_plan_assets"], pbo["ending_pbo"])
    cost = PA.net_periodic_pension_cost(service_cost=80_000.0, beginning_pbo=1_000_000.0, discount_rate=0.05,
                                        beginning_plan_assets=900_000.0, expected_return_rate=0.07)
    gain_loss = PA.asset_gain_loss(assets["actual_return_on_assets"], cost["expected_return_on_assets"])
    assert status["ending_pbo"] == pytest.approx(pbo["ending_pbo"])
    assert gain_loss == pytest.approx(assets["actual_return_on_assets"] - cost["expected_return_on_assets"])


def test_from_dict_bundles_everything():
    out = PA.from_dict({"funded_status": {"ending_plan_assets": 100.0, "ending_pbo": 120.0}})
    assert out["funded_status"]["classification"] == "underfunded"
