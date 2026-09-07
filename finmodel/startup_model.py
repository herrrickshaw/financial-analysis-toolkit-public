"""New-business / startup financial model: turns a small set of high-level business assumptions (a revenue ramp,
a margin trajectory, funding rounds) into a full linked three-statement projection and a DCF valuation, then
checks those assumptions against REAL comparable-company data already collected elsewhere in this toolkit
(`data/edgar/<TICKER>.json`, the same extracts the football-field sector checks use) — so a founder's plan gets
checked against real market benchmarks, not just internal consistency.

No new modeling engine here: `build_three_statement()` is a thin translation layer onto the already-tested,
CFI-workbook-reconciled `finmodel.three_statement`, and `dcf_from_projection()` does the same onto
`finmodel.dcf`. The genuinely new piece is `benchmark_against_sector()`, which reads the real per-sector peer
tickers this repo has already validated (steel/oil_gas/software/banking/reit/airline/insurance) and reports
where a plan's assumed terminal-year margin sits relative to those real companies' actual, most recent fiscal
year — not a fabricated "typical startup benchmark."
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from . import three_statement as TS
from .dcf import DCFInputs, run as dcf_run
from .fin import safe_div

ROOT = Path(__file__).resolve().parent.parent

# The real tickers each football-field sector check validated (data/edgar/<ticker>.json) — used only to look up
# real comparable-company margins for benchmark_against_sector(); NOT re-fetched here, NOT fabricated.
SECTOR_PEER_TICKERS: Dict[str, Sequence[str]] = {
    "steel": ("STLD", "X", "CLF", "NUE", "CRS", "RS", "CMC", "WOR"),
    "oil_gas": ("CVX", "XOM", "COP", "EOG", "HES", "MRO", "OXY", "PXD"),
    "software": ("CSCO", "MSFT", "ORCL", "IBM", "ADBE", "CRM"),
    "banking": ("USB", "PNC", "TFC", "MTB", "CFG", "RF", "FITB"),
    "reit": ("O", "NNN", "WPC", "ADC", "EPRT", "FCPT"),
    "airline": ("ALK", "LUV", "DAL", "UAL", "AAL", "JBLU"),
    "insurance": ("TRV", "CB", "ALL", "PGR", "CINF", "WRB"),
}
# the natural (field, revenue_field) for each sector's margin — same convention as `finmodel cycle`'s
# --field/--revenue-field: most sectors use EBIT margin, banking/insurance use ROE, REITs use FFO margin.
SECTOR_DEFAULT_FIELDS: Dict[str, tuple] = {
    "banking": ("net_income", "equity"), "insurance": ("net_income", "equity"), "reit": ("ffo", "revenue"),
}


@dataclass
class StartupInputs:
    name: str
    forecast_years: int
    year0_revenue: float = 0.0                # last actual/seed-year revenue; 0.0 for a pre-revenue business
    revenue_growth: Any = None                 # scalar or list (one per forecast year); ignored if revenue_path given
    revenue_path: Optional[Sequence[float]] = None  # absolute revenue per forecast year — the more natural input
    gross_margin: Any = 0.65                   # scalar or list, 0..1
    payroll_pct_revenue: Any = 0.45            # people costs (S&M+R&D+G&A headcount), % of revenue
    other_opex_pct_revenue: Any = 0.20         # non-payroll opex (tools, hosting, marketing spend, rent…), % of revenue
    capex_pct_revenue: Any = 0.02
    da_pct_ppe: Any = 0.30
    ar_days: Any = 30
    inventory_days: Any = 0
    ap_days: Any = 30
    tax_rate: Any = 0.21
    interest_pct_debt: Any = 0.0
    starting_cash: float = 0.0                 # seed funding already raised, sitting in year-0 cash
    starting_ppe: float = 0.0
    equity_raised: Dict[int, float] = field(default_factory=dict)  # 0-based forecast-year index -> $ raised that year
    debt_raised: Dict[int, float] = field(default_factory=dict)

    def _revenue_growth_list(self) -> List[float]:
        n = self.forecast_years
        if self.revenue_path is not None:
            path = list(self.revenue_path)
            if len(path) != n:
                raise ValueError(f"revenue_path must have {n} values, got {len(path)}")
            prev = self.year0_revenue
            growth = []
            for v in path:
                if prev == 0:
                    raise ValueError("revenue_path implies growth off a zero prior-year base — set year0_revenue "
                                      "to a small positive seed value, or make revenue_path[0] the only nonzero jump.")
                growth.append(v / prev - 1)
                prev = v
            return growth
        if self.revenue_growth is None:
            raise ValueError("give either revenue_growth or revenue_path")
        g = self.revenue_growth
        return [float(g)] * n if isinstance(g, (int, float)) else list(g)


def build_three_statement(inp: StartupInputs) -> TS.ThreeStatementResult:
    """Seed year (year 0) is a bare balance sheet — starting cash/PP&E from initial funding, zero P&L activity —
    so this works equally for a pre-revenue business (year0_revenue=0) and one with some existing run-rate."""
    n = inp.forecast_years
    growth = inp._revenue_growth_list()
    gm = [inp.gross_margin] * n if isinstance(inp.gross_margin, (int, float)) else list(inp.gross_margin)
    other_opex = [inp.other_opex_pct_revenue] * n if isinstance(inp.other_opex_pct_revenue, (int, float)) else list(inp.other_opex_pct_revenue)
    if len(gm) != n or len(other_opex) != n:
        raise ValueError("gross_margin / other_opex_pct_revenue lists must have forecast_years entries")

    # "Rent and Overhead" in finmodel.three_statement is an absolute $/year figure, not a ratio — precompute the
    # revenue path here so a %-of-revenue opex assumption can still be expressed through it.
    revenue_path = [inp.year0_revenue]
    for g in growth:
        revenue_path.append(revenue_path[-1] * (1 + g))
    other_opex_abs = [revenue_path[i + 1] * other_opex[i] for i in range(n)]
    cogs_pct = [1 - m for m in gm]

    # Year 0 is "day one": the company incorporates, raises starting_cash + the value of any contributed/
    # purchased equipment as equity, and immediately spends starting_ppe on that equipment. Modeling the PP&E
    # purchase as year-0 capex (an investing outflow) rather than a free opening balance is what keeps the
    # cash-flow waterfall's computed closing cash equal to the given starting_cash exactly — a non-cash "gift"
    # of PP&E with no matching capex/financing entry would balance the balance sheet but break the cash roll-
    # forward, since equity_issued (financing) has no field for a non-cash contribution.
    total_paid_in = inp.starting_cash + inp.starting_ppe
    seed = TS.HistoricalYear(year=0, revenue=inp.year0_revenue, cogs=inp.year0_revenue,
                             salaries=0.0, rent=0.0, da=0.0, interest=0.0, taxes=0.0, cash=inp.starting_cash,
                             ar=0.0, inventory=0.0, ppe=inp.starting_ppe, ap=0.0, debt=0.0,
                             equity_capital=total_paid_in, retained_earnings=0.0, capex=inp.starting_ppe,
                             debt_issued=0.0, equity_issued=total_paid_in)
    asm = TS.ForecastAssumptions(
        years=n, revenue_growth=growth, cogs_pct=cogs_pct, salaries_pct=inp.payroll_pct_revenue,
        rent=other_opex_abs, da_pct_ppe=inp.da_pct_ppe, interest_pct_debt=inp.interest_pct_debt,
        tax_rate=inp.tax_rate, ar_days=inp.ar_days, inventory_days=inp.inventory_days, ap_days=inp.ap_days,
        capex=[revenue_path[i + 1] * (inp.capex_pct_revenue if isinstance(inp.capex_pct_revenue, (int, float)) else inp.capex_pct_revenue[i]) for i in range(n)],
        debt_issued=[inp.debt_raised.get(i, 0.0) for i in range(n)],
        equity_issued=[inp.equity_raised.get(i, 0.0) for i in range(n)])
    return TS.run([seed], asm, ppe_opening0=0.0, debt_opening0=0.0)


def dcf_from_projection(result: TS.ThreeStatementResult, discount_rate: float, perpetual_growth: float = 0.03,
                        terminal_method: str = "perpetuity", transaction_date: str = "2026-01-01",
                        fiscal_year_end: str = "2026-12-31", shares_outstanding: float = 1_000_000.0,
                        tax_rate: float = 0.21) -> Dict[str, Any]:
    """Translates the forecast years of a StartupInputs projection into finmodel.dcf.DCFInputs (EBIT = EBT +
    interest add-back) and runs the existing, CFI-reconciled DCF engine — no new valuation math here. `tax_rate`
    here is the DCF's own unlevered (EBIT-basis) cash-tax rate; pass the same rate used for the projection's
    StartupInputs.tax_rate for consistency, or a marginal statutory rate if the projection's own rate reflects
    NOL carryforwards or credits you don't want to assume continue into the DCF."""
    n_h = result.n_hist
    ebit = [result.rows["Earnings Before Tax"][i] + result.rows["Interest"][i] for i in range(n_h, len(result.years))]
    da = result.rows["Depreciation & Amortization"][n_h:]
    capex = result.rows["Plus Capex"][n_h:]
    change_nwc = result.rows["Change in NWC"][n_h:]
    inp = DCFInputs(ebit=ebit, da=da, change_nwc=change_nwc, capex=capex, tax_rate=tax_rate,
                    discount_rate=discount_rate, perpetual_growth=perpetual_growth, terminal_method=terminal_method,
                    transaction_date=transaction_date, fiscal_year_end=fiscal_year_end,
                    current_price=1.0,  # no market price exists for a private startup; a nonzero placeholder only
                                        # avoids dcf.run()'s target_price_upside divide-by-zero — not used below
                    shares_outstanding=shares_outstanding, debt=result.rows["Debt"][n_h - 1] if n_h else 0.0,
                    cash=result.rows["Cash"][n_h - 1] if n_h else 0.0)
    res = dcf_run(inp)
    return {"enterprise_value": res["enterprise_value"], "equity_value": res["equity_value"],
            "value_per_share": res["equity_value_per_share"], "terminal_value": res["terminal_value"],
            "ufcf": res["ufcf"], "assumptions": {"discount_rate": discount_rate,
            "perpetual_growth": perpetual_growth, "implied_tax_rate": tax_rate}}


def benchmark_against_sector(result: TS.ThreeStatementResult, sector: str, exit_year_index: int = -1) -> Dict[str, Any]:
    """Compares the projection's terminal-year (or `exit_year_index`) margin against the REAL, most-recent-fiscal-
    -year margin of each real peer this toolkit already validated for `sector` (data/edgar/<ticker>.json — the
    same extracts docs/FOOTBALL_FIELD_*.md are built on). Raises if `sector` has no real peer data on disk yet —
    this function refuses to fabricate a benchmark rather than silently returning nothing useful."""
    if sector not in SECTOR_PEER_TICKERS:
        raise ValueError(f"no real peer data for sector {sector!r}; available: {sorted(SECTOR_PEER_TICKERS)}")
    field_key, revenue_key = SECTOR_DEFAULT_FIELDS.get(sector, ("operating_income", "revenue"))

    n_h = result.n_hist
    idx = exit_year_index if exit_year_index >= 0 else len(result.years) + exit_year_index
    revenue = result.rows["Revenue"][idx]
    ebit = result.rows["Earnings Before Tax"][idx] + result.rows["Interest"][idx]
    if field_key == "net_income":
        startup_margin = safe_div(result.rows["Net Earnings"][idx], revenue)  # no equity concept for a startup P&L; ROE-style peers compared on net margin instead
    else:
        startup_margin = safe_div(ebit, revenue)

    peer_margins = {}
    for ticker in SECTOR_PEER_TICKERS[sector]:
        path = ROOT / "data" / "edgar" / f"{ticker}.json"
        if not path.exists(): continue
        years = json.loads(path.read_text())["years"]
        latest_fy = sorted(years)[-1]
        row = years[latest_fy]
        num, denom = row.get(field_key), row.get(revenue_key)
        if num is None or not denom: continue
        peer_margins[ticker] = {"fy": latest_fy, "margin": num / denom}

    values = sorted(v["margin"] for v in peer_margins.values())
    lo, hi = (values[0], values[-1]) if values else (None, None)
    inside_range = lo is not None and lo <= startup_margin <= hi
    return {"sector": sector, "field": field_key, "revenue_field": revenue_key, "exit_year": result.years[idx],
            "startup_margin": startup_margin, "real_peer_margins": peer_margins,
            "real_range": {"low": lo, "high": hi}, "inside_real_range": inside_range,
            "note": ("within the real range these peers actually reported" if inside_range else
                     "OUTSIDE every real peer's actual reported range — treat this scenario as aggressive/"
                     "conservative relative to real, mature companies in this sector, not as a typo to silently accept")}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    startup = dict(d["startup"])
    for key in ("equity_raised", "debt_raised"):
        if key in startup:  # JSON object keys are always strings; the model indexes by int forecast-year
            startup[key] = {int(k): v for k, v in startup[key].items()}
    inp = StartupInputs(**startup)
    result = build_three_statement(inp)
    out: Dict[str, Any] = {"three_statement": result.to_dict()}
    if "dcf" in d:
        out["dcf"] = dcf_from_projection(result, **d["dcf"])
    if "benchmark_sector" in d:
        out["benchmark"] = benchmark_against_sector(result, d["benchmark_sector"], d.get("benchmark_exit_year_index", -1))
    return out
