"""Merger (M&A) model: deal-level accretion/dilution and a multi-year pro-forma combination.

Deal level follows the Breaking Into Wall Street 'How Equity Value, Enterprise Value and Multiples
Change in an M&A Deal' workbook (reconciled cell-for-cell in tests/test_merger.py); the multi-year
combination follows the structure shared by the BIWS merger model and the Macabacus merger model:
purchase price allocation (goodwill, PP&E / intangible write-ups, deferred taxes), sources & uses,
combined income statement with synergies, foregone interest on cash, new acquisition debt with
scheduled amortisation and fee amortisation, new shares, EPS accretion / (dilution) and a
'pro-forma' EPS that strips one-off integration costs and write-up D&A.
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import Any, Dict, List, Optional, Sequence

from .fin import safe_div


# ============================================================================ deal level
@dataclass
class Company:
    name: str
    share_price: float
    shares: float                      # diluted shares outstanding
    cash: float = 0.0
    debt: float = 0.0
    preferred: float = 0.0
    noncontrolling: float = 0.0
    ebit: float = 0.0
    da: float = 0.0
    net_interest: float = 0.0          # negative = expense (as in the BIWS sheet)
    tax_rate: float = 0.25

    @property
    def equity_value(self): return self.share_price * self.shares
    @property
    def enterprise_value(self): return self.equity_value - self.cash + self.debt + self.preferred + self.noncontrolling
    @property
    def ebitda(self): return self.ebit + self.da
    @property
    def pretax(self): return self.ebit + self.net_interest
    @property
    def net_income(self): return self.pretax * (1 - self.tax_rate)
    @property
    def eps(self): return safe_div(self.net_income, self.shares)

    def summary(self) -> Dict[str, float]:
        return {"equity_value": self.equity_value, "enterprise_value": self.enterprise_value, "ebitda": self.ebitda,
                "pretax_income": self.pretax, "net_income": self.net_income, "eps": self.eps,
                "ev_ebitda": safe_div(self.enterprise_value, self.ebitda), "ev_ebit": safe_div(self.enterprise_value, self.ebit),
                "pe": safe_div(self.equity_value, self.net_income)}


@dataclass
class DealTerms:
    premium: float = 0.30              # offer premium over target share price
    pct_cash: float = 0.0
    pct_debt: float = 0.0              # pct_stock = 1 - cash - debt
    cash_interest_rate: float = 0.03   # foregone interest on cash used (pre-tax)
    debt_interest_rate: float = 0.06   # cost of new acquisition debt (pre-tax)
    synergies_pretax: float = 0.0
    transaction_fees: float = 0.0      # expensed (reduce pre-tax income in year 1)

    @property
    def pct_stock(self): return max(0.0, 1 - self.pct_cash - self.pct_debt)


def deal(acquirer: Company, target: Company, terms: DealTerms) -> Dict[str, Any]:
    purchase_equity = target.equity_value * (1 + terms.premium)
    purchase_ev = purchase_equity - target.cash + target.debt + target.preferred + target.noncontrolling
    offer_price = purchase_equity / target.shares
    exchange_ratio = offer_price / acquirer.share_price
    cash_used, debt_used, stock_used = purchase_equity * terms.pct_cash, purchase_equity * terms.pct_debt, purchase_equity * terms.pct_stock
    new_shares = stock_used / acquirer.share_price
    combined_shares = acquirer.shares + new_shares
    combined_ev = acquirer.enterprise_value + purchase_ev
    combined_equity = acquirer.equity_value + stock_used
    combined_pretax = (acquirer.pretax + target.pretax - cash_used * terms.cash_interest_rate - debt_used * terms.debt_interest_rate
                       + terms.synergies_pretax - terms.transaction_fees)
    combined_ni = combined_pretax * (1 - acquirer.tax_rate)
    combined_eps = combined_ni / combined_shares
    return {
        "acquirer": acquirer.summary(), "target": target.summary(),
        "purchase_equity_value": purchase_equity, "purchase_enterprise_value": purchase_ev, "offer_price_per_share": offer_price,
        "exchange_ratio": exchange_ratio, "purchase_ev_ebitda": safe_div(purchase_ev, target.ebitda),
        "funding": {"cash": cash_used, "debt": debt_used, "stock": stock_used, "pct_cash": terms.pct_cash, "pct_debt": terms.pct_debt,
                    "pct_stock": terms.pct_stock, "after_tax_cost_of_cash": terms.cash_interest_rate * (1 - acquirer.tax_rate),
                    "after_tax_cost_of_debt": terms.debt_interest_rate * (1 - acquirer.tax_rate),
                    "target_earnings_yield": safe_div(target.net_income * (1 - 0) , purchase_equity)},
        "new_shares_issued": new_shares, "combined_shares": combined_shares,
        "combined": {"enterprise_value": combined_ev, "equity_value": combined_equity, "ebitda": acquirer.ebitda + target.ebitda,
                     "ebit": acquirer.ebit + target.ebit, "pretax_income": combined_pretax, "net_income": combined_ni,
                     "ev_ebitda": safe_div(combined_ev, acquirer.ebitda + target.ebitda), "ev_ebit": safe_div(combined_ev, acquirer.ebit + target.ebit),
                     "pe": safe_div(combined_equity, combined_ni), "eps": combined_eps},
        "accretion_dilution": combined_eps - acquirer.eps, "accretion_dilution_pct": safe_div(combined_eps - acquirer.eps, acquirer.eps),
        "ownership": {"acquirer_holders": safe_div(acquirer.shares, combined_shares), "target_holders": safe_div(new_shares, combined_shares)},
    }


def deal_sensitivity(acquirer: Company, target: Company, terms: DealTerms, premiums: Sequence[float], pct_stocks: Sequence[float]) -> Dict[str, Any]:
    """Accretion/(dilution) % across offer premium (rows) x % stock consideration (cols); cash fills the rest."""
    table = []
    for p in premiums:
        row = []
        for s in pct_stocks:
            t = replace(terms, premium=p, pct_cash=max(0.0, 1 - s - terms.pct_debt))
            row.append(deal(acquirer, target, t)["accretion_dilution_pct"])
        table.append(row)
    return {"rows": list(premiums), "cols": list(pct_stocks), "table": table}


# ============================================================================ multi-year pro forma
@dataclass
class Projection:
    """Standalone projections for one company, one value per forecast year."""
    revenue: List[float]
    cogs: List[float]
    opex: List[float]                     # operating expenses excl. D&A
    da: List[float]
    interest_expense: List[float] = field(default_factory=list)
    interest_income: List[float] = field(default_factory=list)
    other_income: List[float] = field(default_factory=list)
    diluted_shares: List[float] = field(default_factory=list)   # acquirer only


@dataclass
class PPA:
    """Purchase price allocation inputs."""
    seller_book_value: float
    seller_existing_goodwill: float = 0.0
    ppe_writeup: float = 0.0
    ppe_writeup_life: int = 10
    intangibles_writeup: float = 0.0
    intangibles_life: int = 10
    seller_dtl_written_down: float = 0.0


@dataclass
class ProFormaInputs:
    years: int
    acquirer: Projection
    target: Projection
    acquirer_price: float
    acquirer_tax_rate: float
    purchase_equity_value: float
    target_cash: float = 0.0
    target_debt_assumed: float = 0.0
    pct_cash: float = 0.0
    pct_debt: float = 0.0
    ppa: PPA = field(default_factory=lambda: PPA(seller_book_value=0.0))
    cash_interest_rate: float = 0.03      # foregone interest on cash used
    debt_interest_rate: float = 0.06
    debt_amort_pct: float = 0.0           # % of original principal repaid per year; balloon at maturity
    debt_maturity: Optional[int] = None
    debt_issuance_fee_pct: float = 0.0    # capitalised, amortised over maturity
    transaction_fees: float = 0.0         # expensed at close (year 1)
    revenue_synergies: Any = 0.0          # scalar or per year
    revenue_synergy_margin: float = 0.3   # contribution margin on revenue synergies
    cost_synergies: Any = 0.0             # run-rate, per year or scalar
    synergy_realization: Any = 1.0        # scalar or per year
    integration_costs: Any = 0.0          # per year, one-off
    refinance_target_debt: bool = False   # True: target debt repaid from new debt (adds to new debt)

    @property
    def pct_stock(self): return max(0.0, 1 - self.pct_cash - self.pct_debt)


def _exp(v, n):
    if isinstance(v, (int, float)): return [float(v)] * n
    v = [float(x) for x in v]
    if len(v) != n: raise ValueError(f"expected {n} values, got {len(v)}")
    return v


def pro_forma(inp: ProFormaInputs) -> Dict[str, Any]:
    n = inp.years; A, T, P = inp.acquirer, inp.target, inp.ppa
    t_rate = inp.acquirer_tax_rate
    # sources & uses
    cash_used = inp.purchase_equity_value * inp.pct_cash
    debt_new = inp.purchase_equity_value * inp.pct_debt + (inp.target_debt_assumed if inp.refinance_target_debt else 0.0)
    stock_used = inp.purchase_equity_value * inp.pct_stock
    fees_cap = debt_new * inp.debt_issuance_fee_pct
    new_shares = stock_used / inp.acquirer_price
    sources = {"cash": cash_used, "new_debt": debt_new, "stock": stock_used, "total": cash_used + debt_new + stock_used}
    uses = {"purchase_equity": inp.purchase_equity_value, "target_debt_refinanced": inp.target_debt_assumed if inp.refinance_target_debt else 0.0,
            "transaction_fees": inp.transaction_fees, "debt_issuance_fees": fees_cap}
    uses["total"] = sum(v for k, v in uses.items() if k != "total")
    cash_used_total = cash_used + inp.transaction_fees + fees_cap  # fees paid from cash
    # purchase price allocation
    new_dtl = (P.ppe_writeup + P.intangibles_writeup) * t_rate
    goodwill = (inp.purchase_equity_value - P.seller_book_value + P.seller_existing_goodwill - P.ppe_writeup - P.intangibles_writeup
                - P.seller_dtl_written_down + new_dtl)
    ppa = {"purchase_equity_value": inp.purchase_equity_value, "less_seller_book_value": -P.seller_book_value,
           "plus_existing_goodwill_written_off": P.seller_existing_goodwill, "allocable_premium": inp.purchase_equity_value - P.seller_book_value + P.seller_existing_goodwill,
           "less_ppe_writeup": -P.ppe_writeup, "less_intangibles_writeup": -P.intangibles_writeup, "less_dtl_written_down": -P.seller_dtl_written_down,
           "plus_new_dtl": new_dtl, "goodwill": goodwill}
    # per-year schedules
    rev_syn = _exp(inp.revenue_synergies, n); cost_syn = _exp(inp.cost_synergies, n); real = _exp(inp.synergy_realization, n); integ = _exp(inp.integration_costs, n)
    maturity = inp.debt_maturity or n
    debt_bal = [0.0] * n; debt_repay = [0.0] * n; debt_int = [0.0] * n; fee_amort = [0.0] * n; intang_amort = [0.0] * n; ppe_dep = [0.0] * n
    bal = debt_new; intang_left = P.intangibles_writeup; ppe_left = P.ppe_writeup
    for t in range(n):
        yr = t + 1
        repay = bal if yr == maturity else min(bal, debt_new * inp.debt_amort_pct)
        debt_int[t] = bal * inp.debt_interest_rate                    # on opening balance (BIWS convention)
        debt_repay[t] = repay; bal -= repay; debt_bal[t] = bal
        fee_amort[t] = fees_cap / maturity if yr <= maturity else 0.0
        ia = min(P.intangibles_writeup / P.intangibles_life if P.intangibles_life else 0.0, intang_left); intang_amort[t] = ia; intang_left -= ia
        pd = min(P.ppe_writeup / P.ppe_writeup_life if P.ppe_writeup_life else 0.0, ppe_left); ppe_dep[t] = pd; ppe_left -= pd
    def g(lst, t): return lst[t] if t < len(lst) else 0.0
    IS: Dict[str, List[float]] = {k: [0.0] * n for k in (
        "Revenue (acquirer)", "Revenue (target)", "Revenue synergies", "Total Revenue", "COGS", "COGS on revenue synergies", "Gross Profit",
        "Opex", "Cost synergies (realised)", "Amortization of new intangibles", "Depreciation of PP&E write-up", "D&A (existing)",
        "Integration costs", "Transaction fees", "Operating Income", "Interest expense (existing)", "Interest income (existing)",
        "Foregone interest on cash", "Interest on new debt", "Amortization of debt issuance fees", "Other income", "Pre-Tax Income",
        "Income Tax", "Net Income", "Acquirer standalone shares", "New shares issued", "Pro forma shares", "Acquirer standalone EPS",
        "Pro forma EPS", "Accretion / (Dilution) $", "Accretion / (Dilution) %", "Adjusted EPS (ex one-offs & write-up D&A)",
        "Adjusted accretion / (dilution) %", "Cash used for deal", "New debt balance")}
    for t in range(n):
        IS["Revenue (acquirer)"][t] = A.revenue[t]; IS["Revenue (target)"][t] = T.revenue[t]; IS["Revenue synergies"][t] = rev_syn[t] * real[t]
        IS["Total Revenue"][t] = A.revenue[t] + T.revenue[t] + IS["Revenue synergies"][t]
        IS["COGS"][t] = -(A.cogs[t] + T.cogs[t]); IS["COGS on revenue synergies"][t] = -IS["Revenue synergies"][t] * (1 - inp.revenue_synergy_margin)
        IS["Gross Profit"][t] = IS["Total Revenue"][t] + IS["COGS"][t] + IS["COGS on revenue synergies"][t]
        IS["Opex"][t] = -(A.opex[t] + T.opex[t]); IS["Cost synergies (realised)"][t] = cost_syn[t] * real[t]
        IS["Amortization of new intangibles"][t] = -intang_amort[t]; IS["Depreciation of PP&E write-up"][t] = -ppe_dep[t]
        IS["D&A (existing)"][t] = -(A.da[t] + T.da[t]); IS["Integration costs"][t] = -integ[t]
        IS["Transaction fees"][t] = -inp.transaction_fees if t == 0 else 0.0
        IS["Operating Income"][t] = (IS["Gross Profit"][t] + IS["Opex"][t] + IS["Cost synergies (realised)"][t] + IS["Amortization of new intangibles"][t]
                                     + IS["Depreciation of PP&E write-up"][t] + IS["D&A (existing)"][t] + IS["Integration costs"][t] + IS["Transaction fees"][t])
        IS["Interest expense (existing)"][t] = -(g(A.interest_expense, t) + (0.0 if inp.refinance_target_debt else g(T.interest_expense, t)))
        IS["Interest income (existing)"][t] = g(A.interest_income, t) + g(T.interest_income, t)
        IS["Foregone interest on cash"][t] = -cash_used_total * inp.cash_interest_rate
        IS["Interest on new debt"][t] = -debt_int[t]; IS["Amortization of debt issuance fees"][t] = -fee_amort[t]
        IS["Other income"][t] = g(A.other_income, t) + g(T.other_income, t)
        IS["Pre-Tax Income"][t] = (IS["Operating Income"][t] + IS["Interest expense (existing)"][t] + IS["Interest income (existing)"][t]
                                   + IS["Foregone interest on cash"][t] + IS["Interest on new debt"][t] + IS["Amortization of debt issuance fees"][t] + IS["Other income"][t])
        IS["Income Tax"][t] = -IS["Pre-Tax Income"][t] * t_rate; IS["Net Income"][t] = IS["Pre-Tax Income"][t] + IS["Income Tax"][t]
        sh = g(A.diluted_shares, t); IS["Acquirer standalone shares"][t] = sh; IS["New shares issued"][t] = new_shares; IS["Pro forma shares"][t] = sh + new_shares
        a_ni = (A.revenue[t] - A.cogs[t] - A.opex[t] - A.da[t] - g(A.interest_expense, t) + g(A.interest_income, t) + g(A.other_income, t)) * (1 - t_rate)
        IS["Acquirer standalone EPS"][t] = safe_div(a_ni, sh); IS["Pro forma EPS"][t] = safe_div(IS["Net Income"][t], sh + new_shares)
        IS["Accretion / (Dilution) $"][t] = IS["Pro forma EPS"][t] - IS["Acquirer standalone EPS"][t]
        IS["Accretion / (Dilution) %"][t] = safe_div(IS["Accretion / (Dilution) $"][t], IS["Acquirer standalone EPS"][t])
        adj = (IS["Pre-Tax Income"][t] - IS["Integration costs"][t] - IS["Transaction fees"][t] - IS["Amortization of new intangibles"][t] - IS["Depreciation of PP&E write-up"][t]) * (1 - t_rate)
        IS["Adjusted EPS (ex one-offs & write-up D&A)"][t] = safe_div(adj, sh + new_shares)
        IS["Adjusted accretion / (dilution) %"][t] = safe_div(IS["Adjusted EPS (ex one-offs & write-up D&A)"][t] - IS["Acquirer standalone EPS"][t], IS["Acquirer standalone EPS"][t])
        IS["Cash used for deal"][t] = cash_used_total; IS["New debt balance"][t] = debt_bal[t]
    breakeven_syn = [(-IS["Accretion / (Dilution) $"][t] * (sh_ + new_shares) / (1 - t_rate)) if IS["Accretion / (Dilution) $"][t] < 0 else 0.0
                     for t, sh_ in enumerate(IS["Acquirer standalone shares"])]
    return {"years": list(range(1, n + 1)), "sources": sources, "uses": uses, "purchase_price_allocation": ppa, "new_shares_issued": new_shares,
            "exchange_ratio_equivalent": safe_div(inp.purchase_equity_value / inp.acquirer_price, 1.0),
            "debt_schedule": {"Opening": [debt_new] + debt_bal[:-1], "Repayment": debt_repay, "Closing": debt_bal, "Interest": debt_int, "Fee amortization": fee_amort},
            "income_statement": IS, "breakeven_pretax_synergies": breakeven_syn}


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    out: Dict[str, Any] = {}
    if "acquirer" in d and "target" in d and "terms" in d:
        acq, tgt, terms = Company(**d["acquirer"]), Company(**d["target"]), DealTerms(**d["terms"])
        out["deal"] = deal(acq, tgt, terms)
        if "premiums" in d and "pct_stocks" in d:
            out["deal_sensitivity"] = deal_sensitivity(acq, tgt, terms, d["premiums"], d["pct_stocks"])
    if "pro_forma" in d:
        pf = dict(d["pro_forma"])
        pf["acquirer"] = Projection(**pf["acquirer"]); pf["target"] = Projection(**pf["target"])
        if "ppa" in pf: pf["ppa"] = PPA(**pf["ppa"])
        out["pro_forma"] = pro_forma(ProFormaInputs(**pf))
    return out
