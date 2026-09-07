"""Sector-aware tuning built directly from what the real-data checks in docs/FOOTBALL_FIELD_STLD.md (steel) and
docs/FOOTBALL_FIELD_CVX.md (oil & gas) found: a single trailing fiscal year's EBITDA can sit anywhere in a
company's own multi-year earnings cycle, and using it un-normalized in trading-comps or precedent-transaction
multiples silently over- or under-states the "true" multiple depending on whether that year happened to be a
cycle trough (steel's 2025, understating value... no, overstating multiples) or a cycle peak (the oil & gas
precedent targets' pre-deal years, understating multiples). This module does not replace finmodel.comps or
finmodel.dcf — it prepares better INPUTS for them from a company's own EDGAR history (edgar.annual()'s output
shape: {fiscal_year_end: {field: value, ...}}).

Three sectors have been tuned against real multi-year data so far (steel, oil & gas E&P/integrated, and enterprise
technology — see SECTOR_PROFILES); everything else falls back to a clearly-labelled generic default rather than a
fabricated industry assumption.

A caveat the enterprise-technology check (docs/FOOTBALL_FIELD_CSCO.md) surfaced, and that the whole module is built
around: `cycle_diagnostics()` and `dcf_scenarios_from_history()` assume the margin history is MEAN-REVERTING —
true for a commodity producer whose margin swings with a price it doesn't control, but false for a company on a
genuine secular trend (Salesforce shifting from growth-at-all-costs to profitability moved its own margin from
~2% to ~20% over 8 years — real, deliberate, and not something a "trailing median" should be treated as a normal
baseline for). Applying trailing-median normalization to a secularly-trending company would flag its improved,
sustainable margin as a misleading "peak" and understate its DCF. `trend_diagnostics()` (and the `trend` field
`cycle_diagnostics()` now includes) exists to catch this before it happens."""
from __future__ import annotations

import statistics
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


@dataclass
class SectorProfile:
    name: str
    cyclicality: str          # "high" | "moderate" | "low"
    normalize_periods: int    # trailing fiscal years used for a through-cycle baseline
    unlevered_beta: float     # illustrative, Damodaran-style industry-average unlevered beta — not company-specific
    trough_threshold: float   # margin deviation below the trailing median that flags a "trough" year
    peak_threshold: float     # margin deviation above the trailing median that flags a "peak" year
    note: str


SECTOR_PROFILES: Dict[str, SectorProfile] = {
    "steel": SectorProfile("Steel / metals & mining", "high", 8, 1.05, -0.20, 0.20,
        "EBIT margin ranged 8.1%–23.4% for Steel Dynamics over FY2018–2025 (data/edgar/STLD.json) — a >2.5x "
        "peak-to-trough swing driven by steel-price cycles, not company execution; FY2025 (the LTM year both the "
        "comps and precedents in docs/FOOTBALL_FIELD_STLD.md were built on) sits at the trough."),
    "oil_gas": SectorProfile("Oil & gas E&P / integrated", "high", 8, 1.10, -0.20, 0.20,
        "EBIT margin ranged -7.1% to +20.4% for Chevron over FY2018–2025 (data/edgar/CVX.json) — it swings sign "
        "entirely with a commodity price the company does not set; the two precedent-deal targets in "
        "docs/FOOTBALL_FIELD_CVX.md (Pioneer FY2022, Marathon Oil FY2023) both sit near the 2022 price-spike peak."),
    "banking": SectorProfile("Banks / financial institutions", "moderate", 8, 1.05, -0.20, 0.20,
        "ROE (net_income/equity, NOT operating_income/revenue — see the WARNING below) ranged 9.3%-14.5% for US "
        "Bancorp over FY2018-2025 (data/edgar/USB.json), with a real, credit-cycle-driven trough in FY2020 (COVID "
        "loan-loss reserve build) and a reserve-release peak in FY2021 — a genuine cycle, but driven by credit "
        "losses, not a commodity price. WARNING: `field`/`revenue_field` MUST be overridden to "
        "`net_income`/`equity` (i.e. ROE) for any bank — this module's default `operating_income`/`revenue` is "
        "not merely imprecise for a bank, it is MEANINGLESS: verified on real EDGAR data for 7 large US banks "
        "(docs/FOOTBALL_FIELD_USB.md) that the standard XBRL revenue/operating-income tags this module's "
        "`edgar.annual()` extracts for an industrial company are absent, partial, or inconsistent for a bank — "
        "one real filer showed 'operating income' exceeding 'revenue', another showed net income exceeding "
        "'revenue', because a bank's core economics (net interest income = interest income − interest expense, "
        "plus fee income) don't map onto a cost-of-goods-sold income statement at all. Comps for a bank should use "
        "P/B, P/TBV or P/E (all equity-numerator multiples — see finmodel.comps), never EV/EBITDA (bank 'debt' is "
        "mostly customer deposits funding the loan book, not financing debt, so 'enterprise value' itself is not "
        "a meaningful concept); a bank's DCF-equivalent should be a residual-income / excess-return model on ROE "
        "vs. cost of equity (finmodel.residual_income), not an unlevered free-cash-flow DCF."),
    "software": SectorProfile("Enterprise technology / software", "low", 8, 1.15, -0.15, 0.15,
        "EBIT margin ranged 20.8%–27.6% for Cisco over FY2020–2026 (data/edgar/CSCO.json) — a genuinely tight, "
        "low-cyclicality RANGE relative to steel/oil & gas (tighter thresholds reflect that). But tight range is not "
        "the same as no trend: trend_diagnostics() still finds a real, if narrow-band, declining drift within that "
        "range (r=-0.75, ~27.6%→20.8% before a partial FY2026 recovery) — 'low cyclicality' means smaller swings, "
        "not zero drift to check for. WARNING: this profile fits Cisco itself, not the whole sector by label alone — "
        "peers in the same comps set showed a much stronger SECULAR margin-EXPANSION trend over the same window "
        "(Salesforce ~2%→20%, docs/FOOTBALL_FIELD_CSCO.md), which trailing-median normalization would badly misread "
        "as a cyclical peak. Always run trend_diagnostics() before trusting this profile's normalization on a "
        "specific company."),
    "default": SectorProfile("Uncategorised / not yet analysed with real data", "moderate", 5, 1.00, -0.20, 0.20,
        "No sector-specific tuning has been validated against real multi-year EDGAR data for this sector yet — "
        "treat these numbers as a generic starting point, not a calibrated assumption."),
}


def _margins(history: Dict[str, Dict[str, float]], field: str, revenue_field: str, years: Sequence[str]) -> Dict[str, float]:
    return {y: safe_div(history[y].get(field, 0) or 0, history[y].get(revenue_field, 0) or 0)
            for y in years if history.get(y, {}).get(revenue_field)}


def normalize_metric(history: Dict[str, Dict[str, float]], field: str, periods: int = 5, method: str = "median", as_of: Optional[str] = None) -> Dict[str, Any]:
    """Through-cycle baseline for `field` (e.g. "operating_income", "ebitda") from an edgar.annual()-shaped history
    dict: the trailing `periods` fiscal years up to (and including) `as_of` (defaults to the latest available)."""
    years = sorted(history)
    if as_of: years = [y for y in years if y <= as_of]
    window = years[-periods:]
    vals = [history[y][field] for y in window if history[y].get(field) is not None]
    if not vals:
        raise ValueError(f"no data for field {field!r} in the trailing {periods} years")
    fn = {"median": statistics.median, "mean": statistics.fmean, "min": min, "max": max}[method]
    return {"field": field, "method": method, "periods_used": window, "value": fn(vals), "raw_values": vals}


def trend_diagnostics(history: Dict[str, Dict[str, float]], field: str = "operating_income", revenue_field: str = "revenue",
                      periods: int = 8, as_of: Optional[str] = None, strong: float = 0.7, moderate: float = 0.4) -> Dict[str, Any]:
    """Distinguishes a genuine secular trend (margin moving consistently in one direction, e.g. Salesforce's
    growth-to-profitability shift, ~2%→20% over 8 years) from noisy or mean-reverting cyclicality, using the
    correlation between margin and time over the trailing `periods` fiscal years. A strong trend (|r| >= `strong`,
    default 0.7) means trailing-median normalization is the WRONG tool: it would treat a sustainable, structurally
    improved (or deteriorated) margin as a misleading cyclical extreme."""
    years = sorted(history)
    if as_of: years = [y for y in years if y <= as_of]
    margins = _margins(history, field, revenue_field, years[-periods:])
    if len(margins) < 4:
        return {"trend": "insufficient_data"}
    ordered = sorted(margins)
    vals = [margins[y] for y in ordered]
    corr = statistics.correlation(range(len(vals)), vals)
    strength = "strong" if abs(corr) >= strong else "moderate" if abs(corr) >= moderate else "weak/none"
    direction = "improving" if corr > 0 else "declining" if corr < 0 else "flat"
    warning = None
    if strength == "strong":
        warning = (f"a {direction} secular trend (r={corr:.2f}), not mean-reverting cyclicality — trailing-median "
                   f"normalization would misread the latest margin as a cyclical extreme; use the latest year or a "
                   f"short recent window instead, not the trailing median")
    return {"correlation": corr, "trend_strength": strength, "direction": direction if strength != "weak/none" else "none",
            "years_used": ordered, "margin_history": margins, "warning": warning}


def cycle_diagnostics(history: Dict[str, Dict[str, float]], field: str = "operating_income", revenue_field: str = "revenue",
                      periods: int = 8, sector: str = "default", as_of: Optional[str] = None) -> Dict[str, Any]:
    """Compares the latest (or `as_of`) fiscal year's margin on `field` to its own trailing multi-year median margin
    and flags whether that year is likely to distort a trailing-multiple valuation built on it. Thresholds come from
    the sector profile. Also runs `trend_diagnostics()` and attaches its result — a strong secular trend makes the
    trough/peak flag below unreliable; check the `trend` field before trusting it."""
    profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES["default"])
    years = sorted(history)
    if as_of: years = [y for y in years if y <= as_of]
    if not years:
        return {"flag": "no_data"}
    latest = years[-1]
    margins = _margins(history, field, revenue_field, years[-periods:])
    latest_margin = margins.get(latest)
    if latest_margin is None or len(margins) < 2:
        return {"fiscal_year": latest, "flag": "insufficient_data"}
    baseline = statistics.median(list(margins.values()))
    deviation = safe_div(latest_margin - baseline, abs(baseline)) if baseline else (float("inf") if latest_margin else 0.0)
    if deviation <= profile.trough_threshold:
        flag = "trough — trailing multiples built on this year likely OVERstate the true multiple"
    elif deviation >= profile.peak_threshold:
        flag = "peak — trailing multiples built on this year likely UNDERstate the true multiple"
    else:
        flag = "near normal"
    trend = trend_diagnostics(history, field, revenue_field, periods, as_of)
    if trend.get("warning") and flag != "near normal":
        flag += f" — CAUTION: {trend['warning']}"
    return {"fiscal_year": latest, "sector": profile.name, "latest_margin": latest_margin, "median_margin_trailing_years": baseline,
            "deviation_pct": deviation, "flag": flag, "margin_history": margins, "periods_used": years[-periods:], "trend": trend}


def dcf_scenarios_from_history(history: Dict[str, Dict[str, float]], field: str = "operating_income", revenue_field: str = "revenue",
                               periods: int = 8) -> Dict[str, Any]:
    """Data-driven base/bear/blue-sky EBIT-margin targets from a company's OWN historical margin distribution —
    replaces a hand-picked "toward last year's level" assumption with base = trailing median margin, bear = trailing
    minimum, blue_sky = trailing maximum, each computed over the trailing `periods` fiscal years. Works for any
    company with enough EDGAR history; not specific to steel or oil & gas."""
    years = sorted(history)[-periods:]
    margins = _margins(history, field, revenue_field, years)
    if not margins:
        raise ValueError("no revenue/field data to build margin scenarios from")
    vals = list(margins.values())
    return {"years_used": years, "margin_history": margins, "current_margin": margins[years[-1]],
            "base_margin": statistics.median(vals), "bear_margin": min(vals), "blue_sky_margin": max(vals)}


def sector_beta(sector: str) -> float:
    """Illustrative, Damodaran-style unlevered beta for a sector profile — a starting point when a company-specific
    beta isn't available, not a substitute for one."""
    return SECTOR_PROFILES.get(sector, SECTOR_PROFILES["default"]).unlevered_beta


def normalized_comps_metrics(history: Dict[str, Dict[str, float]], sector: str = "default", periods: Optional[int] = None) -> Dict[str, float]:
    """A metrics dict — {"revenue", "ebitda", "ebit", "net_income"} — using through-cycle-normalized EBITDA/EBIT
    (median over the sector's normalize_periods) instead of the raw LTM year, ready to feed finmodel.comps.Peer or
    finmodel.comps.Target. Revenue and net_income stay at the latest LTM year (normalizing every line would also
    distort per-share metrics like P/E in ways this module hasn't validated)."""
    profile = SECTOR_PROFILES.get(sector, SECTOR_PROFILES["default"])
    n = periods or profile.normalize_periods
    latest = sorted(history)[-1]
    ebit_n = normalize_metric(history, "operating_income", n, "median")["value"]
    da_n = normalize_metric(history, "da", n, "median")["value"] if any(history[y].get("da") for y in history) else 0.0
    return {"revenue": history[latest].get("revenue", 0), "ebitda": ebit_n + da_n, "ebit": ebit_n, "net_income": history[latest].get("net_income", 0)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    history = d["history"]
    sector = d.get("sector", "default")
    return {"cycle_diagnostics": cycle_diagnostics(history, sector=sector, periods=d.get("periods", 8), field=d.get("field", "operating_income")),
            "dcf_scenarios": dcf_scenarios_from_history(history, periods=d.get("periods", 8), field=d.get("field", "operating_income")),
            "normalized_metrics": normalized_comps_metrics(history, sector=sector, periods=d.get("periods")),
            "sector_profile": {"name": SECTOR_PROFILES.get(sector, SECTOR_PROFILES["default"]).name, "unlevered_beta": sector_beta(sector)}}
