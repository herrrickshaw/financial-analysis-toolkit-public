"""Percentage-of-completion (cost-to-cost) revenue recognition for long-term contracts -- the construction/
engineering-industry revenue recognition method (ASC 606's output/input-method framework, historically ASC
605-35 / SOP 81-1) flagged as a real, deliberately deferred gap in `docs/FPA_GALLERY_GAP_ANALYSIS.md`
("vertical-specific... no real dataset on hand to reconcile it against yet"). Revisited for the same reason
the items in `docs/DEFERRED_GAPS_REVISITED.md` were: the formula is exact and self-verifying against its own
accounting identity (cumulative recognized revenue must equal exactly the contract price once costs incurred
reach 100% of the total estimate), so no external dataset was actually required to build and test it
correctly.

  * % complete = costs incurred to date / total estimated contract costs -- the "cost-to-cost" method, the
    most common real input measure.
  * Revenue recognized to date = % complete x total contract price; gross profit to date = that revenue less
    costs incurred to date.
  * "Costs and estimated earnings in excess of billings" (an asset) versus "billings in excess of costs and
    estimated earnings" (a liability) is the real balance-sheet classification every construction company's
    10-K reports: whichever of (revenue recognized to date) and (amounts actually billed to date) is larger.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


def percentage_of_completion(costs_incurred_to_date: float, total_estimated_costs: float, contract_price: float,
                             billings_to_date: float = 0.0, revenue_previously_recognized: float = 0.0) -> Dict[str, Any]:
    if total_estimated_costs <= 0:
        raise ValueError("total_estimated_costs must be positive")
    pct_complete = min(1.0, safe_div(costs_incurred_to_date, total_estimated_costs))
    revenue_recognized_to_date = pct_complete * contract_price
    current_period_revenue = revenue_recognized_to_date - revenue_previously_recognized
    gross_profit_to_date = revenue_recognized_to_date - costs_incurred_to_date
    net_billing_position = billings_to_date - revenue_recognized_to_date
    classification = "billings_in_excess_of_costs_liability" if net_billing_position > 0 else "costs_in_excess_of_billings_asset"
    return {"pct_complete": pct_complete, "revenue_recognized_to_date": revenue_recognized_to_date,
            "current_period_revenue": current_period_revenue, "gross_profit_to_date": gross_profit_to_date,
            "estimated_total_gross_profit": contract_price - total_estimated_costs,
            "net_billing_position": abs(net_billing_position), "classification": classification}


def completion_schedule(cost_incurred_by_period: Sequence[float], total_estimated_costs: float, contract_price: float,
                        billings_by_period: Optional[Sequence[float]] = None) -> Dict[str, Any]:
    periods: List[Dict[str, Any]] = []
    cumulative_costs = 0.0
    cumulative_billings = 0.0
    revenue_previously = 0.0
    for i, cost in enumerate(cost_incurred_by_period):
        cumulative_costs += cost
        cumulative_billings += billings_by_period[i] if billings_by_period else 0.0
        row = percentage_of_completion(cumulative_costs, total_estimated_costs, contract_price,
                                       cumulative_billings, revenue_previously)
        row["period"] = i + 1
        row["costs_incurred_this_period"] = cost
        periods.append(row)
        revenue_previously = row["revenue_recognized_to_date"]
    return {"periods": periods, "total_revenue_recognized": revenue_previously,
            "total_costs_incurred": cumulative_costs, "total_gross_profit": revenue_previously - cumulative_costs}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "percentage_of_completion" in d:
        out["percentage_of_completion"] = percentage_of_completion(**d["percentage_of_completion"])
    if "completion_schedule" in d:
        out["completion_schedule"] = completion_schedule(**d["completion_schedule"])
    return out
