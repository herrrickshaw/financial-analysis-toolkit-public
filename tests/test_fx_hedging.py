"""finmodel.fx_hedging: the module's own central claim -- that the forward hedge and the money-market hedge
give EXACTLY the same domestic-currency outcome -- is checked directly for both a receivable and a payable
exposure, alongside a hand calc of the forward rate and forward-hedge value."""
import pytest

from finmodel import fx_hedging as FXH


def test_forward_and_money_market_hedge_match_exactly_for_a_receivable():
    out = FXH.fx_hedge_comparison("receivable", foreign_currency_amount=1_000_000.0, spot_rate=150.0,
                                  domestic_rate=0.03, foreign_rate=0.01, tenor_years=1.0)
    expected_forward_rate = 150.0 * 1.03 / 1.01
    assert out["forward_rate"] == pytest.approx(expected_forward_rate)
    assert out["forward_hedge_value"] == pytest.approx(1_000_000.0 * expected_forward_rate)
    assert out["money_market_hedge_value"] == pytest.approx(out["forward_hedge_value"])


def test_forward_and_money_market_hedge_match_exactly_for_a_payable():
    out = FXH.fx_hedge_comparison("payable", foreign_currency_amount=500_000.0, spot_rate=1.10,
                                  domestic_rate=0.02, foreign_rate=0.045, tenor_years=2.0)
    assert out["money_market_hedge_value"] == pytest.approx(out["forward_hedge_value"], rel=1e-9)


def test_unhedged_value_only_present_when_expected_future_spot_rate_is_given():
    without = FXH.fx_hedge_comparison("receivable", 1_000_000.0, 150.0, 0.03, 0.01, 1.0)
    assert "unhedged_value" not in without
    with_expectation = FXH.fx_hedge_comparison("receivable", 1_000_000.0, 150.0, 0.03, 0.01, 1.0, expected_future_spot_rate=155.0)
    assert with_expectation["unhedged_value"] == pytest.approx(1_000_000.0 * 155.0)


def test_rejects_bad_exposure_type():
    with pytest.raises(ValueError):
        FXH.fx_hedge_comparison("bogus", 1.0, 100.0, 0.03, 0.01, 1.0)


def test_from_dict_bundles_everything():
    out = FXH.from_dict({"fx_hedge_comparison": {"exposure_type": "receivable", "foreign_currency_amount": 1000.0,
                                                 "spot_rate": 80.0, "domestic_rate": 0.05, "foreign_rate": 0.02, "tenor_years": 1.0}})
    assert out["fx_hedge_comparison"]["forward_hedge_value"] > 0
