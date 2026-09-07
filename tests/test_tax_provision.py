"""finmodel.tax_provision: deferred-tax positions and the effective-rate reconciliation are checked against
hand-computed values; the NOL carryforward schedule is checked for its two defining, real statutory rules --
a pre-2018 balance offsets 100% of income until it expires, a post-2017 balance is capped at 80% of whatever
income remains after that."""
import pytest

from finmodel import tax_provision as TP


def test_deferred_tax_position_matches_hand_calc():
    out = TP.deferred_tax_position({
        "warranty_reserve": {"amount": 100_000.0, "type": "deductible"},
        "accelerated_depreciation": {"amount": 300_000.0, "type": "taxable"},
    }, tax_rate=0.21)
    assert out["gross_dta"] == pytest.approx(21_000.0)
    assert out["gross_dtl"] == pytest.approx(63_000.0)
    assert out["net_deferred_tax"] == pytest.approx(-42_000.0)  # net liability


def test_deferred_tax_position_rejects_bad_type():
    with pytest.raises(ValueError):
        TP.deferred_tax_position({"x": {"amount": 1.0, "type": "bogus"}}, tax_rate=0.21)


def test_valuation_allowance_not_required_absent_cumulative_losses():
    out = TP.valuation_allowance(gross_dta=100_000.0, cumulative_pretax_loss_last_3yrs=0.0,
                                 projected_future_taxable_income=0.0, tax_rate=0.21)
    assert out["valuation_allowance_required"] is False
    assert out["net_dta"] == pytest.approx(100_000.0)


def test_valuation_allowance_caps_dta_at_supportable_future_income():
    out = TP.valuation_allowance(gross_dta=100_000.0, cumulative_pretax_loss_last_3yrs=500_000.0,
                                 projected_future_taxable_income=200_000.0, tax_rate=0.21)
    assert out["valuation_allowance_required"] is True
    assert out["valuation_allowance"] == pytest.approx(100_000.0 - 200_000.0 * 0.21)
    assert out["net_dta"] == pytest.approx(200_000.0 * 0.21)


def test_nol_carryforward_post2017_basket_capped_at_80_pct():
    out = TP.nol_carryforward_schedule(pretax_income=[-100.0, -50.0, 80.0, 80.0], tax_rate=0.21)
    y0, y1, y2, y3 = out["years"]
    assert y0["cash_tax"] == pytest.approx(0.0) and y0["closing_post2017_nol"] == pytest.approx(100.0)
    assert y1["closing_post2017_nol"] == pytest.approx(150.0)
    # year 2: 80 of income, at most 80% (=64) can be offset by the post-2017 basket
    assert y2["used_post2017_nol"] == pytest.approx(64.0)
    assert y2["taxable_income"] == pytest.approx(16.0)
    assert y2["cash_tax"] == pytest.approx(16.0 * 0.21)
    assert y2["closing_post2017_nol"] == pytest.approx(150.0 - 64.0)
    assert y3["used_post2017_nol"] == pytest.approx(64.0)
    assert out["total_cash_tax"] == pytest.approx(y2["cash_tax"] + y3["cash_tax"])


def test_nol_carryforward_pre2018_basket_offsets_100_pct_before_expiring():
    out = TP.nol_carryforward_schedule(pretax_income=[50.0], tax_rate=0.21,
                                       opening_pre2018_nol=30.0, pre2018_nol_years_remaining=1)
    y0 = out["years"][0]
    assert y0["expired_pre2018_nol"] == pytest.approx(0.0)
    assert y0["used_pre2018_nol"] == pytest.approx(30.0)          # full 100% offset, no 80% cap
    assert y0["taxable_income"] == pytest.approx(20.0)             # 50 - 30
    assert y0["closing_pre2018_nol"] == pytest.approx(0.0)


def test_nol_carryforward_pre2018_basket_expires_unused():
    out = TP.nol_carryforward_schedule(pretax_income=[50.0], tax_rate=0.21,
                                       opening_pre2018_nol=30.0, pre2018_nol_years_remaining=0)
    y0 = out["years"][0]
    assert y0["expired_pre2018_nol"] == pytest.approx(30.0)
    assert y0["used_pre2018_nol"] == pytest.approx(0.0)
    assert y0["taxable_income"] == pytest.approx(50.0)             # the expired NOL can no longer offset it
    assert out["total_expired_nol"] == pytest.approx(30.0)


def test_effective_tax_rate_reconciliation_matches_hand_calc():
    out = TP.effective_tax_rate_reconciliation(pretax_income=1_000_000.0, statutory_rate=0.21,
                                               permanent_differences={"meals_nondeductible": 50_000.0,
                                                                      "muni_bond_interest": -30_000.0},
                                               tax_credits=10_000.0)
    assert out["statutory_tax"] == pytest.approx(210_000.0)
    assert out["total_tax"] == pytest.approx(210_000.0 + 50_000.0 * 0.21 - 30_000.0 * 0.21 - 10_000.0)
    assert out["effective_tax_rate"] == pytest.approx(out["total_tax"] / 1_000_000.0)


def test_deferred_tax_rollforward():
    out = TP.deferred_tax_rollforward(beginning_balance=100.0, provision_current_year=50.0,
                                      reversal_current_year=20.0, rate_change_adjustment=5.0)
    assert out["ending_balance"] == pytest.approx(135.0)


def test_from_dict_bundles_everything():
    out = TP.from_dict({
        "deferred_tax_position": {"temporary_differences": {"a": {"amount": 100.0, "type": "deductible"}}, "tax_rate": 0.21},
        "deferred_tax_rollforward": {"beginning_balance": 10.0, "provision_current_year": 5.0, "reversal_current_year": 2.0},
    })
    assert out["deferred_tax_position"]["gross_dta"] == pytest.approx(21.0)
    assert out["deferred_tax_rollforward"]["ending_balance"] == pytest.approx(13.0)
