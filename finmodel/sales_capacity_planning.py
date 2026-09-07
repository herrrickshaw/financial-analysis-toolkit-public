"""Sales capacity planning: new-rep productivity ramps and bookings-capacity forecasting -- the real,
standard RevOps/sales-ops technique behind every SaaS company's hiring plan (the same discipline Cube
Software's and Vena's own free-template galleries name as "sales quota & rep-capacity planning" in
`docs/FPA_GALLERY_GAP_ANALYSIS.md`, originally deferred there as "close enough to finmodel.cohort_analysis's
existing... machinery"). Revisited and built as its own small module because the unit of analysis is
genuinely different: `finmodel.cohort_analysis` tracks CUSTOMER retention/revenue by acquisition cohort, this
module tracks SALES REP productivity by hire cohort -- a different real metric (quota attainment, not
retention) even though both use a cohort-by-tenure structure.

  * A new sales rep is rarely fully productive from day one -- the standard convention (widely taught in
    SaaS sales-capacity models, e.g. Bessemer's and SaaStr's own published playbooks) is a ramp curve: a
    rep's quota-attainment capacity climbs from a small fraction in their first period to 100% after some
    number of periods (a common example: 20% / 50% / 80% / 100% across four quarters).
  * Bookings capacity in any period is the sum, across every hire cohort still active, of that cohort's
    headcount x its OWN ramp fraction at its current tenure x the full quota per rep -- a rep hired last
    quarter contributes far less than one hired a year ago, even with the same headcount.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def sales_capacity_schedule(hiring_plan: Sequence[float], ramp_curve: Sequence[float], quota_per_rep_per_period: float) -> Dict[str, Any]:
    """`hiring_plan[t]` = reps hired at the START of period t (0-indexed); `ramp_curve[k]` = the productivity
    fraction (0-1) a cohort achieves in its k-th period since hire (tenure beyond the curve's length holds at
    the curve's last value, i.e. full ramp persists)."""
    periods: List[Dict[str, Any]] = []
    for t in range(len(hiring_plan)):
        capacity = 0.0
        headcount = 0.0
        for hire_period in range(t + 1):
            reps_hired = hiring_plan[hire_period]
            tenure = t - hire_period
            ramp_fraction = ramp_curve[tenure] if tenure < len(ramp_curve) else ramp_curve[-1]
            capacity += reps_hired * ramp_fraction * quota_per_rep_per_period
            headcount += reps_hired
        periods.append({"period": t + 1, "headcount": headcount, "bookings_capacity": capacity})
    return {"periods": periods, "total_capacity": sum(p["bookings_capacity"] for p in periods)}


def reps_needed_for_target(target_bookings_per_period: float, ramp_curve: Sequence[float],
                           quota_per_rep_per_period: float, periods_since_hire: int) -> Dict[str, Any]:
    """How many reps, hired all at once today, are needed so that `periods_since_hire` periods from now
    (at that tenure's ramp fraction) their combined capacity meets `target_bookings_per_period`."""
    ramp_fraction = ramp_curve[periods_since_hire] if periods_since_hire < len(ramp_curve) else ramp_curve[-1]
    effective_quota = ramp_fraction * quota_per_rep_per_period
    return {"ramp_fraction_at_target_period": ramp_fraction, "effective_quota_per_rep": effective_quota,
            "reps_needed": safe_div(target_bookings_per_period, effective_quota)}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "sales_capacity_schedule" in d:
        out["sales_capacity_schedule"] = sales_capacity_schedule(**d["sales_capacity_schedule"])
    if "reps_needed_for_target" in d:
        out["reps_needed_for_target"] = reps_needed_for_target(**d["reps_needed_for_target"])
    return out
