"""Institutional cost-allocation, resource-allocation and income-diversification model, following the EUA–ATHENA
'Toolkit for Financial Management' (2015) and EUA's full-costing guidance:

  1. Resource allocation model — split a funding envelope into direct, formula-driven, top-sliced and strategic parts.
  2. Basic costing model — allocate direct costs to activities (teaching / research / other), then push indirect
     (central administration, support units, facilities) costs to cost objects with drivers (student numbers,
     person-years, effective work time, space), and derive indirect-cost rates on direct salary (the Helsinki /
     Trinity 'full economic costing' pattern in the toolkit's good-practice examples).
  3. Income diversification analysis — income by source with stability and growth potential scores, plus a
     Herfindahl concentration index.

Everything is plain dicts so it can be fed from CSV/JSON and rendered with finmodel.charts."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


# --------------------------------------------------------------------------- 1. resource allocation
def resource_allocation(envelope: float, units: Dict[str, Dict[str, float]], formula_weights: Dict[str, float], top_slice_pct: float = 0.0,
                        strategic: Optional[Dict[str, float]] = None, direct: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """envelope: total funds; units: unit -> {driver: value} (e.g. students, research_income, staff_fte);
    formula_weights: driver -> weight (sums to 1); top_slice_pct: share retained centrally; strategic/direct: unit -> amount."""
    strategic = strategic or {}; direct = direct or {}
    top = envelope * top_slice_pct
    formula_pool = envelope - top - sum(strategic.values()) - sum(direct.values())
    totals = {d: sum(u.get(d, 0) for u in units.values()) for d in formula_weights}
    shares = {u: sum(w * safe_div(units[u].get(d, 0), totals[d]) for d, w in formula_weights.items()) for u in units}
    rows = {u: {"direct": direct.get(u, 0.0), "formula": formula_pool * shares[u], "strategic": strategic.get(u, 0.0)} for u in units}
    for u in rows: rows[u]["total"] = sum(rows[u].values()); rows[u]["formula_share"] = shares[u]
    return {"envelope": envelope, "top_slice": top, "formula_pool": formula_pool, "units": rows, "check": abs(top + sum(r["total"] for r in rows.values()) - envelope) < 1e-6}


# --------------------------------------------------------------------------- 2. costing model
@dataclass
class CostPool:
    name: str
    amount: float
    driver: str                      # name of the driver used to spread this pool
    kind: str = "indirect"           # "direct" pools are already attributed to a cost object


@dataclass
class CostObject:
    name: str
    activity: str                    # teaching | research | other
    drivers: Dict[str, float] = field(default_factory=dict)      # driver -> quantity (students, person_years, work_time, m2 …)
    direct_costs: float = 0.0
    direct_salary: float = 0.0       # base for the indirect-cost rate


def allocate_costs(objects: Sequence[CostObject], pools: Sequence[CostPool], salary_addon_rate: float = 0.0) -> Dict[str, Any]:
    """Two-step allocation: each pool is spread over cost objects in proportion to the pool's driver; results are summed
    per object and per activity. salary_addon_rate (e.g. 0.53 at Helsinki) grosses up direct salary for paid absences and
    statutory charges before computing indirect-cost rates."""
    alloc: Dict[str, Dict[str, float]] = {o.name: {} for o in objects}
    unallocated = {}
    for p in pools:
        total = sum(o.drivers.get(p.driver, 0) for o in objects)
        if total <= 0:
            unallocated[p.name] = p.amount; continue
        for o in objects:
            alloc[o.name][p.name] = p.amount * o.drivers.get(p.driver, 0) / total
    rows = []
    for o in objects:
        ind = sum(alloc[o.name].values()); salary_full = o.direct_salary * (1 + salary_addon_rate)
        full = o.direct_costs + ind
        rows.append({"object": o.name, "activity": o.activity, "direct": o.direct_costs, "direct_salary_grossed": salary_full, "indirect": ind,
                     "full_cost": full, "indirect_rate_on_salary": safe_div(ind, salary_full), "by_pool": alloc[o.name]})
    by_activity: Dict[str, Dict[str, float]] = {}
    for r in rows:
        a = by_activity.setdefault(r["activity"], {"direct": 0.0, "indirect": 0.0, "full_cost": 0.0, "direct_salary_grossed": 0.0})
        for k in a: a[k] += r[k]
    for a in by_activity.values(): a["indirect_rate_on_salary"] = safe_div(a["indirect"], a["direct_salary_grossed"])
    total_pool = sum(p.amount for p in pools); allocated = sum(r["indirect"] for r in rows)
    return {"objects": rows, "by_activity": by_activity, "pools_total": total_pool, "allocated": allocated, "unallocated": unallocated,
            "check": abs(total_pool - allocated - sum(unallocated.values())) < 1e-6}


def full_cost_price(direct_cost: float, direct_salary: float, indirect_rate_on_salary: float, salary_addon_rate: float = 0.0, margin: float = 0.0) -> Dict[str, float]:
    """Price a project / course at full economic cost: direct + salary add-on + indirect rate × grossed salary (+ margin)."""
    grossed = direct_salary * (1 + salary_addon_rate); indirect = grossed * indirect_rate_on_salary
    full = direct_cost + (grossed - direct_salary) + indirect
    return {"direct": direct_cost, "salary_addon": grossed - direct_salary, "indirect": indirect, "full_cost": full, "price": full * (1 + margin)}


# --------------------------------------------------------------------------- 3. income diversification
def income_diversification(income: Dict[str, float], stability: Optional[Dict[str, float]] = None, potential: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
    """income: source -> amount (public, tuition, business & industry, private sponsors, other …).
    stability / potential: optional 1–5 scores per source (toolkit questions 2 and 3). Returns shares, Herfindahl index
    (1 = single source), effective number of sources, and a priority ranking = potential × (1 − share)."""
    total = sum(income.values()); shares = {k: safe_div(v, total) for k, v in income.items()}
    hhi = sum(s * s for s in shares.values())
    stability = stability or {}; potential = potential or {}
    rows = {k: {"amount": v, "share": shares[k], "stability": stability.get(k), "potential": potential.get(k),
                "priority": (potential.get(k, 0) or 0) * (1 - shares[k])} for k, v in income.items()}
    ranked = sorted(rows, key=lambda k: -rows[k]["priority"])
    weighted_stability = sum((stability.get(k, 0) or 0) * shares[k] for k in income) if stability else None
    return {"total": total, "sources": rows, "hhi": hhi, "effective_sources": safe_div(1, hhi), "ranking": ranked, "weighted_stability": weighted_stability}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "resource_allocation" in d:
        out["resource_allocation"] = resource_allocation(**d["resource_allocation"])
    if "costing" in d:
        c = d["costing"]
        out["costing"] = allocate_costs([CostObject(**o) for o in c["objects"]], [CostPool(**p) for p in c["pools"]], c.get("salary_addon_rate", 0.0))
    if "income" in d:
        out["income_diversification"] = income_diversification(d["income"], d.get("stability"), d.get("potential"))
    return out
