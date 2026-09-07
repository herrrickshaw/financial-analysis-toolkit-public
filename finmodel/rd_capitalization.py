"""R&D capitalization, distilled from CFI 'R&D Capitalization' template (single-vintage straight-line schedule,
reconciled exactly in tests/test_rd_capitalization.py) and generalized to the standard Damodaran cross-sectional
method (each historical year's R&D spend is its own vintage, amortized straight-line over an assumed useful
life; the current year's "R&D asset" is the sum of every vintage's remaining unamortized value, and the current
year's amortization is the sum of every vintage's current-year amortization charge).

Why this exists: R&D is expensed immediately under US GAAP, even though it creates a multi-year economic asset
(chip designs, drug candidates, software IP) the same way capex does. For an R&D-intensive company, reported
EBIT understates true operating profitability (the "investment" is charged in year 1, not spread over its
useful life) and reported invested capital omits the R&D asset entirely, understating ROIC's denominator too —
a well-known, quantifiable distortion (Damodaran's "Value of Growth" and R&D-adjustment research), not unique to
any one sector but sharpest wherever R&D/revenue is high (semiconductors, software, pharma).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .fin import safe_div


@dataclass
class AmortizationYear:
    year: int
    asset_value_start: float
    amortization: float
    asset_value_end: float


def amortization_schedule(spend: float, life_years: int, residual_value: float = 0.0) -> List[AmortizationYear]:
    """Single-vintage straight-line schedule for one year's R&D spend — reconciles exactly to the CFI
    'RD-Capitalization.xlsx' template (spend=100000, residual_value=20000, life_years=5 -> $16,000/yr,
    ending asset value exactly at residual_value)."""
    if life_years <= 0:
        raise ValueError("life_years must be positive")
    annual = (spend - residual_value) / life_years
    rows: List[AmortizationYear] = []
    value = spend
    for y in range(1, life_years + 1):
        start = value
        end = start - annual if y < life_years else residual_value  # last year lands exactly on residual_value
        rows.append(AmortizationYear(year=y, asset_value_start=start, amortization=start - end, asset_value_end=end))
        value = end
    return rows


def capitalize_rd(rd_history: Sequence[float], life_years: int) -> Dict[str, Any]:
    """Damodaran-style cross-sectional R&D capitalization: `rd_history` is R&D spend for consecutive fiscal
    years, OLDEST FIRST, ending with the current year (`rd_history[-1]`). Each year's spend is its own vintage,
    straight-line-amortized to zero over `life_years` (no residual value — a vintage's economic life is, by
    construction, defined to fully "use up"; `amortization_schedule()` above supports a nonzero residual only
    for reconciling to the CFI single-vintage template).

    Convention (standard Damodaran): the CURRENT year's own R&D has not amortized AT ALL yet — it shows at full
    value in the asset and contributes NOTHING to this year's amortization (that starts next year). A vintage
    exactly `life_years` years old contributes its FINAL amortization tranche this year and is then fully
    written off — computing that tranche needs `life_years + 1` years of history; with fewer years available,
    the asset value and amortization are both understated by the missing older tranche(s), same as any
    real-world R&D-capitalization exercise run on a company with a short reported history.

    Returns the CURRENT year's total unamortized R&D asset (sum of every vintage's remaining book value) and
    the CURRENT year's total amortization (sum of every vintage's current-year charge) — both are what you add
    to invested capital and use in the EBIT adjustment, respectively."""
    if life_years <= 0:
        raise ValueError("life_years must be positive")
    if len(rd_history) < 1:
        raise ValueError("rd_history must have at least one year")
    n = len(rd_history)
    annual = lambda spend: spend / life_years
    asset_value = 0.0
    amortization_this_year = 0.0
    per_vintage = []
    for age in range(min(n, life_years)):  # age 0 = this year's spend, age k = k years old
        spend = rd_history[n - 1 - age]
        remaining_value = spend * (life_years - age) / life_years  # age 0 -> full value, not yet amortized
        this_year_amort = annual(spend) if age >= 1 else 0.0       # age 0 contributes no amortization this year
        asset_value += remaining_value
        amortization_this_year += this_year_amort
        per_vintage.append({"years_ago": age, "original_spend": spend, "annual_amortization": annual(spend),
                            "remaining_value": remaining_value})
    if n >= life_years + 1:  # the oldest relevant vintage (exactly life_years old) takes its final tranche today
        amortization_this_year += annual(rd_history[n - 1 - life_years])
    return {"life_years": life_years, "current_year_rd_expense": rd_history[-1],
            "rd_asset": asset_value, "current_year_amortization": amortization_this_year,
            "per_vintage": per_vintage}


def adjusted_ebit(reported_ebit: float, current_year_rd_expense: float, current_year_amortization: float) -> float:
    """Restate EBIT as if R&D were capitalized: add back the GAAP-expensed R&D, subtract the amortization of
    the capitalized R&D asset instead."""
    return reported_ebit + current_year_rd_expense - current_year_amortization


def restate(rd_history: Sequence[float], reported_ebit: float, reported_invested_capital: float,
           life_years: int) -> Dict[str, Any]:
    """Convenience wrapper: capitalizes R&D, restates EBIT and invested capital (adding the R&D asset), and
    reports both the raw and R&D-adjusted operating margin/ROIC-style ratio for direct comparison."""
    cap = capitalize_rd(rd_history, life_years)
    adj_ebit = adjusted_ebit(reported_ebit, cap["current_year_rd_expense"], cap["current_year_amortization"])
    adj_capital = reported_invested_capital + cap["rd_asset"]
    return {"capitalization": cap, "reported_ebit": reported_ebit, "adjusted_ebit": adj_ebit,
            "reported_invested_capital": reported_invested_capital, "adjusted_invested_capital": adj_capital,
            "reported_roic_proxy": safe_div(reported_ebit, reported_invested_capital),
            "adjusted_roic_proxy": safe_div(adj_ebit, adj_capital),
            "ebit_uplift": adj_ebit - reported_ebit, "ebit_uplift_pct": safe_div(adj_ebit, reported_ebit) - 1 if reported_ebit else None}
