"""Cost of capital: CAPM cost of equity, Hamada beta levering, Damodaran-style synthetic credit rating from interest
coverage, after-tax cost of debt and the market-value-weighted WACC — the inputs `dcf.DCFInputs.discount_rate` needs.

Synthetic-rating table: Damodaran's large-firm (market cap > $5bn) coverage-to-rating map with the January-2024
default spreads (ratings.xls / synthetic rating page). Values are illustrative of the method; refresh from
https://pages.stern.nyu.edu/~adamodar/ when using for a live valuation."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Sequence, Tuple

from .fin import safe_div

# (min coverage, max coverage, rating, default spread) — large non-financial firms
SYNTHETIC_RATING_LARGE: List[Tuple[float, float, str, float]] = [
    (8.50, 1e9, "AAA", 0.0059), (6.50, 8.50, "AA", 0.0070), (5.50, 6.50, "A+", 0.0092), (4.25, 5.50, "A", 0.0107), (3.00, 4.25, "A-", 0.0121),
    (2.50, 3.00, "BBB", 0.0147), (2.25, 2.50, "BB+", 0.0174), (2.00, 2.25, "BB", 0.0221), (1.75, 2.00, "B+", 0.0314), (1.50, 1.75, "B", 0.0361),
    (1.25, 1.50, "B-", 0.0524), (0.80, 1.25, "CCC", 0.0851), (0.65, 0.80, "CC", 0.1178), (0.20, 0.65, "C", 0.1700), (-1e9, 0.20, "D", 0.2000)]
# small firms (market cap < $5bn) need higher coverage for the same rating
SYNTHETIC_RATING_SMALL: List[Tuple[float, float, str, float]] = [
    (12.5, 1e9, "AAA", 0.0059), (9.5, 12.5, "AA", 0.0070), (7.5, 9.5, "A+", 0.0092), (6.0, 7.5, "A", 0.0107), (4.5, 6.0, "A-", 0.0121),
    (4.0, 4.5, "BBB", 0.0147), (3.5, 4.0, "BB+", 0.0174), (3.0, 3.5, "BB", 0.0221), (2.5, 3.0, "B+", 0.0314), (2.0, 2.5, "B", 0.0361),
    (1.5, 2.0, "B-", 0.0524), (1.25, 1.5, "CCC", 0.0851), (0.8, 1.25, "CC", 0.1178), (0.5, 0.8, "C", 0.1700), (-1e9, 0.5, "D", 0.2000)]


def synthetic_rating(ebit: float, interest_expense: float, large_firm: bool = True) -> Dict[str, Any]:
    cov = float("inf") if interest_expense <= 0 else ebit / interest_expense
    table = SYNTHETIC_RATING_LARGE if large_firm else SYNTHETIC_RATING_SMALL
    for lo, hi, rating, spread in table:
        if lo <= cov < hi or (cov == float("inf") and hi >= 1e9):
            return {"interest_coverage": cov, "rating": rating, "default_spread": spread}
    return {"interest_coverage": cov, "rating": "D", "default_spread": table[-1][3]}


def cost_of_equity(risk_free: float, beta: float, equity_risk_premium: float, size_premium: float = 0.0, country_risk_premium: float = 0.0, lambda_crp: float = 1.0) -> float:
    """CAPM with optional size and country-risk premia (Damodaran's lambda approach)."""
    return risk_free + beta * equity_risk_premium + size_premium + lambda_crp * country_risk_premium


def unlever_beta(levered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    return levered_beta / (1 + (1 - tax_rate) * debt_to_equity)


def relever_beta(unlevered_beta: float, debt_to_equity: float, tax_rate: float) -> float:
    return unlevered_beta * (1 + (1 - tax_rate) * debt_to_equity)


def bottom_up_beta(peers: Sequence[Dict[str, float]], target_debt_to_equity: float, tax_rate: float, cash_adjust: bool = False) -> Dict[str, Any]:
    """Average peers' unlevered betas (each unlevered at its own D/E and tax rate) and re-lever at the target's D/E.
    peers: [{"beta": ..., "debt_to_equity": ..., "tax_rate": ..., optional "cash_to_firm_value": ...}]."""
    unl = []
    for p in peers:
        b = unlever_beta(p["beta"], p["debt_to_equity"], p.get("tax_rate", tax_rate))
        if cash_adjust and p.get("cash_to_firm_value"): b = b / (1 - p["cash_to_firm_value"])
        unl.append(b)
    avg = sum(unl) / len(unl)
    return {"peer_unlevered_betas": unl, "average_unlevered_beta": avg, "relevered_beta": relever_beta(avg, target_debt_to_equity, tax_rate)}


@dataclass
class WACCInputs:
    risk_free: float
    equity_risk_premium: float
    beta: float
    market_cap: float
    debt: float
    tax_rate: float
    cost_of_debt: Optional[float] = None       # pre-tax; if None, derived as risk_free + synthetic default spread
    ebit: Optional[float] = None
    interest_expense: Optional[float] = None
    large_firm: bool = True
    preferred: float = 0.0
    cost_of_preferred: float = 0.0
    size_premium: float = 0.0
    country_risk_premium: float = 0.0


def wacc(inp: WACCInputs) -> Dict[str, Any]:
    ke = cost_of_equity(inp.risk_free, inp.beta, inp.equity_risk_premium, inp.size_premium, inp.country_risk_premium)
    rating = None
    if inp.cost_of_debt is None:
        if inp.ebit is None or inp.interest_expense is None:
            raise ValueError("give cost_of_debt, or ebit and interest_expense for a synthetic rating")
        rating = synthetic_rating(inp.ebit, inp.interest_expense, inp.large_firm); kd = inp.risk_free + rating["default_spread"]
    else:
        kd = inp.cost_of_debt
    v = inp.market_cap + inp.debt + inp.preferred
    we, wd, wp = safe_div(inp.market_cap, v), safe_div(inp.debt, v), safe_div(inp.preferred, v)
    kd_after = kd * (1 - inp.tax_rate)
    w = we * ke + wd * kd_after + wp * inp.cost_of_preferred
    return {"cost_of_equity": ke, "cost_of_debt_pretax": kd, "cost_of_debt_aftertax": kd_after, "weights": {"equity": we, "debt": wd, "preferred": wp},
            "wacc": w, "synthetic_rating": rating, "debt_to_equity": safe_div(inp.debt, inp.market_cap)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "peers" in d:
        out["bottom_up_beta"] = bottom_up_beta(d["peers"], d["wacc"]["debt"] / d["wacc"]["market_cap"], d["wacc"]["tax_rate"])
        d["wacc"].setdefault("beta", out["bottom_up_beta"]["relevered_beta"])
    out["wacc"] = wacc(WACCInputs(**d["wacc"]))
    return out
