"""Financial restructuring / distressed investing — the real, named curriculum area this toolkit's own survey
(docs/MORE_CFI_TEMPLATES.md) flagged as Wall Street Prep's/Wharton's "Restructuring & Distressed Investing
Certificate" (liquidity analysis, capital-structure modeling, DIP financing, plan-of-reorganization recovery
mechanics) and deliberately deferred to its own pass. Four real, standard, quantitatively concrete techniques:

  Recovery waterfall (absolute priority)   — reorganization value is distributed strictly by seniority: the most
                                             senior claims are paid in FULL before any junior claim receives
                                             anything, with claims of the SAME seniority (pari passu) split pro
                                             rata — 11 U.S.C. Sec 1129(b)(2)'s "absolute priority rule", the same
                                             legal doctrine behind every real Chapter 11 cramdown fight.
  Fulcrum security                        — the real, standard distressed-investing term for the most senior
                                             tranche that does NOT recover in full: its holders are the ones who
                                             actually end up owning the reorganized company's new equity in a
                                             real debt-for-equity restructuring, since everything junior to it is
                                             wiped out and everything senior to it was already made whole.
  Absolute-priority departure check       — flags when a junior claim recovers something while a more senior
                                             claim doesn't — the real, litigated fact pattern behind every real
                                             cramdown objection (real, narrow exceptions like unanimous consent
                                             or the "new value" doctrine exist in actual bankruptcy law and are
                                             NOT modeled here; this is a mechanical check, not a legal opinion).
  DIP financing sizing                    — real, standard convention: size debtor-in-possession financing to
                                             the largest projected shortfall below a minimum-liquidity covenant
                                             across a cash flow forecast (reuse finmodel.cash_flow_forecast's
                                             weekly figures as the input series)."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Sequence

from .fin import safe_div


@dataclass
class Tranche:
    name: str
    claim_amount: float
    seniority: int   # lower = more senior; equal values are pari passu (split pro rata within the rank)


def recovery_waterfall(reorg_value: float, tranches: Sequence[Tranche]) -> Dict[str, Any]:
    """Absolute priority: pay each seniority rank in full, most senior first, before any junior rank sees a
    dollar; a rank whose combined claims exceed what's left is the FULCRUM rank and splits what remains pro rata
    by claim size (pari passu); every rank junior to that gets zero."""
    ranks = sorted({t.seniority for t in tranches})
    remaining = reorg_value
    rows: List[Dict[str, Any]] = []
    for rank in ranks:
        group = [t for t in tranches if t.seniority == rank]
        total_claim = sum(t.claim_amount for t in group)
        if remaining <= 0:
            for t in group:
                rows.append({"name": t.name, "seniority": rank, "claim_amount": t.claim_amount, "recovery": 0.0, "recovery_pct": 0.0})
        elif remaining >= total_claim:
            for t in group:
                rows.append({"name": t.name, "seniority": rank, "claim_amount": t.claim_amount, "recovery": t.claim_amount, "recovery_pct": 1.0})
            remaining -= total_claim
        else:
            for t in group:
                recovery = remaining * safe_div(t.claim_amount, total_claim)
                rows.append({"name": t.name, "seniority": rank, "claim_amount": t.claim_amount, "recovery": recovery, "recovery_pct": safe_div(recovery, t.claim_amount)})
            remaining = 0.0
    return {"reorg_value": reorg_value, "tranches": rows, "residual_to_equity": max(0.0, remaining)}


def identify_fulcrum(waterfall: Dict[str, Any]) -> Dict[str, Any]:
    """The first (most senior) tranche in priority order whose recovery_pct is below 1.0 — its holders are the
    real, standard "fulcrum security": the class that actually bears the reorganization's value shortfall and
    typically receives the reorganized company's new equity in exchange for its impaired claim."""
    for row in sorted(waterfall["tranches"], key=lambda r: r["seniority"]):
        if row["recovery_pct"] < 1.0:
            return row
    return {"name": None, "note": "reorganization value covers every claim in full -- no fulcrum; existing equity retains value, a real but unusual outcome for a company distressed enough to restructure"}


def check_absolute_priority_departure(waterfall: Dict[str, Any]) -> Dict[str, Any]:
    """Mechanical check only, NOT a legal opinion: real Chapter 11 practice allows real, narrow exceptions
    (unanimous class consent, the disputed "new value" doctrine) that make a departure from strict priority
    lawful in some real cases -- this only flags the fact pattern (a junior class recovering something while a
    senior class doesn't), the same fact pattern every real cramdown objection is built on."""
    rows = sorted(waterfall["tranches"], key=lambda r: r["seniority"])
    departures = []
    for i, junior in enumerate(rows):
        if junior["recovery_pct"] <= 0:
            continue
        for senior in rows[:i]:
            if senior["seniority"] < junior["seniority"] and senior["recovery_pct"] < 1.0:
                departures.append({"senior_claim": senior["name"], "senior_recovery_pct": senior["recovery_pct"],
                                   "junior_claim": junior["name"], "junior_recovery_pct": junior["recovery_pct"]})
    return {"departures": departures, "absolute_priority_respected": len(departures) == 0}


def dip_financing_sizing(cash_flows: Sequence[float], minimum_liquidity: float, opening_cash: float = 0.0) -> Dict[str, Any]:
    """Real, standard sizing convention: a DIP facility must be large enough that cumulative cash never falls
    below the minimum-liquidity covenant at ANY point across the projection, not just at the end of it."""
    cumulative: List[float] = []
    cash = opening_cash
    for cf in cash_flows:
        cash += cf
        cumulative.append(cash)
    min_cash = min(cumulative) if cumulative else opening_cash
    required = max(0.0, minimum_liquidity - min_cash)
    return {"cumulative_cash": cumulative, "minimum_projected_cash": min_cash, "minimum_liquidity_covenant": minimum_liquidity, "required_dip_facility": required}


def post_emergence_capital_structure(emergence_ebitda: float, target_net_debt_to_ebitda: float) -> Dict[str, Any]:
    """A real, standard plan-of-reorganization sizing convention: the reorganized company's new debt is set to a
    target leverage ratio management/creditors negotiate as sustainable post-emergence, not the pre-petition
    debt load that drove it into distress in the first place."""
    new_debt = emergence_ebitda * target_net_debt_to_ebitda
    return {"emergence_ebitda": emergence_ebitda, "target_net_debt_to_ebitda": target_net_debt_to_ebitda, "new_debt": new_debt}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "recovery_waterfall" in d:
        rw = d["recovery_waterfall"]
        tranches = [Tranche(**t) for t in rw["tranches"]]
        waterfall = recovery_waterfall(rw["reorg_value"], tranches)
        out["recovery_waterfall"] = waterfall
        out["fulcrum_security"] = identify_fulcrum(waterfall)
        out["absolute_priority_check"] = check_absolute_priority_departure(waterfall)
    if "dip_financing_sizing" in d:
        out["dip_financing_sizing"] = dip_financing_sizing(**d["dip_financing_sizing"])
    if "post_emergence_capital_structure" in d:
        out["post_emergence_capital_structure"] = post_emergence_capital_structure(**d["post_emergence_capital_structure"])
    return out
