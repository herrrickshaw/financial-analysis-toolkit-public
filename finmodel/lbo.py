"""Leveraged buyout model, distilled from A Simple Model's 'Simple LBO (Scenarios and Data Tables)'
workbook, with the cash-sweep and PIK mechanics of the Breaking Into Wall Street LBO examples as options.

Structure (mirrors the workbook, one column per year):
  sources & uses -> closing balance sheet (purchase accounting: goodwill, fees, debt, equity)
  -> income statement (scenario revenue growth, COGS / SG&A % of sales, depreciation waves,
     financing-fee amortisation, tranche interest on average balances, tax)
  -> balance sheet (days-based working capital, PP&E and fee schedules, debt schedules, RE roll)
  -> cash flow (CFO, capex, scheduled amortisation, revolver draw against a minimum cash balance)
  -> exit (EV/EBITDA multiple, net debt bridge) -> sponsor IRR / MOIC (XIRR on dated flows) and
     subordinated-lender IRR (interest + principal + warrant equity) -> scenario x exit-multiple table.

Reconciled cell-for-cell to the workbook's cached values (tests/test_lbo.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import date
from typing import Any, Dict, List, Optional, Sequence

from .fin import to_date, xirr, safe_div


def _exp(v, n: int, name: str = "value") -> List[float]:
    if isinstance(v, (int, float)):
        return [float(v)] * n
    v = [float(x) for x in v]
    if len(v) != n:
        raise ValueError(f"{name}: expected {n} values, got {len(v)}")
    return v


@dataclass
class Tranche:
    """A debt tranche sized as a multiple of closing EBITDA (or an absolute amount)."""
    name: str
    rate: float
    ebitda_multiple: float = 0.0
    amount: Optional[float] = None          # overrides the multiple when given
    amort_years: Optional[int] = None       # straight-line scheduled amortisation; None = bullet
    pik_pct: float = 0.0                    # share of interest paid in kind (accrues to balance)
    sweep_pct: float = 0.0                  # share of excess cash used to prepay this tranche
    warrant_equity_pct: float = 0.0         # equity % handed to this tranche's lenders (mezzanine warrants)


@dataclass
class ClosingBalanceSheet:
    cash: float; ar: float; inventory: float; prepaid: float; ppe: float
    other_assets: float; ap: float; old_debt: float; common_stock: float; retained_earnings: float
    existing_goodwill: float = 0.0


@dataclass
class LBOInputs:
    purchase_price: float                   # enterprise value paid
    closing: ClosingBalanceSheet
    hist_revenue: List[float]               # two historical years (used for COGS%/SG&A% averages)
    hist_cogs: List[float]
    hist_sga: List[float]
    revenue_growth: List[float]             # per forecast year
    sga_pct: Optional[List[float]] = None   # per year; None -> historical average for all years
    cogs_pct: Optional[List[float]] = None  # None -> historical average
    tax_rate: Any = 0.35
    ar_days: Any = 37.0
    inventory_days: Any = 25.0
    ap_days: Any = 33.0
    min_cash: Any = 2000.0
    capex: List[float] = field(default_factory=list)      # per year
    capex_life: Any = 7                     # useful life of each capex wave (years)
    existing_ppe_life: int = 7
    tranches: List[Tranche] = field(default_factory=list)
    revolver_rate: float = 0.08
    revolver_interest: bool = False         # the ASM sheet leaves revolver interest blank; True computes it (iterative)
    transaction_expenses: float = 0.0
    financing_fees: float = 0.0
    fee_amort_years: Optional[int] = None   # None -> the first amortising tranche's years
    exit_multiple: float = 7.0
    closing_date: Any = "2022-12-31"
    interest_on: bool = True
    closing_ebitda: Optional[float] = None  # defaults to last historical EBITDA

    @property
    def years(self) -> int:
        return len(self.revenue_growth)


def run(inp: LBOInputs) -> Dict[str, Any]:
    n = inp.years
    cb = inp.closing
    hist_ebitda = [inp.hist_revenue[i] - inp.hist_cogs[i] - inp.hist_sga[i] for i in range(len(inp.hist_revenue))]
    ebitda0 = inp.closing_ebitda if inp.closing_ebitda is not None else hist_ebitda[-1]

    # ---------------- sources & uses
    tr_amounts = [t.amount if t.amount is not None else ebitda0 * t.ebitda_multiple for t in inp.tranches]
    total_uses = inp.purchase_price + inp.transaction_expenses + inp.financing_fees
    equity = total_uses - sum(tr_amounts)
    seller_proceeds = total_uses - cb.old_debt - inp.transaction_expenses - inp.financing_fees
    book_equity = cb.common_stock + cb.retained_earnings
    goodwill = seller_proceeds - book_equity + cb.existing_goodwill
    sources = {"equity": equity, **{t.name: a for t, a in zip(inp.tranches, tr_amounts)}, "total": total_uses}
    uses = {"seller_proceeds": seller_proceeds, "old_debt_repaid": cb.old_debt, "transaction_expenses": inp.transaction_expenses,
            "financing_fees": inp.financing_fees, "total": total_uses}

    # ---------------- closing balance sheet (col E of the workbook)
    cash0 = cb.cash + equity + sum(tr_amounts) - seller_proceeds - cb.old_debt - inp.transaction_expenses - inp.financing_fees
    fee_asset0 = inp.financing_fees
    close = {"cash": cash0, "ar": cb.ar, "inventory": cb.inventory, "prepaid": cb.prepaid, "ppe": cb.ppe,
             "fee_asset": fee_asset0, "goodwill": goodwill, "other_assets": cb.other_assets, "ap": cb.ap, "old_debt": 0.0,
             "revolver": 0.0, "common_stock": equity, "retained_earnings": -inp.transaction_expenses}
    for t, a in zip(inp.tranches, tr_amounts):
        close[t.name] = a
    ta = cash0 + cb.ar + cb.inventory + cb.prepaid + cb.ppe + fee_asset0 + goodwill + cb.other_assets
    tl = cb.ap + sum(tr_amounts)
    close["check"] = ta - (tl + equity - inp.transaction_expenses)

    # ---------------- assumptions
    A = {
        "growth": _exp(inp.revenue_growth, n, "revenue_growth"),
        "cogs_pct": _exp(inp.cogs_pct if inp.cogs_pct is not None else sum(c / r for c, r in zip(inp.hist_cogs, inp.hist_revenue)) / len(inp.hist_revenue), n),
        "sga_pct": _exp(inp.sga_pct if inp.sga_pct is not None else sum(s / r for s, r in zip(inp.hist_sga, inp.hist_revenue)) / len(inp.hist_revenue), n),
        "tax": _exp(inp.tax_rate, n), "ar_days": _exp(inp.ar_days, n), "inv_days": _exp(inp.inventory_days, n),
        "ap_days": _exp(inp.ap_days, n), "min_cash": _exp(inp.min_cash, n),
        "capex": _exp(inp.capex if inp.capex else 0.0, n), "life": _exp(inp.capex_life, n),
    }
    fee_years = inp.fee_amort_years
    if fee_years is None:
        fee_years = next((t.amort_years for t in inp.tranches if t.amort_years), n)

    # ---------------- depreciation waves & fee amortisation (independent of cash)
    dep = [0.0] * n; dep_detail = []
    base = [cb.ppe / inp.existing_ppe_life if (t + 1) <= inp.existing_ppe_life else 0.0 for t in range(n)]
    dep_detail.append(("existing PP&E", base))
    for k in range(n):                       # wave k starts depreciating in year k
        life = A["life"][k]
        wave = [A["capex"][k] / life if 0 <= t - k < life else 0.0 for t in range(n)]
        dep_detail.append((f"capex year {k+1}", wave))
    for _, w in dep_detail:
        for t in range(n): dep[t] += w[t]
    amort = [fee_asset0 / fee_years if t < fee_years else 0.0 for t in range(n)]

    # ---------------- year loop (iterate for revolver-interest / sweep circularity)
    revolver_int = [0.0] * n
    result: Dict[str, Any] = {}
    for _iteration in range(60):
        rev = [0.0] * n; cogs = [0.0] * n; sga = [0.0] * n; ebitda = [0.0] * n; ebit = [0.0] * n
        interest = [0.0] * n; ebt = [0.0] * n; tax = [0.0] * n; ni = [0.0] * n
        ar = [0.0] * n; inv = [0.0] * n; ap = [0.0] * n; ppe = [0.0] * n; fee = [0.0] * n; cash = [0.0] * n
        re_ = [0.0] * n; revolver = [0.0] * n; cfo = [0.0] * n; cfi = [0.0] * n; cff = [0.0] * n
        tranche_rows: Dict[str, Dict[str, List[float]]] = {t.name: {"begin": [0.0] * n, "sched": [0.0] * n, "sweep": [0.0] * n,
                                                                    "pik": [0.0] * n, "end": [0.0] * n, "cash_interest": [0.0] * n} for t in inp.tranches}
        prev_rev, prev_ar, prev_inv, prev_ap, prev_ppe, prev_fee = inp.hist_revenue[-1], cb.ar, cb.inventory, cb.ap, cb.ppe, fee_asset0
        prev_cash, prev_re, prev_rev_bal = cash0, close["retained_earnings"], 0.0
        prev_bal = {t.name: a for t, a in zip(inp.tranches, tr_amounts)}
        for t in range(n):
            rev[t] = prev_rev * (1 + A["growth"][t]); cogs[t] = rev[t] * A["cogs_pct"][t]; sga[t] = rev[t] * A["sga_pct"][t]
            ebitda[t] = rev[t] - cogs[t] - sga[t]; ebit[t] = ebitda[t] - dep[t] - amort[t]
            # tranche schedules: scheduled amortisation + PIK, interest on average balance (sweep applied after cash known)
            tot_int = revolver_int[t] if inp.revolver_interest else 0.0
            for tr, amt in zip(inp.tranches, tr_amounts):
                row = tranche_rows[tr.name]; b0 = prev_bal[tr.name]
                sched = amt / tr.amort_years if (tr.amort_years and (t + 1) <= tr.amort_years) else 0.0
                sched = min(sched, b0)
                pik = b0 * tr.rate * tr.pik_pct
                sweep = row["sweep"][t]  # from previous iteration
                end = b0 - sched - sweep + pik
                cash_int = (b0 + end) / 2 * tr.rate * (1 - tr.pik_pct)
                row["begin"][t], row["sched"][t], row["pik"][t], row["end"][t], row["cash_interest"][t] = b0, sched, pik, end, cash_int
                tot_int += cash_int + pik
            interest[t] = tot_int if inp.interest_on else 0.0
            ebt[t] = ebit[t] - interest[t]; tax[t] = ebt[t] * A["tax"][t]; ni[t] = ebt[t] - tax[t]
            ar[t] = rev[t] / 365 * A["ar_days"][t]; inv[t] = cogs[t] / 365 * A["inv_days"][t]; ap[t] = cogs[t] / 365 * A["ap_days"][t]
            ppe[t] = prev_ppe + A["capex"][t] - dep[t]; fee[t] = prev_fee - amort[t]
            pik_total = sum(tranche_rows[tr.name]["pik"][t] for tr in inp.tranches)
            cfo[t] = ni[t] + dep[t] + amort[t] + pik_total + (prev_ar - ar[t]) + (prev_inv - inv[t]) + (ap[t] - prev_ap)
            cfi[t] = -A["capex"][t]
            sched_total = sum(tranche_rows[tr.name]["sched"][t] for tr in inp.tranches)
            # cash available before revolver and sweep
            avail = prev_cash + cfo[t] + cfi[t] - sched_total - A["min_cash"][t]
            # cash sweep: excess cash (above minimum) prepays tranches with sweep_pct, in order
            excess = max(avail, 0.0)
            for tr in inp.tranches:
                row = tranche_rows[tr.name]
                if tr.sweep_pct > 0:
                    pay = min(excess * tr.sweep_pct, row["begin"][t] - row["sched"][t] + row["pik"][t])
                    pay = max(pay, 0.0)
                    if abs(pay - row["sweep"][t]) > 1e-9:
                        row["sweep"][t] = pay
                    excess -= pay; avail -= pay
                    row["end"][t] = row["begin"][t] - row["sched"][t] - row["sweep"][t] + row["pik"][t]
            revolver[t] = max(0.0, prev_rev_bal - avail)
            sweep_total = sum(tranche_rows[tr.name]["sweep"][t] for tr in inp.tranches)
            cff[t] = (revolver[t] - prev_rev_bal) - sched_total - sweep_total
            cash[t] = prev_cash + cfo[t] + cfi[t] + cff[t]
            re_[t] = prev_re + ni[t]
            for tr in inp.tranches: prev_bal[tr.name] = tranche_rows[tr.name]["end"][t]
            prev_rev, prev_ar, prev_inv, prev_ap, prev_ppe, prev_fee, prev_cash, prev_re, prev_rev_bal = rev[t], ar[t], inv[t], ap[t], ppe[t], fee[t], cash[t], re_[t], revolver[t]
        new_rev_int = [((revolver[t - 1] if t else 0.0) + revolver[t]) / 2 * inp.revolver_rate for t in range(n)]
        converged = all(abs(a - b) < 1e-9 for a, b in zip(new_rev_int, revolver_int))
        revolver_int = new_rev_int
        sweeps_stable = not any(tr.sweep_pct > 0 for tr in inp.tranches) or _iteration > 0 and result.get("_sweep_sig") == [tranche_rows[tr.name]["sweep"] for tr in inp.tranches]
        result["_sweep_sig"] = [list(tranche_rows[tr.name]["sweep"]) for tr in inp.tranches]
        if converged and (sweeps_stable or not any(tr.sweep_pct > 0 for tr in inp.tranches)):
            break
    result.pop("_sweep_sig", None)

    # ---------------- statements
    debt_total = [revolver[t] + sum(tranche_rows[tr.name]["end"][t] for tr in inp.tranches) for t in range(n)]
    total_assets = [cash[t] + ar[t] + inv[t] + cb.prepaid + ppe[t] + fee[t] + goodwill + cb.other_assets for t in range(n)]
    total_liab = [ap[t] + debt_total[t] for t in range(n)]
    total_eq = [equity + re_[t] for t in range(n)]
    IS = {"Revenue": rev, "Growth %": A["growth"], "COGS": cogs, "Gross Profit": [rev[t] - cogs[t] for t in range(n)], "SG&A": sga,
          "EBITDA": ebitda, "EBITDA margin": [safe_div(ebitda[t], rev[t]) for t in range(n)], "Depreciation": dep, "Amortization": amort,
          "EBIT": ebit, "Interest Expense": interest, "Pretax Income": ebt, "Income Tax": tax, "Net Income": ni}
    BS = {"Cash": cash, "Accounts Receivable": ar, "Inventory": inv, "Prepaid Expenses": [cb.prepaid] * n, "PP&E": ppe,
          "Capitalized Financing Fee": fee, "Goodwill": [goodwill] * n, "Other Assets": [cb.other_assets] * n, "Total Assets": total_assets,
          "Accounts Payable": ap, "Revolver": revolver, **{tr.name: tranche_rows[tr.name]["end"] for tr in inp.tranches},
          "Total Liabilities": total_liab, "Common Stock": [equity] * n, "Retained Earnings": re_, "Total Equity": total_eq,
          "Check": [total_assets[t] - total_liab[t] - total_eq[t] for t in range(n)]}
    CF = {"Net Income": ni, "Depreciation": dep, "Amortization": amort, "PIK interest": [sum(tranche_rows[tr.name]["pik"][t] for tr in inp.tranches) for t in range(n)],
          "Change in AR": [(cb.ar if t == 0 else ar[t - 1]) - ar[t] for t in range(n)],
          "Change in Inventory": [(cb.inventory if t == 0 else inv[t - 1]) - inv[t] for t in range(n)],
          "Change in AP": [ap[t] - (cb.ap if t == 0 else ap[t - 1]) for t in range(n)],
          "Cash from Operations": cfo, "Capex": cfi, "Cash from Investing": cfi,
          "Revolver draw (repay)": [revolver[t] - (revolver[t - 1] if t else 0.0) for t in range(n)],
          **{f"{tr.name} repayment": [-(tranche_rows[tr.name]["sched"][t] + tranche_rows[tr.name]["sweep"][t]) for t in range(n)] for tr in inp.tranches},
          "Cash from Financing": cff, "Net Cash Flow": [cfo[t] + cfi[t] + cff[t] for t in range(n)],
          "Beginning Cash": [cash0 if t == 0 else cash[t - 1] for t in range(n)], "Ending Cash": cash}
    debt = {tr.name: {"Beginning": tranche_rows[tr.name]["begin"], "Scheduled amortization": tranche_rows[tr.name]["sched"],
                      "Cash sweep": tranche_rows[tr.name]["sweep"], "PIK accrual": tranche_rows[tr.name]["pik"], "Ending": tranche_rows[tr.name]["end"],
                      "Cash interest": tranche_rows[tr.name]["cash_interest"]} for tr in inp.tranches}
    debt["Revolver"] = {"Ending": revolver, "Interest": revolver_int if inp.revolver_interest else [0.0] * n}

    # ---------------- exit & returns
    d0 = to_date(inp.closing_date)
    dates = [d0] + [date(d0.year + t + 1, d0.month, d0.day) for t in range(n)]
    ev_exit = inp.exit_multiple * ebitda[-1]
    equity_exit = ev_exit - debt_total[-1] + cash[-1]
    warrant_pct = sum(tr.warrant_equity_pct for tr in inp.tranches)
    sponsor_pct = 1 - warrant_pct
    sponsor_flows = [-equity] + [0.0] * (n - 1) + [sponsor_pct * equity_exit]
    try: sponsor_irr = xirr(sponsor_flows, dates)
    except ValueError: sponsor_irr = float("nan")
    returns = {"exit_ebitda": ebitda[-1], "exit_multiple": inp.exit_multiple, "exit_enterprise_value": ev_exit, "less_debt": -debt_total[-1],
               "plus_cash": cash[-1], "exit_equity_value": equity_exit, "sponsor_equity_pct": sponsor_pct,
               "sponsor": {"flows": sponsor_flows, "dates": [d.isoformat() for d in dates], "irr": sponsor_irr,
                           "moic": safe_div(sum(sponsor_flows[1:]), equity)}}
    for tr, amt in zip(inp.tranches, tr_amounts):
        row = tranche_rows[tr.name]
        flows = [-amt] + [row["cash_interest"][t] + row["sched"][t] + row["sweep"][t] for t in range(n)]
        flows[-1] += row["end"][-1] + tr.warrant_equity_pct * equity_exit
        try: irr_ = xirr(flows, dates)
        except ValueError: irr_ = float("nan")
        returns[tr.name] = {"flows": flows, "irr": irr_, "moic": safe_div(sum(flows[1:]), amt)}
    entry = {"ebitda": ebitda0, "purchase_price": inp.purchase_price, "ev_ebitda": safe_div(inp.purchase_price, ebitda0),
             "debt": sum(tr_amounts), "debt_ebitda": safe_div(sum(tr_amounts), ebitda0), "equity_pct": safe_div(equity, total_uses)}
    return {**result, "years": list(range(1, n + 1)), "entry": entry, "sources": sources, "uses": uses, "closing_balance_sheet": close,
            "assumptions": A, "depreciation_detail": dep_detail, "income_statement": IS, "balance_sheet": BS, "cash_flow": CF,
            "debt_schedule": debt, "returns": returns, "balanced": all(abs(x) < 1e-6 for x in BS["Check"])}


def sensitivity(inp: LBOInputs, scenarios: Dict[str, Sequence[float]], exit_multiples: Sequence[float],
                metric: str = "sponsor") -> Dict[str, Any]:
    """IRR table: rows = revenue-growth scenarios, cols = exit multiples (the workbook's data tables)."""
    table = {}
    for name, growth in scenarios.items():
        row = []
        for m in exit_multiples:
            r = run(replace(inp, revenue_growth=list(growth), exit_multiple=m))
            row.append(r["returns"][metric]["irr"] if metric == "sponsor" else r["returns"][metric]["irr"])
        table[name] = row
    return {"exit_multiples": list(exit_multiples), "metric": metric, "table": table}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    d["closing"] = ClosingBalanceSheet(**d["closing"])
    d["tranches"] = [Tranche(**t) for t in d.get("tranches", [])]
    scen = d.pop("scenarios", None); mults = d.pop("exit_multiples", None)
    inp = LBOInputs(**d)
    out = run(inp)
    if scen and mults:
        out["sensitivity"] = sensitivity(inp, scen, mults)
    return out
