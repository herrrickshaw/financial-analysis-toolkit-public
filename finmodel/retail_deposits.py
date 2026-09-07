"""Retail time-deposit mechanics: Fixed Deposits (FD) and Recurring Deposits (RD), the two standard Indian
(and broader South Asian) retail savings products, plus the real TDS withholding rule that applies to both.

  * FD: a lump sum compounds at a fixed rate with a stated compounding frequency (quarterly is the
    near-universal Indian-bank convention) -- plain compound interest, `FV = P(1+r/n)^(n*t)`.
  * RD: a fixed monthly installment is deposited every month; each installment is its own deposit that
    compounds (quarterly, the same convention) from ITS OWN deposit date to maturity, not from day one --
    so an installment made in month k of an n-month RD only earns interest for the remaining (n-k) months.
    Summing every installment's own future value is the direct, unambiguous way to compute the maturity
    value (RBI requires banks to compute RD interest on a compounding basis; simulating each installment
    separately, rather than using one of the several inconsistently-quoted closed-form "banker's formulas"
    circulating online, is the most defensible way to reproduce that requirement exactly).
  * TDS (tax deducted at source): under Section 194A of India's Income Tax Act, once a resident depositor's
    interest income from a bank in a financial year crosses a threshold (Rs 40,000 for most depositors, Rs
    50,000 for senior citizens), the bank withholds TDS at 10% on the FULL interest amount -- not merely the
    portion above the threshold, a real and commonly-misunderstood point of Indian tax law.
"""
from __future__ import annotations

from typing import Any, Dict

from .fin import safe_div


def fixed_deposit_maturity(principal: float, annual_rate: float, tenure_years: float, compounding_frequency: int = 4) -> Dict[str, Any]:
    maturity_value = principal * (1 + annual_rate / compounding_frequency) ** (compounding_frequency * tenure_years)
    return {"principal": principal, "maturity_value": maturity_value, "interest_earned": maturity_value - principal}


def recurring_deposit_maturity(monthly_installment: float, annual_rate: float, tenure_months: int,
                               compounding_frequency: int = 4) -> Dict[str, Any]:
    """Simulates every monthly installment's own future value from its deposit date to maturity, each
    compounding at `annual_rate` with `compounding_frequency` compounding periods per year."""
    installments = []
    maturity_value = 0.0
    for k in range(1, tenure_months + 1):
        years_remaining = (tenure_months - k) / 12.0
        fv = monthly_installment * (1 + annual_rate / compounding_frequency) ** (compounding_frequency * years_remaining)
        installments.append({"installment_number": k, "years_to_maturity": years_remaining, "future_value": fv})
        maturity_value += fv
    total_deposited = monthly_installment * tenure_months
    return {"installments": installments, "total_deposited": total_deposited, "maturity_value": maturity_value,
            "interest_earned": maturity_value - total_deposited}


def recurring_deposit_premature_value(monthly_installment: float, installments_made: int, applicable_rate: float,
                                      compounding_frequency: int = 4) -> Dict[str, Any]:
    """Value if an RD is closed early after `installments_made` deposits: each already-made installment is
    simulated forward only to the closure date (month `installments_made`), at the lower `applicable_rate`
    banks pay on premature closure (the rate actually earned for the period completed, not the contracted
    rate)."""
    total = 0.0
    for k in range(1, installments_made + 1):
        years_held = (installments_made - k) / 12.0
        total += monthly_installment * (1 + applicable_rate / compounding_frequency) ** (compounding_frequency * years_held)
    total_deposited = monthly_installment * installments_made
    return {"total_deposited": total_deposited, "premature_value": total, "interest_earned": total - total_deposited}


def tds_on_interest(interest_earned: float, tds_threshold: float = 40000.0, tds_rate: float = 0.10) -> Dict[str, Any]:
    """Section 194A: TDS applies to the ENTIRE interest amount, not just the excess over the threshold, once
    the threshold is crossed."""
    tds_amount = interest_earned * tds_rate if interest_earned > tds_threshold else 0.0
    return {"interest_earned": interest_earned, "tds_applicable": tds_amount > 0, "tds_amount": tds_amount,
            "net_interest": interest_earned - tds_amount}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "fixed_deposit_maturity" in d:
        out["fixed_deposit_maturity"] = fixed_deposit_maturity(**d["fixed_deposit_maturity"])
    if "recurring_deposit_maturity" in d:
        out["recurring_deposit_maturity"] = recurring_deposit_maturity(**d["recurring_deposit_maturity"])
    if "recurring_deposit_premature_value" in d:
        out["recurring_deposit_premature_value"] = recurring_deposit_premature_value(**d["recurring_deposit_premature_value"])
    if "tds_on_interest" in d:
        out["tds_on_interest"] = tds_on_interest(**d["tds_on_interest"])
    return out
