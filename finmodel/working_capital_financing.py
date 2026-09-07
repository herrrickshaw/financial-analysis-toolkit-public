"""Working-capital financing economics: the real, standard formulas a corporate treasury function uses to
cost out short-term financing choices -- distinct from finmodel.ratios' cash-conversion-cycle DIAGNOSTICS
(inventory/receivable/payable days), this module prices the actual financing instruments a company uses to
FUND that cycle.

  * Invoice factoring: a factor advances a percentage of an invoice's face value immediately and charges a
    discount fee for the period until collection; the effective annualized cost annualizes that fee over the
    actual number of days the advance is outstanding (standard factoring-industry math).
  * The cost of NOT taking an early-payment discount (trade-credit terms like "2/10, net 30"): a classic
    corporate-finance formula (Brealey, Myers & Allen, *Principles of Corporate Finance*) for the implied
    annualized interest rate a buyer pays by waiting the full term instead of paying early --
    APR = (discount% / (1 - discount%)) x (365 / (full_days - discount_days)).
  * Asset-based lending (ABL) borrowing-base availability: the standard revolver sizing formula lenders use
    -- a percentage advance rate against eligible receivables and inventory, less any balance already drawn.
"""
from __future__ import annotations

from typing import Any, Dict

from .fin import safe_div


def factoring_cost(invoice_amount: float, advance_rate: float, discount_fee_pct: float, days_to_collect: float) -> Dict[str, Any]:
    """`advance_rate` and `discount_fee_pct` are both fractions of the invoice face value (e.g. 0.80 and
    0.02). The factor advances `advance_rate x invoice_amount` up front and keeps `discount_fee_pct x
    invoice_amount` as its fee out of the reserve released on collection."""
    advance_amount = invoice_amount * advance_rate
    fee_amount = invoice_amount * discount_fee_pct
    reserve_released = invoice_amount * (1 - advance_rate) - fee_amount
    net_proceeds = advance_amount + reserve_released
    effective_annual_rate = safe_div(fee_amount, advance_amount) * safe_div(365.0, days_to_collect)
    return {"advance_amount": advance_amount, "fee_amount": fee_amount, "reserve_released": reserve_released,
            "net_proceeds": net_proceeds, "effective_annual_rate": effective_annual_rate}


def early_payment_discount_apr(discount_pct: float, discount_days: float, net_days: float) -> float:
    """The annualized cost of forgoing an early-payment discount (e.g. terms "2/10, net 30" ->
    discount_pct=0.02, discount_days=10, net_days=30). Raises ValueError if net_days <= discount_days."""
    if net_days <= discount_days:
        raise ValueError("net_days must exceed discount_days")
    return safe_div(discount_pct, 1 - discount_pct) * (365.0 / (net_days - discount_days))


def asset_based_lending_availability(ar_balance: float, ar_advance_rate: float, inventory_balance: float,
                                     inventory_advance_rate: float, existing_draws: float = 0.0) -> Dict[str, Any]:
    borrowing_base = ar_balance * ar_advance_rate + inventory_balance * inventory_advance_rate
    return {"borrowing_base": borrowing_base, "existing_draws": existing_draws,
            "available_to_draw": borrowing_base - existing_draws}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "factoring_cost" in d:
        out["factoring_cost"] = factoring_cost(**d["factoring_cost"])
    if "early_payment_discount_apr" in d:
        out["early_payment_discount_apr"] = early_payment_discount_apr(**d["early_payment_discount_apr"])
    if "asset_based_lending_availability" in d:
        out["asset_based_lending_availability"] = asset_based_lending_availability(**d["asset_based_lending_availability"])
    return out
