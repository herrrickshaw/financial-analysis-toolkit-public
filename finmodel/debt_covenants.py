"""Debt covenant compliance testing -- the real, standard set of financial covenants every corporate credit
agreement includes, tested from the BORROWER's own side. Distinct from `finmodel.bank_model`'s leverage ratio
(a BANK's own regulatory capital ratio, Tier 1 capital / total assets) and from `finmodel.cash_flow_forecast`'s
minimum-cash covenant (a pure liquidity test) -- this module covers the income-statement-driven leverage and
coverage covenants that actually govern most corporate term loans and revolving credit facilities.

  * Leverage ratio (Total Debt / EBITDA) is a MAXIMUM covenant -- the borrower must stay AT OR BELOW a
    stated multiple.
  * Interest coverage ratio (EBITDA / Interest Expense) is a MINIMUM covenant -- the borrower must stay AT OR
    ABOVE a stated multiple.
  * Fixed charge coverage ratio (FCCR) is the real, stricter minimum covenant credit agreements layer on top
    of interest coverage: (EBITDA - capex - cash taxes) / (interest expense + scheduled principal payments),
    since a borrower can cover pure interest comfortably while still being unable to service the actual
    combined cash burden of capex, taxes, and mandatory amortization.
  * Every covenant test here reports a "headroom" figure -- the real number a CFO's treasury function
    actually tracks quarter to quarter, since a covenant that is merely compliant today with shrinking
    headroom is a materially different risk than one with a wide, stable buffer.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def leverage_ratio_covenant(total_debt: float, ebitda: float, max_leverage_ratio: float) -> Dict[str, Any]:
    ratio = safe_div(total_debt, ebitda)
    return {"covenant": "leverage_ratio", "leverage_ratio": ratio, "max_allowed": max_leverage_ratio,
            "compliant": ratio <= max_leverage_ratio, "headroom": max_leverage_ratio - ratio}


def interest_coverage_covenant(ebitda: float, interest_expense: float, min_interest_coverage: float) -> Dict[str, Any]:
    ratio = safe_div(ebitda, interest_expense)
    return {"covenant": "interest_coverage_ratio", "interest_coverage_ratio": ratio, "min_required": min_interest_coverage,
            "compliant": ratio >= min_interest_coverage, "headroom": ratio - min_interest_coverage}


def fixed_charge_coverage_covenant(ebitda: float, capex: float, cash_taxes: float, interest_expense: float,
                                   scheduled_principal_payments: float, min_fccr: float) -> Dict[str, Any]:
    numerator = ebitda - capex - cash_taxes
    denominator = interest_expense + scheduled_principal_payments
    ratio = safe_div(numerator, denominator)
    return {"covenant": "fixed_charge_coverage_ratio", "fixed_charge_coverage_ratio": ratio, "min_required": min_fccr,
            "compliant": ratio >= min_fccr, "headroom": ratio - min_fccr}


def covenant_compliance_summary(covenants: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    breaches = [c for c in covenants if not c["compliant"]]
    return {"total_covenants_tested": len(covenants), "all_compliant": len(breaches) == 0, "breaches": breaches}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    tested: List[Dict[str, Any]] = []
    if "leverage_ratio_covenant" in d:
        out["leverage_ratio_covenant"] = leverage_ratio_covenant(**d["leverage_ratio_covenant"])
        tested.append(out["leverage_ratio_covenant"])
    if "interest_coverage_covenant" in d:
        out["interest_coverage_covenant"] = interest_coverage_covenant(**d["interest_coverage_covenant"])
        tested.append(out["interest_coverage_covenant"])
    if "fixed_charge_coverage_covenant" in d:
        out["fixed_charge_coverage_covenant"] = fixed_charge_coverage_covenant(**d["fixed_charge_coverage_covenant"])
        tested.append(out["fixed_charge_coverage_covenant"])
    if tested:
        out["covenant_compliance_summary"] = covenant_compliance_summary(tested)
    return out
