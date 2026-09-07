"""Earnout / contingent-consideration valuation (ASC 805 fair-value measurement of M&A contingent
consideration) -- flagged as a real, deliberately deferred gap in `docs/OPERATING_FINANCE_TOOLS.md` until it
had a proper formula set rather than being a thin wrapper. Two real, standard methods, matched to two real
earnout structures:

  * A milestone-based earnout (e.g. "pay $10M if the product ships on time," "pay $5M if a key employee
    stays two years") has a small number of discrete, enumerable outcomes -- fair value is the
    probability-weighted expected payout, discounted at a rate reflecting the earnout's own risk
    (standard scenario-analysis practice for contingent consideration under ASC 805/820).
  * A financial-metric earnout (e.g. "pay $10M if trailing revenue exceeds $50M at the two-year mark") has a
    CONTINUOUS underlying uncertain metric assumed to follow the same lognormal diffusion Black-Scholes
    assumes for a stock price -- fair value is exactly a cash-or-nothing digital option's value, reusing this
    toolkit's own `finmodel.options.norm_cdf`: the risk-neutral probability the metric exceeds the threshold
    at the measurement date is N(d2), and the earnout's present value is the payout, discounted, times that
    probability. This is the real, standard option-pricing approach every Big 4 valuation practice uses for
    market-condition or performance-condition earnouts (see e.g. Deloitte's and KPMG's own contingent-
    consideration valuation guidance).
"""
from __future__ import annotations

import math
from typing import Any, Dict, Sequence

from .options import norm_cdf


def scenario_weighted_earnout(scenarios: Sequence[Dict[str, float]], discount_rate: float, years_to_payout: float) -> Dict[str, Any]:
    """`scenarios`: [{"probability": 0.6, "payout": 10_000_000.0}, ...], probabilities summing to 1.0."""
    total_probability = sum(s["probability"] for s in scenarios)
    if abs(total_probability - 1.0) > 1e-6:
        raise ValueError(f"scenario probabilities must sum to 1.0, got {total_probability}")
    expected_payout = sum(s["probability"] * s["payout"] for s in scenarios)
    present_value = expected_payout / (1 + discount_rate) ** years_to_payout
    return {"expected_payout": expected_payout, "discount_rate": discount_rate,
            "years_to_payout": years_to_payout, "present_value": present_value}


def binary_metric_earnout(metric_current_value: float, threshold: float, volatility: float, risk_free_rate: float,
                          years_to_measurement: float, payout_if_achieved: float) -> Dict[str, Any]:
    """Values a "pay X if metric exceeds threshold at measurement date" earnout as a cash-or-nothing digital
    option, treating `metric_current_value` as the Black-Scholes "spot" and `threshold` as the "strike"."""
    if years_to_measurement <= 0 or volatility <= 0:
        raise ValueError("years_to_measurement and volatility must both be positive")
    d1 = (math.log(metric_current_value / threshold) + (risk_free_rate + volatility ** 2 / 2) * years_to_measurement) / \
         (volatility * math.sqrt(years_to_measurement))
    d2 = d1 - volatility * math.sqrt(years_to_measurement)
    risk_neutral_probability_achieved = norm_cdf(d2)
    discount_factor = math.exp(-risk_free_rate * years_to_measurement)
    present_value = payout_if_achieved * discount_factor * risk_neutral_probability_achieved
    return {"risk_neutral_probability_achieved": risk_neutral_probability_achieved,
            "discount_factor": discount_factor, "payout_if_achieved": payout_if_achieved, "present_value": present_value}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "scenario_weighted_earnout" in d:
        out["scenario_weighted_earnout"] = scenario_weighted_earnout(**d["scenario_weighted_earnout"])
    if "binary_metric_earnout" in d:
        out["binary_metric_earnout"] = binary_metric_earnout(**d["binary_metric_earnout"])
    return out
