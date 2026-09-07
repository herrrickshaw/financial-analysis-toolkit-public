"""Lessee lease accounting under US GAAP (ASC 842) -- the real, near-universal corporate accounting standard
every company with real-estate, equipment, or vehicle leases applies, joining ASC 740 (`finmodel.
tax_provision`) and ASC 606 (`finmodel.percentage_of_completion`) as the third major accounting standard this
toolkit implements directly rather than only through a valuation lens. This module follows ASC 842
specifically, which keeps the dual finance/operating classification below; IFRS 16 (the international
equivalent) is a real, deliberately DIFFERENT standard for lessees -- it removed the operating-lease
classification entirely, so under IFRS 16 every lease (short-term/low-value exceptions aside) is accounted
for using the "finance lease" mechanic this module implements, with no single-line-item operating-lease
treatment at all.

  * Classification (ASC 842-10-25-2): a lease is a FINANCE lease if it transfers ownership, has a bargain
    purchase option reasonably certain to be exercised, the asset is so specialized it has no alternative
    use to the lessor, OR two quantitative proxies carried forward from the old ASC 840 bright-line tests and
    still widely used in practice as "reasonably certain" indicators: the lease term is >=75% of the asset's
    remaining economic life, or the present value of lease payments is >=90% of the asset's fair value.
    Anything not meeting any of these criteria is an OPERATING lease.
  * Both lease types initially recognize the SAME lease liability (the present value of lease payments) and
    right-of-use (ROU) asset -- the real, defining change ASC 842/IFRS 16 made versus the old rules, which
    kept operating leases off-balance-sheet entirely.
  * The two types diverge in how expense is recognized afterward. A FINANCE lease looks like a loan: interest
    accrues on the declining liability balance (front-loaded, like any amortizing loan) while the ROU asset
    is amortized straight-line separately -- so total expense DECLINES over the lease term. An OPERATING
    lease instead recognizes a SINGLE, LEVEL total lease expense every period (the sum of all undiscounted
    payments divided evenly across periods); the ROU asset amortization is a "plug" -- straight-line expense
    minus that period's interest accretion on the liability -- which is what keeps the liability and the ROU
    asset moving together even though the P&L shows one flat number.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


def classify_lease(lease_term_years: float, asset_economic_life_years: float, pv_lease_payments: float,
                   asset_fair_value: float, transfers_ownership: bool = False, bargain_purchase_option: bool = False,
                   specialized_asset_no_alternative_use: bool = False) -> Dict[str, Any]:
    reasons: List[str] = []
    if transfers_ownership:
        reasons.append("ownership transfers to the lessee by the end of the lease term")
    if bargain_purchase_option:
        reasons.append("a bargain purchase option is reasonably certain to be exercised")
    economic_life_pct = safe_div(lease_term_years, asset_economic_life_years)
    if economic_life_pct >= 0.75:
        reasons.append(f"lease term is {economic_life_pct:.0%} of the asset's remaining economic life (>=75%)")
    fair_value_pct = safe_div(pv_lease_payments, asset_fair_value)
    if fair_value_pct >= 0.90:
        reasons.append(f"present value of payments is {fair_value_pct:.0%} of the asset's fair value (>=90%)")
    if specialized_asset_no_alternative_use:
        reasons.append("the asset is so specialized it has no alternative use to the lessor at lease end")
    classification = "finance" if reasons else "operating"
    return {"classification": classification, "reasons": reasons,
            "economic_life_pct": economic_life_pct, "fair_value_pct": fair_value_pct}


def initial_measurement(lease_payments: Sequence[float], discount_rate: float, initial_direct_costs: float = 0.0,
                        prepaid_lease_payments: float = 0.0, lease_incentives_received: float = 0.0) -> Dict[str, Any]:
    lease_liability = sum(p / (1 + discount_rate) ** (i + 1) for i, p in enumerate(lease_payments))
    rou_asset = lease_liability + initial_direct_costs + prepaid_lease_payments - lease_incentives_received
    return {"lease_liability": lease_liability, "rou_asset": rou_asset}


def finance_lease_schedule(lease_payments: Sequence[float], discount_rate: float,
                          useful_life_years: Optional[float] = None) -> Dict[str, Any]:
    n = len(lease_payments)
    useful_life_years = useful_life_years or n
    liability = sum(p / (1 + discount_rate) ** (i + 1) for i, p in enumerate(lease_payments))
    rou_asset = liability
    annual_amortization = rou_asset / useful_life_years
    schedule: List[Dict[str, Any]] = []
    balance = liability
    rou_balance = rou_asset
    for i, payment in enumerate(lease_payments):
        interest = balance * discount_rate
        principal = payment - interest
        balance -= principal
        rou_balance = max(0.0, rou_balance - annual_amortization)
        schedule.append({"period": i + 1, "interest_expense": interest, "amortization_expense": annual_amortization,
                         "total_expense": interest + annual_amortization, "liability_balance": balance,
                         "rou_asset_balance": rou_balance})
    return {"initial_liability": liability, "initial_rou_asset": rou_asset, "schedule": schedule}


def operating_lease_schedule(lease_payments: Sequence[float], discount_rate: float) -> Dict[str, Any]:
    n = len(lease_payments)
    liability = sum(p / (1 + discount_rate) ** (i + 1) for i, p in enumerate(lease_payments))
    rou_asset = liability
    straight_line_expense = sum(lease_payments) / n
    schedule: List[Dict[str, Any]] = []
    liability_balance = liability
    rou_balance = rou_asset
    for i, payment in enumerate(lease_payments):
        interest_accretion = liability_balance * discount_rate
        liability_balance -= (payment - interest_accretion)
        rou_amortization = straight_line_expense - interest_accretion
        rou_balance -= rou_amortization
        schedule.append({"period": i + 1, "straight_line_expense": straight_line_expense,
                         "interest_accretion": interest_accretion, "rou_amortization": rou_amortization,
                         "liability_balance": liability_balance, "rou_asset_balance": rou_balance})
    return {"initial_liability": liability, "initial_rou_asset": rou_asset,
            "straight_line_expense": straight_line_expense, "schedule": schedule}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "classify_lease" in d:
        out["classify_lease"] = classify_lease(**d["classify_lease"])
    if "initial_measurement" in d:
        out["initial_measurement"] = initial_measurement(**d["initial_measurement"])
    if "finance_lease_schedule" in d:
        out["finance_lease_schedule"] = finance_lease_schedule(**d["finance_lease_schedule"])
    if "operating_lease_schedule" in d:
        out["operating_lease_schedule"] = operating_lease_schedule(**d["operating_lease_schedule"])
    return out
