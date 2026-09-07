"""Project finance and real-estate income-approach valuation — a real, distinct curriculum area from corporate
3-statement/DCF modeling (this toolkit's catalog survey confirms Wall Street Prep and BIWS both teach it as a
standalone course, separate from their core financial-modeling tracks): non-recourse infrastructure/renewable-
energy debt is sized against CFADS (Cash Flow Available for Debt Service), not a company-level WACC-based DCF.

  DSCR (Debt Service Coverage Ratio) = CFADS / debt service — the period-by-period covenant lenders test.
  Debt sculpting        — real project debt is repaid on a SCULPTED (uneven) schedule sized so DSCR sits at
                          exactly the lender's minimum covenant every period, maximizing the debt a project's
                          own cash flow can support — the opposite of a corporate loan's flat amortization.
  LLCR (Loan Life Coverage Ratio) = PV(CFADS over the remaining debt tenor, at the debt's own rate) / outstanding
                          debt balance — a forward-looking cousin of DSCR lenders also covenant on.
  Cap rate / NOI         — the real-estate income approach: value = Net Operating Income / capitalization rate,
                          the direct-cap analogue of a DCF's terminal-value multiple, standard practice for an
                          income-producing property."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import npv, safe_div


def dscr(cfads: Sequence[float], debt_service: Sequence[float]) -> List[float]:
    if len(cfads) != len(debt_service):
        raise ValueError("cfads and debt_service must have the same length")
    return [safe_div(c, d, default=float("inf")) for c, d in zip(cfads, debt_service)]


def size_debt_by_dscr(cfads: Sequence[float], target_dscr: float, interest_rate: float) -> Dict[str, Any]:
    """The maximum debt a project's own cash flow can support: PV, at the debt's interest rate, of each period's
    debt-service CAPACITY (cfads / target_dscr) — the real, standard project-finance sizing convention."""
    if target_dscr <= 0:
        raise ValueError("target_dscr must be positive")
    capacity = [c / target_dscr for c in cfads]
    max_debt = npv(interest_rate, capacity)
    return {"cfads": list(cfads), "debt_service_capacity": capacity, "target_dscr": target_dscr, "max_debt_sized": max_debt}


def sculpted_amortization(cfads: Sequence[float], initial_debt: float, target_dscr: float, interest_rate: float, tol: float = 1.0) -> Dict[str, Any]:
    """The real, uneven repayment schedule that keeps DSCR at exactly `target_dscr` every period until the debt
    is retired — later periods (once the balance and interest charge have shrunk) repay MORE principal than
    earlier ones, the defining shape of a sculpted schedule versus a flat corporate amortization."""
    if target_dscr <= 0:
        raise ValueError("target_dscr must be positive")
    balance = float(initial_debt)
    schedule: List[Dict[str, float]] = []
    for c in cfads:
        interest = balance * interest_rate
        capacity = c / target_dscr
        principal = min(balance, max(0.0, capacity - interest))
        debt_service = interest + principal
        period_dscr = safe_div(c, debt_service, default=float("inf"))
        balance -= principal
        schedule.append({"cfads": c, "opening_balance": balance + principal, "interest": interest, "principal": principal,
                          "debt_service": debt_service, "dscr": period_dscr, "closing_balance": balance})
        if balance <= tol:
            balance = 0.0
    return {"schedule": schedule, "fully_repaid": balance <= tol, "ending_balance": balance}


def llcr(cfads_remaining: Sequence[float], outstanding_debt: float, discount_rate: float) -> Dict[str, Any]:
    """Loan Life Coverage Ratio: PV(remaining CFADS over the rest of the debt tenor) / outstanding debt balance —
    a forward-looking covenant (unlike DSCR's single-period snapshot) that captures whether the WHOLE remaining
    cash flow stream still covers the debt, not just the next payment."""
    pv_remaining = npv(discount_rate, cfads_remaining)
    return {"pv_remaining_cfads": pv_remaining, "outstanding_debt": outstanding_debt, "llcr": safe_div(pv_remaining, outstanding_debt, default=float("inf"))}


def cap_rate_valuation(noi: float, cap_rate: float) -> Dict[str, Any]:
    """The real-estate income approach: value = NOI / cap rate — the direct-capitalization analogue of applying
    an exit multiple to terminal EBITDA in a corporate DCF."""
    if cap_rate <= 0:
        raise ValueError("cap_rate must be positive")
    return {"noi": noi, "cap_rate": cap_rate, "value": noi / cap_rate}


def implied_cap_rate(noi: float, price: float) -> Dict[str, Any]:
    """The reverse direction: back out the cap rate an observed transaction price implies, for comping against
    other real, comparable property sales."""
    return {"noi": noi, "price": price, "implied_cap_rate": safe_div(noi, price)}


def levered_cash_on_cash(noi: float, debt_service: float, equity_invested: float) -> Dict[str, Any]:
    """A property investor's real, standard after-financing return metric — distinct from cap rate (which is
    unlevered): the levered cash flow actually distributable to equity, divided by the equity actually invested."""
    levered_cf = noi - debt_service
    return {"noi": noi, "debt_service": debt_service, "levered_cash_flow": levered_cf,
            "equity_invested": equity_invested, "cash_on_cash_return": safe_div(levered_cf, equity_invested)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "size_debt_by_dscr" in d:
        out["size_debt_by_dscr"] = size_debt_by_dscr(**d["size_debt_by_dscr"])
    if "sculpted_amortization" in d:
        out["sculpted_amortization"] = sculpted_amortization(**d["sculpted_amortization"])
    if "llcr" in d:
        out["llcr"] = llcr(**d["llcr"])
    if "cap_rate_valuation" in d:
        out["cap_rate_valuation"] = cap_rate_valuation(**d["cap_rate_valuation"])
    if "levered_cash_on_cash" in d:
        out["levered_cash_on_cash"] = levered_cash_on_cash(**d["levered_cash_on_cash"])
    return out
