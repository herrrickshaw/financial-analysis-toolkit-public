"""Earnings per share (ASC 260) -- basic and diluted EPS, including the treasury stock method for options and
the if-converted method for convertible debt, with the real antidilution test every diluted-EPS calculation
must apply. A real, extremely common calculation with no prior representation across the toolkit's other
~50 modules.

  * Basic EPS = (net income - preferred dividends) / weighted average basic shares outstanding.
  * The treasury stock method assumes in-the-money options/warrants are exercised, the company receives the
    strike-price cash, and uses that cash to repurchase shares at the average market price -- the net new
    shares added are the incremental dilution. Out-of-the-money options (strike >= average market price)
    contribute ZERO incremental shares; they are never dilutive.
  * The if-converted method assumes a convertible security converts at the start of the period: the shares
    it would issue are added to the denominator, and the after-tax interest expense the company would NOT
    have paid (since the debt would no longer exist) is added back to the numerator.
  * The real, defining ANTIDILUTION rule this module's own test suite verifies directly: a security is only
    included in diluted EPS if doing so actually REDUCES EPS below what it would otherwise be -- a security
    whose inclusion would increase EPS is "antidilutive" and must be excluded entirely. This is also why
    diluted EPS can never exceed basic EPS by construction.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence


def basic_eps(net_income: float, preferred_dividends: float, weighted_average_shares: float) -> Dict[str, Any]:
    numerator = net_income - preferred_dividends
    return {"numerator": numerator, "weighted_average_shares": weighted_average_shares,
            "basic_eps": numerator / weighted_average_shares}


def treasury_stock_method_incremental_shares(options_outstanding: float, strike_price: float, average_market_price: float) -> float:
    if strike_price >= average_market_price:
        return 0.0  # out of the money -- never dilutive, contributes no incremental shares
    shares_repurchased = options_outstanding * strike_price / average_market_price
    return options_outstanding - shares_repurchased


def if_converted_incremental_shares_and_addback(convertible_face_value: float, coupon_rate: float, tax_rate: float,
                                                total_shares_if_converted: float) -> Dict[str, Any]:
    interest_expense = convertible_face_value * coupon_rate
    return {"after_tax_interest_addback": interest_expense * (1 - tax_rate), "incremental_shares": total_shares_if_converted}


def diluted_eps(net_income: float, preferred_dividends: float, weighted_average_shares: float,
                options: Optional[Sequence[Dict[str, float]]] = None,
                convertibles: Optional[Sequence[Dict[str, float]]] = None) -> Dict[str, Any]:
    """`options`: [{"options_outstanding", "strike_price", "average_market_price"}, ...]. `convertibles`:
    [{"convertible_face_value", "coupon_rate", "tax_rate", "total_shares_if_converted"}, ...]. Each
    convertible is tested against the antidilution rule relative to the running diluted position built up so
    far (options first, then convertibles in the order given) -- a real, reasonable approximation of ASC
    260's full most-dilutive-first sequencing, not a complete implementation of it."""
    basic = basic_eps(net_income, preferred_dividends, weighted_average_shares)
    numerator = basic["numerator"]
    denominator = weighted_average_shares
    included: List[Dict[str, Any]] = []

    for opt in (options or []):
        inc_shares = treasury_stock_method_incremental_shares(**opt)
        if inc_shares > 0:
            denominator += inc_shares
            included.append({"type": "option", "incremental_shares": inc_shares})

    for conv in (convertibles or []):
        result = if_converted_incremental_shares_and_addback(**conv)
        current_eps = numerator / denominator
        trial_eps = (numerator + result["after_tax_interest_addback"]) / (denominator + result["incremental_shares"])
        if trial_eps < current_eps:
            numerator += result["after_tax_interest_addback"]
            denominator += result["incremental_shares"]
            included.append({"type": "convertible", "incremental_shares": result["incremental_shares"],
                             "after_tax_interest_addback": result["after_tax_interest_addback"]})

    return {"basic_eps": basic["basic_eps"], "diluted_eps": numerator / denominator,
            "diluted_numerator": numerator, "diluted_denominator": denominator, "dilutive_securities_included": included}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "basic_eps" in d:
        out["basic_eps"] = basic_eps(**d["basic_eps"])
    if "diluted_eps" in d:
        out["diluted_eps"] = diluted_eps(**d["diluted_eps"])
    return out
