"""Defined-benefit pension accounting (ASC 715) -- the projected benefit obligation (PBO) roll-forward, plan
asset roll-forward, funded status, and net periodic pension cost every company with a defined-benefit plan
reports, with no prior representation across the toolkit's other ~50 modules. `service_cost` and
`actuarial_gain_loss` are treated as caller-supplied inputs (the real output of a plan actuary's own PBO
model), the same design this toolkit already used for Bornhuetter-Ferguson's a-priori expected loss --
neither needs to be re-derived here to build and verify the surrounding roll-forward and cost mechanics
correctly.

  * PBO roll-forward: ending PBO = beginning PBO + service cost + interest cost (beginning PBO x discount
    rate) - benefits paid to retirees + any actuarial gain/loss on the obligation itself (e.g. from a
    discount-rate or demographic-assumption change).
  * Plan-asset roll-forward: ending plan assets = beginning plan assets + the ACTUAL return earned on those
    assets + employer contributions - benefits paid.
  * Funded status = ending plan assets - ending PBO -- negative means underfunded, a real liability the
    balance sheet must show.
  * Net periodic pension cost uses the EXPECTED (long-run assumed) return on assets, not the actual return
    used in the roll-forward above -- the real, defining ASC 715 mechanic that separates a plan's smoothed
    income-statement cost from its actual balance-sheet funded position. The gap between the two returns is
    itself an actuarial gain or loss that accumulates in Other Comprehensive Income rather than hitting net
    income immediately.
"""
from __future__ import annotations

from typing import Any, Dict


def pbo_rollforward(beginning_pbo: float, service_cost: float, discount_rate: float, benefits_paid: float,
                    actuarial_gain_loss: float = 0.0) -> Dict[str, Any]:
    interest_cost = beginning_pbo * discount_rate
    ending_pbo = beginning_pbo + service_cost + interest_cost - benefits_paid + actuarial_gain_loss
    return {"beginning_pbo": beginning_pbo, "service_cost": service_cost, "interest_cost": interest_cost,
            "benefits_paid": benefits_paid, "actuarial_gain_loss": actuarial_gain_loss, "ending_pbo": ending_pbo}


def plan_assets_rollforward(beginning_plan_assets: float, actual_return_on_assets: float,
                            employer_contributions: float, benefits_paid: float) -> Dict[str, Any]:
    ending_plan_assets = beginning_plan_assets + actual_return_on_assets + employer_contributions - benefits_paid
    return {"beginning_plan_assets": beginning_plan_assets, "actual_return_on_assets": actual_return_on_assets,
            "employer_contributions": employer_contributions, "benefits_paid": benefits_paid,
            "ending_plan_assets": ending_plan_assets}


def funded_status(ending_plan_assets: float, ending_pbo: float) -> Dict[str, Any]:
    status = ending_plan_assets - ending_pbo
    classification = "overfunded" if status > 0 else "underfunded" if status < 0 else "fully funded"
    return {"ending_plan_assets": ending_plan_assets, "ending_pbo": ending_pbo,
            "funded_status": status, "classification": classification}


def net_periodic_pension_cost(service_cost: float, beginning_pbo: float, discount_rate: float,
                              beginning_plan_assets: float, expected_return_rate: float,
                              amortization_of_prior_service_cost: float = 0.0,
                              amortization_of_net_actuarial_loss: float = 0.0) -> Dict[str, Any]:
    interest_cost = beginning_pbo * discount_rate
    expected_return_on_assets = beginning_plan_assets * expected_return_rate
    net_periodic_cost = (service_cost + interest_cost - expected_return_on_assets +
                         amortization_of_prior_service_cost + amortization_of_net_actuarial_loss)
    return {"service_cost": service_cost, "interest_cost": interest_cost,
            "expected_return_on_assets": expected_return_on_assets,
            "amortization_of_prior_service_cost": amortization_of_prior_service_cost,
            "amortization_of_net_actuarial_loss": amortization_of_net_actuarial_loss,
            "net_periodic_pension_cost": net_periodic_cost}


def asset_gain_loss(actual_return_on_assets: float, expected_return_on_assets: float) -> float:
    """The gap between the actual return used in the balance-sheet roll-forward and the expected return used
    in the income-statement cost -- a real actuarial gain (positive) or loss (negative) on plan assets."""
    return actual_return_on_assets - expected_return_on_assets


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "pbo_rollforward" in d:
        out["pbo_rollforward"] = pbo_rollforward(**d["pbo_rollforward"])
    if "plan_assets_rollforward" in d:
        out["plan_assets_rollforward"] = plan_assets_rollforward(**d["plan_assets_rollforward"])
    if "funded_status" in d:
        out["funded_status"] = funded_status(**d["funded_status"])
    if "net_periodic_pension_cost" in d:
        out["net_periodic_pension_cost"] = net_periodic_pension_cost(**d["net_periodic_pension_cost"])
    if "asset_gain_loss" in d:
        out["asset_gain_loss"] = {"value": asset_gain_loss(**d["asset_gain_loss"])}
    return out
