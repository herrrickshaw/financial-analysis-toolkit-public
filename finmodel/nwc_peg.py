"""Net working capital peg and closing true-up -- the real, near-universal M&A purchase-agreement mechanic
that has no representation across this toolkit's valuation-focused merger/comps/LBO modules, which price a
deal but don't implement the post-signing working-capital adjustment every real definitive purchase agreement
includes.

  * A deal's price is negotiated against a TARGET ("peg") level of net working capital, typically set as a
    trailing average of the target company's own recent NWC (the standard real convention, since a single
    point-in-time NWC snapshot could be seasonally distorted).
  * At closing, ACTUAL net working capital is measured and compared to the peg. If actual NWC exceeds the
    peg, the seller delivered MORE working capital than was priced into the deal, so the purchase price is
    adjusted UP dollar-for-dollar; if actual NWC falls short of the peg, the price is adjusted DOWN. This is
    the real mechanism that protects a buyer from a seller stripping cash or letting payables balloon (and
    protects a seller from a buyer claiming an unfairly low peg) between signing and closing.
  * Many real agreements also include a threshold ("de minimis" or "basket") below which no adjustment is
    triggered at all -- a small difference is treated as noise rather than worth actually settling.
"""
from __future__ import annotations

from typing import Any, Dict, Sequence


def trailing_average_peg(historical_nwc_values: Sequence[float]) -> float:
    return sum(historical_nwc_values) / len(historical_nwc_values)


def nwc_true_up(actual_nwc_at_closing: float, peg_nwc: float, threshold: float = 0.0) -> Dict[str, Any]:
    difference = actual_nwc_at_closing - peg_nwc
    adjustment = 0.0 if abs(difference) < threshold else difference
    direction = "increase to seller" if adjustment > 0 else "decrease (buyer credit)" if adjustment < 0 else "no adjustment"
    return {"actual_nwc_at_closing": actual_nwc_at_closing, "peg_nwc": peg_nwc, "difference": difference,
            "purchase_price_adjustment": adjustment, "direction": direction}


def working_capital_adjustment(historical_nwc_values: Sequence[float], actual_nwc_at_closing: float,
                               threshold: float = 0.0) -> Dict[str, Any]:
    peg = trailing_average_peg(historical_nwc_values)
    result = nwc_true_up(actual_nwc_at_closing, peg, threshold)
    result["peg_source"] = "trailing_average"
    result["historical_nwc_values"] = list(historical_nwc_values)
    return result


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "nwc_true_up" in d:
        out["nwc_true_up"] = nwc_true_up(**d["nwc_true_up"])
    if "working_capital_adjustment" in d:
        out["working_capital_adjustment"] = working_capital_adjustment(**d["working_capital_adjustment"])
    return out
