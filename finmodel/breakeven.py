"""Break-even and cost-volume-profit (CVP) analysis — one of the most fundamental real corporate-finance/
managerial-accounting techniques, flagged as a real, recurring FP&A template category (SCORE, Smartsheet) that
had no equivalent anywhere in this toolkit despite its wide use in real business planning and lending review.

  Contribution margin       — price less variable cost per unit — the real, standard building block every CVP
                             calculation is built from.
  Break-even point          — the real, standard result: fixed costs / contribution margin per unit (in units),
                             or fixed costs / contribution margin RATIO (in revenue dollars) — the volume at
                             which operating profit is exactly zero.
  Margin of safety           — how far actual/planned sales sit above the break-even point — the real, standard
                             cushion metric a lender or investor reads before anything else in a CVP analysis.
  Degree of operating        — % change in operating profit for a 1% change in sales — the real, standard
  leverage (DOL)              measure of how much a business's fixed-cost structure amplifies (or dampens) the
                             swing in profit from a change in volume, the CVP analogue of financial leverage."""
from __future__ import annotations

from typing import Any, Dict

from .fin import safe_div


def contribution_margin(price_per_unit: float, variable_cost_per_unit: float) -> Dict[str, Any]:
    cm = price_per_unit - variable_cost_per_unit
    return {"price_per_unit": price_per_unit, "variable_cost_per_unit": variable_cost_per_unit,
            "contribution_margin_per_unit": cm, "contribution_margin_ratio": safe_div(cm, price_per_unit)}


def break_even_point(fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float) -> Dict[str, Any]:
    cm = contribution_margin(price_per_unit, variable_cost_per_unit)
    units = safe_div(fixed_costs, cm["contribution_margin_per_unit"])
    revenue = units * price_per_unit
    return {"fixed_costs": fixed_costs, "contribution_margin_per_unit": cm["contribution_margin_per_unit"],
            "contribution_margin_ratio": cm["contribution_margin_ratio"], "break_even_units": units, "break_even_revenue": revenue}


def margin_of_safety(actual_or_planned_units: float, break_even_units: float, price_per_unit: float) -> Dict[str, Any]:
    unit_cushion = actual_or_planned_units - break_even_units
    return {"unit_cushion": unit_cushion, "revenue_cushion": unit_cushion * price_per_unit,
            "margin_of_safety_pct": safe_div(unit_cushion, actual_or_planned_units)}


def degree_of_operating_leverage(units: float, price_per_unit: float, variable_cost_per_unit: float, fixed_costs: float) -> Dict[str, Any]:
    """DOL = contribution margin / operating profit, evaluated at the given unit volume — the real, standard
    measure of how much a 1% change in sales volume amplifies the % change in operating profit, given the
    business's current fixed-cost base."""
    cm = contribution_margin(price_per_unit, variable_cost_per_unit)
    total_contribution = units * cm["contribution_margin_per_unit"]
    operating_profit = total_contribution - fixed_costs
    return {"total_contribution_margin": total_contribution, "operating_profit": operating_profit,
            "degree_of_operating_leverage": safe_div(total_contribution, operating_profit)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "contribution_margin" in d:
        out["contribution_margin"] = contribution_margin(**d["contribution_margin"])
    if "break_even_point" in d:
        out["break_even_point"] = break_even_point(**d["break_even_point"])
    if "margin_of_safety" in d:
        p = dict(d["margin_of_safety"])
        if "break_even_units" not in p and "break_even_point" in out:
            p["break_even_units"] = out["break_even_point"]["break_even_units"]
        out["margin_of_safety"] = margin_of_safety(**p)
    if "degree_of_operating_leverage" in d:
        out["degree_of_operating_leverage"] = degree_of_operating_leverage(**d["degree_of_operating_leverage"])
    return out
