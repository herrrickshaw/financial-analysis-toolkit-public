"""Bond price sensitivity: Macaulay duration, modified duration, DV01, and convexity -- the analytic toolkit
Bruce Tuckman's NYU Stern fixed-income course (and his own standard textbook, *Fixed Income Securities:
Tools for Today's Markets*) builds before pricing, hedging, or investing in any bond, and a real gap this
toolkit had despite already touching bonds in finmodel.convertible_bonds (a bond floor plus an embedded
option) and finmodel.cmo (PSA prepayment and tranche weighted-average life) -- neither computes a bond's
own basic price-sensitivity measures.

  * Price = sum of each period's cash flow discounted at the periodic yield.
  * Macaulay duration = the cash-flow-weighted average time (in years) until a bondholder receives their
    money back -- the "center of gravity" of the bond's cash flows.
  * Modified duration = Macaulay duration / (1 + periodic yield) -- the first-order percentage price change
    for a 1-unit change in yield; DV01 is that same sensitivity expressed in dollars for a 1-basis-point move.
  * Convexity is the second-order (curvature) correction: a bond's actual price change for a large yield
    move is better approximated by both duration AND convexity together than by duration alone.

This module's own test suite verifies its output against a classic textbook reference point: a 2-year,
10%-coupon, annual-pay bond priced at par (10% yield) has a Macaulay duration of almost exactly 1.91 years.
"""
from __future__ import annotations

from typing import Any, Dict, Sequence


def bond_price_and_duration(cash_flows: Sequence[float], yield_rate: float, periods_per_year: int = 2) -> Dict[str, Any]:
    """`cash_flows[k]` is the payment received at the END of period `k+1` (so `cash_flows[0]` is the first
    coupon, one period from now); `yield_rate` is the annual yield, compounded `periods_per_year` times."""
    y = yield_rate / periods_per_year
    n = len(cash_flows)
    pv = [cf / (1 + y) ** (k + 1) for k, cf in enumerate(cash_flows)]
    price = sum(pv)
    macaulay_duration_periods = sum((k + 1) * pv_k for k, pv_k in enumerate(pv)) / price
    macaulay_duration_years = macaulay_duration_periods / periods_per_year
    modified_duration = macaulay_duration_years / (1 + y)
    dv01 = modified_duration * price * 0.0001
    convexity = sum((k + 1) * (k + 2) * pv_k for k, pv_k in enumerate(pv)) / (price * (1 + y) ** 2 * periods_per_year ** 2)
    return {"price": price, "macaulay_duration_years": macaulay_duration_years,
            "modified_duration": modified_duration, "dv01": dv01, "convexity": convexity}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "bond_price_and_duration" in d:
        out["bond_price_and_duration"] = bond_price_and_duration(**d["bond_price_and_duration"])
    return out
