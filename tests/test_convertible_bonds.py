"""finmodel.convertible_bonds: the bond floor is checked against a hand-computed PV, the conversion mechanics
are checked against their exact definitions, and the two-component estimate is checked for the real property
that makes it economically sane -- it must never fall below immediate conversion value."""
import pytest

from finmodel import convertible_bonds as CB


def test_conversion_ratio_and_value():
    ratio = CB.conversion_ratio(par_value=1000.0, conversion_price=50.0)
    assert ratio == 20.0
    assert CB.conversion_value(ratio, stock_price=45.0) == 900.0


def test_conversion_premium():
    assert CB.conversion_premium(bond_price=990.0, conv_value=900.0) == pytest.approx(0.10)


def test_bond_floor_matches_hand_calc_zero_coupon_case():
    # a zero-coupon case is the simplest hand check: bond_floor should just be the PV of principal alone
    out = CB.bond_floor(coupon_rate=0.0, par_value=1000.0, years_to_maturity=2, straight_yield=0.10, coupons_per_year=1)
    assert out["pv_coupons"] == 0.0
    assert out["pv_principal"] == pytest.approx(1000.0 / 1.10 ** 2)
    assert out["bond_floor"] == pytest.approx(1000.0 / 1.10 ** 2)


def test_bond_floor_with_coupons_exceeds_zero_coupon_floor():
    zero = CB.bond_floor(coupon_rate=0.0, par_value=1000.0, years_to_maturity=5, straight_yield=0.06)
    with_coupon = CB.bond_floor(coupon_rate=0.02, par_value=1000.0, years_to_maturity=5, straight_yield=0.06)
    assert with_coupon["bond_floor"] > zero["bond_floor"]


def test_convertible_value_never_falls_below_immediate_conversion_value():
    # the real, exact property: you could always convert right now, so the convertible can never be worth less.
    out = CB.convertible_bond_value(par_value=1000.0, conversion_price=50.0, stock_price=45.0, coupon_rate=0.02,
                                    years_to_maturity=5, straight_yield=0.06, risk_free_rate=0.04, volatility=0.35)
    assert out["estimated_value"] >= out["conversion_value"]


def test_convertible_value_rises_with_stock_price():
    low = CB.convertible_bond_value(par_value=1000.0, conversion_price=50.0, stock_price=30.0, coupon_rate=0.02,
                                    years_to_maturity=5, straight_yield=0.06, risk_free_rate=0.04, volatility=0.35)
    high = CB.convertible_bond_value(par_value=1000.0, conversion_price=50.0, stock_price=70.0, coupon_rate=0.02,
                                     years_to_maturity=5, straight_yield=0.06, risk_free_rate=0.04, volatility=0.35)
    assert high["estimated_value"] > low["estimated_value"]
    assert high["conversion_value"] > low["conversion_value"]


def test_deep_out_of_the_money_convertible_trades_near_its_bond_floor():
    out = CB.convertible_bond_value(par_value=1000.0, conversion_price=200.0, stock_price=5.0, coupon_rate=0.02,
                                    years_to_maturity=5, straight_yield=0.06, risk_free_rate=0.04, volatility=0.35)
    assert out["estimated_value"] == pytest.approx(out["bond_floor"], rel=0.05)


def test_from_dict_computes_conversion_premium_using_computed_conversion_value():
    d = {"convertible_bond_value": {"par_value": 1000.0, "conversion_price": 50.0, "stock_price": 45.0, "coupon_rate": 0.02,
                                    "years_to_maturity": 5, "straight_yield": 0.06, "risk_free_rate": 0.04, "volatility": 0.35},
         "conversion_premium": {"bond_price": 1050.0}}
    out = CB.from_dict(d)
    assert out["conversion_premium"] == pytest.approx(1050.0 / 900.0 - 1)
