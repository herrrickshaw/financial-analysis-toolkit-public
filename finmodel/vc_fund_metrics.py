"""VC/PE fund performance metrics: the standard LP-reporting measures (ILPA's own reporting template defines
DPI/RVPI/TVPI exactly this way) plus a deal-level MOIC/IRR helper and a GP/LP carry waterfall — the fund
performance analytics and LP reporting a VC fund's own finance function (or an outsourced fund-administration/
advisory firm) produces every quarter.

  DPI  (Distributions to Paid-In)   = distributions / paid_in       — realized, cash-on-cash multiple
  RVPI (Residual Value to Paid-In)  = NAV / paid_in                 — unrealized multiple
  TVPI (Total Value to Paid-In)     = DPI + RVPI = (distributions + NAV) / paid_in
  IRR                               = XIRR of (capital calls as negative, distributions as positive, NAV as a
                                       final "distribution" on the as-of date) — reuses finmodel.fin.xirr,
                                       the same primitive the DCF/comps engines already use.

Carry waterfall here is the standard "European" (whole-fund) structure: return of capital to LPs, then a
preferred return (hurdle, compounded from each call's own date), then a 100% GP catch-up up to the target carry
share of profit-above-capital, then a final LP/GP split (usually 80/20) on everything after — distilled from
ILPA's own waterfall guidance and Metrick & Yasuda's *Venture Capital and the Finance of Innovation*.

`american_waterfall()` is the deal-by-deal ("American") alternative — flagged as a real, deliberately
deferred gap in `docs/OPERATING_FINANCE_TOOLS.md` until there was "a real multi-year fund dataset to model it
against." Revisited in `docs/DEFERRED_GAPS_REVISITED.md`-style reasoning: the objection didn't actually apply
once a small, hand-constructed multi-deal example (a winner realized before a loser) is enough to demonstrate
and test the real mechanic a full historical fund dataset was never strictly required for.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div, xirr


@dataclass
class CashFlow:
    date: str          # ISO date
    amount: float       # capital calls are NEGATIVE (cash leaving the LP), distributions are POSITIVE


def fund_metrics(cashflows: Sequence[CashFlow], nav: float, as_of: str) -> Dict[str, Any]:
    """Standard fund-level LP metrics as of `as_of` (NAV's valuation date). `cashflows` should include every
    capital call (negative) and distribution (positive) to date; NAV is the current unrealized portfolio value."""
    paid_in = -sum(c.amount for c in cashflows if c.amount < 0)
    distributions = sum(c.amount for c in cashflows if c.amount > 0)
    dpi = safe_div(distributions, paid_in)
    rvpi = safe_div(nav, paid_in)
    tvpi = dpi + rvpi
    irr_flows = [c.amount for c in cashflows] + [nav]
    irr_dates = [c.date for c in cashflows] + [as_of]
    try:
        irr = xirr(irr_flows, irr_dates)
    except (ValueError, OverflowError):
        irr = None
    return {"as_of": as_of, "paid_in": paid_in, "distributions": distributions, "nav": nav,
            "dpi": dpi, "rvpi": rvpi, "tvpi": tvpi, "irr": irr}


def deal_metrics(invested: float, proceeds_to_date: float, current_value: float,
                 cashflow_dates: Optional[Sequence[str]] = None, cashflow_amounts: Optional[Sequence[float]] = None,
                 as_of: Optional[str] = None) -> Dict[str, Any]:
    """Single-investment MOIC (always computable) and, if real dated cash flows are supplied, IRR too. MOIC =
    (proceeds to date + current unrealized value) / invested capital — the deal-level analogue of fund TVPI."""
    moic = safe_div(proceeds_to_date + current_value, invested)
    out: Dict[str, Any] = {"invested": invested, "proceeds_to_date": proceeds_to_date, "current_value": current_value, "moic": moic}
    if cashflow_dates and cashflow_amounts and as_of:
        flows = list(cashflow_amounts) + [current_value]
        dates = list(cashflow_dates) + [as_of]
        try:
            out["irr"] = xirr(flows, dates)
        except (ValueError, OverflowError):
            out["irr"] = None
    return out


def carry_waterfall(cashflows: Sequence[CashFlow], nav: float, as_of: str, hurdle_rate: float = 0.08,
                    carry_pct: float = 0.20, gp_commitment_pct: float = 0.0) -> Dict[str, Any]:
    """European (whole-fund) waterfall: (1) return LPs' paid-in capital, (2) pay LPs a preferred return
    (hurdle, compounded daily-equivalent via (1+hurdle)^years from each call's own date to `as_of`) on their
    called capital, (3) 100% GP catch-up until the GP's cumulative carry equals `carry_pct` of profit already
    distributed above return-of-capital, (4) split everything remaining `1-carry_pct`/`carry_pct` LP/GP.
    Assumes all distributable value (past distributions + current NAV, i.e. TVPI's numerator) is being
    allocated as of `as_of` — a whole-fund, as-if-liquidated-today view, not a running historical allocation."""
    from datetime import date as _date
    from .fin import to_date
    paid_in = -sum(c.amount for c in cashflows if c.amount < 0)
    total_value = sum(c.amount for c in cashflows if c.amount > 0) + nav  # distributions to date + unrealized NAV
    as_of_d = to_date(as_of)
    hurdle_amount = 0.0
    for c in cashflows:
        if c.amount < 0:
            years = (as_of_d - to_date(c.date)).days / 365.25
            hurdle_amount += -c.amount * ((1 + hurdle_rate) ** years - 1)

    remaining = total_value
    lp_total = 0.0; gp_total = 0.0
    # tier 1: return of capital
    tier1 = min(remaining, paid_in)
    lp_total += tier1; remaining -= tier1
    # tier 2: preferred return (hurdle)
    tier2 = min(remaining, hurdle_amount)
    lp_total += tier2; remaining -= tier2
    # tier 3: GP catch-up -- 100% to GP until GP's share of (tier2 + catch-up) equals carry_pct of that same sum
    catch_up_target = tier2 * carry_pct / (1 - carry_pct) if carry_pct < 1 else remaining
    tier3 = min(remaining, catch_up_target)
    gp_total += tier3; remaining -= tier3
    # tier 4: residual split
    lp_total += remaining * (1 - carry_pct)
    gp_total += remaining * carry_pct

    lp_net_multiple = safe_div(lp_total, paid_in)
    return {"paid_in": paid_in, "total_value": total_value, "hurdle_amount": hurdle_amount,
            "tiers": {"return_of_capital": tier1, "preferred_return": tier2, "gp_catch_up": tier3,
                     "residual_split_lp": remaining * (1 - carry_pct), "residual_split_gp": remaining * carry_pct},
            "lp_total": lp_total, "gp_total": gp_total, "lp_net_tvpi": lp_net_multiple,
            "effective_carry_pct_of_profit": safe_div(gp_total, max(total_value - paid_in, 1e-9))}


def american_waterfall(deals: Sequence[Dict[str, Any]], hurdle_rate: float = 0.08, carry_pct: float = 0.20) -> Dict[str, Any]:
    """Each deal: {"name": str, "invested": float, "proceeds": float, "invested_date": str, "realized_date":
    str}. Deals are processed in `realized_date` order; EACH ONE pays out its own return-of-capital/
    preferred-return/GP-catch-up/residual-split tiers as it is realized (unlike `carry_waterfall`'s
    whole-fund snapshot), so a GP can receive carry on an early winner before a later loser is realized.
    After every deal, checks whether the GP's CUMULATIVE carry received so far exceeds `carry_pct` of the
    fund's CUMULATIVE profit across every deal realized so far; if a later loser shrinks that cumulative
    profit below what already-paid carry implies, the excess is a real CLAWBACK the GP owes LPs back -- the
    provision every American-waterfall fund agreement includes precisely because deal-by-deal payout creates
    this risk that a whole-fund waterfall never has."""
    from .fin import to_date
    sorted_deals = sorted(deals, key=lambda dl: to_date(dl["realized_date"]))
    results: List[Dict[str, Any]] = []
    cumulative_invested = 0.0
    cumulative_proceeds = 0.0
    cumulative_gp_received = 0.0
    for deal in sorted_deals:
        invested = deal["invested"]
        proceeds = deal["proceeds"]
        years = (to_date(deal["realized_date"]) - to_date(deal["invested_date"])).days / 365.25
        remaining = proceeds
        tier1 = min(remaining, invested); remaining -= tier1
        hurdle_amount = invested * ((1 + hurdle_rate) ** years - 1)
        tier2 = min(remaining, hurdle_amount); remaining -= tier2
        catch_up_target = tier2 * carry_pct / (1 - carry_pct) if carry_pct < 1 else remaining
        tier3 = min(remaining, catch_up_target); remaining -= tier3
        tier4_gp = remaining * carry_pct
        tier4_lp = remaining * (1 - carry_pct)
        gp_this_deal = tier3 + tier4_gp
        lp_this_deal = tier1 + tier2 + tier4_lp

        cumulative_invested += invested
        cumulative_proceeds += proceeds
        cumulative_gp_received += gp_this_deal
        cumulative_fund_profit = cumulative_proceeds - cumulative_invested
        target_cumulative_gp_carry = carry_pct * max(0.0, cumulative_fund_profit)
        clawback_owed = max(0.0, cumulative_gp_received - target_cumulative_gp_carry)

        results.append({"name": deal.get("name"), "invested": invested, "proceeds": proceeds,
                        "gp_payout": gp_this_deal, "lp_payout": lp_this_deal,
                        "cumulative_gp_received": cumulative_gp_received,
                        "cumulative_fund_profit": cumulative_fund_profit,
                        "target_cumulative_gp_carry": target_cumulative_gp_carry,
                        "clawback_owed": clawback_owed})
    return {"deals": results, "total_gp_payout": sum(r["gp_payout"] for r in results),
            "total_lp_payout": sum(r["lp_payout"] for r in results),
            "final_clawback_owed": results[-1]["clawback_owed"] if results else 0.0}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    cashflows = [CashFlow(**c) for c in d["cashflows"]]
    out: Dict[str, Any] = {"fund_metrics": fund_metrics(cashflows, d["nav"], d["as_of"])}
    if "carry" in d:
        c = d["carry"]
        out["carry_waterfall"] = carry_waterfall(cashflows, d["nav"], d["as_of"], **c)
    if "deals" in d:
        out["deals"] = {name: deal_metrics(**params) for name, params in d["deals"].items()}
    if "american_waterfall" in d:
        out["american_waterfall"] = american_waterfall(**d["american_waterfall"])
    return out
