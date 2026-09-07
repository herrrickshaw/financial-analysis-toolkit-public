"""Actuarial loss reserving: the chain-ladder method for estimating unpaid claims (IBNR) from a cumulative
loss development triangle -- the standard technique behind every P&C insurer's and self-insured corporate
risk department's reserve estimate, distinct from finmodel.insurance_pricing (which prices a policy going
forward, not reserves for claims already incurred). Distilled from the Casualty Actuarial Society's own
exam syllabus (Friedland, *Estimating Unpaid Claims Using Basic Techniques*, ch. 7).

A triangle is a ragged list of accident-year rows, each holding CUMULATIVE paid (or incurred) losses by
development period; more recent accident years have fewer known periods (the "triangle" shape). The method:

  1. age-to-age (link) factor for period j->j+1 = sum of period-(j+1) values / sum of period-j values,
     using only accident years that have BOTH periods reported (the standard volume-weighted average).
  2. cumulative development factor (CDF) from period j to ultimate = product of every age-to-age factor
     from j onward (the last known period's CDF is 1.0 -- this triangle's data treats it as fully developed).
  3. projected ultimate for an accident year = its latest known cumulative value * the CDF for that period.
  4. IBNR (incurred but not reported) = projected ultimate - latest known cumulative value.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def age_to_age_factors(triangle: Sequence[Sequence[float]]) -> List[float]:
    """Volume-weighted age-to-age factors for every development-period transition present in the triangle."""
    n_periods = max(len(row) for row in triangle)
    factors: List[float] = []
    for j in range(n_periods - 1):
        numerator = sum(row[j + 1] for row in triangle if len(row) > j + 1)
        denominator = sum(row[j] for row in triangle if len(row) > j + 1)
        factors.append(safe_div(numerator, denominator, default=1.0))
    return factors


def cumulative_development_factors(factors: Sequence[float]) -> List[float]:
    """CDF[j] = product of factors[j:] (development remaining from period j to ultimate); the final period's
    CDF is 1.0 since the triangle's data treats it as already fully developed."""
    n_periods = len(factors) + 1
    cdfs = [1.0] * n_periods
    running = 1.0
    for j in range(n_periods - 2, -1, -1):
        running *= factors[j]
        cdfs[j] = running
    return cdfs


def chain_ladder(triangle: Sequence[Sequence[float]]) -> Dict[str, Any]:
    """Full chain-ladder run: age-to-age factors, cumulative development factors, and per-accident-year
    projected ultimates / IBNR."""
    if not triangle or any(len(row) == 0 for row in triangle):
        raise ValueError("triangle must be non-empty with no empty rows")
    factors = age_to_age_factors(triangle)
    cdfs = cumulative_development_factors(factors)
    accident_years: List[Dict[str, Any]] = []
    for i, row in enumerate(triangle):
        latest_period = len(row) - 1
        latest_cumulative = row[-1]
        ultimate = latest_cumulative * cdfs[latest_period]
        accident_years.append({
            "accident_year_index": i, "latest_period": latest_period, "latest_cumulative": latest_cumulative,
            "cdf_to_ultimate": cdfs[latest_period], "ultimate": ultimate, "ibnr": ultimate - latest_cumulative,
        })
    total_latest = sum(ay["latest_cumulative"] for ay in accident_years)
    total_ultimate = sum(ay["ultimate"] for ay in accident_years)
    return {"age_to_age_factors": factors, "cumulative_development_factors": cdfs,
            "accident_years": accident_years, "total_latest_cumulative": total_latest,
            "total_ultimate": total_ultimate, "total_ibnr": total_ultimate - total_latest}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    return {"chain_ladder": chain_ladder(d["triangle"])}
