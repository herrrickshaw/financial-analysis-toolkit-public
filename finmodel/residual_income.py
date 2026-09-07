"""Residual-income (Edwards–Bell–Ohlson) equity valuation and EVA / economic-profit firm valuation.

Residual income: RI_t = NI_t − k_e × B_{t−1}; equity value = B_0 + Σ PV(RI_t) + PV(terminal RI), with the terminal
value either a fading persistence (ω, RI_{T+1} = ω × RI_T, value = RI_{T+1} / (1 + k_e − ω)) or a growing perpetuity.
Clean-surplus accounting rolls book value forward: B_t = B_{t−1} + NI_t − dividends_t.

EVA: EVA_t = NOPAT_t − WACC × invested capital_{t−1}; firm value = capital_0 + Σ PV(EVA_t) + PV(terminal EVA);
equity = firm value − net debt. Both reconcile to a DCF when assumptions are consistent (CFA Level II reading;
FinModeling's residual-operating-income model)."""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


def residual_income(book_value_0: float, net_income: Sequence[float], dividends: Sequence[float], cost_of_equity: float,
                    terminal: str = "persistence", persistence: float = 0.6, terminal_growth: float = 0.0, shares: Optional[float] = None,
                    price: Optional[float] = None) -> Dict[str, Any]:
    n = len(net_income)
    if len(dividends) != n: raise ValueError("net_income and dividends must have the same length")
    ke = cost_of_equity
    bv = [book_value_0]; ri = []; pv = []
    for t in range(n):
        ri_t = net_income[t] - ke * bv[-1]; ri.append(ri_t); pv.append(ri_t / (1 + ke) ** (t + 1))
        bv.append(bv[-1] + net_income[t] - dividends[t])
    if terminal == "persistence":
        tv = ri[-1] * persistence / (1 + ke - persistence)
    elif terminal == "growth":
        if ke <= terminal_growth: raise ValueError("cost of equity must exceed terminal growth")
        tv = ri[-1] * (1 + terminal_growth) / (ke - terminal_growth)
    elif terminal == "none":
        tv = 0.0
    else:
        raise ValueError("terminal must be persistence | growth | none")
    pv_tv = tv / (1 + ke) ** n
    equity = book_value_0 + sum(pv) + pv_tv
    out = {"book_value": bv, "residual_income": ri, "pv_residual_income": pv, "terminal_residual_income_value": tv, "pv_terminal": pv_tv,
           "equity_value": equity, "share_of_value_from_book": safe_div(book_value_0, equity), "roe": [safe_div(net_income[t], bv[t]) for t in range(n)], "cost_of_equity": ke}
    if shares:
        out["value_per_share"] = equity / shares
        if price: out["premium_to_price"] = out["value_per_share"] / price - 1
    return out


def eva(invested_capital_0: float, nopat: Sequence[float], net_investment: Sequence[float], wacc: float, terminal_growth: float = 0.0,
        net_debt: float = 0.0, shares: Optional[float] = None) -> Dict[str, Any]:
    n = len(nopat)
    if len(net_investment) != n: raise ValueError("nopat and net_investment must have the same length")
    cap = [invested_capital_0]; e = []; pv = []
    for t in range(n):
        e_t = nopat[t] - wacc * cap[-1]; e.append(e_t); pv.append(e_t / (1 + wacc) ** (t + 1)); cap.append(cap[-1] + net_investment[t])
    if wacc <= terminal_growth: raise ValueError("wacc must exceed terminal growth")
    tv = e[-1] * (1 + terminal_growth) / (wacc - terminal_growth); pv_tv = tv / (1 + wacc) ** n
    firm = invested_capital_0 + sum(pv) + pv_tv; equity = firm - net_debt
    out = {"invested_capital": cap, "eva": e, "pv_eva": pv, "mva": sum(pv) + pv_tv, "terminal_eva_value": tv, "pv_terminal": pv_tv, "firm_value": firm, "equity_value": equity,
           "roic": [safe_div(nopat[t], cap[t]) for t in range(n)], "wacc": wacc}
    if shares: out["value_per_share"] = equity / shares
    return out


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out = {}
    if "residual_income" in d: out["residual_income"] = residual_income(**d["residual_income"])
    if "eva" in d: out["eva"] = eva(**d["eva"])
    return out
