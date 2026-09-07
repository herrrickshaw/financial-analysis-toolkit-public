"""Budget-vs-actual variance and financial-statement trend analysis — real, standard FP&A techniques flagged by
a cross-source survey of real, publicly-listed FP&A template galleries (Cube Software, Vena Solutions, PivotXL
and Coefficient all name budget-vs-actual variance reporting among their top downloaded templates; PivotXL names
horizontal and vertical analysis explicitly) with no prior equivalent in this toolkit.

  Volume/price variance     — the real, standard two-factor decomposition of a revenue (or similarly structured
                             cost) variance: how much of the gap between budget and actual came from selling a
                             different QUANTITY than planned versus a different PRICE than planned — not just a
                             single "actual minus budget" number that can't tell you which lever moved.
  Sales mix/quantity        — the real, standard MULTI-PRODUCT extension (Horngren's cost-accounting convention):
  variance                   splits the total volume variance further into a SALES MIX variance (selling a
                             different proportion of high/low-margin products than planned) and a SALES QUANTITY
                             variance (selling more or fewer units in total, at the planned mix).
  Horizontal analysis       — year-over-year (or period-over-period) % change for every line of a financial
                             statement — the real, standard trend-detection technique run before anything else
                             in equity research and credit analysis.
  Vertical (common-size)    — every line of a financial statement expressed as a % of a base line (revenue for
  analysis                   an income statement, total assets for a balance sheet) — the real, standard way to
                             compare companies of very different absolute scale, or track one company's own cost
                             structure evolving over time."""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def budget_vs_actual_variance(budget_volume: float, actual_volume: float, budget_price: float, actual_price: float) -> Dict[str, Any]:
    """The real, standard two-factor convention (price variance valued at ACTUAL volume, volume variance valued
    at BUDGET price): the two components sum EXACTLY to the total variance, verified as an algebraic identity,
    not an approximation."""
    budget_total = budget_volume * budget_price
    actual_total = actual_volume * actual_price
    volume_variance = (actual_volume - budget_volume) * budget_price
    price_variance = (actual_price - budget_price) * actual_volume
    total_variance = actual_total - budget_total
    return {"budget_total": budget_total, "actual_total": actual_total, "volume_variance": volume_variance,
            "price_variance": price_variance, "total_variance": total_variance,
            "reconciles": abs(volume_variance + price_variance - total_variance) < 1e-6}


def sales_mix_and_volume_variance(products: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """products: [{"name", "budget_units", "actual_units", "budget_contribution_margin_per_unit"}, ...]. The
    real, standard multi-product decomposition: total volume variance splits into a sales MIX variance (a
    different proportion of high/low-margin products than planned) and a sales QUANTITY variance (more or fewer
    total units, at the planned mix) — the two sum exactly to the combined volume variance across all products."""
    total_budget_units = sum(p["budget_units"] for p in products)
    total_actual_units = sum(p["actual_units"] for p in products)
    rows: List[Dict[str, Any]] = []
    total_mix_variance = 0.0
    total_quantity_variance = 0.0
    for p in products:
        budget_mix_pct = safe_div(p["budget_units"], total_budget_units)
        actual_units_at_budget_mix = total_actual_units * budget_mix_pct
        mix_variance = (p["actual_units"] - actual_units_at_budget_mix) * p["budget_contribution_margin_per_unit"]
        quantity_variance = (actual_units_at_budget_mix - p["budget_units"]) * p["budget_contribution_margin_per_unit"]
        total_mix_variance += mix_variance
        total_quantity_variance += quantity_variance
        rows.append({"name": p["name"], "budget_mix_pct": budget_mix_pct, "actual_units_at_budget_mix": actual_units_at_budget_mix,
                    "mix_variance": mix_variance, "quantity_variance": quantity_variance})
    return {"products": rows, "total_sales_mix_variance": total_mix_variance, "total_sales_quantity_variance": total_quantity_variance,
            "total_volume_variance": total_mix_variance + total_quantity_variance}


def horizontal_analysis(line_items_by_period: Dict[str, Sequence[float]]) -> Dict[str, Any]:
    """Real, standard period-over-period % change for every line — the first thing run before anything else in
    equity research or credit analysis. The first period's change is always None (nothing to compare against)."""
    out: Dict[str, Any] = {}
    for name, values in line_items_by_period.items():
        pct_change = [None] + [safe_div(values[i] - values[i - 1], abs(values[i - 1])) for i in range(1, len(values))]
        out[name] = {"values": list(values), "pct_change": pct_change}
    return out


def vertical_analysis(line_items_by_period: Dict[str, Sequence[float]], base_line_values: Sequence[float]) -> Dict[str, List[float]]:
    """Every line expressed as a % of `base_line_values` for that SAME period (revenue for an income statement,
    total assets for a balance sheet) — the real, standard "common-size" technique."""
    return {name: [safe_div(values[i], base_line_values[i]) for i in range(len(values))] for name, values in line_items_by_period.items()}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "budget_vs_actual_variance" in d:
        out["budget_vs_actual_variance"] = budget_vs_actual_variance(**d["budget_vs_actual_variance"])
    if "sales_mix_and_volume_variance" in d:
        out["sales_mix_and_volume_variance"] = sales_mix_and_volume_variance(d["sales_mix_and_volume_variance"]["products"])
    if "horizontal_analysis" in d:
        out["horizontal_analysis"] = horizontal_analysis(d["horizontal_analysis"]["line_items_by_period"])
    if "vertical_analysis" in d:
        v = d["vertical_analysis"]
        out["vertical_analysis"] = vertical_analysis(v["line_items_by_period"], v["base_line_values"])
    return out
