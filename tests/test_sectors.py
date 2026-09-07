"""Tests for finmodel.sectors, including regression checks against the real committed EDGAR extracts that the
football-field docs (docs/FOOTBALL_FIELD_STLD.md, docs/FOOTBALL_FIELD_CVX.md) found were cycle-distorted by hand —
this module should flag the same years as trough/peak automatically."""
import json
from pathlib import Path

import pytest

from finmodel import sectors

ROOT = Path(__file__).resolve().parent.parent


def synthetic_history(margins, revenue=1000.0):
    """years 2018..2018+len-1, revenue flat, EBIT = margin * revenue, no D&A."""
    return {f"{2018+i}-12-31": {"revenue": revenue, "operating_income": revenue * m} for i, m in enumerate(margins)}


def test_normalize_metric_uses_trailing_window_and_method():
    h = {f"{2018+i}-12-31": {"operating_income": v} for i, v in enumerate([10, 20, 30, 40, 50])}
    r = sectors.normalize_metric(h, "operating_income", periods=3, method="median")
    assert r["periods_used"] == ["2020-12-31", "2021-12-31", "2022-12-31"] and r["value"] == 40
    assert sectors.normalize_metric(h, "operating_income", periods=3, method="mean")["value"] == pytest.approx(40)
    assert sectors.normalize_metric(h, "operating_income", periods=2, method="max")["value"] == 50
    with pytest.raises(ValueError):
        sectors.normalize_metric({}, "operating_income")


def test_cycle_diagnostics_flags_trough_and_peak_on_synthetic_cycle():
    # a steady 10% margin except one deep trough year
    h = synthetic_history([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.03])
    d = sectors.cycle_diagnostics(h, periods=8, sector="steel")
    assert d["fiscal_year"] == "2025-12-31" and "trough" in d["flag"] and d["deviation_pct"] < -0.20
    # a steady margin except one spike-peak year
    h2 = synthetic_history([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.30])
    d2 = sectors.cycle_diagnostics(h2, periods=8, sector="oil_gas")
    assert "peak" in d2["flag"] and d2["deviation_pct"] > 0.20
    # a genuinely unremarkable year
    h3 = synthetic_history([0.10, 0.11, 0.09, 0.10, 0.11, 0.09, 0.10, 0.105])
    assert sectors.cycle_diagnostics(h3, periods=8)["flag"] == "near normal"


def test_dcf_scenarios_from_history_matches_trailing_extremes():
    h = synthetic_history([0.05, 0.10, 0.15, 0.20, 0.08])
    s = sectors.dcf_scenarios_from_history(h, periods=5)
    assert s["current_margin"] == pytest.approx(0.08) and s["base_margin"] == pytest.approx(0.10)
    assert s["bear_margin"] == pytest.approx(0.05) and s["blue_sky_margin"] == pytest.approx(0.20)


def test_sector_beta_and_profile_fallback():
    assert sectors.sector_beta("steel") == sectors.SECTOR_PROFILES["steel"].unlevered_beta
    assert sectors.sector_beta("some_sector_nobody_has_analysed") == sectors.SECTOR_PROFILES["default"].unlevered_beta


def test_normalized_comps_metrics_only_normalizes_margin_lines():
    h = synthetic_history([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.03])
    for y in h: h[y]["da"] = 50.0; h[y]["net_income"] = h[y]["operating_income"] * 0.7
    m = sectors.normalized_comps_metrics(h, sector="steel")
    latest = sorted(h)[-1]
    assert m["revenue"] == h[latest]["revenue"] and m["net_income"] == h[latest]["net_income"]   # not normalized
    assert m["ebit"] == pytest.approx(100.0) and m["ebit"] != h[latest]["operating_income"]        # normalized (median of steady 10% years)


def test_from_dict_bundles_everything():
    h = synthetic_history([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.03])
    out = sectors.from_dict({"history": h, "sector": "steel", "periods": 8})
    assert set(out) == {"cycle_diagnostics", "dcf_scenarios", "normalized_metrics", "sector_profile"}
    assert out["sector_profile"]["name"] == "Steel / metals & mining"


# ---- regression: the real EDGAR data behind the two published football-field checks
def _real_history(ticker):
    return json.loads((ROOT / "data" / "edgar" / f"{ticker}.json").read_text())["years"]


def test_stld_fy2025_flags_as_trough_on_real_data():
    d = sectors.cycle_diagnostics(_real_history("STLD"), periods=8, sector="steel")
    assert d["fiscal_year"] == "2025-12-31" and "trough" in d["flag"]


def test_pxd_fy2022_flags_as_peak_on_real_data():
    d = sectors.cycle_diagnostics(_real_history("PXD"), periods=8, sector="oil_gas", as_of="2022-12-31")
    assert d["fiscal_year"] == "2022-12-31" and "peak" in d["flag"]


def test_cvx_own_cycle_is_wide_and_current_year_below_median():
    d = sectors.cycle_diagnostics(_real_history("CVX"), periods=8, sector="oil_gas")
    assert d["fiscal_year"] == "2025-12-31"
    assert d["median_margin_trailing_years"] > d["latest_margin"]   # 2025 sits below Chevron's own trailing median margin


def test_trend_diagnostics_detects_strong_monotonic_trend():
    up = synthetic_history([0.02, 0.03, 0.04, 0.08, 0.10, 0.14, 0.17, 0.20])   # a Salesforce-shaped ramp
    t = sectors.trend_diagnostics(up, periods=8)
    assert t["trend_strength"] == "strong" and t["direction"] == "improving" and t["correlation"] > 0.9 and t["warning"]
    down = synthetic_history([0.20, 0.17, 0.14, 0.10, 0.08, 0.04, 0.03, 0.02])
    assert sectors.trend_diagnostics(down, periods=8)["direction"] == "declining"


def test_trend_diagnostics_weak_on_noisy_or_cyclical_data():
    h = synthetic_history([0.10, 0.15, 0.09, 0.16, 0.10, 0.14, 0.11, 0.15])   # oscillates, no consistent direction
    t = sectors.trend_diagnostics(h, periods=8)
    assert t["trend_strength"] == "weak/none" and t["direction"] == "none" and t["warning"] is None
    assert sectors.trend_diagnostics(synthetic_history([0.1, 0.1, 0.1]), periods=8) == {"trend": "insufficient_data"}


def test_cycle_diagnostics_appends_trend_caution_to_a_misleading_peak_flag():
    # a genuine secular ramp: the latest year is correctly a statistical "peak" vs trailing median, but it is NOT
    # a cyclical extreme, and cycle_diagnostics should say so rather than silently calling it a peak.
    h = synthetic_history([0.02, 0.03, 0.04, 0.08, 0.10, 0.14, 0.17, 0.20])
    d = sectors.cycle_diagnostics(h, periods=8, sector="software")
    assert "peak" in d["flag"] and "CAUTION" in d["flag"] and d["trend"]["trend_strength"] == "strong"
    # a real cyclical peak (no secular trend) should NOT get the caution suffix
    cyc = synthetic_history([0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.10, 0.30])
    d2 = sectors.cycle_diagnostics(cyc, periods=8, sector="oil_gas")
    assert "peak" in d2["flag"] and "CAUTION" not in d2["flag"]


# ---- regression: the real EDGAR data behind the third (enterprise-tech) football-field check
def test_crm_secular_margin_expansion_flagged_as_trend_not_cycle_on_real_data():
    d = sectors.cycle_diagnostics(_real_history("CRM"), periods=8, sector="software")
    assert "peak" in d["flag"] and "CAUTION" in d["flag"] and d["trend"]["direction"] == "improving"


def test_csco_own_margin_has_tight_range_but_a_real_gentle_trend_on_real_data():
    # Cisco's absolute margin range (20.8%-27.6%) is far tighter than steel's or oil & gas's, but that is a
    # statement about RANGE, not about trend: the correlation module still (correctly) picks up a real, if narrow-
    # band, declining drift over the window (~27.6% -> 20.8% before a partial FY2026 recovery to 24.3%) — a useful
    # reminder that "low cyclicality" (SECTOR_PROFILES["software"]) does not mean "no trend to check for."
    d = sectors.cycle_diagnostics(_real_history("CSCO"), periods=8, sector="software")
    assert d["flag"] == "near normal"   # the sector's tighter ±15% thresholds still call FY2026 unremarkable
    assert d["trend"]["trend_strength"] == "strong" and d["trend"]["direction"] == "declining"


# ---- regression: the real EDGAR data behind the fourth (banking) football-field check
def test_usb_roe_cycle_shows_real_covid_trough_on_real_data():
    h = _real_history("USB")
    trough = sectors.cycle_diagnostics(h, periods=8, sector="banking", field="net_income", revenue_field="equity", as_of="2020-12-31")
    assert trough["fiscal_year"] == "2020-12-31" and "trough" in trough["flag"]
    # 2021's reserve-release rebound is real and visible in the margin history (the max ROE year over FY2018-2025),
    # even though as_of="2021-12-31" alone doesn't cross the peak threshold — with only 4 trailing years available
    # at that point, +6.5% deviation from a small-sample median isn't the same statistical situation as steel's or
    # oil & gas's peak/trough years, which had a full 8-year trailing window to compare against. `flag` only ever
    # evaluates the latest/as-of year, not a retrospective scan of history — this checks the retrospective fact
    # directly instead.
    full = sectors.cycle_diagnostics(h, periods=8, sector="banking", field="net_income", revenue_field="equity")
    assert max(full["margin_history"], key=full["margin_history"].get) == "2021-12-31"


def test_default_field_is_meaningless_for_a_bank_on_real_data():
    # the point SECTOR_PROFILES["banking"]'s note makes: operating_income/revenue for a real bank filer is not
    # merely imprecise, EBIT can exceed "revenue" outright because the tags don't capture a bank's real income
    # statement structure — confirms the warning is grounded in an actual observed filer, not a hypothetical.
    h = _real_history("STI")
    fy2018 = h["2018-12-31"]
    assert fy2018["operating_income"] > fy2018["revenue"]


def _with_ffo(history):
    h = json.loads(json.dumps(history))
    for r in h.values():
        if r.get("net_income") is not None and r.get("da") is not None:
            r["ffo"] = r["net_income"] + r["da"]
    return h


def test_net_income_understates_ffo_for_every_real_reit_peer():
    # root cause of docs/FOOTBALL_FIELD_O.md's P/E-vs-P/FFO finding: real-estate D&A is a large enough non-cash
    # charge that net income is well under FFO for every one of the six real net-lease REITs checked, FY2025 —
    # this alone (not a chosen price) is why a net-income-based multiple runs high relative to an FFO-based one.
    for ticker in ("O", "NNN", "WPC", "ADC", "EPRT", "FCPT"):
        r = _real_history(ticker)["2025-12-31"]
        ffo = r["net_income"] + r["da"]
        assert r["net_income"] / ffo < 0.75, f"{ticker}: net income is not meaningfully below FFO"


def test_reit_ffo_margin_shows_no_cycle_on_real_data_despite_real_multiple_swing():
    # the blind-spot finding in SECTOR_PROFILES["reit"]'s note: cycle_diagnostics() on O's real FFO-margin
    # history reports "near normal" with a weak/none trend, even though O's real year-end P/FFO trading multiple
    # (computed directly in docs/FOOTBALL_FIELD_O.md, not through this module) swung 12.5x-18.7x over the same
    # window — this module only ever looks at fundamentals, never a market multiple, so it cannot see that cycle.
    h = _with_ffo(_real_history("O"))
    d = sectors.cycle_diagnostics(h, field="ffo", revenue_field="revenue", periods=8, sector="reit")
    assert d["fiscal_year"] == "2025-12-31"
    assert d["flag"] == "near normal"
    assert abs(d["deviation_pct"]) < 0.10
    t = sectors.trend_diagnostics(h, field="ffo", revenue_field="revenue", periods=8)
    assert t["trend_strength"] == "weak/none"


def test_reit_debt_tags_are_missing_for_some_filers_not_others():
    # SECTOR_PROFILES["reit"]'s other real finding, and a real correction of an earlier overgeneralization while
    # writing this check: finmodel.edgar's debt_total/_current/_noncurrent tags return None for the target (O)
    # and 2 of 5 peers (NNN, ADC) for FY2025 — but NOT for the other 3 peers, which still report a populated
    # debt_total. This is real filer-by-filer variation, not a sector-wide XBRL gap; the positive-control half of
    # this test (WPC/EPRT/FCPT) is what makes that a checked fact rather than an unverified absence claim.
    for ticker in ("O", "NNN", "ADC"):
        r = _real_history(ticker)["2025-12-31"]
        assert r.get("debt_total") is None and r.get("debt_current") is None and r.get("debt_noncurrent") is None
    for ticker in ("WPC", "EPRT", "FCPT"):
        r = _real_history(ticker)["2025-12-31"]
        assert r.get("debt_total") is not None
