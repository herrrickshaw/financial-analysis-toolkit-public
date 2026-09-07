"""RBI asset classification and provisioning (India's IRAC norms -- Income Recognition, Asset
Classification and Provisioning) -- the regulatory framework every Indian bank runs its loan book through
every quarter, distinct from finmodel.bank_model's US-style CECL provisioning and from
finmodel.loss_reserving's actuarial claim triangles. Distilled from RBI's Master Circular on Prudential
Norms on Income Recognition, Asset Classification and Provisioning pertaining to Advances (rates below are
illustrative of the published norms as a worked example -- RBI amends specific segment rates periodically,
so a live provisioning calculation should be checked against the current circular).

  * An account 1-90 days past due (DPD) stays "Standard" for classification purposes but is flagged as a
    Special Mention Account (SMA-0 for 1-30 DPD, SMA-1 for 31-60, SMA-2 for 61-90) -- RBI's 2019 early-
    warning framework.
  * 91+ DPD makes an account a Non-Performing Asset (NPA); it is then bucketed by how long it has REMAINED
    an NPA (not by DPD, which keeps growing): Sub-standard (<=1 year as an NPA), Doubtful-1 (1-2 years),
    Doubtful-2 (2-3 years), Doubtful-3 (>3 years). A separate "Loss" category applies once the asset is
    identified as uncollectible by the bank, auditors, or an RBI inspection.
  * Provisioning is charged at different rates for the SECURED and UNSECURED portions of an NPA's
    outstanding balance -- unsecured exposure is provisioned much more aggressively, up to 100% from the
    first NPA day count in Doubtful-2 onward.
"""
from __future__ import annotations

from typing import Any, Dict

STANDARD_PROVISION_RATE = 0.0040  # RBI's general/standard-asset provisioning rate (segment-specific rates vary)

# (secured_rate, unsecured_rate) by classification bucket, per RBI's published provisioning norms
_PROVISION_RATES = {
    "Sub-standard": (0.15, 0.25),
    "Doubtful-1": (0.25, 1.00),
    "Doubtful-2": (0.40, 1.00),
    "Doubtful-3": (1.00, 1.00),
    "Loss": (1.00, 1.00),
}


def classify_asset(days_past_due: int, npa_age_days: int = 0) -> str:
    """`npa_age_days` (days since the account was FIRST classified an NPA) only matters once `days_past_due`
    has crossed the 90-day NPA threshold; it is ignored for a still-Standard/SMA account."""
    if days_past_due <= 0:
        return "Standard"
    if days_past_due <= 30:
        return "SMA-0"
    if days_past_due <= 60:
        return "SMA-1"
    if days_past_due <= 90:
        return "SMA-2"
    if npa_age_days <= 365:
        return "Sub-standard"
    if npa_age_days <= 730:
        return "Doubtful-1"
    if npa_age_days <= 1095:
        return "Doubtful-2"
    return "Doubtful-3"


def provisioning_requirement(classification: str, outstanding_amount: float, secured_amount: float = None) -> Dict[str, Any]:
    if secured_amount is None:
        secured_amount = outstanding_amount
    secured_amount = min(secured_amount, outstanding_amount)
    unsecured_amount = outstanding_amount - secured_amount
    if classification in ("Standard", "SMA-0", "SMA-1", "SMA-2"):
        provision = outstanding_amount * STANDARD_PROVISION_RATE
        return {"classification": classification, "outstanding_amount": outstanding_amount,
                "provision_required": provision, "provision_rate_effective": STANDARD_PROVISION_RATE}
    if classification not in _PROVISION_RATES:
        raise ValueError(f"unknown classification: {classification}")
    secured_rate, unsecured_rate = _PROVISION_RATES[classification]
    provision = secured_amount * secured_rate + unsecured_amount * unsecured_rate
    return {"classification": classification, "outstanding_amount": outstanding_amount,
            "secured_amount": secured_amount, "unsecured_amount": unsecured_amount,
            "secured_provision": secured_amount * secured_rate, "unsecured_provision": unsecured_amount * unsecured_rate,
            "provision_required": provision, "provision_rate_effective": provision / outstanding_amount if outstanding_amount else 0.0}


def npa_provisioning(days_past_due: int, outstanding_amount: float, npa_age_days: int = 0, secured_amount: float = None) -> Dict[str, Any]:
    classification = classify_asset(days_past_due, npa_age_days)
    return provisioning_requirement(classification, outstanding_amount, secured_amount)


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "npa_provisioning" in d:
        out["npa_provisioning"] = npa_provisioning(**d["npa_provisioning"])
    if "loan_book" in d:
        out["loan_book"] = [npa_provisioning(**account) for account in d["loan_book"]]
        out["total_provision_required"] = sum(a["provision_required"] for a in out["loan_book"])
    return out
