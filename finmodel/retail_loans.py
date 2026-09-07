"""Retail-loan (EMI / reducing-balance) mechanics -- the monthly consumer-lending analogue of
finmodel.project_finance's annual, DSCR-driven debt sizing. Every bank's home/auto/personal-loan EMI is
computed on the reducing (declining) balance method, the standard worldwide since usury-transparency rules
(in India, RBI's own lending guidelines mandate reducing-balance disclosure): interest each month is charged
only on the OUTSTANDING balance, and the EMI is the level payment that fully amortizes the loan.

  * EMI = the fixed monthly payment (`finmodel.fin.pmt`, sign-flipped so it reads as a positive outflow).
  * Part-prepayment has two real, mutually exclusive strategies every bank actually offers a borrower:
    "reduce_tenure" (keep the EMI the same, pay off sooner) always saves MORE total interest than
    "reduce_emi" (keep the tenure the same, pay less each month) for the same prepayment amount, because
    reducing tenure removes interest-bearing months entirely rather than just shrinking each month's charge.
  * A floating-rate reset (a real, recurring event on any adjustable-rate loan) faces the same two-strategy
    choice: re-EMI (recompute the payment for the unchanged remaining tenure) or re-tenure (recompute the
    remaining term for the unchanged EMI).
  * Loan eligibility by FOIR (Fixed Obligation to Income Ratio) is the underwriting metric Indian banks
    (SBI, HDFC, ICICI and others) publish directly in their retail-lending policies: total EMI obligations
    (existing + proposed) must not exceed a fixed fraction of gross monthly income.
"""
from __future__ import annotations

from typing import Any, Dict, List

from .fin import pmt


def emi(principal: float, annual_rate: float, tenure_months: int) -> float:
    """The level monthly reducing-balance payment that fully amortizes `principal` over `tenure_months`."""
    monthly_rate = annual_rate / 12
    return -pmt(monthly_rate, tenure_months, principal)


def _simulate_amortization(principal: float, monthly_rate: float, payment: float, max_months: int) -> Dict[str, Any]:
    balance = principal
    months = 0
    total_interest = 0.0
    schedule: List[Dict[str, Any]] = []
    while balance > 1e-6 and months < max_months:
        interest = balance * monthly_rate
        principal_component = payment - interest
        if principal_component >= balance:
            principal_component = balance
        balance -= principal_component
        total_interest += interest
        months += 1
        schedule.append({"month": months, "interest": interest, "principal": principal_component, "closing_balance": balance})
    return {"months": months, "total_interest": total_interest, "schedule": schedule, "closing_balance": balance}


def amortization_schedule(principal: float, annual_rate: float, tenure_months: int) -> Dict[str, Any]:
    monthly_rate = annual_rate / 12
    payment = emi(principal, annual_rate, tenure_months)
    result = _simulate_amortization(principal, monthly_rate, payment, max_months=tenure_months + 1)
    return {"emi": payment, "schedule": result["schedule"], "total_interest": result["total_interest"],
            "total_payment": principal + result["total_interest"]}


def prepayment_impact(principal: float, annual_rate: float, tenure_months: int, prepayment_amount: float,
                      prepayment_month: int, strategy: str = "reduce_tenure") -> Dict[str, Any]:
    """Applies a lump-sum prepayment after `prepayment_month` regular EMIs and reworks the remaining schedule
    under the chosen strategy, reporting the interest actually saved versus completing the original schedule."""
    if strategy not in ("reduce_tenure", "reduce_emi"):
        raise ValueError("strategy must be 'reduce_tenure' or 'reduce_emi'")
    if not (1 <= prepayment_month < tenure_months):
        raise ValueError("prepayment_month must be between 1 and tenure_months - 1")
    monthly_rate = annual_rate / 12
    original = amortization_schedule(principal, annual_rate, tenure_months)
    original_emi = original["emi"]
    interest_paid_before = sum(r["interest"] for r in original["schedule"][:prepayment_month])
    balance_before = original["schedule"][prepayment_month - 1]["closing_balance"]
    balance_after_prepay = max(0.0, balance_before - prepayment_amount)
    remaining_months_original = tenure_months - prepayment_month

    if balance_after_prepay <= 1e-6:
        new_total_interest = interest_paid_before
        return {"strategy": strategy, "loan_fully_repaid": True, "prepayment_month": prepayment_month,
                "interest_paid_before_prepayment": interest_paid_before,
                "original_total_interest": original["total_interest"], "new_total_interest": new_total_interest,
                "interest_saved": original["total_interest"] - new_total_interest}

    if strategy == "reduce_emi":
        new_payment = -pmt(monthly_rate, remaining_months_original, balance_after_prepay)
    else:
        new_payment = original_emi
    remaining = _simulate_amortization(balance_after_prepay, monthly_rate, new_payment, max_months=remaining_months_original + 1)
    new_total_interest = interest_paid_before + remaining["total_interest"]
    return {"strategy": strategy, "loan_fully_repaid": False, "prepayment_month": prepayment_month,
            "prepayment_amount": prepayment_amount, "balance_after_prepayment": balance_after_prepay,
            "new_emi": new_payment, "new_tenure_months": prepayment_month + remaining["months"],
            "original_total_interest": original["total_interest"], "new_total_interest": new_total_interest,
            "interest_saved": original["total_interest"] - new_total_interest}


def floating_rate_reset(outstanding_balance: float, remaining_tenure_months: int, old_rate: float, new_rate: float,
                        strategy: str = "reduce_emi", current_emi: float | None = None) -> Dict[str, Any]:
    if strategy not in ("reduce_tenure", "reduce_emi"):
        raise ValueError("strategy must be 'reduce_tenure' or 'reduce_emi'")
    new_monthly_rate = new_rate / 12
    if strategy == "reduce_emi":
        new_payment = -pmt(new_monthly_rate, remaining_tenure_months, outstanding_balance)
        new_tenure_months = remaining_tenure_months
    else:
        if current_emi is None:
            raise ValueError("current_emi is required for strategy='reduce_tenure'")
        remaining = _simulate_amortization(outstanding_balance, new_monthly_rate, current_emi, max_months=1200)
        new_payment = current_emi
        new_tenure_months = remaining["months"]
    return {"strategy": strategy, "old_rate": old_rate, "new_rate": new_rate,
            "new_emi": new_payment, "new_tenure_months": new_tenure_months}


def foreclosure_payoff(principal: float, annual_rate: float, tenure_months: int, foreclosure_month: int,
                       foreclosure_charge_pct: float = 0.0) -> Dict[str, Any]:
    if not (1 <= foreclosure_month <= tenure_months):
        raise ValueError("foreclosure_month must be between 1 and tenure_months")
    schedule = amortization_schedule(principal, annual_rate, tenure_months)
    outstanding = schedule["schedule"][foreclosure_month - 1]["closing_balance"]
    charge = outstanding * foreclosure_charge_pct
    interest_paid_to_date = sum(r["interest"] for r in schedule["schedule"][:foreclosure_month])
    return {"outstanding_balance": outstanding, "foreclosure_charge": charge,
            "payoff_amount": outstanding + charge, "interest_paid_to_date": interest_paid_to_date,
            "interest_saved_vs_completing_tenure": schedule["total_interest"] - interest_paid_to_date}


def loan_eligibility_foir(monthly_gross_income: float, existing_emis: float, annual_rate: float,
                          tenure_months: int, foir_limit: float = 0.50) -> Dict[str, Any]:
    """Fixed Obligation to Income Ratio underwriting: the maximum NEW loan principal a borrower qualifies
    for, given their existing EMI obligations must not push total EMIs past `foir_limit` of gross income."""
    max_total_emi = monthly_gross_income * foir_limit
    available_emi_capacity = max(0.0, max_total_emi - existing_emis)
    monthly_rate = annual_rate / 12
    if monthly_rate == 0:
        max_eligible_principal = available_emi_capacity * tenure_months
    else:
        max_eligible_principal = available_emi_capacity * (1 - (1 + monthly_rate) ** (-tenure_months)) / monthly_rate
    return {"max_total_emi": max_total_emi, "available_emi_capacity": available_emi_capacity,
            "max_eligible_principal": max_eligible_principal}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "emi_calculation" in d:
        out["emi_calculation"] = {"emi": emi(**d["emi_calculation"])}
    if "amortization_schedule" in d:
        out["amortization_schedule"] = amortization_schedule(**d["amortization_schedule"])
    if "prepayment_impact" in d:
        out["prepayment_impact"] = prepayment_impact(**d["prepayment_impact"])
    if "floating_rate_reset" in d:
        out["floating_rate_reset"] = floating_rate_reset(**d["floating_rate_reset"])
    if "foreclosure_payoff" in d:
        out["foreclosure_payoff"] = foreclosure_payoff(**d["foreclosure_payoff"])
    if "loan_eligibility_foir" in d:
        out["loan_eligibility_foir"] = loan_eligibility_foir(**d["loan_eligibility_foir"])
    return out
