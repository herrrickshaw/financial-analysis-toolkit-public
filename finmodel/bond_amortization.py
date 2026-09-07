"""Bond premium/discount amortization under the effective-interest method (ASC 835-30, the required method
under US GAAP -- straight-line amortization is permitted only when it is not materially different) -- the
issuer-side accounting counterpart to `finmodel.fixed_income_risk`'s investor-side duration/convexity risk
metrics, and a real, standard corporate-finance mechanic with no prior representation across the toolkit's
other ~50 modules.

  * A bond's issue price is the present value of its coupons and face value, discounted at the market
    (effective) yield rather than its own stated coupon rate. If the coupon rate exceeds the market rate,
    the bond issues at a PREMIUM (issue price > face value); if the coupon rate is below the market rate, it
    issues at a DISCOUNT (issue price < face value).
  * Each period, interest expense = the carrying value x the market rate (NOT the coupon rate) -- the whole
    point of the effective-interest method. Amortization = cash interest actually paid minus that interest
    expense; a premium bond amortizes DOWN toward face value (cash paid exceeds expense), a discount bond
    amortizes UP toward face value (expense exceeds cash paid).
  * The real, defining identity this module's own test suite verifies directly: regardless of whether the
    bond issued at a premium or a discount, its carrying value converges to EXACTLY the face value by the
    final period -- the entire premium or discount must be fully amortized away by maturity.
"""
from __future__ import annotations

from typing import Any, Dict, List


def bond_amortization_schedule(face_value: float, coupon_rate: float, market_rate: float, periods: int,
                               periods_per_year: int = 2) -> Dict[str, Any]:
    coupon_per_period = face_value * coupon_rate / periods_per_year
    market_rate_per_period = market_rate / periods_per_year
    issue_price = sum(coupon_per_period / (1 + market_rate_per_period) ** (i + 1) for i in range(periods)) + \
                  face_value / (1 + market_rate_per_period) ** periods
    carrying_value = issue_price
    schedule: List[Dict[str, Any]] = []
    for i in range(periods):
        interest_expense = carrying_value * market_rate_per_period
        amortization = coupon_per_period - interest_expense
        carrying_value = carrying_value - amortization
        schedule.append({"period": i + 1, "interest_expense": interest_expense, "cash_interest_paid": coupon_per_period,
                         "amortization": amortization, "carrying_value": carrying_value})
    tol = max(1e-6, abs(face_value) * 1e-9)  # guards against floating-point noise around an exact par price
    if issue_price > face_value + tol:
        issued_at = "premium"
    elif issue_price < face_value - tol:
        issued_at = "discount"
    else:
        issued_at = "par"
    return {"issue_price": issue_price, "premium_or_discount": issue_price - face_value,
            "issued_at": issued_at, "schedule": schedule}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "bond_amortization_schedule" in d:
        out["bond_amortization_schedule"] = bond_amortization_schedule(**d["bond_amortization_schedule"])
    return out
