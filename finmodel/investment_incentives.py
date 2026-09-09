"""Investment-incentive mechanics used by Indian central and state government schemes that support
manufacturing/business investment -- e.g. Madhya Pradesh's Investment Promotion Assistance ("BIPA")
under its MSME/industrial policy, comparable schemes in other states, and central schemes such as the
Production Linked Incentive (PLI). No prior representation across the toolkit's other ~60 modules.

These schemes look different state to state and scheme to scheme, but in practice they are all built
from a small, repeating set of mechanics:

  * A CAPITAL SUBSIDY: a flat percentage of eligible fixed capital investment (FCI), capped in absolute
    terms or as a percentage of FCI.
  * An INTEREST SUBSIDY: a percentage of interest actually paid on a term loan, reimbursed annually up to
    a per-annum cap, for a fixed tenure.
  * A NET-TAX (state GST/VAT) REIMBURSEMENT: a percentage of the net state tax actually paid by the unit,
    reimbursed annually up to a per-annum cap, for a fixed tenure, with the CUMULATIVE reimbursement also
    bounded by an overall scheme cap (commonly expressed as a percentage of FCI) -- this is the structural
    shape of Madhya Pradesh's "Basic/Yearly Investment Promotion Assistance" and its state-policy
    equivalents elsewhere.
  * An EMPLOYMENT GENERATION SUBSIDY: a flat amount per eligible employee per month, for a fixed duration,
    capped.
  * An AD VALOREM DUTY EXEMPTION: a percentage of an otherwise-payable statutory charge (stamp duty,
    electricity duty) that is exempted or reimbursed.
  * An INCREMENTAL-METRIC-LINKED INCENTIVE: a percentage of the increase in some metric (typically sales
    turnover) over a base-year value, capped -- the mechanic used by the central PLI schemes, which pay a
    percentage of INCREMENTAL sales over a base year rather than a percentage of investment.

This module implements each mechanic once, generically, so a specific scheme (state or central) is just a
set of parameters plugged into these functions -- not a bespoke formula per scheme. `docs/` in this repo
separately catalogs the actual, citation-backed parameters of specific real schemes; this module holds only
the arithmetic, which is exactly and independently verifiable regardless of which scheme's numbers you use.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def capital_investment_subsidy(eligible_investment: float, subsidy_rate: float, subsidy_cap: float) -> Dict[str, Any]:
    raw_entitlement = eligible_investment * subsidy_rate
    subsidy_amount = min(raw_entitlement, subsidy_cap)
    return {"raw_entitlement": raw_entitlement, "subsidy_cap": subsidy_cap, "subsidy_amount": subsidy_amount,
            "capped": raw_entitlement > subsidy_cap}


def interest_subsidy_schedule(annual_interest_paid: Sequence[float], subsidy_rate: float, annual_cap: float,
                              tenure_years: int) -> Dict[str, Any]:
    schedule: List[Dict[str, Any]] = []
    total_subsidy = 0.0
    for year in range(1, tenure_years + 1):
        interest_paid = annual_interest_paid[year - 1] if year - 1 < len(annual_interest_paid) else 0.0
        entitlement = interest_paid * subsidy_rate
        subsidy_paid = min(entitlement, annual_cap)
        total_subsidy += subsidy_paid
        schedule.append({"year": year, "interest_paid": interest_paid, "entitlement": entitlement,
                         "subsidy_paid": subsidy_paid, "capped": entitlement > subsidy_paid})
    return {"schedule": schedule, "total_subsidy": total_subsidy}


def net_tax_reimbursement_schedule(annual_net_tax_paid: Sequence[float], reimbursement_rate: float,
                                   annual_cap: float, tenure_years: int, overall_cap: float) -> Dict[str, Any]:
    """The "Investment Promotion Assistance" / BIPA-style mechanic: each year's reimbursement is the lesser
    of (rate x net tax paid) and the per-annum cap, but the running CUMULATIVE total is also bounded by
    `overall_cap` -- once the scheme's lifetime ceiling is hit, later years pay nothing more."""
    schedule: List[Dict[str, Any]] = []
    cumulative = 0.0
    for year in range(1, tenure_years + 1):
        tax_paid = annual_net_tax_paid[year - 1] if year - 1 < len(annual_net_tax_paid) else 0.0
        entitlement = tax_paid * reimbursement_rate
        year_amount_before_overall_cap = min(entitlement, annual_cap)
        remaining_under_overall_cap = max(overall_cap - cumulative, 0.0)
        year_amount = min(year_amount_before_overall_cap, remaining_under_overall_cap)
        cumulative += year_amount
        schedule.append({"year": year, "net_tax_paid": tax_paid, "entitlement": entitlement,
                         "reimbursement_paid": year_amount,
                         "overall_cap_binding": year_amount < year_amount_before_overall_cap})
    return {"schedule": schedule, "total_reimbursement": cumulative, "overall_cap": overall_cap,
            "overall_cap_exhausted": cumulative >= overall_cap}


def employment_generation_subsidy(eligible_employees: float, per_employee_monthly_amount: float, months: float,
                                  scheme_cap: float) -> Dict[str, Any]:
    raw_entitlement = eligible_employees * per_employee_monthly_amount * months
    subsidy_amount = min(raw_entitlement, scheme_cap)
    return {"raw_entitlement": raw_entitlement, "subsidy_amount": subsidy_amount, "capped": raw_entitlement > scheme_cap}


def ad_valorem_duty_exemption(payable_amount: float, exemption_pct: float) -> Dict[str, Any]:
    """A flat percentage exemption/reimbursement of an otherwise-payable statutory charge -- stamp duty on
    land/lease registration, electricity duty, mandi tax, etc. all take this same shape."""
    exempted_amount = payable_amount * exemption_pct
    return {"payable_amount": payable_amount, "exemption_pct": exemption_pct, "exempted_amount": exempted_amount,
            "net_payable": payable_amount - exempted_amount}


def incremental_metric_linked_incentive(base_year_value: float, current_year_value: float, incentive_rate: float,
                                        cap: float) -> Dict[str, Any]:
    """The PLI mechanic: an incentive on the INCREASE in a metric (typically sales turnover) over a base
    year, not on investment or tax paid. No incentive accrues if the current year is below the base year."""
    incremental_value = max(0.0, current_year_value - base_year_value)
    entitlement = incremental_value * incentive_rate
    incentive_amount = min(entitlement, cap)
    return {"incremental_value": incremental_value, "entitlement": entitlement, "incentive_amount": incentive_amount,
            "capped": entitlement > incentive_amount}


def combined_incentive_package(components: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`components`: [{"scheme_name": "MP BIPA", "jurisdiction": "state", "amount": 12.5}, ...].
    `jurisdiction` is expected to be "state" or "central"."""
    by_scheme: Dict[str, float] = {}
    by_jurisdiction: Dict[str, float] = {}
    total = 0.0
    for c in components:
        amount = c["amount"]
        by_scheme[c["scheme_name"]] = by_scheme.get(c["scheme_name"], 0.0) + amount
        by_jurisdiction[c["jurisdiction"]] = by_jurisdiction.get(c["jurisdiction"], 0.0) + amount
        total += amount
    return {"total_incentive_value": total, "by_scheme": by_scheme, "by_jurisdiction": by_jurisdiction}


def effective_capex_after_incentives(gross_capex: float, upfront_capital_subsidies: float) -> Dict[str, Any]:
    net_capex = gross_capex - upfront_capital_subsidies
    return {"gross_capex": gross_capex, "upfront_capital_subsidies": upfront_capital_subsidies,
            "net_capex": net_capex, "effective_subsidy_pct": safe_div(upfront_capital_subsidies, gross_capex)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "capital_investment_subsidy" in d:
        out["capital_investment_subsidy"] = capital_investment_subsidy(**d["capital_investment_subsidy"])
    if "interest_subsidy_schedule" in d:
        out["interest_subsidy_schedule"] = interest_subsidy_schedule(**d["interest_subsidy_schedule"])
    if "net_tax_reimbursement_schedule" in d:
        out["net_tax_reimbursement_schedule"] = net_tax_reimbursement_schedule(**d["net_tax_reimbursement_schedule"])
    if "employment_generation_subsidy" in d:
        out["employment_generation_subsidy"] = employment_generation_subsidy(**d["employment_generation_subsidy"])
    if "ad_valorem_duty_exemptions" in d:
        out["ad_valorem_duty_exemptions"] = [ad_valorem_duty_exemption(**item) for item in d["ad_valorem_duty_exemptions"]]
    if "incremental_metric_linked_incentive" in d:
        out["incremental_metric_linked_incentive"] = incremental_metric_linked_incentive(**d["incremental_metric_linked_incentive"])
    if "combined_incentive_package" in d:
        out["combined_incentive_package"] = combined_incentive_package(d["combined_incentive_package"])
    if "effective_capex_after_incentives" in d:
        out["effective_capex_after_incentives"] = effective_capex_after_incentives(**d["effective_capex_after_incentives"])
    return out
