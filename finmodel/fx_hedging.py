"""Corporate FX transaction-exposure hedging: the forward hedge versus money-market hedge versus staying
unhedged comparison every international-finance textbook (Eun & Resnick's *International Financial
Management*) walks through for a company with a future foreign-currency receivable or payable -- the
corporate-treasury risk-management use of covered interest rate parity, distinct from `finmodel.carry_trade`'s
speculative "borrow low, invest high" application of the same identity. Quote convention: `spot_rate` and
`forward_rate` are units of DOMESTIC currency per 1 unit of the FOREIGN currency the exposure is denominated
in.

  * Forward hedge: lock in today's no-arbitrage forward rate (covered interest rate parity: `F = S (1+
    domestic)^t / (1+foreign)^t`) to convert the exposure at a known rate regardless of where the spot rate
    actually ends up.
  * Money-market hedge: for a RECEIVABLE, borrow `FC/(1+foreign)^t` in the foreign currency today (an amount
    that grows via the foreign interest rate to exactly the receivable's face value at maturity), convert it
    to domestic currency immediately at today's SPOT rate, then invest that domestic amount at the domestic
    rate until the receivable is actually due. For a PAYABLE, the mirror-image construction (invest in the
    foreign currency today, funded by borrowing domestically) locks in the same effective outcome.
  * The real, well-known result this module's own test suite verifies directly: the forward hedge and the
    money-market hedge give EXACTLY the same domestic-currency outcome, because covered interest rate parity
    is precisely the identity that makes the forward rate and the money-market construction cancel out
    algebraically -- there is no economic difference between the two, only an operational one (which one a
    company can actually access).
"""
from __future__ import annotations

from typing import Any, Dict, Optional


def fx_hedge_comparison(exposure_type: str, foreign_currency_amount: float, spot_rate: float, domestic_rate: float,
                        foreign_rate: float, tenor_years: float, expected_future_spot_rate: Optional[float] = None) -> Dict[str, Any]:
    """`exposure_type`: 'receivable' (a future foreign-currency inflow -- higher domestic value is better) or
    'payable' (a future foreign-currency outflow -- lower domestic value is better); the hedge constructions
    themselves are identical either way, only the interpretation of "better" differs."""
    if exposure_type not in ("receivable", "payable"):
        raise ValueError("exposure_type must be 'receivable' or 'payable'")
    forward_rate = spot_rate * (1 + domestic_rate) ** tenor_years / (1 + foreign_rate) ** tenor_years
    forward_hedge_value = foreign_currency_amount * forward_rate

    fc_amount_today = foreign_currency_amount / (1 + foreign_rate) ** tenor_years
    domestic_amount_today = fc_amount_today * spot_rate
    money_market_hedge_value = domestic_amount_today * (1 + domestic_rate) ** tenor_years

    result: Dict[str, Any] = {"exposure_type": exposure_type, "forward_rate": forward_rate,
                              "forward_hedge_value": forward_hedge_value, "money_market_hedge_value": money_market_hedge_value}
    if expected_future_spot_rate is not None:
        result["unhedged_value"] = foreign_currency_amount * expected_future_spot_rate
    return result


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "fx_hedge_comparison" in d:
        out["fx_hedge_comparison"] = fx_hedge_comparison(**d["fx_hedge_comparison"])
    return out
