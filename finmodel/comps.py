"""Comparable companies (trading comps) and precedent transactions engine, with the football-field summary.

Structure follows the Breaking Into Wall Street public-comps / M&A-comps workbooks and the free CFI
'Comparable Company Analysis' and 'Valuation Model – Comps, Precedents, Football Field' templates:

  peer spreading  : equity value = price × diluted shares; EV = equity + debt + preferred + NCI + other − cash
  multiples       : EV / revenue, EV / EBITDA, EV / EBIT (LTM and forward years), P / E — 'NM' when negative or ≥ 100x
  statistics      : max, 75th percentile, median, 25th percentile, min (Excel QUARTILE, inclusive), mean
  implied value   : multiple × target metric → implied EV → equity bridge (cash, investments, NOLs, debt,
                    preferred, NCI, pensions, leases…) → implied share price and premium / (discount) to current
  precedents      : deal EV / LTM revenue / EBITDA / EBIT and offer premia to 1-day / 1-week / 1-month prior prices
  football field  : low–high implied price per method (comps, precedents, DCF, 52-week range) for charts.range_bars

Reconciled to the cached values of those workbooks in tests/test_comps.py.
"""
from __future__ import annotations

import math
import statistics
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div

NM = "NM"


@dataclass
class Peer:
    name: str
    price: float
    diluted_shares: float
    cash: float = 0.0                 # positive number (subtracted from EV)
    debt: float = 0.0
    preferred: float = 0.0
    nci: float = 0.0                  # non-controlling interests and other EV adjustments
    metrics: Dict[str, float] = field(default_factory=dict)   # e.g. {"revenue_ltm": ..., "ebitda_ltm": ..., "net_income_ltm": ...}
    net_debt: Optional[float] = None  # if given, overrides cash/debt (CFI template style)
    ticker: str = ""

    @property
    def equity_value(self) -> float:
        return self.price * self.diluted_shares

    @property
    def enterprise_value(self) -> float:
        if self.net_debt is not None:
            return self.equity_value + self.net_debt
        return self.equity_value - self.cash + self.debt + self.preferred + self.nci


@dataclass
class Target:
    name: str
    price: float
    diluted_shares: float
    metrics: Dict[str, float]
    bridge: Dict[str, float] = field(default_factory=dict)    # signed items added to EV to get equity (cash +, debt −, …)
    net_debt: Optional[float] = None                          # CFI style: equity = EV − net debt

    def bridge_total(self) -> float:
        if self.net_debt is not None:
            return -self.net_debt
        return sum(self.bridge.values())


# multiple name -> (numerator: "ev" | "equity", metric key)
DEFAULT_MULTIPLES = {"EV / Revenue": ("ev", "revenue"), "EV / EBITDA": ("ev", "ebitda"), "EV / EBIT": ("ev", "ebit"), "P / E": ("equity", "net_income")}


def multiple(numerator: float, metric: Optional[float], cap: float = 100.0):
    """BIWS rule: negative or ≥ cap multiples are 'NM'; missing metric is 'N/A'."""
    if metric is None:
        return "N/A"
    try:
        m = numerator / metric
    except ZeroDivisionError:
        return "N/A"
    if m < 0 or m >= cap:
        return NM
    return m


def quartile_inc(values: Sequence[float], q: int) -> float:
    """Excel QUARTILE / QUARTILE.INC."""
    xs = sorted(values)
    if not xs: return float("nan")
    pos = (len(xs) - 1) * q / 4.0; lo, hi = int(math.floor(pos)), int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def stats(values: Sequence[Any]) -> Dict[str, float]:
    xs = [float(v) for v in values if isinstance(v, (int, float)) and not isinstance(v, bool) and not math.isnan(v)]
    if not xs:
        return {k: float("nan") for k in ("max", "p75", "median", "p25", "min", "mean")} | {"n": 0}
    return {"max": max(xs), "p75": quartile_inc(xs, 3), "median": float(statistics.median(xs)), "p25": quartile_inc(xs, 1),
            "min": min(xs), "mean": sum(xs) / len(xs), "n": len(xs)}


def spread(peers: Sequence[Peer], multiples: Optional[Dict[str, tuple]] = None, periods: Sequence[str] = ("ltm",), cap: float = 100.0) -> Dict[str, Any]:
    """Compute EV, equity value and every multiple for each peer plus summary statistics per multiple/period."""
    multiples = multiples or DEFAULT_MULTIPLES
    rows = []
    for p in peers:
        row = {"name": p.name, "ticker": p.ticker, "price": p.price, "diluted_shares": p.diluted_shares, "equity_value": p.equity_value,
               "enterprise_value": p.enterprise_value, "metrics": dict(p.metrics), "multiples": {}}
        for label, (num, key) in multiples.items():
            for per in periods:
                mk = f"{key}_{per}"
                if mk not in p.metrics and per == "ltm" and key in p.metrics:
                    mk = key
                row["multiples"][f"{label} {per.upper()}"] = multiple(p.enterprise_value if num == "ev" else p.equity_value, p.metrics.get(mk), cap)
        rows.append(row)
    summary = {}
    for label in rows[0]["multiples"] if rows else []:
        summary[label] = stats([r["multiples"][label] for r in rows])
    ops = {}
    for key in sorted({k for p in peers for k in p.metrics}):
        ops[key] = stats([p.metrics[key] for p in peers if key in p.metrics])
    return {"peers": rows, "summary": summary, "operating_stats": ops, "multiples": {k: {"numerator": v[0], "metric": v[1]} for k, v in multiples.items()}}


def implied_valuation(target: Target, comps: Dict[str, Any], stat_keys: Sequence[str] = ("max", "p75", "median", "p25", "min"), multiples: Optional[Dict[str, tuple]] = None) -> Dict[str, Any]:
    """Apply each multiple's peer statistics to the target's metric → implied EV/equity → share price and premium."""
    multiples = multiples or comps.get("multiples") and {k: (v["numerator"], v["metric"]) for k, v in comps["multiples"].items()} or DEFAULT_MULTIPLES
    out = {"target": target.name, "current_price": target.price, "diluted_shares": target.diluted_shares, "bridge": dict(target.bridge), "bridge_total": target.bridge_total(), "rows": []}
    for label, s in comps["summary"].items():
        base = label.rsplit(" ", 1)[0]; per = label.rsplit(" ", 1)[1].lower()
        num, key = multiples.get(base, (None, None))
        if num is None: continue
        mk = f"{key}_{per}" if f"{key}_{per}" in target.metrics else key
        metric = target.metrics.get(mk)
        if metric is None: continue
        row = {"multiple": label, "target_metric": metric, "numerator": num, "implied": {}}
        for sk in stat_keys:
            m = s.get(sk)
            if m is None or (isinstance(m, float) and math.isnan(m)): continue
            value = m * metric
            equity = value + target.bridge_total() if num == "ev" else value
            price = safe_div(equity, target.diluted_shares)
            row["implied"][sk] = {"multiple": m, "enterprise_value": value if num == "ev" else equity - target.bridge_total(), "equity_value": equity,
                                  "share_price": price, "premium_to_current": safe_div(price, target.price) - 1 if target.price else float("nan")}
        out["rows"].append(row)
    prices = [v["share_price"] for r in out["rows"] for v in r["implied"].values()]
    out["range"] = {"low": min(prices), "high": max(prices)} if prices else {"low": float("nan"), "high": float("nan")}
    return out


@dataclass
class Deal:
    acquirer: str
    target: str
    date: str
    enterprise_value: float
    ltm_revenue: Optional[float] = None
    ltm_ebitda: Optional[float] = None
    ltm_ebit: Optional[float] = None
    offer_price: Optional[float] = None
    price_1d_prior: Optional[float] = None
    price_1w_prior: Optional[float] = None
    price_1m_prior: Optional[float] = None
    equity_value: Optional[float] = None
    multiples: Dict[str, float] = field(default_factory=dict)   # pre-computed multiples (CFI template style)


def precedents(deals: Sequence[Deal], cap: float = 100.0) -> Dict[str, Any]:
    rows = []
    for d in deals:
        m = dict(d.multiples)
        if d.ltm_revenue is not None: m["EV / Revenue LTM"] = multiple(d.enterprise_value, d.ltm_revenue, cap)
        if d.ltm_ebitda is not None: m["EV / EBITDA LTM"] = multiple(d.enterprise_value, d.ltm_ebitda, cap)
        if d.ltm_ebit is not None: m["EV / EBIT LTM"] = multiple(d.enterprise_value, d.ltm_ebit, cap)
        prem = {}
        for lab, ref in (("1-day", d.price_1d_prior), ("1-week", d.price_1w_prior), ("1-month", d.price_1m_prior)):
            if d.offer_price is not None and ref:
                prem[lab] = d.offer_price / ref - 1
        rows.append({"acquirer": d.acquirer, "target": d.target, "date": d.date, "enterprise_value": d.enterprise_value,
                     "ltm_revenue": d.ltm_revenue, "ltm_ebitda": d.ltm_ebitda, "ltm_ebit": d.ltm_ebit, "multiples": m, "premiums": prem})
    labels = sorted({k for r in rows for k in r["multiples"]}, key=lambda s: ["EV / Revenue", "EV / EBITDA", "EV / EBIT"].index(s.rsplit(" ", 1)[0]) if s.rsplit(" ", 1)[0] in ("EV / Revenue", "EV / EBITDA", "EV / EBIT") else 9)
    summary = {lab: stats([r["multiples"].get(lab) for r in rows]) for lab in labels}
    summary_premiums = {lab: stats([r["premiums"].get(lab) for r in rows]) for lab in ("1-day", "1-week", "1-month") if any(lab in r["premiums"] for r in rows)}
    summary_ev = stats([r["enterprise_value"] for r in rows])
    return {"deals": rows, "summary": summary, "premium_summary": summary_premiums, "enterprise_value_stats": summary_ev,
            "multiples": {"EV / Revenue": {"numerator": "ev", "metric": "revenue"}, "EV / EBITDA": {"numerator": "ev", "metric": "ebitda"}, "EV / EBIT": {"numerator": "ev", "metric": "ebit"}}}


def football_field(target: Target, methods: Dict[str, Any], extra: Optional[Dict[str, tuple]] = None, stat_low: str = "p25", stat_high: str = "p75",
                   multiples: Optional[Dict[str, Dict[str, tuple]]] = None) -> Dict[str, Any]:
    """methods: name -> spread()/precedents() result. Returns per-method (low, high) implied share prices plus extras
    such as {"DCF": (28, 36), "52-week": (22, 30)}. `multiples` optionally overrides the numerator/metric map per method
    (e.g. to apply a peer table's EV-based 'P/E' as a true equity multiple)."""
    items: List[Dict[str, Any]] = []
    for name, comps in methods.items():
        iv = implied_valuation(target, comps, stat_keys=(stat_low, "median", stat_high), multiples=(multiples or {}).get(name))
        lows = [r["implied"][stat_low]["share_price"] for r in iv["rows"] if stat_low in r["implied"]]
        highs = [r["implied"][stat_high]["share_price"] for r in iv["rows"] if stat_high in r["implied"]]
        if lows and highs:
            items.append({"method": name, "low": min(lows), "high": max(highs), "median": statistics.median([r["implied"]["median"]["share_price"] for r in iv["rows"] if "median" in r["implied"]])})
    for name, (lo, hi) in (extra or {}).items():
        items.append({"method": name, "low": lo, "high": hi, "median": (lo + hi) / 2})
    return {"target": target.name, "current_price": target.price, "items": items}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    target = Target(**d["target"]) if "target" in d else None
    periods = d.get("periods", ["ltm"])
    if "peers" in d:
        comps = spread([Peer(**p) for p in d["peers"]], periods=periods)
        out["comps"] = comps
        if target: out["implied_from_comps"] = implied_valuation(target, comps)
    if "deals" in d:
        prec = precedents([Deal(**x) for x in d["deals"]])
        out["precedents"] = prec
        if target: out["implied_from_precedents"] = implied_valuation(target, prec)
    if target and ("peers" in d or "deals" in d):
        methods = {k: out[v] for k, v in (("Trading comps", "comps"), ("Precedent transactions", "precedents")) if v in out}
        out["football_field"] = football_field(target, methods, {k: tuple(v) for k, v in d.get("extra_ranges", {}).items()},
                                               stat_low=d.get("stat_low", "p25"), stat_high=d.get("stat_high", "p75"))
    return out
