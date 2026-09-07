"""Investment securities classification (ASC 320) -- trading, available-for-sale (AFS), and held-to-maturity
(HTM) securities, and the real, structurally different way each routes its unrealized gains and losses. A
real, common corporate accounting classification with no prior representation across the toolkit's other
~50 modules.

  * TRADING securities are carried at fair value, and unrealized gains/losses hit NET INCOME immediately --
    the most aggressive treatment, for securities a company actively trades.
  * AVAILABLE-FOR-SALE securities are ALSO carried at fair value, but unrealized gains/losses instead flow
    through OTHER COMPREHENSIVE INCOME (OCI), bypassing net income entirely until the security is actually
    sold, at which point the cumulative unrealized amount is "recycled" out of OCI into net income as a
    realized gain/loss -- a real, distinct mechanic called a reclassification adjustment.
  * HELD-TO-MATURITY securities are carried at AMORTIZED COST, with no unrealized gain/loss recognized at all
    (only an other-than-temporary-impairment write-down would hit the financial statements) -- the only one
    of the three classifications available where the company has both the intent AND the ability to hold the
    security to maturity.
"""
from __future__ import annotations

from typing import Any, Dict

_VALID_CLASSIFICATIONS = ("trading", "available_for_sale", "held_to_maturity")


def classify_and_measure(cost_basis: float, fair_value: float, classification: str) -> Dict[str, Any]:
    if classification not in _VALID_CLASSIFICATIONS:
        raise ValueError(f"classification must be one of {_VALID_CLASSIFICATIONS}")
    unrealized_gain_loss = fair_value - cost_basis
    if classification == "trading":
        carrying_value, income_statement_impact, oci_impact = fair_value, unrealized_gain_loss, 0.0
    elif classification == "available_for_sale":
        carrying_value, income_statement_impact, oci_impact = fair_value, 0.0, unrealized_gain_loss
    else:  # held_to_maturity
        carrying_value, income_statement_impact, oci_impact = cost_basis, 0.0, 0.0
    return {"classification": classification, "cost_basis": cost_basis, "fair_value": fair_value,
            "unrealized_gain_loss": unrealized_gain_loss, "carrying_value": carrying_value,
            "income_statement_impact": income_statement_impact, "oci_impact": oci_impact}


def realized_gain_loss_on_sale(cost_basis: float, sale_price: float, classification: str,
                               cumulative_oci_recognized: float = 0.0) -> Dict[str, Any]:
    """When an AFS security is sold, its previously OCI-recognized cumulative unrealized amount is
    reclassified out of OCI into net income -- the real "recycling" mechanic that has no equivalent for
    trading (already in net income) or HTM (never marked to fair value) securities."""
    if classification not in _VALID_CLASSIFICATIONS:
        raise ValueError(f"classification must be one of {_VALID_CLASSIFICATIONS}")
    realized_gain_loss = sale_price - cost_basis
    reclassification_from_oci = cumulative_oci_recognized if classification == "available_for_sale" else 0.0
    return {"realized_gain_loss": realized_gain_loss, "reclassification_adjustment_from_oci": reclassification_from_oci}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "classify_and_measure" in d:
        out["classify_and_measure"] = classify_and_measure(**d["classify_and_measure"])
    if "realized_gain_loss_on_sale" in d:
        out["realized_gain_loss_on_sale"] = realized_gain_loss_on_sale(**d["realized_gain_loss_on_sale"])
    return out
