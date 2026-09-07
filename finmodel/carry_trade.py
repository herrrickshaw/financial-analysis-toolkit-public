"""FX carry trade and covered interest rate parity (CIP) -- the classic "borrow low-yield currency, invest
in high-yield currency" trade (JPY/AUD, USD/INR, and every other funding/target currency pair a global-macro
desk runs), and the no-arbitrage relationship that prices its forward hedge. Quote convention throughout:
`spot_rate` and `forward_rate` are units of the FUNDING currency per 1 unit of the TARGET (investment)
currency; `domestic_rate` is the funding currency's interest rate, `foreign_rate` is the target currency's.
Distilled from Hull's *Options, Futures, and Other Derivatives* (CIP) and Eun & Resnick's *International
Financial Management* (uncovered interest rate parity / the carry trade).

  * Covered interest rate parity: the no-arbitrage forward rate is `F = S (1+domestic)^t / (1+foreign)^t` --
    if it didn't hold, an investor could borrow one currency, convert, invest in the other, and lock in a
    forward hedge for a riskless profit.
  * A carry trade is a bet AGAINST uncovered interest rate parity: it borrows the low-rate currency and
    invests in the high-rate one WITHOUT hedging the FX exposure, profiting exactly as long as the target
    currency doesn't depreciate by more than the interest-rate differential implies.
  * The break-even depreciation for an unhedged carry trade is, by construction, EXACTLY the forward
    premium/discount that covered interest rate parity implies -- the well-known result that a carry trade's
    whole economic bet is that the future spot rate will NOT move to where the forward rate already sits
    (the "forward premium puzzle" empirically documented in FX markets since Fama (1984)).
"""
from __future__ import annotations

from typing import Any, Dict

from .fin import safe_div


def covered_interest_rate_parity(spot_rate: float, domestic_rate: float, foreign_rate: float, tenor_years: float) -> Dict[str, Any]:
    forward_rate = spot_rate * (1 + domestic_rate) ** tenor_years / (1 + foreign_rate) ** tenor_years
    return {"spot_rate": spot_rate, "forward_rate": forward_rate,
            "forward_premium_pct": safe_div(forward_rate, spot_rate) - 1}


def uncovered_carry_return(spot_rate: float, expected_future_spot_rate: float, domestic_rate: float,
                           foreign_rate: float, tenor_years: float, notional: float = 1.0) -> Dict[str, Any]:
    """Borrows `notional` units of the funding currency, converts to the target currency at `spot_rate`,
    invests at `foreign_rate`, converts back at `expected_future_spot_rate`, and repays the funding-currency
    loan at `domestic_rate` -- the real, unhedged carry-trade cash flow, all in funding-currency terms."""
    target_units = notional / spot_rate
    value_at_maturity_target = target_units * (1 + foreign_rate) ** tenor_years
    funding_proceeds = value_at_maturity_target * expected_future_spot_rate
    repayment = notional * (1 + domestic_rate) ** tenor_years
    profit = funding_proceeds - repayment
    return {"funding_proceeds": funding_proceeds, "repayment": repayment, "profit": profit,
            "return_pct": safe_div(profit, notional)}


def break_even_depreciation(domestic_rate: float, foreign_rate: float, tenor_years: float) -> Dict[str, Any]:
    """The maximum the target (investment) currency can depreciate against the funding currency before an
    unhedged carry trade's profit turns negative -- exactly the CIP forward premium (see module docstring)."""
    ratio = (1 + domestic_rate) ** tenor_years / (1 + foreign_rate) ** tenor_years
    return {"break_even_future_spot_over_spot": ratio, "break_even_depreciation_pct": ratio - 1}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "covered_interest_rate_parity" in d:
        out["covered_interest_rate_parity"] = covered_interest_rate_parity(**d["covered_interest_rate_parity"])
    if "uncovered_carry_return" in d:
        out["uncovered_carry_return"] = uncovered_carry_return(**d["uncovered_carry_return"])
    if "break_even_depreciation" in d:
        out["break_even_depreciation"] = break_even_depreciation(**d["break_even_depreciation"])
    return out
