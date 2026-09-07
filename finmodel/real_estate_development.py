"""Ground-up real-estate development pro forma: total development cost, a construction-loan draw schedule
with capitalized interest, and the two metrics every development deal is actually underwritten on -- yield
on cost and the development spread against market cap rates -- distinct from finmodel.project_finance's
cap_rate_valuation (which prices an ALREADY-STABILIZED asset, not a ground-up build). Terminology and
method follow standard real-estate-finance teaching (Geltner, Miller, Clayton & Eichholtz, *Commercial Real
Estate Analysis and Investments*; Linneman, *Real Estate Finance and Investments*).

  * Total development cost (TDC) = land + hard costs (construction) + soft costs (design, permits, fees) +
    a contingency reserve.
  * A construction loan draws down over the build period; interest on the drawn balance is typically
    CAPITALIZED (added to the loan balance, not paid in cash) via an interest reserve, so the loan balance at
    completion is the sum of every draw plus every period's accrued interest.
  * Yield on cost = stabilized NOI / total cost basis (draws + capitalized interest) -- the development
    analogue of a cap rate, compared against the market exit cap rate to size the developer's margin.
  * Development spread = yield on cost - exit cap rate, in basis points -- developers typically require
    100-200 bps of spread to compensate for construction, lease-up and market risk relative to buying an
    already-stabilized asset at the market cap rate.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import irr, safe_div


def total_development_cost(land_cost: float, hard_costs: float, soft_costs: float, contingency_pct: float = 0.0) -> Dict[str, Any]:
    base = land_cost + hard_costs + soft_costs
    contingency = base * contingency_pct
    return {"land_cost": land_cost, "hard_costs": hard_costs, "soft_costs": soft_costs,
            "contingency": contingency, "total_development_cost": base + contingency}


def construction_loan_schedule(draws: Sequence[float], interest_rate_annual: float, periods_per_year: int = 12) -> Dict[str, Any]:
    """Walks the draw schedule period by period, capitalizing interest on the BEGINNING balance each period
    (drawn funds start accruing interest from the following period, the standard construction-loan
    convention) into the ending balance."""
    periodic_rate = interest_rate_annual / periods_per_year
    balance = 0.0
    periods: List[Dict[str, Any]] = []
    total_capitalized_interest = 0.0
    for draw in draws:
        interest = balance * periodic_rate
        balance = balance + draw + interest
        total_capitalized_interest += interest
        periods.append({"draw": draw, "interest_accrued": interest, "ending_balance": balance})
    return {"periods": periods, "total_draws": sum(draws), "total_capitalized_interest": total_capitalized_interest,
            "ending_loan_balance": balance}


def yield_on_cost(stabilized_noi: float, total_cost_basis: float) -> float:
    return safe_div(stabilized_noi, total_cost_basis)


def development_spread(yield_on_cost_value: float, exit_cap_rate: float) -> Dict[str, Any]:
    return {"yield_on_cost": yield_on_cost_value, "exit_cap_rate": exit_cap_rate,
            "spread_bps": (yield_on_cost_value - exit_cap_rate) * 10000}


def development_pro_forma(draws: Sequence[float], interest_rate_annual: float, stabilized_noi: float,
                          exit_cap_rate: float, periods_per_year: int = 12) -> Dict[str, Any]:
    """Combines the construction-loan schedule with a stabilized exit valuation into the full unlevered
    development pro forma: total cost basis, exit value, development profit, yield on cost, development
    spread, and the unlevered development IRR (draws as period outflows, the exit sale as the final inflow
    in the same period as the last draw -- i.e. assuming the asset is sold immediately upon stabilization)."""
    loan = construction_loan_schedule(draws, interest_rate_annual, periods_per_year)
    total_cost_basis = loan["total_draws"] + loan["total_capitalized_interest"]
    exit_value = safe_div(stabilized_noi, exit_cap_rate)
    yoc = yield_on_cost(stabilized_noi, total_cost_basis)
    spread = development_spread(yoc, exit_cap_rate)
    cash_flows = [-d for d in draws]
    cash_flows[-1] += exit_value
    period_irr = irr(cash_flows)
    annual_irr = (1 + period_irr) ** periods_per_year - 1
    return {"construction_loan": loan, "total_cost_basis": total_cost_basis, "exit_value": exit_value,
            "development_profit": exit_value - total_cost_basis, "yield_on_cost": yoc,
            "development_spread_bps": spread["spread_bps"], "unlevered_irr_periodic": period_irr,
            "unlevered_irr_annual": annual_irr}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "total_development_cost" in d:
        out["total_development_cost"] = total_development_cost(**d["total_development_cost"])
    if "development_pro_forma" in d:
        out["development_pro_forma"] = development_pro_forma(**d["development_pro_forma"])
    return out
