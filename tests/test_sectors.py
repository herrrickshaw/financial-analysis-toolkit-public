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


def test_alk_covid_ebit_margin_is_the_most_extreme_real_swing_checked():
    # SECTOR_PROFILES["airline"]'s headline real finding: Alaska Air Group's FY2020 EBIT margin collapse is the
    # most extreme swing this module has been tuned on across every sector, and it's a discrete demand shock
    # (COVID), not a commodity/credit/rate cycle. Grounds "high" cyclicality in an actual observed filer.
    h = _real_history("ALK")
    fy2020 = h["2020-12-31"]
    assert fy2020["operating_income"] / fy2020["revenue"] < -0.45


def test_periods_8_bear_case_is_the_covid_year_and_unusable_for_a_dcf():
    # the DCF trap SECTOR_PROFILES["airline"] documents: dcf_scenarios_from_history's usual periods=8 default
    # returns the literal FY2020 pandemic margin as "bear_margin" — not a plausible recurring bear case — while
    # periods=5 (post-recovery years only) gives a real, usable range instead.
    h = _real_history("ALK")
    s8 = sectors.dcf_scenarios_from_history(h, periods=8)
    assert s8["years_used"] == sorted(s8["years_used"])
    assert s8["bear_margin"] < -0.40, "periods=8's bear case should still be the COVID year"
    s5 = sectors.dcf_scenarios_from_history(h, periods=5)
    assert "2020-12-31" not in s5["years_used"]
    assert -0.05 < s5["bear_margin"] < 0.05, "periods=5's bear case should be a plausible, non-catastrophic margin"


def test_trend_detection_flags_covid_cliff_as_a_trend_but_resolves_over_a_longer_window():
    # the second real trap SECTOR_PROFILES["airline"] documents: a short window ending right after a one-off
    # catastrophic year can look exactly like a genuine secular trend to a correlation-based detector. The SAME
    # company's longer window (which includes the recovery) correctly resolves this back to weak/none.
    h = _real_history("ALK")
    short = sectors.trend_diagnostics(h, periods=5, as_of="2020-12-31")
    assert short["trend_strength"] == "strong" and short["correlation"] < 0
    long = sectors.trend_diagnostics(h, periods=8)
    assert long["trend_strength"] == "weak/none"


def test_airline_ebitdar_lease_adjustment_compresses_the_multiple_on_real_data():
    # SECTOR_PROFILES["airline"]'s EV/EBITDAR finding: adding back the real, ASC-842-disclosed operating lease
    # cost/liability compresses the multiple for a real, lease-heavy peer (JetBlue) — verified directly from
    # committed EDGAR data, not from the doc's prose.
    r = _real_history("JBLU")["2025-12-31"]
    ebitda, olc, oll, debt = r["ebitda"], r["operating_lease_cost"], r["operating_lease_liability_total"], r["debt_total"]
    assert olc is not None and oll is not None
    ebitdar = ebitda + olc
    assert ebitdar > ebitda
    # a real, lease-heavy carrier's lease liability should be a material fraction of its financing debt, not
    # a rounding error — confirms this isn't a trivial adjustment for JetBlue specifically.
    assert oll / debt > 0.05


def test_southwest_lease_cost_tag_is_dominated_by_uncapitalized_variable_cost():
    # SECTOR_PROFILES["airline"]'s filer-inconsistency finding: Southwest's own aggregate LeaseCost tag is
    # mostly VariableLeaseCost, which ASC 842 expenses as incurred with no matching balance-sheet liability —
    # confirms why finmodel.edgar keeps these as separate fields rather than treating LeaseCost as a safe
    # fallback for operating_lease_cost.
    r = _real_history("LUV")["2025-12-31"]
    assert r.get("operating_lease_cost") is None
    assert r["total_lease_cost"] is not None and r["variable_lease_cost"] is not None
    assert r["variable_lease_cost"] / r["total_lease_cost"] > 0.7


def test_airline_capex_tags_are_additive_components_not_fallback_alternatives():
    # a real finding surfaced while building the airline check: Alaska Air Group's real total capex sums two
    # separate XBRL tags (flight equipment + other PP&E) rather than one aggregate — the same class of trap as
    # the REIT debt tags, fixed the same way debt_total already was (sum the components, don't pick just one).
    r = _real_history("ALK")["2024-12-31"]
    assert r["capex"] == r["capex_flight_equipment"] + r["capex_other_ppe"]
    assert r["capex_flight_equipment"] / r["capex"] < 0.8, "flight equipment alone should understate real total capex"


def test_wrb_da_tag_is_negative_because_it_bundles_investment_accretion():
    # SECTOR_PROFILES["insurance"]'s EBITDA finding: W. R. Berkley's own "da" value is genuinely negative for
    # FY2025, because finmodel.edgar's preferred D&A tag (DepreciationAmortizationAndAccretionNet) bundles in
    # bond-portfolio premium/discount accretion for a filer with a large investment book -- real evidence that
    # EBITDA doesn't work for an insurer, a different root cause from banking's revenue-tag mismatch.
    r = _real_history("WRB")["2025-12-31"]
    assert r["da"] < 0


def test_chubb_has_no_da_or_ebitda_tag_at_all():
    r = _real_history("CB")["2025-12-31"]
    assert r.get("da") is None and r.get("ebitda") is None


def test_every_real_pc_insurer_peer_shows_a_real_2022_bvps_decline():
    # the sector-defining real finding: EVERY one of 5 real P&C peers shows a real book-value-per-share decline
    # in FY2022 (the historic bond selloff), independently re-derived from committed EDGAR data. TRV and CB and
    # PGR stay net-income-positive that year regardless -- book value and earnings genuinely decouple for an
    # insurer, unlike a bank (credit losses hit both together).
    profitable_but_bvps_fell = 0
    for ticker in ("TRV", "CB", "ALL", "PGR", "CINF"):
        h = _real_history(ticker)
        bvps_2021 = h["2021-12-31"]["equity"] / h["2021-12-31"]["diluted_shares"]
        bvps_2022 = h["2022-12-31"]["equity"] / h["2022-12-31"]["diluted_shares"]
        assert bvps_2022 < bvps_2021, f"{ticker}: expected a real FY2022 BVPS decline"
        if h["2022-12-31"]["net_income"] > 0:
            profitable_but_bvps_fell += 1
    assert profitable_but_bvps_fell >= 3, "at least 3 of 5 peers should be net-income-positive despite the BVPS decline"


def test_trv_roe_rose_in_2022_purely_from_the_shrunken_book_value_denominator():
    # the connected ROE trap: Travelers' real measured ROE ROSE in FY2022 versus FY2021, purely because its own
    # AOCI-driven book-value decline shrank the denominator -- not because net income improved.
    h = _real_history("TRV")
    r2021, r2022 = h["2021-12-31"], h["2022-12-31"]
    roe_2021 = r2021["net_income"] / r2021["equity"]
    roe_2022 = r2022["net_income"] / r2022["equity"]
    assert roe_2022 > roe_2021
    assert r2022["net_income"] < r2021["net_income"], "the ROE rise must not be from higher net income"


def test_trv_roe_trend_is_strong_and_improving_a_real_trend_guard_callback():
    # the callback to the software check's trend guard, on a totally different sector: TRV's real ROE trend is
    # genuinely strong and improving, not the FY2022 denominator artifact alone -- confirmed by checking that
    # 2024-2025 (the highest ROE years) come after book value had already recovered past its pre-2022 peak.
    h = _real_history("TRV")
    t = sectors.trend_diagnostics(h, field="net_income", revenue_field="equity", periods=8)
    assert t["trend_strength"] == "strong" and t["direction"] == "improving"
    bvps_2021 = h["2021-12-31"]["equity"] / h["2021-12-31"]["diluted_shares"]
    bvps_2025 = h["2025-12-31"]["equity"] / h["2025-12-31"]["diluted_shares"]
    roe_2025 = h["2025-12-31"]["net_income"] / h["2025-12-31"]["equity"]
    roe_2021 = h["2021-12-31"]["net_income"] / h["2021-12-31"]["equity"]
    assert bvps_2025 > bvps_2021, "book value must have recovered past its pre-2022 peak"
    assert roe_2025 > roe_2021, "ROE improvement must persist even once book value is no longer shrunken"


def test_wrb_diluted_shares_had_a_real_persistent_xbrl_scale_error():
    # the bonus finding: W. R. Berkley's own diluted share count was filed at ~1/1000th scale for FY2017-2022,
    # verified directly against the committed extract, and it remains wrong today (FY2022 never got re-filed as
    # a comparative year again once it aged out of later 10-Ks' comparative window).
    h = _real_history("WRB")
    contaminated = h["2022-12-31"]["diluted_shares"]
    clean_neighbor = h["2025-12-31"]["diluted_shares"]
    assert contaminated * 100 < clean_neighbor, "FY2022's share count should still be ~1000x too small"


def test_txn_silicon_cycle_shows_a_real_pandemic_peak_and_normalization():
    # SECTOR_PROFILES["semiconductor"]'s cyclicality finding: TXN's real EBIT margin swung to a genuine
    # pandemic-chip-shortage peak in FY2022 and has since normalized lower -- a sixth distinct real mechanism
    # (inventory/demand bullwhip), verified directly against the committed extract.
    h = _real_history("TXN")
    margins = {y: h[y]["operating_income"] / h[y]["revenue"] for y in h if h[y].get("operating_income") and h[y].get("revenue")}
    assert max(margins, key=margins.get) == "2022-12-31"
    assert margins["2022-12-31"] > 0.48
    assert margins["2025-12-31"] < margins["2022-12-31"] - 0.10, "margin should have normalized well below the pandemic peak"


def test_on_semi_rnd_tag_fallback_is_real_and_populated():
    # a real, narrower tag-fallback fix: ON Semiconductor's own R&D tag is
    # ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost, not the plain tag this module otherwise
    # expects -- confirms the fallback actually populates real data, not just that it doesn't crash.
    r = _real_history("ON")["2025-12-31"]
    assert r.get("rnd") is not None and r["rnd"] > 0
    assert r["rnd"] / r["revenue"] < 0.15, "ON's real R&D intensity should be the lowest of the semiconductor peer set"


def test_on_semi_real_rnd_spend_has_declined_since_its_2021_peak():
    # grounds SECTOR_PROFILES["semiconductor"]'s counter-example claim: ON's own real R&D spend trajectory is
    # flat-to-declining since FY2021, the real reason its own R&D-capitalization uplift comes out negative
    # while every other real peer with a growing R&D budget shows a positive one.
    h = _real_history("ON")
    assert h["2021-12-31"]["rnd"] > h["2025-12-31"]["rnd"]


def test_duk_default_field_needs_no_override_but_shows_a_real_secular_trend():
    # SECTOR_PROFILES["utility"]'s headline finding: unlike banking/REIT/insurance, DUK's default field
    # (operating_income/revenue) needs no override -- but unlike airlines/semiconductors (where the default field
    # showed real mean-reverting cyclicality), DUK's real margin shows a genuine, strong SECULAR IMPROVEMENT
    # (rate-base growth), a third sector confirming the software/insurance trend-guard generalizes.
    h = _real_history("DUK")
    diag = sectors.cycle_diagnostics(h, field="operating_income", revenue_field="revenue", periods=8, sector="utility")
    trend = sectors.trend_diagnostics(h, field="operating_income", revenue_field="revenue", periods=8)
    assert diag["latest_margin"] > 0.25 and diag["flag"].startswith("peak")
    assert trend["trend_strength"] == "strong" and trend["direction"] == "improving"


def test_duk_real_capex_persistently_exceeds_da_every_year():
    # the real, sector-defining finding this check is built around: capex has run ~1.8-2.1x real D&A every single
    # year FY2019-2025 -- not a temporary supercycle (semiconductors) but a persistent structural pattern, the
    # reason a utility DCF should hold capex/revenue flat rather than taper it.
    h = _real_history("DUK")
    years = [y for y in sorted(h)[-7:] if h[y].get("capex") and h[y].get("da")]
    assert len(years) == 7
    for y in years:
        assert h[y]["capex"] > 1.5 * h[y]["da"], f"{y}: capex should persistently exceed D&A for a rate-base-growth utility"


def test_xel_roe_dilution_is_a_real_trend_not_the_usual_cyclicality_drivers():
    # peer Xcel Energy's real ROE (net_income/equity, the banking/insurance override) held a tight band for seven
    # straight years before a real FY2025 drop -- caused by a real forward equity offering funding its capital
    # plan, not any prior sector's cyclicality mechanism (commodity price, credit losses, rate-sensitivity, demand
    # shock, catastrophe losses, the silicon cycle).
    h = _real_history("XEL")
    roe = {y: h[y]["net_income"] / h[y]["equity"] for y in ("2018-12-31", "2019-12-31", "2020-12-31", "2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31")}
    assert max(roe.values()) - min(roe.values()) < 0.01, "XEL's ROE should be remarkably tight FY2018-2024"
    assert h["2025-12-31"]["net_income"] / h["2025-12-31"]["equity"] < min(roe.values()) - 0.01
    assert h["2025-12-31"]["equity"] / h["2024-12-31"]["equity"] - 1 > 0.15, "the real equity jump behind the ROE drop"


def test_abbv_raw_margin_trend_is_distorted_by_real_iprd_charges():
    # SECTOR_PROFILES["pharma"]'s headline finding: the RAW field shows a misleadingly negative-leaning
    # correlation driven by the real FY2024 acquired-IPR&D charge trough.
    h = _real_history("ABBV")
    trend_raw = sectors.trend_diagnostics(h, field="operating_income", revenue_field="revenue", periods=8)
    assert trend_raw["correlation"] < -0.25


def test_abbv_adjusted_margin_trend_is_genuinely_weak_once_iprd_is_removed():
    # once the real, lumpy, one-time acquired-IPR&D write-offs are added back (adjusted_operating_income,
    # precomputed in data/edgar/ABBV.json), the trend resolves to genuinely weak -- meaning the GENERIC
    # dcf_scenarios_from_history() trailing min/median/max is appropriate here, unlike DUK/TRV/CSCO.
    h = _real_history("ABBV")
    trend_adj = sectors.trend_diagnostics(h, field="adjusted_operating_income", revenue_field="revenue", periods=8)
    assert abs(trend_adj["correlation"]) < 0.20
    assert trend_adj["trend_strength"] == "weak/none"


def test_abbv_real_acquired_iprd_writeoff_is_material_and_growing():
    # real, verified against SEC's live XBRL API: AbbVie's own acquired-IPR&D write-off ran $0.7B-$5.0B/year
    # FY2020-2025, with FY2025's real charge the largest in the series (from the 2024-closed ImmunoGen and
    # Cerevel Therapeutics acquisitions).
    h = _real_history("ABBV")
    charges = {y: h[y]["acquired_iprd_writeoff"] for y in ("2020-12-31", "2021-12-31", "2022-12-31", "2023-12-31", "2024-12-31", "2025-12-31")}
    assert all(c > 0 for c in charges.values())
    assert charges["2025-12-31"] == max(charges.values())
    assert charges["2025-12-31"] / h["2025-12-31"]["revenue"] > 0.05


def test_abbv_iprd_writeoff_compresses_reported_margin_materially_in_fy2025():
    h = _real_history("ABBV")
    r = h["2025-12-31"]
    reported_margin = r["operating_income"] / r["revenue"]
    adjusted_margin = r["adjusted_operating_income"] / r["revenue"]
    assert adjusted_margin - reported_margin > 0.05, "the real FY2025 IPR&D charge should compress margin by several points"
