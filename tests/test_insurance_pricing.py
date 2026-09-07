"""finmodel.insurance_pricing: combined ratio and operating ratio are checked against their exact real
definitions (including the case where a combined ratio above 100% is still overall profitable once investment
income is counted), and rate-making is checked against the loss-cost-multiplier closed form."""
import pytest

from finmodel import insurance_pricing as I


def test_combined_ratio_matches_hand_calc():
    out = I.combined_ratio(incurred_losses=650.0, underwriting_expenses=300.0, earned_premium=1000.0)
    assert out["loss_ratio"] == 0.65
    assert out["expense_ratio"] == 0.30
    assert out["combined_ratio"] == pytest.approx(0.95)
    assert out["underwriting_profitable"] is True


def test_combined_ratio_above_one_is_not_underwriting_profitable():
    out = I.combined_ratio(incurred_losses=700.0, underwriting_expenses=350.0, earned_premium=1000.0)
    assert out["combined_ratio"] == pytest.approx(1.05)
    assert out["underwriting_profitable"] is False


def test_operating_ratio_can_be_profitable_despite_a_combined_ratio_above_one():
    # the real refinement this metric exists for: a real insurer can run underwriting at a small loss and still
    # be profitable overall once float/investment income is counted.
    out = I.operating_ratio(combined_ratio_value=1.05, investment_income=100.0, earned_premium=1000.0)
    assert out["operating_ratio"] == pytest.approx(0.95)
    assert out["overall_profitable"] is True


def test_rate_making_premium_matches_closed_form():
    out = I.rate_making_premium(pure_premium=500.0, expense_ratio_value=0.25, target_profit_margin=0.05)
    assert out["loss_cost_multiplier"] == pytest.approx(1 / 0.70)
    assert out["gross_premium"] == pytest.approx(500.0 / 0.70)


def test_rate_making_premium_rejects_expenses_plus_margin_at_or_above_one():
    with pytest.raises(ValueError):
        I.rate_making_premium(pure_premium=500.0, expense_ratio_value=0.6, target_profit_margin=0.45)


def test_from_dict_chains_combined_ratio_into_operating_ratio():
    d = {"combined_ratio": {"incurred_losses": 650.0, "underwriting_expenses": 300.0, "earned_premium": 1000.0},
         "operating_ratio": {"investment_income": 80.0, "earned_premium": 1000.0}}
    out = I.from_dict(d)
    assert out["operating_ratio"]["combined_ratio"] == pytest.approx(0.95)
    assert out["operating_ratio"]["operating_ratio"] == pytest.approx(0.87)
