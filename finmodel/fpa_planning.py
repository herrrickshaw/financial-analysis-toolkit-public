"""Forward-looking FP&A planning: headcount/workforce cost planning and driver-based rolling forecasts — real,
standard techniques flagged as top-downloaded templates by a cross-source survey of FP&A template galleries
(Cube Software, Vena Solutions and PivotXL all name both) with no prior equivalent in this toolkit.

  Headcount cost schedule   — the real, standard build every FP&A team runs before an opex budget means
                             anything: roles starting at different months, each carrying a FULLY-LOADED cost
                             (base salary plus a real, standard benefits/payroll-tax load, typically 20-30% of
                             base) — not a flat headcount x average-salary approximation.
  Rolling forecast          — the real, defining mechanic that separates FP&A forecasting from a static annual
                             budget: each period, the forecast re-anchors off the LATEST ACTUAL and extends N
                             periods forward on a driver assumption, rather than staying fixed against a budget
                             set once at the start of the year regardless of how actuals have since come in."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def headcount_cost_schedule(roles: Sequence[Dict[str, Any]], months: int, benefits_load_pct: float = 0.25) -> Dict[str, Any]:
    """roles: [{"title", "start_month" (0-indexed), "monthly_base_salary", "count"}, ...]. Fully-loaded monthly
    cost = base salary x (1 + benefits_load_pct) x headcount, starting the month each role's cohort actually
    starts — not month 0 for every role, the real shape of a real hiring plan."""
    schedule = [0.0] * months
    role_rows: List[Dict[str, Any]] = []
    for role in roles:
        loaded_monthly_cost = role["monthly_base_salary"] * (1 + benefits_load_pct) * role["count"]
        for m in range(role["start_month"], months):
            schedule[m] += loaded_monthly_cost
        role_rows.append({"title": role["title"], "count": role["count"], "loaded_monthly_cost_per_role": loaded_monthly_cost,
                          "start_month": role["start_month"]})
    return {"monthly_cost": schedule, "total_cost": sum(schedule), "benefits_load_pct": benefits_load_pct, "roles": role_rows}


def rolling_forecast(actuals_to_date: Sequence[float], driver_growth_rate: float, forecast_periods: int) -> Dict[str, Any]:
    """The real, defining rolling-forecast mechanic: re-anchor off the LAST REAL ACTUAL (not a stale budget
    baseline) and extend forward at a driver-based growth assumption for `forecast_periods` more periods."""
    if not actuals_to_date:
        raise ValueError("actuals_to_date must have at least one period")
    forecast = [actuals_to_date[-1]]
    for _ in range(forecast_periods):
        forecast.append(forecast[-1] * (1 + driver_growth_rate))
    return {"actuals_to_date": list(actuals_to_date), "forecast": forecast[1:], "combined": list(actuals_to_date) + forecast[1:],
            "driver_growth_rate": driver_growth_rate}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "headcount_cost_schedule" in d:
        out["headcount_cost_schedule"] = headcount_cost_schedule(**d["headcount_cost_schedule"])
    if "rolling_forecast" in d:
        out["rolling_forecast"] = rolling_forecast(**d["rolling_forecast"])
    return out
