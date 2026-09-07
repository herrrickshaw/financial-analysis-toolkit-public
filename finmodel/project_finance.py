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
                          income-producing property.
  Interest-only + bullet — a real, standard alternative to both a flat corporate annuity and DSCR sculpting: no
                          principal repaid until a single bullet at maturity, real lender offer terms for
                          shorter project-finance facilities or where a refinancing/asset sale is expected —
                          maximizes near-term cash-flow relief at the cost of more total interest paid over the
                          facility's life, checked here against a real balloon-coverage metric (does cash
                          actually accumulated over the interest-only years cover the bullet) rather than
                          assuming refinancing risk away."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import npv, pmt, safe_div


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


def level_annuity_schedule(loan_amount: float, interest_rate: float, tenure_years: int) -> Dict[str, Any]:
    """The standard corporate-loan amortization: equal total debt service every period. The baseline this
    module's other two structures (DSCR-sculpted, interest-only + bullet) are usually compared against."""
    payment = -pmt(interest_rate, tenure_years, loan_amount)
    balance = float(loan_amount)
    schedule: List[Dict[str, Any]] = []
    for year in range(1, tenure_years + 1):
        interest = balance * interest_rate
        principal = min(balance, payment - interest)
        debt_service = interest + principal
        balance -= principal
        schedule.append({"year": year, "interest": interest, "principal": principal, "debt_service": debt_service, "closing_balance": balance})
    return {"schedule": schedule, "total_interest": sum(r["interest"] for r in schedule), "level_payment": payment}


def interest_only_bullet_schedule(loan_amount: float, interest_rate: float, tenure_years: int) -> Dict[str, Any]:
    """No principal repaid until a single bullet at maturity — real, standard lender-offered terms for shorter
    project-finance facilities or where refinancing/an asset sale is expected. Interest accrues on the full,
    never-amortizing balance for the whole tenure, so total interest paid is real and HIGHER than an amortizing
    structure's over the same life — the direct trade-off for the near-term cash-flow relief."""
    schedule: List[Dict[str, Any]] = []
    for year in range(1, tenure_years + 1):
        interest = loan_amount * interest_rate
        principal = loan_amount if year == tenure_years else 0.0
        schedule.append({"year": year, "interest": interest, "principal": principal, "debt_service": interest + principal,
                         "closing_balance": 0.0 if year == tenure_years else loan_amount})
    return {"schedule": schedule, "total_interest": sum(r["interest"] for r in schedule), "bullet_principal": loan_amount}


def balloon_coverage_ratio(accumulated_cash_before_maturity: float, bullet_principal: float) -> Dict[str, Any]:
    """Real, standard risk check for an interest-only/bullet structure: does cash actually ACCUMULATED over the
    facility's interest-only life cover the bullet on its own, without relying on refinancing or an asset sale —
    the real question a lender or borrower needs answered before signing up to a bullet structure, since a
    stand-alone DSCR reading in the maturity year (one year's CFADS against a full principal repayment) is not
    a meaningful covenant test by itself."""
    return {"accumulated_cash": accumulated_cash_before_maturity, "bullet_principal": bullet_principal,
            "coverage_ratio": safe_div(accumulated_cash_before_maturity, bullet_principal)}


def compare_debt_structures(loan_amount: float, interest_rate: float, tenure_years: int, cfads: Sequence[float],
                            target_dscr: float = 1.5) -> Dict[str, Any]:
    """Side by side, the three real debt-structuring options this module supports, given the SAME project cash
    flow: a level annuity (the corporate-loan default), a DSCR-sculpted schedule (uneven, maximizing sized debt
    at a target covenant), and an interest-only/bullet structure — the real trade-off a borrower and lender
    negotiate over (total interest cost vs. near-term cash-flow relief vs. covenant headroom), quantified
    directly rather than argued about in the abstract."""
    annuity = level_annuity_schedule(loan_amount, interest_rate, tenure_years)
    io_bullet = interest_only_bullet_schedule(loan_amount, interest_rate, tenure_years)
    sculpted = sculpted_amortization(cfads, loan_amount, target_dscr, interest_rate)

    def _summary(schedule: Sequence[Dict[str, Any]], total_interest: float) -> Dict[str, Any]:
        # only over periods where debt is still outstanding -- a structure that retires debt early (sculpting
        # can do this at a generous covenant) leaves zero debt service afterward, which isn't a coverage test.
        dscrs = [safe_div(cfads[i], schedule[i]["debt_service"]) for i in range(len(schedule)) if schedule[i]["debt_service"] > 0]
        return {"total_interest": total_interest, "year1_debt_service": schedule[0]["debt_service"],
                "min_dscr": min(dscrs) if dscrs else float("nan"), "average_dscr": sum(dscrs) / len(dscrs) if dscrs else float("nan")}

    sculpted_total_interest = sum(r["interest"] for r in sculpted["schedule"])
    return {"level_annuity": _summary(annuity["schedule"], annuity["total_interest"]),
            "interest_only_bullet": _summary(io_bullet["schedule"], io_bullet["total_interest"]),
            "dscr_sculpted": _summary(sculpted["schedule"], sculpted_total_interest)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "size_debt_by_dscr" in d:
        out["size_debt_by_dscr"] = size_debt_by_dscr(**d["size_debt_by_dscr"])
    if "sculpted_amortization" in d:
        out["sculpted_amortization"] = sculpted_amortization(**d["sculpted_amortization"])
    if "llcr" in d:
        out["llcr"] = llcr(**d["llcr"])
    if "level_annuity_schedule" in d:
        out["level_annuity_schedule"] = level_annuity_schedule(**d["level_annuity_schedule"])
    if "interest_only_bullet_schedule" in d:
        out["interest_only_bullet_schedule"] = interest_only_bullet_schedule(**d["interest_only_bullet_schedule"])
    if "balloon_coverage_ratio" in d:
        out["balloon_coverage_ratio"] = balloon_coverage_ratio(**d["balloon_coverage_ratio"])
    if "compare_debt_structures" in d:
        out["compare_debt_structures"] = compare_debt_structures(**d["compare_debt_structures"])
    if "cap_rate_valuation" in d:
        out["cap_rate_valuation"] = cap_rate_valuation(**d["cap_rate_valuation"])
    if "levered_cash_on_cash" in d:
        out["levered_cash_on_cash"] = levered_cash_on_cash(**d["levered_cash_on_cash"])
    return out
