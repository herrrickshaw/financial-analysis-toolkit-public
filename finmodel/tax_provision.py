"""Corporate income-tax provision mechanics under ASC 740 (US GAAP) / IAS 12 -- the deferred-tax and
NOL-carryforward machinery a tax-provision workpaper or a Big 4 tax-accounting service actually builds,
distinct from finmodel.dcf.unlevered_tax_schedule (a DCF-diagnostic that just taxes EBIT directly with a
simple loss carryforward, no statutory usage limits or vintage tracking) and from the DTL a purchase-price
allocation books at close (finmodel.ppa_valuation -- a one-time step-up event, not a recurring provision).

  * A DEDUCTIBLE temporary difference (book expense recognized before it is tax-deductible, e.g. a warranty
    reserve or bad-debt allowance) gives rise to a Deferred Tax ASSET = amount x tax_rate.
  * A TAXABLE temporary difference (e.g. accelerated tax depreciation vs. straight-line book depreciation)
    gives rise to a Deferred Tax LIABILITY = amount x tax_rate.
  * A valuation allowance is required against a DTA when negative evidence (ASC 740-10-30's own example: a
    cumulative pretax loss over the last three years) isn't outweighed by positive evidence (projected
    future taxable income sufficient to use the DTA).
  * Net operating losses under the post-2017 Tax Cuts and Jobs Act (IRC S 172, as amended): NOLs generated
    in 2018 or later never expire but can offset at most 80% of a future year's taxable income; NOLs from
    BEFORE 2018 keep the old rules -- 100% offset, but expire after 20 years. This module tracks the two
    vintages as separate baskets, using the pre-2018 basket first (100% offset) before the post-2017 basket
    (80%-capped) against whatever taxable income remains.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def deferred_tax_position(temporary_differences: Dict[str, Dict[str, Any]], tax_rate: float) -> Dict[str, Any]:
    """`temporary_differences`: {name: {"amount": float, "type": "deductible"|"taxable"}}. Returns the DTA/DTL
    for each item and the net position (positive = net deferred tax ASSET, negative = net LIABILITY)."""
    items: Dict[str, Dict[str, Any]] = {}
    gross_dta = 0.0
    gross_dtl = 0.0
    for name, item in temporary_differences.items():
        amount = float(item["amount"])
        kind = item["type"]
        if kind not in ("deductible", "taxable"):
            raise ValueError(f"{name}: type must be 'deductible' or 'taxable'")
        value = amount * tax_rate
        items[name] = {"amount": amount, "type": kind, "deferred_tax": value}
        if kind == "deductible":
            gross_dta += value
        else:
            gross_dtl += value
    return {"items": items, "gross_dta": gross_dta, "gross_dtl": gross_dtl, "net_deferred_tax": gross_dta - gross_dtl}


def valuation_allowance(gross_dta: float, cumulative_pretax_loss_last_3yrs: float,
                        projected_future_taxable_income: float, tax_rate: float) -> Dict[str, Any]:
    """ASC 740-10-30's "more likely than not" realizability test, simplified to its most commonly cited
    trigger: a cumulative pretax LOSS over the trailing three years is treated as significant negative
    evidence, capping the supportable DTA at the tax benefit of projected future taxable income. Absent that
    negative evidence, the full DTA is assumed realizable (the standard default)."""
    if cumulative_pretax_loss_last_3yrs <= 0:
        return {"valuation_allowance_required": False, "valuation_allowance": 0.0, "net_dta": gross_dta}
    supportable_dta = max(0.0, projected_future_taxable_income) * tax_rate
    allowance = max(0.0, gross_dta - supportable_dta)
    return {"valuation_allowance_required": allowance > 0, "valuation_allowance": allowance,
            "net_dta": gross_dta - allowance}


def nol_carryforward_schedule(pretax_income: Sequence[float], tax_rate: float,
                              opening_pre2018_nol: float = 0.0, pre2018_nol_years_remaining: int = 0,
                              opening_post2017_nol: float = 0.0) -> Dict[str, Any]:
    """Walks `pretax_income` year by year across two NOL baskets. Pre-2018 NOLs are used first (100% offset,
    no annual cap) and expire once `pre2018_nol_years_remaining` counts down past zero; post-2017 NOLs are
    then used against whatever income remains, capped at 80% of that remainder, and never expire."""
    years: List[Dict[str, Any]] = []
    pre2018 = float(opening_pre2018_nol)
    pre2018_years_left = int(pre2018_nol_years_remaining)
    post2017 = float(opening_post2017_nol)
    total_cash_tax = 0.0
    total_expired = 0.0
    for income in pretax_income:
        expired_this_year = 0.0
        pre2018_years_left -= 1
        if pre2018_years_left < 0 and pre2018 > 0:
            expired_this_year = pre2018
            pre2018 = 0.0
        if income < 0:
            use_pre2018 = use_post2017 = 0.0
            taxable_income = 0.0
            cash_tax = 0.0
            post2017 += -income
        else:
            use_pre2018 = min(pre2018, income)
            remaining = income - use_pre2018
            use_post2017 = min(post2017, 0.8 * remaining)
            taxable_income = remaining - use_post2017
            cash_tax = taxable_income * tax_rate
            pre2018 -= use_pre2018
            post2017 -= use_post2017
        total_cash_tax += cash_tax
        total_expired += expired_this_year
        years.append({"pretax_income": income, "expired_pre2018_nol": expired_this_year,
                      "used_pre2018_nol": use_pre2018, "used_post2017_nol": use_post2017,
                      "taxable_income": taxable_income, "cash_tax": cash_tax,
                      "closing_pre2018_nol": pre2018, "closing_post2017_nol": post2017})
    return {"years": years, "total_cash_tax": total_cash_tax, "total_expired_nol": total_expired,
            "closing_pre2018_nol": pre2018, "closing_post2017_nol": post2017}


def effective_tax_rate_reconciliation(pretax_income: float, statutory_rate: float,
                                      permanent_differences: Dict[str, float], tax_credits: float = 0.0) -> Dict[str, Any]:
    """The rate-reconciliation table every 10-K tax footnote publishes: statutory tax, plus the tax effect of
    each permanent difference (a positive amount is taxable income/non-deductible expense not in book pretax
    income and so increases tax; negative is the reverse), less tax credits, to the effective rate."""
    statutory_tax = pretax_income * statutory_rate
    permanent_effects = {name: amount * statutory_rate for name, amount in permanent_differences.items()}
    total_tax = statutory_tax + sum(permanent_effects.values()) - tax_credits
    return {"statutory_tax": statutory_tax, "permanent_effects": permanent_effects, "tax_credits": tax_credits,
            "total_tax": total_tax, "effective_tax_rate": safe_div(total_tax, pretax_income)}


def deferred_tax_rollforward(beginning_balance: float, provision_current_year: float,
                             reversal_current_year: float, rate_change_adjustment: float = 0.0) -> Dict[str, Any]:
    ending_balance = beginning_balance + provision_current_year - reversal_current_year + rate_change_adjustment
    return {"beginning_balance": beginning_balance, "provision_current_year": provision_current_year,
            "reversal_current_year": reversal_current_year, "rate_change_adjustment": rate_change_adjustment,
            "ending_balance": ending_balance}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "deferred_tax_position" in d:
        p = d["deferred_tax_position"]
        out["deferred_tax_position"] = deferred_tax_position(p["temporary_differences"], p["tax_rate"])
    if "valuation_allowance" in d:
        out["valuation_allowance"] = valuation_allowance(**d["valuation_allowance"])
    if "nol_carryforward_schedule" in d:
        out["nol_carryforward_schedule"] = nol_carryforward_schedule(**d["nol_carryforward_schedule"])
    if "effective_tax_rate_reconciliation" in d:
        out["effective_tax_rate_reconciliation"] = effective_tax_rate_reconciliation(**d["effective_tax_rate_reconciliation"])
    if "deferred_tax_rollforward" in d:
        out["deferred_tax_rollforward"] = deferred_tax_rollforward(**d["deferred_tax_rollforward"])
    return out
