"""Revolving-credit interest mechanics: cash-credit/overdraft (CC/OD) bank accounts and credit-card billing
cycles both charge interest on a FLUCTUATING daily balance rather than a fixed EMI schedule -- a genuinely
different mechanic from finmodel.retail_loans' fixed reducing-balance amortization. Both products use the
same underlying "average daily balance" method (sum each day's outstanding balance x that day's interest
rate); this module implements that once and applies it to both real product contexts.

  * Cash credit / overdraft: an Indian bank sanctions a limit against which a borrower draws down and repays
    freely; interest is charged on the actual daily outstanding balance, typically debited (capitalized)
    monthly -- the standard mechanic behind every working-capital CC/OD facility.
  * Credit-card minimum-payment trap: paying only the contractual minimum (the greater of a fixed floor or a
    percentage of the outstanding balance) every month, rather than the full statement balance, stretches
    payoff over years and multiplies the interest actually paid -- the real, commonly-cited illustration in
    every consumer-finance textbook and regulatory financial-literacy disclosure (the US CARD Act of 2009
    requires card issuers to print exactly this minimum-payment-warning table on every statement).
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def daily_balance_interest(daily_balances: Sequence[float], annual_rate: float, days_in_year: int = 365) -> Dict[str, Any]:
    daily_rate = annual_rate / days_in_year
    total_interest = sum(b * daily_rate for b in daily_balances)
    n = len(daily_balances)
    average_balance = safe_div(sum(daily_balances), n)
    return {"total_interest": total_interest, "average_balance": average_balance, "num_days": n,
            "effective_annualized_rate_on_average_balance": safe_div(total_interest, average_balance) * safe_div(365.0, n)}


def credit_card_minimum_payment_schedule(balance: float, annual_rate: float, min_payment_pct: float = 0.05,
                                         min_payment_floor: float = 200.0, max_months: int = 600) -> Dict[str, Any]:
    """Simulates paying only the contractual minimum every month -- `max(min_payment_pct x balance,
    min_payment_floor)` -- until the balance is paid off (or `max_months` is reached without payoff, which
    itself is a real, meaningful result: the minimum payment doesn't even cover accruing interest)."""
    monthly_rate = annual_rate / 12
    b = balance
    total_interest = 0.0
    schedule: List[Dict[str, Any]] = []
    m = 0
    while b > 0.01 and m < max_months:
        opening = b
        interest = opening * monthly_rate
        payment = max(opening * min_payment_pct, min_payment_floor)
        payment = min(payment, opening + interest)
        principal_component = payment - interest
        closing = opening - principal_component
        total_interest += interest
        m += 1
        schedule.append({"month": m, "opening_balance": opening, "interest": interest, "payment": payment,
                         "principal": principal_component, "closing_balance": closing})
        b = closing
    paid_off = b <= 0.01
    return {"paid_off": paid_off, "months_to_payoff": m if paid_off else None, "total_interest_paid": total_interest,
            "total_paid": balance + total_interest if paid_off else None, "schedule": schedule}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "daily_balance_interest" in d:
        out["daily_balance_interest"] = daily_balance_interest(**d["daily_balance_interest"])
    if "credit_card_minimum_payment_schedule" in d:
        out["credit_card_minimum_payment_schedule"] = credit_card_minimum_payment_schedule(**d["credit_card_minimum_payment_schedule"])
    return out
