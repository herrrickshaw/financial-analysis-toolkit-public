"""Convertible bond valuation — a real, named fixed-income category at both Wall Street Prep and CFI (this
toolkit's catalog survey), and a natural real integration point for `finmodel.options`: a convertible bond IS,
by real market convention, a straight bond PLUS an embedded call option on the issuer's own stock.

  Bond floor            — the PV of the bond's coupons and principal at the market yield for a comparable
                          NON-convertible bond of the same issuer — the real floor value the convertible
                          shouldn't trade below even if the conversion option were worthless.
  Conversion value       — conversion_ratio x current stock price — what an investor gets by converting right
                          now; the convertible must always be worth at least this (you could always convert).
  Two-component estimate — the real, standard practitioner approximation: convertible value ~ bond floor +
                          value of the embedded call (Black-Scholes on the stock, strike = conversion price,
                          scaled by the conversion ratio — reusing `finmodel.options.black_scholes` directly)."""
from __future__ import annotations

from typing import Any, Dict

from .fin import npv, safe_div
from .options import black_scholes


def conversion_ratio(par_value: float, conversion_price: float) -> float:
    return safe_div(par_value, conversion_price)


def conversion_value(shares_per_bond: float, stock_price: float) -> float:
    return shares_per_bond * stock_price


def conversion_premium(bond_price: float, conv_value: float) -> float:
    return safe_div(bond_price, conv_value) - 1


def bond_floor(coupon_rate: float, par_value: float, years_to_maturity: float, straight_yield: float, coupons_per_year: int = 2) -> Dict[str, Any]:
    """The PV of the SAME bond's cash flows if it had no conversion right at all, discounted at the market yield
    for the issuer's comparable straight (non-convertible) debt — real, standard practice, since a convertible
    always carries a lower coupon than straight debt in exchange for the conversion option."""
    n = round(years_to_maturity * coupons_per_year)
    coupon = par_value * coupon_rate / coupons_per_year
    rate_per_period = straight_yield / coupons_per_year
    pv_coupons = npv(rate_per_period, [coupon] * n)
    pv_principal = par_value / (1 + rate_per_period) ** n
    return {"pv_coupons": pv_coupons, "pv_principal": pv_principal, "bond_floor": pv_coupons + pv_principal}


def convertible_bond_value(par_value: float, conversion_price: float, stock_price: float, coupon_rate: float,
                           years_to_maturity: float, straight_yield: float, risk_free_rate: float, volatility: float,
                           coupons_per_year: int = 2) -> Dict[str, Any]:
    """The real, standard two-component approximation. Floored at conversion_value (a real, exact property: you
    could always convert immediately, so the convertible can never be worth less than that), since the additive
    approximation is not exact and can occasionally understate deep-in-the-money cases."""
    ratio = conversion_ratio(par_value, conversion_price)
    floor = bond_floor(coupon_rate, par_value, years_to_maturity, straight_yield, coupons_per_year)
    call = black_scholes(spot=stock_price, strike=conversion_price, rate=risk_free_rate, vol=volatility, time=years_to_maturity, option_type="call")
    option_value = ratio * call["price"]
    conv_value = conversion_value(ratio, stock_price)
    two_component_value = floor["bond_floor"] + option_value
    return {"conversion_ratio": ratio, "bond_floor": floor["bond_floor"], "option_value": option_value,
            "conversion_value": conv_value, "two_component_value": two_component_value,
            "estimated_value": max(two_component_value, conv_value)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "bond_floor" in d:
        out["bond_floor"] = bond_floor(**d["bond_floor"])
    if "convertible_bond_value" in d:
        v = convertible_bond_value(**d["convertible_bond_value"])
        out["convertible_bond_value"] = v
        if "conversion_premium" in d:
            p = d["conversion_premium"]
            out["conversion_premium"] = conversion_premium(p["bond_price"], v["conversion_value"])
    return out
