"""Sum-of-the-parts valuation: value each segment with its own multiple (or a supplied DCF / asset value), subtract
capitalised unallocated corporate costs, apply an optional conglomerate discount, bridge to equity and per share.
Mirrors the SOTP tabs in agentii / governed-dcf and the Damodaran 'valuing a multi-business company' recipe."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


@dataclass
class Segment:
    name: str
    metric: float = 0.0                 # EBITDA, EBIT, revenue … of the segment
    multiple: float = 0.0               # applied to metric
    metric_name: str = "EBITDA"
    value: Optional[float] = None       # override: DCF / NAV / market value of the segment
    ownership: float = 1.0              # economic stake (e.g. 0.6 for a listed 60% subsidiary)
    note: str = ""


def sotp(segments: Sequence[Segment], corporate_costs: float = 0.0, corporate_cost_multiple: float = 0.0, net_debt: float = 0.0,
         other_adjustments: Optional[Dict[str, float]] = None, conglomerate_discount: float = 0.0, shares: Optional[float] = None, price: Optional[float] = None) -> Dict[str, Any]:
    rows = []
    for s in segments:
        gross = s.value if s.value is not None else s.metric * s.multiple
        rows.append({"segment": s.name, "metric_name": s.metric_name, "metric": s.metric, "multiple": s.multiple if s.value is None else safe_div(s.value, s.metric),
                     "gross_value": gross, "ownership": s.ownership, "attributable_value": gross * s.ownership, "method": "override" if s.value is not None else "multiple", "note": s.note})
    gross_ev = sum(r["attributable_value"] for r in rows)
    corp = -abs(corporate_costs) * corporate_cost_multiple
    ev_before = gross_ev + corp
    disc = -ev_before * conglomerate_discount
    ev = ev_before + disc
    adj = other_adjustments or {}
    equity = ev - net_debt + sum(adj.values())
    for r in rows: r["share_of_gross"] = safe_div(r["attributable_value"], gross_ev)
    out = {"segments": rows, "gross_enterprise_value": gross_ev, "capitalised_corporate_costs": corp, "conglomerate_discount": disc, "enterprise_value": ev,
           "less_net_debt": -net_debt, "other_adjustments": adj, "equity_value": equity,
           "bridge": [("Segments (attributable)", gross_ev), ("Corporate costs", corp), ("Conglomerate discount", disc), ("Net debt", -net_debt)] + [(k, v) for k, v in adj.items()] + [("Equity value", equity)]}
    if shares:
        out["value_per_share"] = equity / shares
        if price: out["premium_to_price"] = out["value_per_share"] / price - 1; out["implied_market_discount"] = 1 - price / out["value_per_share"]
    return out


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    segs = [Segment(**s) for s in d.pop("segments")]
    return sotp(segs, **d)
