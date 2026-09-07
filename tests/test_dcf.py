"""Reconcile to cached values of the CFI 'DCF Model Template (Updated)'."""
import math
import pytest
from finmodel import dcf


def test_reconciles_to_cfi_workbook(dcf_inputs):
    inp = dcf.DCFInputs(**dcf.clean(dcf_inputs))
    r = dcf.run(inp)
    assert r["year_fraction"][0] == pytest.approx(0.5)
    assert r["year_fraction"][1:] == pytest.approx([1, 1, 1, 1])
    assert r["ufcf"] == pytest.approx([35494.262, 37715.192065, 41501.0737282, 43510.4616657, 47008.0299436], rel=1e-9)
    tv = r["terminal_value"]
    assert tv["perpetuity_growth"] == pytest.approx(537980.7871321079)
    assert tv["ev_ebitda"] == pytest.approx(546277.7332654343)
    assert tv["used"] == pytest.approx(542129.260198771)
    assert r["enterprise_value"] == pytest.approx(462982.9754462675, rel=1e-9)
    assert r["equity_value"] == pytest.approx(672532.4958114524, rel=1e-9)
    assert r["equity_value_per_share"] == pytest.approx(33.62662479057262, rel=1e-9)
    assert r["market"]["enterprise_value"] == pytest.approx(290450.4796348151)
    assert r["target_price_upside"] == pytest.approx(0.3450649916229047, rel=1e-9)
    assert r["irr"] == pytest.approx(0.2634776532649994, abs=1e-7)
    assert r["dates"] == ["2017-12-31", "2018-06-30", "2019-06-30", "2020-06-30", "2021-06-30", "2022-06-30"]


def test_terminal_methods_and_sensitivity(dcf_inputs):
    base = {k: v for k, v in dcf_inputs.items() if not k.startswith("_")}
    p = dcf.run(dcf.DCFInputs(**{**base, "terminal_method": "perpetuity"}))
    m = dcf.run(dcf.DCFInputs(**{**base, "terminal_method": "multiple"}))
    a = dcf.run(dcf.DCFInputs(**base))
    assert min(p["enterprise_value"], m["enterprise_value"]) < a["enterprise_value"] < max(p["enterprise_value"], m["enterprise_value"])
    s = dcf.sensitivity(dcf.DCFInputs(**base), [0.10, 0.12, 0.14], [0.02, 0.03, 0.04])
    assert s["table"][1][1] == pytest.approx(a["equity_value_per_share"])
    assert s["table"][0][2] > s["table"][2][0]  # low WACC / high g is worth more
    with pytest.raises(ValueError):
        dcf.run(dcf.DCFInputs(**{**base, "discount_rate": 0.02}))


def test_capex_list_and_fye_feb29():
    inp = dcf.DCFInputs(ebit=[100, 100], da=[10, 10], change_nwc=[0, 0], capex=[5, 6], transaction_date="2023-12-31", fiscal_year_end="2024-02-29")
    r = dcf.run(inp)
    assert r["capex"] == [5, 6]
    assert r["dates"][1:] == ["2024-02-29", "2025-02-28"]


def test_reverse_dcf_and_monte_carlo():
    import json, pathlib
    from finmodel import dcf
    d = json.loads((pathlib.Path(__file__).resolve().parent.parent / "examples" / "cfi_dcf.json").read_text())
    inp = dcf.DCFInputs(**dcf.clean(d))
    rg = dcf.implied_growth(inp)
    assert rg["implied_growth"] is not None and -0.2 <= rg["implied_growth"] < inp.discount_rate
    # plugging the implied growth back in reproduces the price under the perpetuity method
    import copy
    x = copy.copy(inp); x.terminal_method = "perpetuity"; x.perpetual_growth = rg["implied_growth"]
    assert abs(dcf.run(x)["equity_value_per_share"] - inp.current_price) < 1e-6
    mc = dcf.monte_carlo(inp, runs=300, seed=1)
    assert mc["runs"] == 300 and mc["percentiles"][5] <= mc["median"] <= mc["percentiles"][95]
    assert 0 <= mc["prob_value_above_price"] <= 1 and sum(mc["histogram"]["counts"]) == 300
    assert dcf.monte_carlo(inp, runs=50, seed=1)["median"] == dcf.monte_carlo(inp, runs=50, seed=1)["median"]   # seeded → reproducible


def test_mid_year_convention_raises_value():
    import json, pathlib, copy
    from finmodel import dcf
    d = json.loads((pathlib.Path(__file__).resolve().parent.parent / "examples" / "cfi_dcf.json").read_text())
    inp = dcf.DCFInputs(**dcf.clean(d)); base = dcf.run(inp)
    x = copy.copy(inp); x.mid_year = True; mid = dcf.run(x)
    assert mid["mid_year"] and mid["enterprise_value"] > base["enterprise_value"]
    # the uplift is bounded by half a period of discounting on the explicit cash flows
    pv_fcf_base = base["enterprise_value"] - base["terminal_value"]["used"] / (1 + inp.discount_rate) ** sum(base["year_fraction"])
    assert 0 < mid["enterprise_value"] - base["enterprise_value"] < pv_fcf_base * ((1 + inp.discount_rate) ** 0.5 - 1) * 1.05


def test_unlevered_tax_schedule_matches_hand_calc_with_a_loss_carryforward():
    ebit = [-100.0, 200.0, 200.0]
    out = dcf.unlevered_tax_schedule(ebit, tax_rate=0.25)
    assert out[0] == 0.0                       # a loss pays no tax
    assert out[1] == pytest.approx(25.0)        # (200 - 100 loss c/f) * 0.25
    assert out[2] == pytest.approx(50.0)        # no losses left; full 200 * 0.25


def test_check_unlevered_tax_consistency_flags_a_real_double_counted_shield():
    # real, verified reference case from this toolkit's own due-diligence pass on a project-finance model:
    # EBIT and the ACTUAL (levered, after-interest) cash tax the model deducted from an otherwise-unlevered FCF.
    ebit = [-89463, 257821, 343071, 405138, 446838, 570578, 557578, 544578, 531578, 518578]
    levered_tax_used = [0, 29790.71, 80058.47, 96401.02, 107635.20, 139537.31, 137040.88, 134563.84, 132106.68, 129669.89]
    out = dcf.check_unlevered_tax_consistency(ebit, levered_tax_used, tax_rate=0.2517)
    assert out["likely_uses_levered_tax"] is True
    assert out["total_gap_undiscounted"] == pytest.approx(41716, abs=1)


def test_check_unlevered_tax_consistency_passes_a_correctly_unlevered_build():
    ebit = [-100.0, 200.0, 200.0]
    correct_tax = dcf.unlevered_tax_schedule(ebit, tax_rate=0.25)
    out = dcf.check_unlevered_tax_consistency(ebit, correct_tax, tax_rate=0.25)
    assert out["likely_uses_levered_tax"] is False
    assert out["flagged_periods"] == []
    assert out["total_gap_undiscounted"] == pytest.approx(0.0)


def test_check_unlevered_tax_consistency_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        dcf.check_unlevered_tax_consistency([100.0, 200.0], [25.0], tax_rate=0.25)
