"""Real, named Big 4 audit-analytics techniques — this toolkit's market survey found Deloitte's Omnia/Argus
platforms, EY's and PwC's own audit-analytics tooling, and third-party tools (DataSnipper) all four firms use,
converge on the same two real, well-documented, quantitatively implementable procedures for testing an entire
population of transactions rather than a sample (see docs/BIG4_AUTOMATION.md):

  Benford's Law digit-conformity testing — a real, well-documented empirical regularity: in many naturally
    occurring numerical datasets (transaction amounts, financial-statement line items), the LEADING digit d
    follows P(d) = log10(1 + 1/d), not a uniform 1/9 — small leading digits (1, 2) are genuinely far more common
    than large ones (8, 9). Deviation from this distribution, measured via Nigrini's real, published Mean
    Absolute Deviation (MAD) statistic, is a standard forensic-accounting screen used to prioritize which
    accounts or entries deserve closer scrutiny — NOT proof of fraud by itself, and not every dataset is
    Benford-shaped to begin with (assigned/sequential numbers, data with a hard minimum or maximum, are real
    exceptions this test is not meant for).
  Rule-based journal-entry testing (JET) — a real, standard ISA 240 / AS 2401 fraud-risk-response procedure:
    scan the full population of journal entries (not a sample) for known anomaly patterns — round-dollar
    amounts (more consistent with an estimate than a transaction), postings outside business hours or on
    weekends (unusual timing for a routine operational entry), and amounts sitting just under a disclosed
    approval threshold (the classic structuring/split-invoice pattern)."""
from __future__ import annotations

import math
from collections import Counter
from typing import Any, Dict, List, Optional, Sequence

BENFORD_FIRST_DIGIT: Dict[int, float] = {d: math.log10(1 + 1 / d) for d in range(1, 10)}

# Nigrini's real, published MAD conformity thresholds for the first-digit test (widely cited forensic-accounting
# convention — see docs/BIG4_AUTOMATION.md for sourcing).
MAD_THRESHOLDS = [(0.000, 0.006, "close conformity"), (0.006, 0.012, "acceptable conformity"),
                  (0.012, 0.015, "marginally acceptable"), (0.015, float("inf"), "nonconformity")]


def first_digit(x: float) -> Optional[int]:
    x = abs(x)
    if x == 0:
        return None
    while x < 1: x *= 10
    while x >= 10: x /= 10
    return int(x)


def benford_first_digit_test(values: Sequence[float]) -> Dict[str, Any]:
    digits = [d for d in (first_digit(v) for v in values) if d is not None]
    n = len(digits)
    if n == 0:
        raise ValueError("no nonzero values to test")
    counts = Counter(digits)
    observed = {d: counts.get(d, 0) / n for d in range(1, 10)}
    mad = sum(abs(observed[d] - BENFORD_FIRST_DIGIT[d]) for d in range(1, 10)) / 9
    conformity = next(label for lo, hi, label in MAD_THRESHOLDS if lo <= mad < hi)
    return {"n": n, "observed_distribution": observed, "expected_distribution": dict(BENFORD_FIRST_DIGIT),
            "mad": mad, "conformity": conformity}


def journal_entry_test(entries: Sequence[Dict[str, Any]], approval_threshold: Optional[float] = None,
                       round_dollar_threshold: float = 1000) -> Dict[str, Any]:
    """entries: dicts carrying at least `amount`, and optionally `is_weekend` (bool) / `hour` (0-23, posting
    time-of-day) — real, standard rule-based JE-testing flags, each independently real and commonly cited (not a
    combined fraud score): round-dollar amounts, weekend postings, after-hours postings (outside 06:00-20:00),
    and amounts sitting just under a disclosed approval threshold."""
    flagged: List[Dict[str, Any]] = []
    for e in entries:
        reasons: List[str] = []
        amt = e.get("amount", 0)
        if amt and round_dollar_threshold and abs(amt) % round_dollar_threshold == 0:
            reasons.append("round_dollar_amount")
        if e.get("is_weekend"):
            reasons.append("weekend_posting")
        if e.get("hour") is not None and not (6 <= e["hour"] <= 20):
            reasons.append("after_hours_posting")
        if approval_threshold and amt and approval_threshold * 0.95 <= abs(amt) < approval_threshold:
            reasons.append("just_under_approval_threshold")
        if reasons:
            flagged.append({**e, "flags": reasons})
    return {"n_entries": len(entries), "n_flagged": len(flagged), "flagged": flagged}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "benford" in d:
        out["benford"] = benford_first_digit_test(d["benford"]["values"])
    if "journal_entries" in d:
        je = d["journal_entries"]
        out["journal_entries"] = journal_entry_test(je["entries"], approval_threshold=je.get("approval_threshold"),
                                                     round_dollar_threshold=je.get("round_dollar_threshold", 1000))
    return out
