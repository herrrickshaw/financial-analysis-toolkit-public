"""Credit-card asset-backed securitization (master trust) mechanics -- a real, structurally different
securitization from finmodel.cmo's RMBS-style mortgage-pool PSA prepayment and sequential-pay tranching,
flagged explicitly as a gap in `docs/PROFESSOR_COURSE_SURVEY.md` (P C Narayan's IIM Bangalore banking-risk
course names credit-card securitization as a distinct topic from RMBS). Distilled from the standard
master-trust structure every real card-issuer trust prospectus (Citibank Credit Card Master Trust, Chase
Issuance Trust) discloses, and from Fabozzi's own ABS handbook chapter on credit-card receivables.

  * A credit-card receivables pool has no fixed amortization schedule the way a mortgage does -- balances
    revolve as cardholders draw and repay. During the trust's REVOLVING period, principal collected from the
    pool is reinvested to buy new receivables, so the investor certificate balance stays FLAT and investors
    receive interest only; only once the trust enters its AMORTIZATION period does collected principal
    actually flow through to pay down the certificate.
  * Excess spread = portfolio yield - (investor certificate rate + servicing fee rate + net charge-off
    rate) -- the trust's own profitability cushion. The standard, real early-amortization trigger defined in
    every card master-trust prospectus fires when the TRAILING 3-MONTH AVERAGE excess spread falls to zero
    or below, forcing the trust straight into amortization regardless of its originally scheduled revolving
    period, to protect investors before losses actually erode principal.
  * Amortization itself is either "pass-through" (100% of principal collected each month goes straight to
    investors until the certificate is retired) or "controlled amortization" (a level monthly payment over a
    stated number of months, the gentler real structure card issuers prefer when collections comfortably
    exceed the level payment).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


def excess_spread(portfolio_yield: float, certificate_rate: float, servicing_fee_rate: float, charge_off_rate: float) -> float:
    return portfolio_yield - certificate_rate - servicing_fee_rate - charge_off_rate


def early_amortization_trigger(monthly_excess_spreads: Sequence[float], window: int = 3) -> Dict[str, Any]:
    """Flags the first month whose trailing `window`-month average excess spread is <= 0 -- the standard
    real trigger every credit-card master-trust prospectus defines this way."""
    rolling_averages: List[float] = []
    triggered_month: Optional[int] = None
    for i in range(len(monthly_excess_spreads)):
        start = max(0, i - window + 1)
        window_slice = monthly_excess_spreads[start:i + 1]
        avg = sum(window_slice) / len(window_slice)
        rolling_averages.append(avg)
        if triggered_month is None and len(window_slice) == window and avg <= 0:
            triggered_month = i + 1  # 1-indexed month
    return {"rolling_averages": rolling_averages, "triggered": triggered_month is not None, "triggered_month": triggered_month}


def master_trust_cash_flows(receivables_balance: float, monthly_payment_rate: float, revolving_period_months: int,
                            certificate_balance: float, certificate_rate: float, amortization_method: str = "pass_through",
                            controlled_amortization_months: Optional[int] = None, max_months: int = 600) -> Dict[str, Any]:
    """Walks the trust month by month. During the revolving period, principal collected is reinvested
    (certificate balance stays flat, investors receive interest only); afterward, `amortization_method`
    controls how collected principal pays down the certificate."""
    if amortization_method not in ("pass_through", "controlled_amortization"):
        raise ValueError("amortization_method must be 'pass_through' or 'controlled_amortization'")
    if amortization_method == "controlled_amortization" and not controlled_amortization_months:
        raise ValueError("controlled_amortization_months is required for amortization_method='controlled_amortization'")
    monthly_rate = certificate_rate / 12
    principal_collected_per_month = receivables_balance * monthly_payment_rate
    controlled_payment = safe_div(certificate_balance, controlled_amortization_months) if controlled_amortization_months else None
    schedule: List[Dict[str, Any]] = []
    cert_balance = certificate_balance
    month = 0
    while cert_balance > 0.01 and month < max_months:
        month += 1
        investor_interest = cert_balance * monthly_rate
        if month <= revolving_period_months:
            principal_to_investors = 0.0
        elif amortization_method == "pass_through":
            principal_to_investors = min(cert_balance, principal_collected_per_month)
        else:
            principal_to_investors = min(cert_balance, controlled_payment, principal_collected_per_month)
        cert_balance -= principal_to_investors
        schedule.append({"month": month, "interest_paid": investor_interest,
                         "principal_paid": principal_to_investors, "closing_certificate_balance": cert_balance})
    return {"schedule": schedule, "months_to_full_paydown": month, "revolving_period_months": revolving_period_months,
            "fully_paid_down": cert_balance <= 0.01}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "excess_spread" in d:
        out["excess_spread"] = {"value": excess_spread(**d["excess_spread"])}
    if "early_amortization_trigger" in d:
        out["early_amortization_trigger"] = early_amortization_trigger(**d["early_amortization_trigger"])
    if "master_trust_cash_flows" in d:
        out["master_trust_cash_flows"] = master_trust_cash_flows(**d["master_trust_cash_flows"])
    return out
