"""finmodel.bond_amortization: the issue price and first-period interest expense are checked against an
independent recomputation of the same formulas; the module is checked for correctly classifying a discount
versus a premium bond from the coupon-vs-market-rate comparison; and, for both cases, checked against the
real, defining identity that the carrying value converges to EXACTLY the face value by the final period."""
import pytest

from finmodel import bond_amortization as BA


def test_discount_bond_issue_price_and_first_period_matches_independent_calc():
    face, coupon, market, periods, ppy = 1_000_000.0, 0.08, 0.10, 10, 2
    out = BA.bond_amortization_schedule(face, coupon, market, periods, ppy)
    coupon_per_period = face * coupon / ppy
    market_rate_per_period = market / ppy
    expected_issue_price = sum(coupon_per_period / (1 + market_rate_per_period) ** (i + 1) for i in range(periods)) + \
        face / (1 + market_rate_per_period) ** periods
    assert out["issue_price"] == pytest.approx(expected_issue_price)
    assert out["issued_at"] == "discount"
    assert out["issue_price"] < face
    first = out["schedule"][0]
    assert first["interest_expense"] == pytest.approx(expected_issue_price * market_rate_per_period)
    assert first["cash_interest_paid"] == pytest.approx(coupon_per_period)


def test_discount_bond_carrying_value_increases_toward_face_and_ends_exactly_at_par():
    out = BA.bond_amortization_schedule(face_value=1_000_000.0, coupon_rate=0.08, market_rate=0.10, periods=10, periods_per_year=2)
    values = [row["carrying_value"] for row in out["schedule"]]
    assert values == sorted(values)  # strictly increasing toward face value
    assert out["schedule"][-1]["carrying_value"] == pytest.approx(1_000_000.0, abs=1e-4)


def test_premium_bond_carrying_value_decreases_toward_face_and_ends_exactly_at_par():
    out = BA.bond_amortization_schedule(face_value=1_000_000.0, coupon_rate=0.10, market_rate=0.08, periods=10, periods_per_year=2)
    assert out["issued_at"] == "premium"
    assert out["issue_price"] > 1_000_000.0
    values = [row["carrying_value"] for row in out["schedule"]]
    assert values == sorted(values, reverse=True)  # strictly decreasing toward face value
    assert out["schedule"][-1]["carrying_value"] == pytest.approx(1_000_000.0, abs=1e-4)


def test_par_bond_has_no_premium_or_discount():
    out = BA.bond_amortization_schedule(face_value=1_000_000.0, coupon_rate=0.08, market_rate=0.08, periods=10, periods_per_year=2)
    assert out["issued_at"] == "par"
    assert out["issue_price"] == pytest.approx(1_000_000.0)
    assert all(row["amortization"] == pytest.approx(0.0, abs=1e-6) for row in out["schedule"])


def test_from_dict_bundles_everything():
    out = BA.from_dict({"bond_amortization_schedule": {"face_value": 1000.0, "coupon_rate": 0.05, "market_rate": 0.06, "periods": 4}})
    assert out["bond_amortization_schedule"]["issued_at"] == "discount"
