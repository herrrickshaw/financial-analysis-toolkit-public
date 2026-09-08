"""Warranty reserve accrual and the trade-receivables allowance for credit losses (CECL, ASC 326) -- two
real, common expected-value loss accruals with no prior representation across the toolkit's other ~50
modules, distinct from `finmodel.bank_model`'s CECL provisioning for LOANS (a different asset class, usually
estimated with a statistical PD/LGD approach rather than the aging-schedule convention used for trade
receivables).

  * A warranty reserve is built with the expected-cost method: each period's ADDITION to the reserve is
    units sold this period x the expected failure rate x the average repair/replacement cost -- an accrual
    made at the time of SALE, not when a claim is actually filed, since the obligation to repair already
    exists at the point of sale. The reserve then rolls forward like any other accrued liability: beginning
    balance + additions - actual costs incurred as claims are paid = ending balance.
  * The trade-receivables allowance under CECL's aging-schedule method buckets receivables by how overdue
    they are and applies a DIFFERENT expected-loss rate to each bucket -- older, more overdue balances
    carry a materially higher expected-loss rate than current receivables, the real, standard convention
    (distinct from a single blanket loss-rate percentage applied uniformly across the whole receivables
    balance).
"""
from __future__ import annotations

from typing import Any, Dict, List, Sequence


def warranty_reserve_rollforward(beginning_reserve: float, units_sold: float, failure_rate: float,
                                 average_repair_cost: float, actual_warranty_costs_incurred: float) -> Dict[str, Any]:
    additions = units_sold * failure_rate * average_repair_cost
    ending_reserve = beginning_reserve + additions - actual_warranty_costs_incurred
    return {"beginning_reserve": beginning_reserve, "additions": additions,
            "actual_warranty_costs_incurred": actual_warranty_costs_incurred, "ending_reserve": ending_reserve}


def receivables_allowance_aging_method(aging_buckets: Sequence[Dict[str, Any]]) -> Dict[str, Any]:
    """`aging_buckets`: [{"bucket": "current", "balance": 500000.0, "expected_loss_rate": 0.01}, ...]."""
    bucket_detail: List[Dict[str, Any]] = []
    for b in aging_buckets:
        allowance = b["balance"] * b["expected_loss_rate"]
        bucket_detail.append({"bucket": b["bucket"], "balance": b["balance"],
                              "expected_loss_rate": b["expected_loss_rate"], "allowance": allowance})
    total_receivables = sum(b["balance"] for b in aging_buckets)
    total_allowance = sum(b["allowance"] for b in bucket_detail)
    return {"buckets": bucket_detail, "total_receivables": total_receivables, "total_allowance": total_allowance,
            "net_realizable_receivables": total_receivables - total_allowance}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    if "warranty_reserve_rollforward" in d:
        out["warranty_reserve_rollforward"] = warranty_reserve_rollforward(**d["warranty_reserve_rollforward"])
    if "receivables_allowance_aging_method" in d:
        out["receivables_allowance_aging_method"] = receivables_allowance_aging_method(**d["receivables_allowance_aging_method"])
    return out
