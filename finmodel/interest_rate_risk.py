"""Bank interest-rate risk (ALM): the repricing-gap model taught in every "Financial Institutions" course
(Ohio State's BUSFIN 4265, Saunders & Cornett's *Financial Institutions Management*, Rose & Hudgins' *Bank
Management & Financial Services*) -- a real gap flagged in this toolkit's own docs/BANKING_LITERATURE_
SURVEY.md and closed here now that a standalone, user-supplied bucketed-gap input (rather than a full real
bank balance sheet) is enough to compute it correctly.

  * A repricing (funding) gap buckets a bank's assets and liabilities by how soon each REPRICES (matures or
    resets its rate), not by contractual maturity -- a floating-rate loan reprices immediately even though it
    doesn't mature for years.
  * Gap = Rate-Sensitive Assets (RSA) - Rate-Sensitive Liabilities (RSL) in a bucket. A POSITIVE (asset-
    sensitive) gap means net interest income RISES when rates rise (assets reprice up before liabilities
    catch up); a NEGATIVE (liability-sensitive) gap means the opposite.
  * The first-order approximation every textbook gives for NII sensitivity to a parallel rate shock is
    simply Delta NII = Gap x Delta(rate) -- exactly what `nii_sensitivity` computes here.
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence

from .fin import safe_div


def repricing_gap(buckets: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """Each bucket: {"name": str, "rate_sensitive_assets": float, "rate_sensitive_liabilities": float}."""
    rows: List[Dict[str, Any]] = []
    cumulative = 0.0
    total_rsa = 0.0
    for b in buckets:
        gap = b["rate_sensitive_assets"] - b["rate_sensitive_liabilities"]
        cumulative += gap
        total_rsa += b["rate_sensitive_assets"]
        rows.append({"name": b["name"], "rate_sensitive_assets": b["rate_sensitive_assets"],
                     "rate_sensitive_liabilities": b["rate_sensitive_liabilities"], "gap": gap,
                     "cumulative_gap": cumulative})
    return {"buckets": rows, "total_gap": cumulative, "gap_ratio": safe_div(cumulative, total_rsa)}


def nii_sensitivity(buckets: Sequence[Dict[str, Any]], rate_shock: float) -> Dict[str, Any]:
    """First-order NII sensitivity to a parallel rate shock (`rate_shock` as a decimal, e.g. 0.01 for +100bp),
    applied to the CUMULATIVE gap through the end of the bucket schedule (the standard simplifying
    convention when no bucket-by-bucket repricing-date detail is being tracked separately)."""
    gap_result = repricing_gap(buckets)
    delta_nii = gap_result["total_gap"] * rate_shock
    return {"total_gap": gap_result["total_gap"], "rate_shock": rate_shock, "delta_nii": delta_nii,
            "nii_rises_with_rates": gap_result["total_gap"] > 0}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "repricing_gap" in d:
        out["repricing_gap"] = repricing_gap(d["repricing_gap"]["buckets"])
    if "nii_sensitivity" in d:
        out["nii_sensitivity"] = nii_sensitivity(**d["nii_sensitivity"])
    return out
