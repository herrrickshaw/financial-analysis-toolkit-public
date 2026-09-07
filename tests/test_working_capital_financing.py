"""finmodel.working_capital_financing: factoring economics and the early-payment-discount APR are checked
against hand-computed values (the discount APR case reproduces the textbook "2/10, net 30" example), and
the ABL borrowing-base calculation is checked against a hand-computed advance-rate blend."""
import pytest

from finmodel import working_capital_financing as WCF


def test_factoring_cost_matches_hand_calc():
    out = WCF.factoring_cost(invoice_amount=100_000.0, advance_rate=0.80, discount_fee_pct=0.02, days_to_collect=30.0)
    assert out["advance_amount"] == pytest.approx(80_000.0)
    assert out["fee_amount"] == pytest.approx(2_000.0)
    assert out["reserve_released"] == pytest.approx(18_000.0)
    assert out["net_proceeds"] == pytest.approx(98_000.0)  # invoice less the fee, regardless of advance timing
    assert out["effective_annual_rate"] == pytest.approx((2_000.0 / 80_000.0) * (365.0 / 30.0))


def test_early_payment_discount_apr_matches_the_classic_2_10_net_30_example():
    apr = WCF.early_payment_discount_apr(discount_pct=0.02, discount_days=10, net_days=30)
    assert apr == pytest.approx((0.02 / 0.98) * (365.0 / 20.0))
    assert apr == pytest.approx(0.3724, abs=1e-3)  # ~37.2%, the standard textbook figure for these terms


def test_early_payment_discount_apr_rejects_non_positive_window():
    with pytest.raises(ValueError):
        WCF.early_payment_discount_apr(discount_pct=0.02, discount_days=30, net_days=30)


def test_asset_based_lending_availability_matches_hand_calc():
    out = WCF.asset_based_lending_availability(ar_balance=1_000_000.0, ar_advance_rate=0.85,
                                               inventory_balance=500_000.0, inventory_advance_rate=0.50,
                                               existing_draws=600_000.0)
    assert out["borrowing_base"] == pytest.approx(850_000.0 + 250_000.0)
    assert out["available_to_draw"] == pytest.approx(1_100_000.0 - 600_000.0)


def test_from_dict_bundles_everything():
    out = WCF.from_dict({
        "factoring_cost": {"invoice_amount": 1000.0, "advance_rate": 0.8, "discount_fee_pct": 0.02, "days_to_collect": 30.0},
        "early_payment_discount_apr": {"discount_pct": 0.01, "discount_days": 10, "net_days": 60},
    })
    assert out["factoring_cost"]["advance_amount"] == pytest.approx(800.0)
    assert out["early_payment_discount_apr"] == pytest.approx((0.01 / 0.99) * (365.0 / 50.0))
