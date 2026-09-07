"""finmodel.fixed_income_risk: checked against the classic textbook reference bond (a 2-year, 10%-coupon,
annual-pay bond priced at par when the yield equals the coupon, with Macaulay duration ~1.91 years), against
the real property that a longer-maturity bond at the same coupon/yield has strictly higher duration, and
against the exact identity that a zero-coupon bond's Macaulay duration equals its own maturity."""
import pytest

from finmodel import fixed_income_risk as FIR


def test_two_year_ten_percent_par_bond_matches_the_classic_textbook_reference():
    out = FIR.bond_price_and_duration(cash_flows=[10.0, 110.0], yield_rate=0.10, periods_per_year=1)
    assert out["price"] == pytest.approx(100.0, abs=1e-6)  # coupon == yield -> priced at par
    assert out["macaulay_duration_years"] == pytest.approx(1.9091, abs=1e-3)
    assert out["modified_duration"] == pytest.approx(1.9091 / 1.10, abs=1e-3)
    assert out["dv01"] == pytest.approx(out["modified_duration"] * 100.0 * 0.0001, abs=1e-6)


def test_longer_maturity_bond_has_strictly_higher_duration():
    short = FIR.bond_price_and_duration(cash_flows=[10.0, 110.0], yield_rate=0.10, periods_per_year=1)
    long = FIR.bond_price_and_duration(cash_flows=[10.0, 10.0, 10.0, 10.0, 110.0], yield_rate=0.10, periods_per_year=1)
    assert long["macaulay_duration_years"] > short["macaulay_duration_years"]


def test_zero_coupon_bond_duration_equals_its_own_maturity():
    out = FIR.bond_price_and_duration(cash_flows=[0.0, 0.0, 0.0, 100.0], yield_rate=0.05, periods_per_year=1)
    assert out["macaulay_duration_years"] == pytest.approx(4.0)
    assert out["price"] == pytest.approx(100.0 / 1.05 ** 4)


def test_from_dict_bundles_everything():
    out = FIR.from_dict({"bond_price_and_duration": {"cash_flows": [10.0, 110.0], "yield_rate": 0.10, "periods_per_year": 1}})
    assert out["bond_price_and_duration"]["price"] == pytest.approx(100.0, abs=1e-6)
