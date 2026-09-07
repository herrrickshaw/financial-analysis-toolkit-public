"""Unlevered DCF, distilled from CFI 'DCF Model Template (Updated)'.

  UFCF  = EBIT - cash taxes + D&A - capex - change in NWC
  TV    = average of  perpetuity-growth TV  and  exit EV/EBITDA-multiple TV   (CFI default; selectable)
  EV    = XNPV(discount rate, [0, UFCF_1*yf_1, ..., UFCF_n*yf_n, TV], dates)  -- stub-period aware
  Equity value = EV + cash - debt ;  per share = / shares ;  IRR = XIRR of (-market EV, flows..., TV)

Dates: period t ends on the fiscal-year-end month/day of (FYE.year + t); the first period runs from the
transaction date to that FYE, so its year-fraction (Excel YEARFRAC basis 0) scales the first flow.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Sequence

from .fin import to_date, yearfrac, xnpv, xirr


@dataclass
class DCFInputs:
    ebit: List[float]
    da: List[float]
    change_nwc: List[float]
    capex: Any                     # scalar or list (per forecast year)
    tax_rate: float = 0.25
    discount_rate: float = 0.12
    perpetual_growth: float = 0.03
    ev_ebitda_multiple: float = 7.0
    transaction_date: Any = "2017-12-31"
    fiscal_year_end: Any = "2018-06-30"
    current_price: float = 25.0
    shares_outstanding: float = 20000.0
    debt: float = 30000.0
    cash: float = 0.0
    terminal_method: str = "average"   # "average" | "perpetuity" | "multiple"
    yearfrac_basis: int = 0
    mid_year: bool = False             # discount each period's cash flow from the middle of the period (terminal value stays at period end)

    def capex_list(self) -> List[float]:
        n = len(self.ebit)
        if isinstance(self.capex, (int, float)):
            return [float(self.capex)] * n
        c = [float(x) for x in self.capex]
        if len(c) != n:
            raise ValueError("capex list must match ebit length")
        return c


def period_dates(transaction_date, fiscal_year_end, n: int) -> List[date]:
    """[transaction_date, FYE(y0), FYE(y0+1), ..., FYE(y0+n-1)]"""
    t0 = to_date(transaction_date)
    fye = to_date(fiscal_year_end)
    out = [t0]
    for t in range(n):
        y = fye.year + t
        d = fye.day
        # handle Feb-29 style FYE safely
        while True:
            try:
                out.append(date(y, fye.month, d))
                break
            except ValueError:
                d -= 1
    return out


def run(inp: DCFInputs) -> Dict[str, Any]:
    n = len(inp.ebit)
    if not (len(inp.da) == len(inp.change_nwc) == n):
        raise ValueError("ebit, da and change_nwc must have the same length")
    capex = inp.capex_list()
    dates = period_dates(inp.transaction_date, inp.fiscal_year_end, n)
    yf = [yearfrac(dates[t], dates[t + 1], inp.yearfrac_basis) for t in range(n)]
    taxes = [e * inp.tax_rate for e in inp.ebit]
    ufcf = [inp.ebit[t] - taxes[t] + inp.da[t] - capex[t] - inp.change_nwc[t] for t in range(n)]
    ebitda_last = inp.ebit[-1] + inp.da[-1]
    r, g = inp.discount_rate, inp.perpetual_growth
    if r <= g:
        raise ValueError("discount rate must exceed perpetual growth rate")
    tv_perp = ufcf[-1] * (1 + g) / (r - g)
    tv_mult = inp.ev_ebitda_multiple * ebitda_last
    tv = {"average": (tv_perp + tv_mult) / 2, "perpetuity": tv_perp, "multiple": tv_mult}[inp.terminal_method]

    market_cap = inp.shares_outstanding * inp.current_price
    market_ev = market_cap + inp.debt - inp.cash

    # valuation flows: entry 0, scaled FCFs, terminal value at last date
    val_flows = [0.0] + [ufcf[t] * yf[t] for t in range(n)] + [tv]
    val_dates = dates + [dates[-1]]
    if inp.mid_year:
        from datetime import timedelta
        mid = [dates[t] + timedelta(days=(dates[t + 1] - dates[t]).days / 2) for t in range(n)]
        # xnpv discounts relative to its first date, so anchor both legs at the actual valuation date (dates[0])
        # with an explicit zero cash flow, rather than letting the first midpoint become time zero.
        ev = xnpv(r, [0.0] + [ufcf[t] * yf[t] for t in range(n)], [dates[0]] + mid) + xnpv(r, [0.0, tv], [dates[0], dates[-1]])
    else:
        ev = xnpv(r, val_flows, val_dates)
    equity = ev + inp.cash - inp.debt
    per_share = equity / inp.shares_outstanding

    # rate-of-return flows: pay market EV at entry, receive FCFs and TV
    irr_flows = [-market_ev] + [ufcf[t] * yf[t] for t in range(n)] + [tv]
    try:
        irr_val = xirr(irr_flows, val_dates)
    except ValueError:
        irr_val = float("nan")

    return {
        "dates": [d.isoformat() for d in dates],
        "years": [d.year for d in dates[1:]],
        "year_fraction": yf,
        "ebit": list(inp.ebit), "cash_taxes": taxes, "da": list(inp.da), "capex": capex,
        "change_nwc": list(inp.change_nwc), "ufcf": ufcf,
        "terminal_value": {"perpetuity_growth": tv_perp, "ev_ebitda": tv_mult, "used": tv, "method": inp.terminal_method},
        "valuation_flows": val_flows,
        "enterprise_value": ev, "plus_cash": inp.cash, "less_debt": inp.debt,
        "equity_value": equity, "equity_value_per_share": per_share,
        "market": {"market_cap": market_cap, "plus_debt": inp.debt, "less_cash": inp.cash,
                   "enterprise_value": market_ev, "price": inp.current_price},
        "target_price_upside": per_share / inp.current_price - 1,
        "upside_per_share": per_share - inp.current_price,
        "irr": irr_val,
        "discount_rate": r, "perpetual_growth": g, "mid_year": inp.mid_year,
    }


def sensitivity(inp: DCFInputs, discount_rates: Sequence[float], growth_rates: Sequence[float],
                metric: str = "equity_value_per_share") -> Dict[str, Any]:
    """2-D table of `metric` across discount rate (rows) x perpetual growth (cols)."""
    from dataclasses import replace
    table = []
    for r in discount_rates:
        row = []
        for g in growth_rates:
            try:
                row.append(run(replace(inp, discount_rate=r, perpetual_growth=g))[metric])
            except ValueError:
                row.append(float("nan"))
        table.append(row)
    return {"rows": list(discount_rates), "cols": list(growth_rates), "metric": metric, "table": table}


def clean(d: Dict[str, Any]) -> Dict[str, Any]:
    """Drop comment keys (those starting with '_')."""
    return {k: v for k, v in d.items() if not str(k).startswith("_")}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return run(DCFInputs(**clean(d)))


# ----------------------------------------------------------------------------- DCF diagnostics
def unlevered_tax_schedule(ebit: Sequence[float], tax_rate: float) -> List[float]:
    """The correct 'as if all-equity-financed' tax build, with its own independent loss-carryforward chain (real
    NOLs are tracked on EBIT alone, not on EBIT-less-interest) — the real fix from this toolkit's own
    due-diligence pass on a real project-finance model, whose otherwise-unlevered free cash flow was deducting
    the company's actual, interest-deductible (levered) cash tax bill instead."""
    taxes: List[float] = []
    loss_cf = 0.0
    for e in ebit:
        taxable = max(0.0, e - loss_cf)
        taxes.append(taxable * tax_rate)
        loss_cf = max(0.0, loss_cf - e) if e >= 0 else -e
    return taxes


def check_unlevered_tax_consistency(ebit: Sequence[float], cash_taxes_used: Sequence[float], tax_rate: float,
                                    tolerance: float = 0.01) -> Dict[str, Any]:
    """Flags the real, easy-to-miss DCF-construction bug this check is named for: an unlevered free cash flow
    (no interest subtracted) that nonetheless deducts a LEVERED cash tax figure — one already computed on
    after-interest taxable income — rather than the hypothetical unlevered tax above. Discounting such a cash
    flow at a WACC that ALSO carries an after-tax cost of debt term double-counts the interest tax shield: once
    via the lower taxes in the numerator, once via the discount rate in the denominator. `cash_taxes_used` is
    whatever tax figure the free-cash-flow build ACTUALLY subtracts — pass the real, filed/modeled cash tax
    line to check it, or a hypothetical one to confirm a fix. Real loss carryforwards can make a genuinely
    CORRECT unlevered build look "flagged" if `cash_taxes_used` was computed with a different NOL assumption
    than this function's own chain — treat a flagged period as a lead to investigate, not an automatic verdict."""
    correct = unlevered_tax_schedule(ebit, tax_rate)
    n = len(ebit)
    if len(cash_taxes_used) != n:
        raise ValueError("ebit and cash_taxes_used must have the same length")
    gap = [correct[i] - cash_taxes_used[i] for i in range(n)]
    flagged = [i for i in range(n) if abs(gap[i]) > tolerance * max(1.0, abs(correct[i]))]
    return {"correct_unlevered_tax": correct, "cash_taxes_used": list(cash_taxes_used), "gap": gap,
            "flagged_periods": flagged, "likely_uses_levered_tax": len(flagged) > n // 2,
            "total_gap_undiscounted": sum(gap)}


# ----------------------------------------------------------------------------- reverse DCF and Monte Carlo
def implied_growth(inp: DCFInputs, target_price: Optional[float] = None, lo: float = -0.20, hi: float = 0.20, tol: float = 1e-9) -> Dict[str, Any]:
    """Reverse DCF: the perpetual growth rate at which the model's equity value per share equals the current (or a
    target) price, holding every other assumption fixed. Uses the perpetuity terminal method so the answer is exact;
    bisection on [lo, hi] (growth must stay below the discount rate)."""
    import copy
    price = inp.current_price if target_price is None else target_price
    base = copy.copy(inp); base.terminal_method = "perpetuity"
    hi = min(hi, base.discount_rate - 1e-4)

    def f(g):
        x = copy.copy(base); x.perpetual_growth = g; return run(x)["equity_value_per_share"] - price
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        return {"implied_growth": None, "price": price, "bracket": [lo, hi], "note": "no growth rate in the bracket reproduces the price"}
    for _ in range(200):
        mid = (lo + hi) / 2; fm = f(mid)
        if abs(fm) < tol or hi - lo < tol: break
        if flo * fm < 0: hi, fhi = mid, fm
        else: lo, flo = mid, fm
    return {"implied_growth": mid, "price": price, "model_growth": inp.perpetual_growth, "discount_rate": base.discount_rate,
            "reading": "market prices in faster perpetual growth than the model" if mid > inp.perpetual_growth else "market prices in slower perpetual growth than the model"}


def monte_carlo(inp: DCFInputs, runs: int = 2000, seed: int = 7, discount_rate_sd: float = 0.01, growth_sd: float = 0.005,
                ebit_scale_sd: float = 0.10, capex_scale_sd: float = 0.10, percentiles: Sequence[float] = (5, 25, 50, 75, 95)) -> Dict[str, Any]:
    """Probabilistic DCF: draws discount rate, perpetual growth, an EBIT scale factor (applied to every forecast year) and a
    capex scale factor from normal distributions around the base case, re-runs the model and reports the distribution of
    equity value per share. Dependency-free (random.gauss), seeded for reproducibility; growth is capped below the
    discount rate."""
    import copy, random, statistics
    rng = random.Random(seed); out: List[float] = []; evs: List[float] = []
    for _ in range(runs):
        x = copy.copy(inp)
        x.discount_rate = max(0.01, rng.gauss(inp.discount_rate, discount_rate_sd))
        x.perpetual_growth = min(rng.gauss(inp.perpetual_growth, growth_sd), x.discount_rate - 0.005)
        es = max(0.0, rng.gauss(1.0, ebit_scale_sd)); cs = max(0.0, rng.gauss(1.0, capex_scale_sd))
        x.ebit = [e * es for e in inp.ebit]; x.capex = [c * cs for c in inp.capex_list()]
        r = run(x); out.append(r["equity_value_per_share"]); evs.append(r["enterprise_value"])
    xs = sorted(out)
    pct = {p: xs[min(len(xs) - 1, int(round(p / 100 * (len(xs) - 1))))] for p in percentiles}
    prob_above = sum(1 for v in out if v > inp.current_price) / len(out)
    hist_lo, hist_hi = xs[0], xs[-1]; bins = 20; width = (hist_hi - hist_lo) / bins or 1.0
    hist = [0] * bins
    for v in xs: hist[min(bins - 1, int((v - hist_lo) / width))] += 1
    return {"runs": runs, "seed": seed, "mean": statistics.fmean(out), "median": statistics.median(out), "stdev": statistics.pstdev(out), "percentiles": pct,
            "prob_value_above_price": prob_above, "current_price": inp.current_price, "histogram": {"edges": [hist_lo + i * width for i in range(bins + 1)], "counts": hist},
            "enterprise_value_mean": statistics.fmean(evs), "assumptions": {"discount_rate_sd": discount_rate_sd, "growth_sd": growth_sd, "ebit_scale_sd": ebit_scale_sd, "capex_scale_sd": capex_scale_sd}}
