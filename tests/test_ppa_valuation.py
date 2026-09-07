"""finmodel.ppa_valuation: relief-from-royalty and MPEEM are checked against hand-computed present values before
the Tax Amortization Benefit gross-up, then the TAB factor itself is checked against its closed-form definition,
and allocate() is checked for the real ASC 805 residual property (goodwill = price - net identifiable assets)."""
import pytest

from finmodel import ppa_valuation as PPA


def test_tab_factor_matches_closed_form():
    r, t, n = 0.12, 0.25, 15
    pva = sum(1 / (1 + r) ** i for i in range(1, n + 1))
    expected = 1 / (1 - t * pva / n)
    assert PPA.tab_factor(r, t, n) == pytest.approx(expected)


def test_tab_factor_is_greater_than_one():
    # the whole point of TAB: it grosses UP the pre-tax-benefit value, never down
    assert PPA.tab_factor(0.10, 0.25, 15) > 1.0


def test_relief_from_royalty_pv_before_tab_matches_hand_calc():
    out = PPA.relief_from_royalty(revenue=[100.0, 100.0], royalty_rate=0.05, tax_rate=0.20, discount_rate=0.10, include_tab=False)
    # after-tax royalty = 100*0.05*0.8 = 4.0 each year; PV = 4/1.1 + 4/1.1**2
    assert out["pv_before_tab"] == pytest.approx(4.0 / 1.1 + 4.0 / 1.1 ** 2)
    assert out["value"] == out["pv_before_tab"]  # TAB excluded -> value equals the raw PV
    assert out["tab_factor"] == 1.0


def test_relief_from_royalty_with_tab_is_larger():
    with_tab = PPA.relief_from_royalty(revenue=[100.0] * 5, royalty_rate=0.03, tax_rate=0.25, discount_rate=0.12, include_tab=True)
    without_tab = PPA.relief_from_royalty(revenue=[100.0] * 5, royalty_rate=0.03, tax_rate=0.25, discount_rate=0.12, include_tab=False)
    assert with_tab["value"] > without_tab["value"]
    assert with_tab["pv_before_tab"] == without_tab["pv_before_tab"]


def test_mpeem_excess_earnings_deducts_contributory_asset_charges():
    out = PPA.mpeem(operating_income=[10.0, 10.0], contributory_asset_charges=[3.0, 3.0], tax_rate=0.20, discount_rate=0.10, include_tab=False)
    assert out["excess_earnings_pretax"] == [7.0, 7.0]
    assert out["excess_earnings_aftertax"] == pytest.approx([5.6, 5.6])
    assert out["pv_before_tab"] == pytest.approx(5.6 / 1.1 + 5.6 / 1.1 ** 2)


def test_mpeem_mismatched_lengths_raises():
    with pytest.raises(ValueError):
        PPA.mpeem(operating_income=[1.0, 2.0], contributory_asset_charges=[1.0], tax_rate=0.2, discount_rate=0.1)


def test_contributory_asset_charge_sums_fair_value_times_required_return():
    assets = {"working_capital": (10.0, 0.05), "fixed_assets": (20.0, 0.08)}
    assert PPA.contributory_asset_charge(assets) == pytest.approx(10.0 * 0.05 + 20.0 * 0.08)


def test_cost_approach_applies_obsolescence():
    out = PPA.cost_approach(replacement_cost=100.0, obsolescence_pct=0.25)
    assert out["value"] == 75.0


def test_allocate_goodwill_is_the_real_asc805_residual():
    out = PPA.allocate(purchase_price=1000.0, net_identifiable_assets_fair_value=400.0, intangible_values={"trade_name": 100.0, "customer_relationships": 200.0})
    assert out["total_intangibles"] == 300.0
    assert out["total_identifiable_assets"] == 700.0
    assert out["goodwill"] == 300.0
    assert out["intangibles_writeup"] == 300.0  # feeds directly into finmodel.merger.PPA


def test_allocate_can_produce_negative_goodwill_a_real_bargain_purchase_signal():
    # ASC 805-30-25: if identifiable net assets exceed the price, it's a real (rare) "bargain purchase" gain, not
    # an error to hide -- allocate() should report the negative value plainly rather than clamping it to zero.
    out = PPA.allocate(purchase_price=100.0, net_identifiable_assets_fair_value=150.0, intangible_values={})
    assert out["goodwill"] == -50.0


def test_from_dict_wires_method_outputs_into_allocation():
    d = {"relief_from_royalty": {"trade_name": {"revenue": [10.0, 10.0], "royalty_rate": 0.05, "tax_rate": 0.25, "discount_rate": 0.10, "include_tab": False}},
         "cost_approach": {"workforce": {"replacement_cost": 5.0}},
         "allocation": {"purchase_price": 100.0, "net_identifiable_assets_fair_value": 50.0}}
    out = PPA.from_dict(d)
    expected_trade_name = out["relief_from_royalty"]["trade_name"]["value"]
    expected_workforce = out["cost_approach"]["workforce"]["value"]
    assert out["allocation"]["intangible_values"]["trade_name"] == pytest.approx(expected_trade_name)
    assert out["allocation"]["intangible_values"]["workforce"] == pytest.approx(expected_workforce)
    assert out["allocation"]["goodwill"] == pytest.approx(100.0 - 50.0 - expected_trade_name - expected_workforce)
