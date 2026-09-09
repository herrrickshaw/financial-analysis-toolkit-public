"""India corporate tax regime comparison for new manufacturing investment (Section 115BAB vs 115BAA vs the
standard regime), and the CGTMSE credit-guarantee fee's effect on a project's debt-service coverage -- two
real financing/tax mechanics that change a project's actual bankability beyond the state/central capital
incentives already modeled in `finmodel.investment_incentives` and `finmodel.project_bankability`. No prior
representation across the toolkit's other ~65 modules.

Section 115BAB (new manufacturing companies) offers a 15% base tax rate versus Section 115BAA's 22%
(existing domestic companies) or the pre-2019 standard regime's 30% -- but is available only to companies
incorporated on/after 1.10.2019 that commence manufacturing by a statutory cutoff (31.3.2024, per this
toolkit's own research; see `docs/INDIA_CENTRAL_INVESTMENT_INCENTIVES.md`), and forgoes most other
deductions, including additional depreciation. The EFFECTIVE rate in every case is exact statutory
arithmetic, not an estimate: `base_rate * (1 + surcharge_rate) * (1 + cess_rate)`. This module computes that
identity, then the resulting post-tax cash flow and IRR under each regime, so the real choice a new
manufacturer faces shows up as a number, not just a rate comparison.

Minimum Alternate Tax (MAT) does NOT apply to 115BAA/115BAB electors but CAN bind a standard-regime company
whose book profit exceeds its taxable income -- this module does not model MAT, since that depends on
book-vs-tax income differences this toolkit has no visibility into. Treat the standard-regime effective rate
computed here as a FLOOR, not a ceiling, for a company that would otherwise be MAT-bound.

CGTMSE's financing effect is different in kind from a tax election: it gives a lender collateral-free
comfort to extend a loan a borrower might not otherwise qualify for, at the cost of an annual guarantee fee
(0.37%-1.20% p.a. of the covered loan amount, per its own published fee schedule -- see
`docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md`) layered onto the loan's own debt-service coverage test as a
real, if usually small, additional cash outflow. `cgtmse_adjusted_dscr` reuses the same amortization math as
`finmodel.project_bankability.debt_service_coverage_ratio` and reports the DSCR with and without that fee
side by side, so the fee's real (small) cost is visible rather than the scheme being treated as a free
DSCR improvement -- its real value is loan ACCESS, not a better covenant ratio.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import irr, pmt, safe_div


def effective_corporate_tax_rate(base_rate: float, surcharge_rate: float, cess_rate: float) -> Dict[str, Any]:
    effective_rate = base_rate * (1 + surcharge_rate) * (1 + cess_rate)
    return {"base_rate": base_rate, "surcharge_rate": surcharge_rate, "cess_rate": cess_rate,
            "effective_rate": effective_rate}


def post_tax_project_returns(pre_tax_annual_cash_flow: float, total_capex: float, project_life_years: int,
                             effective_tax_rate: float) -> Dict[str, Any]:
    post_tax_annual_cash_flow = pre_tax_annual_cash_flow * (1 - effective_tax_rate)
    cashflow = [-total_capex] + [post_tax_annual_cash_flow] * project_life_years
    return {"post_tax_annual_cash_flow": post_tax_annual_cash_flow, "irr_post_tax": irr(cashflow)}


def tax_regime_comparison(pre_tax_annual_cash_flow: float, total_capex: float, project_life_years: int,
                          regimes: Dict[str, Dict[str, float]]) -> Dict[str, Any]:
    """`regimes`: e.g. {"115BAB": {"base_rate": 0.15, "surcharge_rate": 0.10, "cess_rate": 0.04}, ...}."""
    results: Dict[str, Any] = {}
    for name, params in regimes.items():
        rate = effective_corporate_tax_rate(**params)
        returns = post_tax_project_returns(pre_tax_annual_cash_flow, total_capex, project_life_years,
                                           rate["effective_rate"])
        results[name] = {**rate, **returns}
    best = max(results, key=lambda name: results[name]["irr_post_tax"])
    return {"regimes": results, "best_regime": best,
            "irr_uplift_of_best_vs_worst": max(r["irr_post_tax"] for r in results.values()) -
                                           min(r["irr_post_tax"] for r in results.values())}


def cgtmse_guarantee_fee(loan_amount: float, annual_fee_rate: float) -> Dict[str, Any]:
    return {"loan_amount": loan_amount, "annual_fee_rate": annual_fee_rate, "annual_fee": loan_amount * annual_fee_rate}


def cgtmse_adjusted_dscr(annual_cash_flow: float, loan_amount: float, interest_rate: float, tenure_years: int,
                         annual_fee_rate: float, min_dscr: float) -> Dict[str, Any]:
    annual_debt_service = -pmt(interest_rate, tenure_years, loan_amount)
    fee = cgtmse_guarantee_fee(loan_amount, annual_fee_rate)["annual_fee"]
    total_annual_outflow = annual_debt_service + fee
    return {"annual_debt_service": annual_debt_service, "annual_guarantee_fee": fee,
            "total_annual_debt_service_with_fee": total_annual_outflow,
            "dscr_with_cgtmse_fee": safe_div(annual_cash_flow, total_annual_outflow),
            "dscr_without_fee_for_comparison": safe_div(annual_cash_flow, annual_debt_service),
            "min_dscr_required": min_dscr, "compliant": safe_div(annual_cash_flow, total_annual_outflow) >= min_dscr}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "tax_regime_comparison" in d:
        p = d["tax_regime_comparison"]
        out["tax_regime_comparison"] = tax_regime_comparison(p["pre_tax_annual_cash_flow"], p["total_capex"],
                                                              p["project_life_years"], p["regimes"])
    if "cgtmse_adjusted_dscr" in d:
        out["cgtmse_adjusted_dscr"] = cgtmse_adjusted_dscr(**d["cgtmse_adjusted_dscr"])
    return out
