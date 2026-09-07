"""finmodel.eps_calculation: basic EPS, the treasury stock method, and the if-converted method are each
checked against hand calculations; diluted EPS is checked against a full hand-traced example combining both
dilutive securities, and against the real, defining antidilution rule that a security increasing EPS must be
excluded -- which is also why diluted EPS can never exceed basic EPS."""
import pytest

from finmodel import eps_calculation as EPS


def test_basic_eps_matches_hand_calc():
    out = EPS.basic_eps(net_income=1_000_000.0, preferred_dividends=100_000.0, weighted_average_shares=500_000.0)
    assert out["numerator"] == pytest.approx(900_000.0)
    assert out["basic_eps"] == pytest.approx(1.80)


def test_treasury_stock_method_in_the_money_matches_hand_calc():
    inc_shares = EPS.treasury_stock_method_incremental_shares(options_outstanding=50_000.0, strike_price=20.0, average_market_price=25.0)
    shares_repurchased = 50_000.0 * 20.0 / 25.0
    assert inc_shares == pytest.approx(50_000.0 - shares_repurchased)
    assert inc_shares == pytest.approx(10_000.0)


def test_treasury_stock_method_out_of_the_money_contributes_zero():
    assert EPS.treasury_stock_method_incremental_shares(50_000.0, strike_price=30.0, average_market_price=25.0) == 0.0


def test_if_converted_matches_hand_calc():
    out = EPS.if_converted_incremental_shares_and_addback(convertible_face_value=5_000_000.0, coupon_rate=0.05,
                                                          tax_rate=0.21, total_shares_if_converted=200_000.0)
    assert out["after_tax_interest_addback"] == pytest.approx(5_000_000.0 * 0.05 * (1 - 0.21))
    assert out["incremental_shares"] == pytest.approx(200_000.0)


def test_diluted_eps_full_example_includes_both_dilutive_securities():
    out = EPS.diluted_eps(net_income=1_000_000.0, preferred_dividends=100_000.0, weighted_average_shares=500_000.0,
                          options=[{"options_outstanding": 50_000.0, "strike_price": 20.0, "average_market_price": 25.0}],
                          convertibles=[{"convertible_face_value": 5_000_000.0, "coupon_rate": 0.05, "tax_rate": 0.21,
                                        "total_shares_if_converted": 200_000.0}])
    assert out["basic_eps"] == pytest.approx(1.80)
    expected_numerator = 900_000.0 + 5_000_000.0 * 0.05 * 0.79
    expected_denominator = 500_000.0 + 10_000.0 + 200_000.0
    assert out["diluted_numerator"] == pytest.approx(expected_numerator)
    assert out["diluted_denominator"] == pytest.approx(expected_denominator)
    assert out["diluted_eps"] == pytest.approx(expected_numerator / expected_denominator)
    assert out["diluted_eps"] < out["basic_eps"]
    assert len(out["dilutive_securities_included"]) == 2


def test_diluted_eps_excludes_an_antidilutive_convertible():
    # a high coupon rate and very few shares issued on conversion would INCREASE EPS -> must be excluded
    out = EPS.diluted_eps(net_income=1_000_000.0, preferred_dividends=100_000.0, weighted_average_shares=500_000.0,
                          convertibles=[{"convertible_face_value": 5_000_000.0, "coupon_rate": 0.15, "tax_rate": 0.21,
                                        "total_shares_if_converted": 1_000.0}])
    assert out["diluted_eps"] == pytest.approx(out["basic_eps"])
    assert out["dilutive_securities_included"] == []


def test_from_dict_bundles_everything():
    out = EPS.from_dict({"basic_eps": {"net_income": 100.0, "preferred_dividends": 0.0, "weighted_average_shares": 50.0}})
    assert out["basic_eps"]["basic_eps"] == pytest.approx(2.0)
