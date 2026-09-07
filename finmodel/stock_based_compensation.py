"""Stock-based compensation expense (ASC 718) -- RSU and stock-option grant expense recognition, reusing
this toolkit's own Black-Scholes engine (`finmodel.options`) for option grants rather than reimplementing
option pricing. A real, extremely common corporate accounting topic with no prior representation across the
toolkit's other ~50 modules.

  * An RSU's grant-date fair value is simply shares granted x the stock price at grant -- no option-pricing
    model is needed, since an RSU carries no strike price or optionality. A stock option's grant-date fair
    value needs an option-pricing model; this module calls `finmodel.options.black_scholes` directly rather
    than reimplementing it.
  * ASC 718 permits either of two real expense-attribution methods for a multi-tranche graded-vesting award:
    STRAIGHT-LINE (the whole award's total fair value is expensed evenly over the full vesting period, as one
    unit) or GRADED/ACCELERATED (FIN 28's method: each vesting tranche is treated as its own sub-award,
    expensed straight-line over ITS OWN, typically shorter, vesting period). Both methods must expense
    EXACTLY the same total fair value by the time the full award is vested -- they only differ in timing --
    but graded vesting always front-loads MORE expense into the earlier periods, since shorter-vesting
    tranches concentrate their cost into fewer periods. This module's own test suite verifies both the timing
    difference and the equal-total identity directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .options import black_scholes


def rsu_grant_fair_value(shares_granted: float, grant_date_share_price: float) -> float:
    return shares_granted * grant_date_share_price


def stock_option_grant_fair_value(shares_granted: float, spot: float, strike: float, rate: float, vol: float,
                                  time: float, dividend_yield: float = 0.0) -> Dict[str, Any]:
    per_share = black_scholes(spot, strike, rate, vol, time, dividend_yield, "call")["price"]
    return {"fair_value_per_share": per_share, "total_fair_value": shares_granted * per_share}


def straight_line_expense_schedule(total_fair_value: float, vesting_periods: int) -> Dict[str, Any]:
    period_expense = total_fair_value / vesting_periods
    schedule: List[Dict[str, Any]] = []
    cumulative = 0.0
    for i in range(vesting_periods):
        cumulative += period_expense
        schedule.append({"period": i + 1, "expense": period_expense, "cumulative_expense": cumulative})
    return {"total_fair_value": total_fair_value, "period_expense": period_expense, "schedule": schedule}


def graded_vesting_expense_schedule(total_fair_value: float, tranches: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`tranches`: [{"pct_of_award": 0.25, "vesting_periods": 12}, ...], `pct_of_award` summing to 1.0 -- each
    tranche's own share of the total fair value is expensed straight-line over its own vesting period (the
    FIN 28 accelerated-attribution method)."""
    total_pct = sum(t["pct_of_award"] for t in tranches)
    if abs(total_pct - 1.0) > 1e-6:
        raise ValueError(f"tranche pct_of_award must sum to 1.0, got {total_pct}")
    max_periods = max(t["vesting_periods"] for t in tranches)
    period_expense = [0.0] * max_periods
    for t in tranches:
        tranche_value = total_fair_value * t["pct_of_award"]
        tranche_period_expense = tranche_value / t["vesting_periods"]
        for p in range(t["vesting_periods"]):
            period_expense[p] += tranche_period_expense
    schedule: List[Dict[str, Any]] = []
    cumulative = 0.0
    for i, e in enumerate(period_expense):
        cumulative += e
        schedule.append({"period": i + 1, "expense": e, "cumulative_expense": cumulative})
    return {"total_fair_value": total_fair_value, "schedule": schedule}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "rsu_grant_fair_value" in d:
        out["rsu_grant_fair_value"] = {"value": rsu_grant_fair_value(**d["rsu_grant_fair_value"])}
    if "stock_option_grant_fair_value" in d:
        out["stock_option_grant_fair_value"] = stock_option_grant_fair_value(**d["stock_option_grant_fair_value"])
    if "straight_line_expense_schedule" in d:
        out["straight_line_expense_schedule"] = straight_line_expense_schedule(**d["straight_line_expense_schedule"])
    if "graded_vesting_expense_schedule" in d:
        out["graded_vesting_expense_schedule"] = graded_vesting_expense_schedule(**d["graded_vesting_expense_schedule"])
    return out
