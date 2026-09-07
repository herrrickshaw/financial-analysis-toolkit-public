"""finmodel.startup_model: the three-statement wiring balances (including two real regressions found while
building it — a non-cash PP&E contribution, and a mid-stream funding round), the DCF translation runs, and the
sector benchmark reads real, already-committed peer data rather than a fabricated "typical startup" range."""
import json
from pathlib import Path

import pytest

from finmodel import startup_model as SM

ROOT = Path(__file__).resolve().parent.parent


def _base_inputs(**overrides):
    kwargs = dict(name="Test Co.", forecast_years=3, year0_revenue=100_000,
                  revenue_growth=[2.0, 1.0, 0.5], gross_margin=0.7, payroll_pct_revenue=0.5,
                  other_opex_pct_revenue=0.2, starting_cash=500_000)
    kwargs.update(overrides)
    return SM.StartupInputs(**kwargs)


def test_balances_with_plain_cash_seed():
    r = SM.build_three_statement(_base_inputs())
    assert r.balanced
    assert all(abs(x) < 1e-6 for x in r.rows["Balance Sheet Check"])


def test_balances_with_a_non_cash_ppe_contribution():
    # regression: an earlier version gave the seed year free PP&E with no matching capex/financing entry,
    # which balanced the balance sheet's two totals individually but broke the cash roll-forward (the
    # cash-flow statement's computed closing cash didn't match the given starting_cash) -- a constant
    # Balance Sheet Check offset exactly equal to starting_ppe.
    r = SM.build_three_statement(_base_inputs(starting_ppe=150_000))
    assert r.balanced
    assert r.rows["Cash"][0] == 500_000
    assert r.rows["Closing Cash Balance"][0] == pytest.approx(500_000)


def test_balances_with_a_mid_stream_funding_round():
    r = SM.build_three_statement(_base_inputs(equity_raised={1: 8_000_000}))
    assert r.balanced
    # equity_raised uses a 0-based forecast-year index; index 1 is the SECOND forecast year (row index n_hist+1)
    n_h = r.n_hist
    assert r.rows["Issuance (repayment) of equity"][n_h + 1] == 8_000_000
    assert r.rows["Issuance (repayment) of equity"][n_h] == 0.0


def test_revenue_path_mode_produces_the_exact_requested_revenue():
    path = [800_000, 2_500_000, 6_000_000]
    r = SM.build_three_statement(_base_inputs(revenue_growth=None, revenue_path=path, year0_revenue=200_000))
    n_h = r.n_hist
    assert r.rows["Revenue"][n_h:] == pytest.approx(path)


def test_revenue_path_rejects_a_zero_prior_year_base():
    with pytest.raises(ValueError, match="zero prior-year base"):
        SM.build_three_statement(_base_inputs(revenue_growth=None, revenue_path=[1.0, 2.0, 3.0], year0_revenue=0.0))


def test_dcf_from_projection_runs_and_produces_a_finite_value():
    r = SM.build_three_statement(_base_inputs())
    d = SM.dcf_from_projection(r, discount_rate=0.25, shares_outstanding=1_000_000)
    assert d["value_per_share"] == d["equity_value"] / 1_000_000
    for key in ("enterprise_value", "equity_value", "value_per_share"):
        assert d[key] == d[key]  # not NaN


def test_dcf_from_projection_ebit_adds_back_interest():
    # with real, nonzero debt/interest in the projection, the DCF's unlevered EBIT must exceed EBT by exactly
    # the interest expense for every forecast year -- confirms the add-back, not just that both numbers exist.
    r = SM.build_three_statement(_base_inputs(debt_raised={0: 1_000_000}, interest_pct_debt=0.08))
    n_h = r.n_hist
    interest = r.rows["Interest"][n_h:]
    assert any(v > 0 for v in interest), "test precondition: interest should be nonzero at least one year"
    ebt = r.rows["Earnings Before Tax"][n_h:]
    d = SM.dcf_from_projection(r, discount_rate=0.25)
    # dcf_from_projection doesn't expose its internal ebit list, so recompute the same way it does and compare
    ebit_expected = [ebt[i] + interest[i] for i in range(len(ebt))]
    from finmodel.dcf import DCFInputs, run as dcf_run
    inp = DCFInputs(ebit=ebit_expected, da=r.rows["Depreciation & Amortization"][n_h:], change_nwc=r.rows["Change in NWC"][n_h:],
                    capex=r.rows["Plus Capex"][n_h:], tax_rate=0.21, discount_rate=0.25, current_price=1.0,
                    shares_outstanding=1_000_000, debt=r.rows["Debt"][n_h - 1], cash=r.rows["Cash"][n_h - 1],
                    transaction_date="2026-01-01", fiscal_year_end="2026-12-31",
                    terminal_method="perpetuity")  # match dcf_from_projection's own defaults (DCFInputs itself defaults to "average")
    expected = dcf_run(inp)
    assert d["equity_value"] == pytest.approx(expected["equity_value"])


def test_benchmark_against_sector_reads_real_committed_peer_data():
    r = SM.build_three_statement(_base_inputs(forecast_years=1, revenue_growth=[0.0]))
    b = SM.benchmark_against_sector(r, "software")
    assert b["sector"] == "software"
    assert "CSCO" in b["real_peer_margins"]
    # cross-check one real peer's margin directly against the committed extract, not against this module's own math
    csco = json.loads((ROOT / "data" / "edgar" / "CSCO.json").read_text())["years"]
    latest_fy = sorted(csco)[-1]
    row = csco[latest_fy]
    expected_margin = row["operating_income"] / row["revenue"]
    assert b["real_peer_margins"]["CSCO"]["margin"] == pytest.approx(expected_margin)


def test_benchmark_flags_a_margin_outside_the_real_range():
    # 0% terminal margin (revenue_growth=[0,0,0] with cogs==revenue always) is below every real software peer
    r = SM.build_three_statement(_base_inputs(gross_margin=0.0, payroll_pct_revenue=1.0, other_opex_pct_revenue=1.0))
    b = SM.benchmark_against_sector(r, "software")
    assert b["inside_real_range"] is False
    assert "OUTSIDE" in b["note"]


def test_benchmark_rejects_an_unknown_sector_rather_than_fabricating_one():
    r = SM.build_three_statement(_base_inputs())
    with pytest.raises(ValueError, match="no real peer data"):
        SM.benchmark_against_sector(r, "quantum_computing")


def test_from_dict_end_to_end_with_the_bundled_example():
    d = json.loads((ROOT / "examples" / "startup_saas.json").read_text())
    out = SM.from_dict(d)
    assert out["three_statement"]["balanced"] is True
    assert out["dcf"]["equity_value"] == out["dcf"]["equity_value"]  # not NaN
    assert out["benchmark"]["sector"] == "software"
