"""Purchase price allocation (PPA) intangible-asset valuation — the real, named ASC 805 / IFRS 3 methods that
sit behind KPMG's own publicly described "purchase price allocation support" service (this toolkit's market
survey of Big 4 financial-modeling services; see docs/BIG4_AUTOMATION.md).

`finmodel.merger.PPA` already allocates a purchase price given an `intangibles_writeup` figure — but it takes
that number as an ASSUMPTION. This module DERIVES it, the way a real valuation team would: value each
identifiable intangible asset by the income-approach method appropriate to it, then let goodwill fall out as the
real ASC 805 residual (not a hand-picked plug).

  Relief-from-royalty  — trade names, technology: value = PV(after-tax royalty payments avoided by owning the
                        asset instead of licensing it), grossed up by a Tax Amortization Benefit (TAB) factor.
  MPEEM                — customer relationships: value = PV(after-tax "excess earnings" left over once every
                        OTHER contributory asset — working capital, fixed assets, assembled workforce, other
                        intangibles — has earned its own required return), also TAB-grossed.
  Cost approach        — assets with no defensible income/market approach (assembled workforce, some fixed
                        assets): replacement cost less obsolescence.

Tax Amortization Benefit (TAB): real, standard valuation convention (AICPA/ASA guidance) — a US-tax-paying
buyer amortizes an acquired intangible straight-line over 15 years under IRC §197, so the pre-TAB income-approach
value understates what a buyer would actually pay by the PV of that future tax shield. The closed-form TAB
multiplier: 1 / (1 - tax_rate × PVA_n / n), where PVA_n is the n-year present-value-annuity factor at the
valuation discount rate."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .fin import npv, safe_div


def tab_factor(discount_rate: float, tax_rate: float, periods: int = 15) -> float:
    """Tax Amortization Benefit multiplier for a US-tax-paying buyer (IRC §197, straight-line over `periods`
    years — 15 is the real statutory default). Grosses up an income-approach value for the PV of future tax
    savings from amortizing the resulting intangible asset."""
    pva = sum(1 / (1 + discount_rate) ** t for t in range(1, periods + 1))
    denom = 1 - tax_rate * pva / periods
    if denom <= 0:
        raise ValueError("tax_rate/discount_rate/periods combination makes the TAB denominator non-positive")
    return 1 / denom


def relief_from_royalty(revenue: Sequence[float], royalty_rate: float, tax_rate: float, discount_rate: float,
                        include_tab: bool = True, tax_amortization_periods: int = 15) -> Dict[str, Any]:
    """revenue: projected revenue attributable to the asset being valued (e.g. trade-name-branded sales), one
    entry per forecast year. royalty_rate: the market royalty rate a licensee would pay for equivalent rights,
    supported by comparable licensing transactions in real practice."""
    pretax_royalty = [r * royalty_rate for r in revenue]
    aftertax_royalty = [r * (1 - tax_rate) for r in pretax_royalty]
    pv = npv(discount_rate, aftertax_royalty)
    tab = tab_factor(discount_rate, tax_rate, tax_amortization_periods) if include_tab else 1.0
    value = pv * tab
    return {"pretax_royalty": pretax_royalty, "aftertax_royalty": aftertax_royalty, "pv_before_tab": pv,
            "tab_factor": tab, "value": value, "royalty_rate": royalty_rate, "discount_rate": discount_rate}


def contributory_asset_charge(assets: Dict[str, Sequence[float]]) -> float:
    """A single period's total contributory-asset charge: assets is {name: (fair_value, required_return)} —
    the real MPEEM convention that every OTHER asset supporting the customer relationship (working capital,
    fixed assets, assembled workforce, other intangibles) must earn its own required return before what's left
    counts as "excess earnings" attributable to the customer asset itself."""
    return sum(fv * rr for fv, rr in assets.values())


def mpeem(operating_income: Sequence[float], contributory_asset_charges: Sequence[float], tax_rate: float,
         discount_rate: float, include_tab: bool = True, tax_amortization_periods: int = 15) -> Dict[str, Any]:
    """operating_income: projected pretax operating income attributable to the (already-attrited) existing
    customer base, one entry per forecast year. contributory_asset_charges: that same year's total charge for
    every OTHER asset's required return (see contributory_asset_charge()) — subtracted before tax, since it's a
    real economic cost of generating the revenue, not an after-the-fact allocation."""
    n = len(operating_income)
    if len(contributory_asset_charges) != n:
        raise ValueError("operating_income and contributory_asset_charges must have the same length")
    excess_pretax = [operating_income[t] - contributory_asset_charges[t] for t in range(n)]
    excess_aftertax = [e * (1 - tax_rate) for e in excess_pretax]
    pv = npv(discount_rate, excess_aftertax)
    tab = tab_factor(discount_rate, tax_rate, tax_amortization_periods) if include_tab else 1.0
    value = pv * tab
    return {"excess_earnings_pretax": excess_pretax, "excess_earnings_aftertax": excess_aftertax,
            "pv_before_tab": pv, "tab_factor": tab, "value": value, "discount_rate": discount_rate}


def cost_approach(replacement_cost: float, obsolescence_pct: float = 0.0) -> Dict[str, Any]:
    """Real, standard fallback for assets with no defensible income/market approach — e.g. assembled workforce,
    some acquired fixed assets: replacement cost less physical/functional/economic obsolescence."""
    value = replacement_cost * (1 - obsolescence_pct)
    return {"replacement_cost": replacement_cost, "obsolescence_pct": obsolescence_pct, "value": value}


def allocate(purchase_price: float, net_identifiable_assets_fair_value: float, intangible_values: Dict[str, float]) -> Dict[str, Any]:
    """The real ASC 805 residual principle: identify and value every intangible asset individually first;
    goodwill is whatever's left over, not a hand-picked plug. `net_identifiable_assets_fair_value` should exclude
    the intangibles being valued here (working capital, PP&E, other tangible/monetary assets and liabilities at
    fair value) to avoid double-counting."""
    total_intangibles = sum(intangible_values.values())
    total_identifiable = net_identifiable_assets_fair_value + total_intangibles
    goodwill = purchase_price - total_identifiable
    return {"purchase_price": purchase_price, "net_identifiable_assets_fair_value": net_identifiable_assets_fair_value,
            "intangible_values": dict(intangible_values), "total_intangibles": total_intangibles,
            "total_identifiable_assets": total_identifiable, "goodwill": goodwill,
            "goodwill_pct_of_price": safe_div(goodwill, purchase_price),
            "intangibles_writeup": total_intangibles}   # feeds directly into finmodel.merger.PPA(intangibles_writeup=...)


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "relief_from_royalty" in d:
        out["relief_from_royalty"] = {name: relief_from_royalty(**params) for name, params in d["relief_from_royalty"].items()}
    if "mpeem" in d:
        out["mpeem"] = {name: mpeem(**params) for name, params in d["mpeem"].items()}
    if "cost_approach" in d:
        out["cost_approach"] = {name: cost_approach(**params) for name, params in d["cost_approach"].items()}
    if "allocation" in d:
        intangible_values: Dict[str, float] = dict(d["allocation"].get("intangible_values", {}))
        for src in ("relief_from_royalty", "mpeem", "cost_approach"):
            for name, r in out.get(src, {}).items():
                intangible_values.setdefault(name, r["value"])
        out["allocation"] = allocate(d["allocation"]["purchase_price"], d["allocation"]["net_identifiable_assets_fair_value"], intangible_values)
    return out
