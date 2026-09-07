"""SaaS/subscription cohort analysis and LTV — CFI's own named "Cohort Analysis" and "LTV CAC Ratio" templates
(this toolkit's catalog flagged both as real, uncovered titles), a natural extension of `finmodel.startup_model`
specifically for a subscription business's real, standard unit economics.

  Retention curve            — the fraction of a cohort still active N periods after acquisition; the whole
                               basis for a real cohort-based revenue forecast (as opposed to `finmodel.
                               startup_model`'s single blended growth-rate assumption).
  GRR vs NRR                 — Gross Revenue Retention (churn/contraction only, capped at 100%) versus Net
                               Revenue Retention (also credits expansion/upsell from the SAME existing customers,
                               which can push NRR above 100% — the real, standard metric investors watch, and a
                               real, easy point of confusion with GRR).
  LTV (lifetime value)       — the real, exact form (sum of each future period's retained revenue, discounted)
                               and the real, standard CLOSED-FORM approximation (ARPU x gross margin / churn
                               rate) that assumes constant geometric churn — checked against each other.
  LTV:CAC and CAC payback    — the real, standard SaaS unit-economics checks (a LTV:CAC >= 3x and payback under
                               ~12-18 months are common real investor rules of thumb, not hard thresholds)."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def cohort_retention_curve(cohort_size: float, retained_customers_by_period: Sequence[float]) -> Dict[str, Any]:
    return {"cohort_size": cohort_size, "retained_customers": list(retained_customers_by_period),
            "retention_pct": [safe_div(r, cohort_size) for r in retained_customers_by_period]}


def ltv_from_retention_curve(retention_pct: Sequence[float], arpu: float, gross_margin: float, discount_rate: float = 0.0) -> Dict[str, Any]:
    """The real, exact form: sum, over every future period the cohort's own retention curve covers, of that
    period's still-retained fraction x ARPU x gross margin, discounted back to present value."""
    periods = [r * arpu * gross_margin / (1 + discount_rate) ** t for t, r in enumerate(retention_pct)]
    return {"periods": periods, "ltv": sum(periods)}


def ltv_simplified(arpu: float, gross_margin: float, monthly_churn_rate: float) -> Dict[str, Any]:
    """The real, standard closed-form approximation assuming constant (geometric) monthly churn — a fast
    estimate, not a substitute for the exact retention-curve form above when a real cohort curve is available."""
    if monthly_churn_rate <= 0:
        raise ValueError("monthly_churn_rate must be positive")
    return {"arpu": arpu, "gross_margin": gross_margin, "monthly_churn_rate": monthly_churn_rate,
            "ltv": arpu * gross_margin / monthly_churn_rate, "average_customer_lifetime_months": 1 / monthly_churn_rate}


def revenue_retention(beginning_revenue: float, expansion: float, contraction: float, churned: float) -> Dict[str, Any]:
    """GRR excludes expansion (capped at 100% by construction, since it only ever reflects loss); NRR credits it
    back in and can exceed 100% — the real, standard distinction between the two metrics."""
    grr = safe_div(beginning_revenue - contraction - churned, beginning_revenue)
    nrr = safe_div(beginning_revenue + expansion - contraction - churned, beginning_revenue)
    return {"beginning_revenue": beginning_revenue, "expansion": expansion, "contraction": contraction, "churned": churned,
            "gross_revenue_retention": grr, "net_revenue_retention": nrr}


def ltv_to_cac(ltv: float, cac: float) -> Dict[str, Any]:
    return {"ltv": ltv, "cac": cac, "ratio": safe_div(ltv, cac)}


def cac_payback_months(cac: float, arpu: float, gross_margin: float) -> Dict[str, Any]:
    monthly_gross_profit = arpu * gross_margin
    return {"cac": cac, "monthly_gross_profit": monthly_gross_profit, "cac_payback_months": safe_div(cac, monthly_gross_profit)}


def cohort_revenue_projection(cohorts: Sequence[Dict[str, Any]], periods: int) -> Dict[str, Any]:
    """cohorts: [{"starting_period": int, "size": float, "retention_pct": [...], "arpu": float}, ...]. Aggregates
    every cohort's own (offset) retention curve into a single calendar-period revenue projection — the real
    mechanic that makes cohort-based forecasting different from applying one blended growth rate to total
    revenue (`finmodel.startup_model`'s simpler approach)."""
    revenue_by_period = [0.0] * periods
    for cohort in cohorts:
        start = cohort["starting_period"]
        for t, r in enumerate(cohort["retention_pct"]):
            calendar_period = start + t
            if 0 <= calendar_period < periods:
                revenue_by_period[calendar_period] += r * cohort["size"] * cohort["arpu"]
    return {"revenue_by_period": revenue_by_period, "total_revenue": sum(revenue_by_period)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "retention_curve" in d:
        out["retention_curve"] = cohort_retention_curve(**d["retention_curve"])
    if "ltv_from_retention_curve" in d:
        out["ltv_from_retention_curve"] = ltv_from_retention_curve(**d["ltv_from_retention_curve"])
    if "ltv_simplified" in d:
        out["ltv_simplified"] = ltv_simplified(**d["ltv_simplified"])
    if "revenue_retention" in d:
        out["revenue_retention"] = revenue_retention(**d["revenue_retention"])
    if "ltv_to_cac" in d:
        out["ltv_to_cac"] = ltv_to_cac(**d["ltv_to_cac"])
    if "cac_payback_months" in d:
        out["cac_payback_months"] = cac_payback_months(**d["cac_payback_months"])
    if "cohort_revenue_projection" in d:
        out["cohort_revenue_projection"] = cohort_revenue_projection(**d["cohort_revenue_projection"])
    return out
