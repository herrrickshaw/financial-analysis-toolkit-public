"""Composite financial-health scores that the popular open-source screeners ship (telmus, FinAnalyzer, quantmodels) and
that the paid CFI 'Financial Analysis' templates approximate with ratio dashboards:

  * Altman Z-score (1968 manufacturing form + 1983 Z' private-firm and Z'' non-manufacturing/emerging-market forms)
  * Beneish M-score (8-variable 1999 model; > −1.78 flags likely earnings manipulation)
  * Piotroski F-score (9 binary signals on profitability, leverage/liquidity and operating efficiency)

Inputs are plain dicts of two consecutive fiscal years in the shape produced by finmodel.edgar.annual() (revenue,
cogs, operating_income, net_income, cfo, da, total_assets, current_assets, current_liabilities, receivables, ppe,
equity, retained_earnings, debt_total, total_liabilities, diluted_shares, sga, market_cap …)."""
from __future__ import annotations

import math
from typing import Any, Dict, Optional

from .fin import safe_div


def altman_z(cur: Dict[str, float], market_cap: Optional[float] = None, variant: str = "public") -> Dict[str, Any]:
    ta = cur.get("total_assets", 0) or 0
    wc = (cur.get("current_assets", 0) or 0) - (cur.get("current_liabilities", 0) or 0)
    tl = cur.get("total_liabilities") or (ta - (cur.get("equity", 0) or 0))
    x1 = safe_div(wc, ta); x2 = safe_div(cur.get("retained_earnings", 0) or 0, ta); x3 = safe_div(cur.get("operating_income", 0) or 0, ta)
    x5 = safe_div(cur.get("revenue", 0) or 0, ta)
    if variant == "public":
        x4 = safe_div(market_cap if market_cap is not None else cur.get("equity", 0), tl)
        z = 1.2 * x1 + 1.4 * x2 + 3.3 * x3 + 0.6 * x4 + 1.0 * x5; zones = (1.81, 2.99)
    elif variant == "private":
        x4 = safe_div(cur.get("equity", 0) or 0, tl)
        z = 0.717 * x1 + 0.847 * x2 + 3.107 * x3 + 0.420 * x4 + 0.998 * x5; zones = (1.23, 2.90)
    else:  # non-manufacturing / emerging-market Z''
        x4 = safe_div(cur.get("equity", 0) or 0, tl)
        z = 6.56 * x1 + 3.26 * x2 + 6.72 * x3 + 1.05 * x4; zones = (1.10, 2.60)
    zone = "distress" if z < zones[0] else "grey" if z < zones[1] else "safe"
    return {"z": z, "zone": zone, "variant": variant, "components": {"working_capital/TA": x1, "retained_earnings/TA": x2, "EBIT/TA": x3, "equity/TL": x4, "sales/TA": x5}}


def beneish_m(cur: Dict[str, float], prev: Dict[str, float]) -> Dict[str, Any]:
    def g(d, k): return d.get(k, 0) or 0
    rev_c, rev_p = g(cur, "revenue"), g(prev, "revenue")
    dsri = safe_div(safe_div(g(cur, "receivables"), rev_c), safe_div(g(prev, "receivables"), rev_p), 1.0)
    gm_c = safe_div(rev_c - g(cur, "cogs"), rev_c); gm_p = safe_div(rev_p - g(prev, "cogs"), rev_p)
    gmi = safe_div(gm_p, gm_c, 1.0)
    aq = lambda d: 1 - safe_div(g(d, "current_assets") + g(d, "ppe") + g(d, "securities"), g(d, "total_assets"))
    aqi = safe_div(aq(cur), aq(prev), 1.0)
    sgi = safe_div(rev_c, rev_p, 1.0)
    depi = safe_div(safe_div(g(prev, "da"), g(prev, "da") + g(prev, "ppe")), safe_div(g(cur, "da"), g(cur, "da") + g(cur, "ppe")), 1.0)
    sgai = safe_div(safe_div(g(cur, "sga"), rev_c), safe_div(g(prev, "sga"), rev_p), 1.0)
    lvgi = safe_div(safe_div(g(cur, "debt_total") + g(cur, "current_liabilities"), g(cur, "total_assets")), safe_div(g(prev, "debt_total") + g(prev, "current_liabilities"), g(prev, "total_assets")), 1.0)
    tata = safe_div(g(cur, "net_income") - g(cur, "cfo"), g(cur, "total_assets"))
    m = -4.84 + 0.92 * dsri + 0.528 * gmi + 0.404 * aqi + 0.892 * sgi + 0.115 * depi - 0.172 * sgai + 4.679 * tata - 0.327 * lvgi
    return {"m": m, "likely_manipulator": m > -1.78, "components": {"DSRI": dsri, "GMI": gmi, "AQI": aqi, "SGI": sgi, "DEPI": depi, "SGAI": sgai, "TATA": tata, "LVGI": lvgi}}


def piotroski_f(cur: Dict[str, float], prev: Dict[str, float]) -> Dict[str, Any]:
    def g(d, k): return d.get(k, 0) or 0
    roa_c = safe_div(g(cur, "net_income"), g(prev, "total_assets") or g(cur, "total_assets")); roa_p = safe_div(g(prev, "net_income"), g(prev, "total_assets"))
    cfo_c = g(cur, "cfo")
    lev_c = safe_div(g(cur, "debt_total"), g(cur, "total_assets")); lev_p = safe_div(g(prev, "debt_total"), g(prev, "total_assets"))
    cr_c = safe_div(g(cur, "current_assets"), g(cur, "current_liabilities")); cr_p = safe_div(g(prev, "current_assets"), g(prev, "current_liabilities"))
    sh_c = g(cur, "diluted_shares") or g(cur, "shares"); sh_p = g(prev, "diluted_shares") or g(prev, "shares")
    gm_c = safe_div(g(cur, "revenue") - g(cur, "cogs"), g(cur, "revenue")); gm_p = safe_div(g(prev, "revenue") - g(prev, "cogs"), g(prev, "revenue"))
    at_c = safe_div(g(cur, "revenue"), g(cur, "total_assets")); at_p = safe_div(g(prev, "revenue"), g(prev, "total_assets"))
    signals = {"ROA > 0": roa_c > 0, "CFO > 0": cfo_c > 0, "ROA improving": roa_c > roa_p, "CFO > net income (accruals)": cfo_c > g(cur, "net_income"),
               "Leverage falling": lev_c < lev_p, "Current ratio rising": cr_c > cr_p, "No new shares": sh_c <= sh_p, "Gross margin rising": gm_c > gm_p, "Asset turnover rising": at_c > at_p}
    f = sum(signals.values())
    return {"f": f, "grade": "strong" if f >= 7 else "weak" if f <= 3 else "middle", "signals": signals}


def health(cur: Dict[str, float], prev: Dict[str, float], market_cap: Optional[float] = None, variant: str = "public") -> Dict[str, Any]:
    return {"altman": altman_z(cur, market_cap, variant), "beneish": beneish_m(cur, prev), "piotroski": piotroski_f(cur, prev)}
