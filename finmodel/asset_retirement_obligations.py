"""Asset retirement obligations (ASC 410) -- the real liability-recognition and accretion mechanic every
company with a legal obligation to decommission, dismantle, or remediate a long-lived asset applies (oil and
gas wells, mines, nuclear facilities, leased real estate with a restoration clause). No prior representation
across the toolkit's other ~50 modules.

  * At the asset's in-service date, the ARO liability is recognized at the PRESENT VALUE of the estimated
    future retirement cost, discounted at the entity's credit-adjusted risk-free rate -- and the SAME amount
    is capitalized as an addition to the related asset's own carrying value (it becomes part of what gets
    depreciated over the asset's life, not an expense recognized up front).
  * Each subsequent period, the liability grows through ACCRETION expense (conceptually identical to
    interest accruing on a discounted liability) at the SAME rate used at initial recognition -- which is
    precisely why, by construction, the liability's balance at the retirement date must equal EXACTLY the
    original estimated future cost: accretion at rate r for n years exactly reverses the 1/(1+r)^n discounting
    applied at recognition. This module's own test suite verifies that exact identity.
  * At settlement, the actual retirement cost is compared to the accreted liability balance; any difference
    is recognized as a real settlement gain or loss.
"""
from __future__ import annotations

from typing import Any, Dict, List


def initial_aro_recognition(estimated_future_cost: float, discount_rate: float, years_to_retirement: float) -> Dict[str, Any]:
    initial_liability = estimated_future_cost / (1 + discount_rate) ** years_to_retirement
    return {"initial_aro_liability": initial_liability, "capitalized_asset_retirement_cost": initial_liability}


def accretion_schedule(initial_aro_liability: float, discount_rate: float, years_to_retirement: int) -> Dict[str, Any]:
    schedule: List[Dict[str, Any]] = []
    balance = initial_aro_liability
    for year in range(1, years_to_retirement + 1):
        accretion_expense = balance * discount_rate
        balance += accretion_expense
        schedule.append({"year": year, "accretion_expense": accretion_expense, "aro_liability_balance": balance})
    return {"schedule": schedule, "final_aro_liability": balance}


def settlement_gain_loss(actual_settlement_cost: float, aro_liability_at_settlement: float) -> Dict[str, Any]:
    gain_loss = aro_liability_at_settlement - actual_settlement_cost
    classification = "gain" if gain_loss > 0 else "loss" if gain_loss < 0 else "no gain or loss"
    return {"gain_loss": gain_loss, "classification": classification}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "initial_aro_recognition" in d:
        out["initial_aro_recognition"] = initial_aro_recognition(**d["initial_aro_recognition"])
    if "accretion_schedule" in d:
        out["accretion_schedule"] = accretion_schedule(**d["accretion_schedule"])
    if "settlement_gain_loss" in d:
        out["settlement_gain_loss"] = settlement_gain_loss(**d["settlement_gain_loss"])
    return out
