"""Project bankability and investability ranking: turning a state/sector project's capex and incentive
stack (from `finmodel.sector_investment_model`) into IRR, simple ROI, and payback metrics computed BOTH with
and without incentives, so projects can be ranked on their own merits and the specific effect of
incentives -- which projects incentives make bankable, not merely cheaper -- is visible rather than buried
in a single blended number. No prior representation across the toolkit's other ~60 modules.

The central point this module exists to make: incentives don't just lower a project's effective cost, they
can change WHETHER it clears a lender's or investor's hurdle rate at all. A project with a below-hurdle IRR
on its own capex and operating cash flow can become bankable once its actual, correctly-timed incentive cash
flows are added on top -- `rank_projects` flags exactly this transition (`incentive_enabled_projects`)
rather than collapsing everything into one "effective cost" figure that hides it.

Incentive cash-flow timing is taken directly from `finmodel.sector_investment_model.incentive_present_value`'s
own `detail` list -- an upfront component is netted against day-zero capex (matching how that module already
treats it), and a recurring component's own `annual_amounts` are added, year by year, to the project's
operating cash flow -- never re-derived or re-assumed here.

`debt_service_coverage_ratio` adds the specific covenant a lender actually tests before disbursing: is
operating cash flow enough to cover the loan's own annual repayment (principal + interest, via
`finmodel.fin.pmt`'s amortization math), by at least the lender's minimum DSCR. Real lender terms differ in
one important way this function is built to respect: IREDA (for renewable-energy projects) publishes an
explicit, dated minimum-DSCR schedule (1.2x-1.4x depending on sector and loan structure); SBI and REC do not
publicly disclose a DSCR floor at all for general project finance, so the generic 1.20x-1.25x figure used for
those cases is a general project-finance industry convention, not a specific disclosed lender requirement --
`docs/INDIA_PROJECT_FINANCE_LENDING_TERMS.md` catalogs exactly which is which, with sourcing.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import irr, pmt, safe_div


def annual_incentive_cashflow(incentive_detail: Sequence[Dict[str, Any]], project_life_years: int) -> List[float]:
    """Sums every RECURRING incentive component's own `annual_amounts`, year by year, padding with zero past
    a component's own tenure and truncating anything beyond `project_life_years`. Upfront components are
    excluded -- they're netted against day-zero capex in `project_returns` instead."""
    cashflow = [0.0] * project_life_years
    for c in incentive_detail:
        if c.get("timing") != "recurring":
            continue
        for year_index, amount in enumerate(c.get("annual_amounts", [])):
            if year_index < project_life_years:
                cashflow[year_index] += amount
    return cashflow


def project_returns(total_capex: float, upfront_incentive_value: float, incentive_detail: Sequence[Dict[str, Any]],
                    annual_operating_cash_flow: float, project_life_years: int) -> Dict[str, Any]:
    incentive_cashflow = annual_incentive_cashflow(incentive_detail, project_life_years)
    avg_recurring_incentive = safe_div(sum(incentive_cashflow), project_life_years)
    net_day0_investment = total_capex - upfront_incentive_value

    cashflow_without = [-total_capex] + [annual_operating_cash_flow] * project_life_years
    cashflow_with = [-net_day0_investment] + [annual_operating_cash_flow + incentive_cashflow[y]
                                              for y in range(project_life_years)]

    return {
        "irr_without_incentives": irr(cashflow_without),
        "irr_with_incentives": irr(cashflow_with),
        "irr_uplift": irr(cashflow_with) - irr(cashflow_without),
        "simple_roi_without_incentives": safe_div(annual_operating_cash_flow, total_capex),
        "simple_roi_with_incentives": safe_div(annual_operating_cash_flow + avg_recurring_incentive, net_day0_investment),
        "payback_years_without_incentives": safe_div(total_capex, annual_operating_cash_flow),
        "payback_years_with_incentives": safe_div(net_day0_investment, annual_operating_cash_flow + avg_recurring_incentive),
    }


def rank_projects(entries: Sequence[Dict[str, Any]], hurdle_rate: float) -> Dict[str, Any]:
    """`entries`: each carrying `state`, `sector`, `total_capex`, `upfront_incentive_value`,
    `incentive_detail` (the `detail` list from `incentive_present_value`), `annual_operating_cash_flow`, and
    `project_life_years`. Computes `project_returns` for each, ranks by IRR without and with incentives
    separately, and flags every project whose IRR clears `hurdle_rate` WITH incentives but not without --
    the projects incentives make bankable rather than merely more attractive."""
    scored: List[Dict[str, Any]] = []
    for e in entries:
        returns = project_returns(total_capex=e["total_capex"], upfront_incentive_value=e["upfront_incentive_value"],
                                  incentive_detail=e["incentive_detail"],
                                  annual_operating_cash_flow=e["annual_operating_cash_flow"],
                                  project_life_years=e["project_life_years"])
        scored.append({"state": e["state"], "sector": e["sector"], **returns})

    ranked_without = sorted(scored, key=lambda p: p["irr_without_incentives"], reverse=True)
    ranked_with = sorted(scored, key=lambda p: p["irr_with_incentives"], reverse=True)
    incentive_enabled = [p for p in scored
                        if p["irr_without_incentives"] < hurdle_rate <= p["irr_with_incentives"]]

    def _summary(p: Dict[str, Any], key: str) -> Dict[str, Any]:
        return {"state": p["state"], "sector": p["sector"], key: p[key]}

    return {
        "hurdle_rate": hurdle_rate,
        "projects": scored,
        "ranked_by_irr_without_incentives": [_summary(p, "irr_without_incentives") for p in ranked_without],
        "ranked_by_irr_with_incentives": [_summary(p, "irr_with_incentives") for p in ranked_with],
        "incentive_enabled_projects": [{"state": p["state"], "sector": p["sector"],
                                        "irr_without_incentives": p["irr_without_incentives"],
                                        "irr_with_incentives": p["irr_with_incentives"]} for p in incentive_enabled],
    }


def debt_service_coverage_ratio(annual_cash_flow: float, loan_amount: float, interest_rate: float,
                                tenure_years: int, min_dscr: float) -> Dict[str, Any]:
    """`loan_amount` is the debt portion of capex (e.g. 70% under the common 70:30 debt:equity norm both SBI
    and REC apply). Annual debt service is the loan's own level annual repayment via `finmodel.fin.pmt`
    (Excel-PMT convention, so its return is negated back to a positive outflow here)."""
    annual_debt_service = -pmt(interest_rate, tenure_years, loan_amount)
    dscr = safe_div(annual_cash_flow, annual_debt_service)
    return {"annual_debt_service": annual_debt_service, "dscr": dscr, "min_dscr_required": min_dscr,
            "compliant": dscr >= min_dscr}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "project_returns" in d:
        out["project_returns"] = project_returns(**d["project_returns"])
    if "rank_projects" in d:
        p = d["rank_projects"]
        out["rank_projects"] = rank_projects(p["entries"], p["hurdle_rate"])
    if "debt_service_coverage_ratio" in d:
        out["debt_service_coverage_ratio"] = debt_service_coverage_ratio(**d["debt_service_coverage_ratio"])
    if "dscr_matrix" in d:
        results = []
        for e in d["dscr_matrix"]:
            r = debt_service_coverage_ratio(annual_cash_flow=e["annual_cash_flow"], loan_amount=e["loan_amount"],
                                            interest_rate=e["interest_rate"], tenure_years=e["tenure_years"],
                                            min_dscr=e["min_dscr"])
            results.append({"state": e["state"], "sector": e["sector"], "lender": e.get("lender", ""), **r})
        out["dscr_matrix"] = results
    return out
