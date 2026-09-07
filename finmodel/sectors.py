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
    "reit": SectorProfile("REITs / real estate", "moderate", 8, 0.90, -0.20, 0.20,
        "Two real findings from Realty Income (O) and five net-lease peers (docs/FOOTBALL_FIELD_O.md — "
        "data/edgar/{O,NNN,WPC,ADC,EPRT,FCPT}.json), FY2025, real 2026-07-02 prices: (1) P/E is badly misleading "
        "for a REIT — real-estate depreciation is a large non-cash charge against an asset that usually "
        "appreciates, so P/E ranged 22.9x-54.3x across the six peers while P/FFO (funds from operations = "
        "net income + real-estate D&A, the REIT-standard non-GAAP metric) sat in a much saner 13.6x-19.4x band "
        "over the SAME six companies. `field`/`revenue_field` should be net_income+da / revenue (i.e. FFO margin), "
        "not raw net_income margin, for a REIT — and even that is a proxy: Nareit's official FFO definition also "
        "excludes gains/losses on real-estate sales, and AFFO (which further adjusts for straight-line rent and "
        "recurring capex) has NO standardized XBRL tag at all across filers, so it isn't derivable from EDGAR the "
        "way FFO's D&A add-back is — a real data-availability ceiling, not a bug in this module. Net debt is *not* "
        "required for comps here (P/E and P/FFO are both equity-numerator, like a bank's P/B), which is fortunate: "
        "verified for FY2025 that finmodel.edgar's debt_total/_current/_noncurrent tags return None for the "
        "target (O) and 2 of 5 peers (NNN, Agree Realty) — Realty Income's own 'LongTermDebt' tag data stops "
        "after FY2016, replaced by disaggregated SecuredDebt/UnsecuredDebt/NotesPayable tags that are ADDITIVE "
        "components, not fallback alternatives, so summing them correctly needs a different TAGS design than "
        "this module's 'first tag wins' fallback tuples. This is real filer-by-filer variation, not a universal "
        "REIT phenomenon: the other 3 of 5 peers (W. P. Carey, Essential Properties, Four Corners) DO still "
        "report a populated debt_total for FY2025 — don't assume a REIT lacks debt data without checking; this "
        "check simply didn't need it, since P/E and P/FFO don't require net debt. (2) Real O "
        "data shows the actual cycle here lives in the MARKET MULTIPLE, not the operating metric this module "
        "normalizes: FFO margin was essentially flat (`cycle_diagnostics(field='ffo', revenue_field='revenue')` "
        "reports 'near normal', deviation <10%, trend 'weak/none'), yet O's real year-end P/FFO swung 12.5x-18.7x "
        "over 2018-2025 — compressing hardest exactly when the Fed hiked rates (2021 peak 18.7x during near-zero "
        "rates -> 2023 trough 12.5x). This module has no visibility into that at all: it only ever looks at a "
        "company's own fundamentals history, never its market price/multiple history, so for a REIT it will "
        "correctly report 'no cycle' while missing the real, rate-driven one entirely — a genuine blind spot, "
        "not a false negative to patch, since fixing it would mean this module starting to look at prices, which "
        "is out of scope for what it does. DCF-equivalent: dividend discount model (Gordon growth), since REITs "
        "must distribute >=90% of taxable income as dividends — O's own real dividend-per-share history shows "
        "growth decelerating from a ~3.55%/yr 11-year CAGR to a ~2.77%/yr trailing-3-year CAGR, real and driven by "
        "the ~4x dilution from stock-funded M&A (VEREIT 2021, Spirit Realty 2024), not a hand-picked assumption."),
    "airline": SectorProfile("Airlines / air transport", "high", 5, 1.30, -0.20, 0.20,
        "Real EBIT margin for Alaska Air Group (data/edgar/ALK.json) swung 22.0% (FY2016) to -49.8% (FY2020) — the "
        "most extreme swing of any sector this module has been tuned on, driven by a fourth distinct mechanism: "
        "not a commodity price (steel/oil & gas), credit losses (banking) or the risk-free rate (REITs), but a "
        "discrete exogenous demand shock (the FY2020 pandemic travel shutdown). WARNING: `normalize_periods` is 5 "
        "here, not this module's usual 8, and that is load-bearing, not cosmetic — verified on real data that "
        "`dcf_scenarios_from_history(periods=8)` returns a bear_margin of -49.8% (literally FY2020), which is not "
        "a usable 'bear case' for a 5-year forward DCF (a company sustaining that margin for 5 straight years is "
        "bankrupt, not bearish); `periods=5` (trailing FY2021-2025, after the initial snap-back) gives a real, "
        "usable bear/base/blue-sky of 0.7%/3.8%/11.1% instead. A second, subtler real finding from the same data: "
        "`trend_diagnostics()` fired a 'declining secular trend' CAUTION (r=-0.80) on the 5-year window ending "
        "FY2020 (`as_of='2020-12-31'`) — a real result, but a misleading one, since it reflects one catastrophic "
        "final data point dragging a short window's correlation, not a genuine multi-year structural decline the "
        "way Salesforce's software-check trend was; the SAME company's 8-year window ending FY2025 (which "
        "includes the recovery years) correctly resolves this back to 'weak/none' (r=0.11). Correlation-based "
        "trend detection cannot, by construction, distinguish 'gradual structural decline' from 'stable, then one "
        "cliff' — both can show a strong |r| over a short-enough window ending right after the cliff. Unlike "
        "banking and REITs, the DEFAULT `field`/`revenue_field` (`operating_income`/`revenue`) is the CORRECT "
        "choice for an airline — no override needed, a useful contrast to keep in mind before assuming every "
        "sector needs one. Separately (not part of `cycle_diagnostics()`, but from the same real check, "
        "docs/FOOTBALL_FIELD_ALK.md): EV/EBITDA understates comparability for a lease-heavy carrier the way it "
        "understated it for a bank's EV — not because EV is meaningless here, but because EBITDA sits below a "
        "real, material rent/lease expense some peers capitalize (own their fleet, showing up as debt+D&A) and "
        "others expense (lease their fleet, showing up as an operating cost, pre-ASC-842 entirely off the balance "
        "sheet). EV/EBITDAR (EBITDA + operating lease cost; EV + the real, ASC-842-disclosed operating lease "
        "liability, replacing the old rule-of-thumb '7-8x annual rent' capitalization estimate for any FY2019+ "
        "filing) is the fix — verified real across 5 of 6 peers (finmodel.edgar's new operating_lease_cost/"
        "operating_lease_liability_total fields), compressing the multiple 8-22% depending on how lease-heavy the "
        "carrier is (largest for JetBlue, whose EBITDA is thin enough that the lease add-back matters "
        "proportionally the most). The 6th peer (Southwest) can't get the same clean adjustment: it doesn't "
        "disaggregate operating lease cost in its XBRL filing at all, and its aggregate 'LeaseCost' tag is "
        "dominated by ~$2.1B of variable lease cost that ASC 842 expenses as incurred with NO matching balance-"
        "sheet liability — real filer-level inconsistency, not a bug in the extraction, and a reason "
        "`finmodel.edgar` keeps `total_lease_cost`/`variable_lease_cost` as separate fields rather than silently "
        "substituting one for operating_lease_cost."),
    "insurance": SectorProfile("Property & casualty insurance / reinsurance", "high", 8, 0.85, -0.20, 0.20,
        "Tuned on Travelers (TRV) and five real P&C peers (CB, ALL, PGR, CINF, WRB), FY2025 real prices/EDGAR "
        "data. Like banking, EBITDA doesn't apply: Chubb reports no da/ebitda tag at all, and W.R. Berkley's `da` "
        "picks up a genuinely NEGATIVE value (-$48.1M, FY2025) because the XBRL tag this module prefers "
        "(`DepreciationAmortizationAndAccretionNet`) bundles in bond-portfolio premium/discount accretion for a "
        "filer with a large investment portfolio — a real, different root cause from the bank check's revenue-tag "
        "mismatch, same conclusion: use P/B, P/TBV and P/E (equity-numerator, see finmodel.comps), never "
        "EV/EBITDA. The REAL, sector-defining finding here is different from both banking and REITs: book value "
        "itself, not the trading multiple (REITs) and not earnings moving together with book value (banking's "
        "credit losses), is directly rate-exposed. Verified across all 5 clean peers: EVERY ONE showed a real "
        "book-value-per-share decline in FY2022 (-9% to -23%) during that year's historic bond selloff, even "
        "though 3 of 5 (TRV, CB, PGR) stayed solidly net-income-positive — because available-for-sale bond "
        "fair-value moves run through OCI (equity), not net income, under GAAP, so BVPS and EPS can genuinely "
        "decouple for an insurer in a way they structurally cannot for a bank's amortized-cost loan book. A real, "
        "connected trap for `field='net_income', revenue_field='equity'` (this sector's ROE override, same as "
        "banking's): TRV's own measured ROE ROSE in FY2022 (13.2%, vs 12.7% in FY2021) purely because its "
        "book-value denominator shrank from the same AOCI hit — an ROE 'improvement' that isn't real earnings "
        "power. (TRV's broader FY2018-2025 ROE trend, 11.0%→19.1%, IS real and `trend_diagnostics()` correctly "
        "flags it 'strong' — verified this isn't just the 2022 denominator artifact, since 2024-2025's ROE, the "
        "highest in the series, comes AFTER book value had already recovered well past its pre-2022 peak.) "
        "Precedents are real, all-cash (AIG/Validus, 2018, $68.00/share — Validus's FY2017 net income was "
        "genuinely negative, a real catastrophe-loss year (Harvey/Irma/Maria), so its P/E is correctly NM, not a "
        "data error; Berkshire/Alleghany, 2022, $848.02/share). DCF-equivalent: residual income (ROE vs cost of "
        "equity, `finmodel.residual_income`) — the SAME generic tool the banking check validated, now confirmed "
        "on a second, independent financial-services sector. Bonus real finding, unrelated to the above but worth "
        "knowing: W.R. Berkley's own `WeightedAverageNumberOfDilutedSharesOutstanding` was filed ~1000x too small "
        "for FY2017-2022 (a real, persistent XBRL filer scale error) — 'latest filing wins' only fixes this while "
        "the bad period still appears as a comparative year in a later 10-K; FY2017-2022 have since aged out of "
        "every subsequent filing's comparative window and remain wrong in SEC's own live API today."),
    "semiconductor": SectorProfile("Semiconductors / analog & mixed-signal", "high", 8, 1.20, -0.20, 0.20,
        "Tuned on Texas Instruments (TXN) and five real peers (ADI, MCHP, NXPI, ON, SWKS), FY2025 real prices/"
        "EDGAR data. Unlike every prior sector, the default operating_income/revenue fields ARE correct here — "
        "no override needed (like airlines, unlike banking/REITs/insurance) — but EV/EBIT alone still "
        "understates value for an R&D-heavy business: GAAP expenses R&D immediately even though it creates a "
        "multi-year economic asset (chip designs) the same way capex does. `finmodel.rd_capitalization` "
        "(new this check, reconciled to CFI's real 'RD-Capitalization.xlsx' single-vintage template, then "
        "generalized to Damodaran's cross-sectional method) capitalizes each historical year's R&D as its own "
        "5-year-amortized vintage and restates EBIT. Real, verified uplift across 5 of 6 peers with growing R&D "
        "budgets: TXN +6.1%, ADI +11.1%, MCHP +16.5%, NXPI +8.0%, SWKS +43.0% (largest for the peer with the "
        "thinnest reported EBIT relative to its R&D spend). ON Semiconductor is the real counter-example: its "
        "own R&D spend has been flat-to-declining since FY2021, so capitalizing it LOWERS adjusted EBIT "
        "(-40.4%) — the mirror-image case, and a reminder that this adjustment's PERCENTAGE impact is amplified "
        "whenever reported EBIT is unusually thin (ON's own FY2025 EBIT margin is real but thin, reflecting the "
        "sector's real demand downturn that year — see the cyclicality note below), not because the underlying "
        "R&D economics are unusual. Verified the same compression on BOTH real, all-cash 2019 precedent deals "
        "(NVIDIA/Mellanox, Infineon/Cypress Semiconductor): raw EV/EBIT of 60.4x and 57.9x compress to 37.2x and "
        "40.5x once each target's own real R&D history is capitalized — a striking, real demonstration of why a "
        "raw GAAP multiple can misstate what an acquirer is actually paying for an R&D-intensive target. A real, "
        "narrower tag-fallback fix found while pulling this data: ON Semiconductor's own R&D tag is "
        "`ResearchAndDevelopmentExpenseExcludingAcquiredInProcessCost`, not the plain `ResearchAndDevelopment"
        "Expense` this module otherwise expects (now a same-field fallback in `finmodel.edgar`, a true "
        "alternative rather than an additive-component trap, since it nets out lumpy acquisition-accounting "
        "IPR&D write-offs that are less comparable across peers anyway). Real cyclicality, a sixth distinct "
        "mechanism from every prior sector: TXN's EBIT margin swung 30.3% (FY2014) to a pandemic-chip-shortage "
        "peak of 50.6% (FY2022) back down to 34.1% (FY2025) — the real 'silicon cycle' bullwhip effect (a "
        "shortage triggers over-ordering, which becomes an inventory glut once demand normalizes), not a "
        "commodity price, credit, rate, demand-shock or catastrophe-loss cycle."),
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
