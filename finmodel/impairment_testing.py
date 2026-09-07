"""Goodwill and long-lived-asset impairment testing — the real, named ASC 350 / ASC 360 tests behind Deloitte's
own publicly described "impairment analysis" service (this toolkit's market survey of Big 4 financial-modeling
services; see docs/BIG4_AUTOMATION.md). Three deliberately DIFFERENT real tests, not one generic formula:

  Goodwill (ASC 350, post-ASU 2017-04 single-step)      — impairment = carrying value − fair value of the
                                                           reporting unit, CAPPED at the goodwill balance itself
                                                           (goodwill can't be written below zero; an excess would
                                                           fall to other assets under a different standard).
  Indefinite-lived intangibles (ASC 350-30)             — the SAME direct fair-value-vs-carrying-value
                                                           comparison, no recoverability screen.
  Long-lived assets held and used (ASC 360)             — a genuinely different, TWO-STEP structure: Step 1
                                                           (recoverability) compares UNDISCOUNTED future cash
                                                           flows to carrying value; only if that fails does
                                                           Step 2 measure the loss as carrying value − fair
                                                           value. The undiscounted-cash-flow screen is real, by
                                                           design a conservative bright line, and the single
                                                           most commonly confused detail in practice — an asset
                                                           can have real, positive economic value on a discounted
                                                           basis and still fail Step 1 on an undiscounted one.

A DCF (`finmodel.dcf`) is a natural, real source for the "fair value" input every test here needs — run the
reporting unit's or asset group's own cash flows through it to get an income-approach fair value, then feed that
number into the appropriate test below."""
from __future__ import annotations

from typing import Any, Dict, Sequence

from .fin import safe_div


def goodwill_impairment_test(reporting_unit_fair_value: float, reporting_unit_carrying_value: float, goodwill_balance: float) -> Dict[str, Any]:
    excess = max(0.0, reporting_unit_carrying_value - reporting_unit_fair_value)
    impairment = min(excess, goodwill_balance)
    return {"reporting_unit_fair_value": reporting_unit_fair_value, "reporting_unit_carrying_value": reporting_unit_carrying_value,
            "goodwill_balance": goodwill_balance, "excess_of_carrying_over_fair_value": excess,
            "impaired": impairment > 0, "impairment_loss": impairment,
            "capped_by_goodwill_balance": excess > goodwill_balance and goodwill_balance > 0,
            "remaining_goodwill": goodwill_balance - impairment}


def indefinite_lived_intangible_impairment_test(fair_value: float, carrying_value: float) -> Dict[str, Any]:
    impairment = max(0.0, carrying_value - fair_value)
    return {"fair_value": fair_value, "carrying_value": carrying_value, "impaired": impairment > 0, "impairment_loss": impairment,
            "remaining_carrying_value": carrying_value - impairment}


def long_lived_asset_impairment_test(undiscounted_cash_flows: Sequence[float], carrying_value: float, fair_value: float) -> Dict[str, Any]:
    total_undiscounted = sum(undiscounted_cash_flows)
    recoverable = total_undiscounted >= carrying_value
    impairment = 0.0 if recoverable else max(0.0, carrying_value - fair_value)
    return {"total_undiscounted_cash_flows": total_undiscounted, "carrying_value": carrying_value, "fair_value": fair_value,
            "step1_recoverable": recoverable, "impaired": impairment > 0, "impairment_loss": impairment,
            "remaining_carrying_value": carrying_value - impairment,
            "note": "Step 1 passed: no impairment measured even if fair value < carrying value" if recoverable else "Step 1 failed: Step 2 measures the loss"}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "goodwill" in d:
        out["goodwill"] = goodwill_impairment_test(**d["goodwill"])
    if "indefinite_lived_intangible" in d:
        out["indefinite_lived_intangible"] = indefinite_lived_intangible_impairment_test(**d["indefinite_lived_intangible"])
    if "long_lived_asset" in d:
        out["long_lived_asset"] = long_lived_asset_impairment_test(**d["long_lived_asset"])
    return out
