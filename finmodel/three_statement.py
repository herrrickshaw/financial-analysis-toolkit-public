"""Linked three-statement model, distilled from CFI 'Case Study - Three Statement Model'.

Layout (per year):  Income Statement -> Balance Sheet -> Cash Flow Statement, supported by
working-capital, PP&E (depreciation) and debt/interest schedules.  Forecast years are driven by
ratio assumptions; historical years are taken as given and their implied ratios are reported.

All maths is pure Python; every row reconciles to the CFI workbook (see tests/test_three_statement.py).
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Sequence

from .fin import safe_div


def _expand(v, n: int, name: str) -> List[float]:
    """Accept a scalar (repeat n times) or a list of length n."""
    if isinstance(v, (int, float)):
        return [float(v)] * n
    v = list(v)
    if len(v) != n:
        raise ValueError(f"{name}: expected {n} values, got {len(v)}")
    return [float(x) for x in v]


@dataclass
class HistoricalYear:
    year: int
    # income statement
    revenue: float
    cogs: float
    salaries: float
    rent: float
    da: float
    interest: float
    taxes: float
    # balance sheet
    cash: float
    ar: float
    inventory: float
    ppe: float
    ap: float
    debt: float
    equity_capital: float
    retained_earnings: float
    # cash-flow drivers
    capex: float
    debt_issued: float = 0.0
    equity_issued: float = 0.0


@dataclass
class ForecastAssumptions:
    """Each field is a scalar or a list with one value per forecast year."""
    years: int
    revenue_growth: Any = 0.10
    cogs_pct: Any = 0.40
    salaries_pct: Any = 0.17
    rent: Any = 0.0                 # absolute amount per year
    da_pct_ppe: Any = 0.35          # % of opening PP&E
    interest_pct_debt: Any = 0.10   # % of average debt
    tax_rate: Any = 0.28
    ar_days: Any = 18
    inventory_days: Any = 80
    ap_days: Any = 37
    capex: Any = 0.0
    debt_issued: Any = 0.0
    equity_issued: Any = 0.0
    days_in_period: Any = 365

    def expanded(self) -> Dict[str, List[float]]:
        n = self.years
        out = {}
        for k, v in asdict(self).items():
            if k == "years":
                continue
            out[k] = _expand(v, n, k)
        return out


@dataclass
class ThreeStatementResult:
    years: List[int]
    n_hist: int
    rows: Dict[str, List[float]] = field(default_factory=dict)
    assumptions: Dict[str, List[float]] = field(default_factory=dict)

    @property
    def balanced(self) -> bool:
        return all(abs(x) <= 1.0 for x in self.rows["Balance Sheet Check"])

    def to_dict(self) -> Dict[str, Any]:
        return {"years": self.years, "n_hist": self.n_hist, "rows": self.rows,
                "assumptions": self.assumptions, "balanced": self.balanced}

    def table(self, section: str | None = None, width: int = 12) -> str:
        """Plain-text table of all rows (or one section)."""
        keys = list(self.rows) if section is None else [k for k in self.rows if k in SECTIONS.get(section, ())]
        head = f"{'':38}" + "".join(f"{y:>{width}}" for y in self.years)
        lines = [head]
        for k in keys:
            vals = self.rows[k]
            cells = "".join(f"{v:>{width},.0f}" if abs(v) >= 100 else f"{v:>{width},.3f}" for v in vals)
            lines.append(f"{k:38}{cells}")
        return "\n".join(lines)


SECTIONS = {
    "income_statement": ("Revenue", "Cost of Goods Sold", "Gross Profit", "Salaries and Benefits", "Rent and Overhead",
                          "Depreciation & Amortization", "Interest", "Total Expenses", "Earnings Before Tax", "Taxes",
                          "Net Earnings"),
    "balance_sheet": ("Cash", "Accounts Receivable", "Inventory", "Property & Equipment", "Total Assets",
                       "Accounts Payable", "Debt", "Total Liabilities", "Equity Capital", "Retained Earnings",
                       "Shareholder's Equity", "Total Liabilities & Shareholder's Equity", "Balance Sheet Check"),
    "cash_flow": ("Net Earnings (CF)", "Plus: Depreciation & Amortization", "Less: Changes in Working Capital",
                   "Cash from Operations", "Investments in Property & Equipment", "Cash from Investing",
                   "Issuance (repayment) of debt", "Issuance (repayment) of equity", "Cash from Financing",
                   "Net Increase (decrease) in Cash", "Opening Cash Balance", "Closing Cash Balance"),
    "schedules": ("NWC: Accounts Receivable", "NWC: Inventory", "NWC: Accounts Payable", "Net Working Capital (NWC)",
                   "Change in NWC", "PPE Opening", "Plus Capex", "Less Depreciation", "PPE Closing",
                   "Debt Opening", "Issuance (repayment)", "Debt Closing", "Interest Expense"),
}


def run(historical: Sequence[HistoricalYear], assumptions: ForecastAssumptions,
        ppe_opening0: float | None = None, debt_opening0: float | None = None) -> ThreeStatementResult:
    """Run the model.  `historical` must contain at least one year (the base year).

    ppe_opening0 / debt_opening0 are the opening balances of the FIRST historical year
    (needed only to display the historical schedules; default to closing balance of that year
    adjusted for the year's flows).
    """
    if not historical:
        raise ValueError("at least one historical year is required")
    hist = list(historical)
    A = assumptions.expanded()
    n_h, n_f = len(hist), assumptions.years
    years = [h.year for h in hist] + [hist[-1].year + i + 1 for i in range(n_f)]
    N = n_h + n_f
    R: Dict[str, List[float]] = {k: [0.0] * N for sec in SECTIONS.values() for k in sec}

    # ---------- historical years: taken as given ----------
    for i, h in enumerate(hist):
        R["Revenue"][i] = h.revenue
        R["Cost of Goods Sold"][i] = h.cogs
        R["Salaries and Benefits"][i] = h.salaries
        R["Rent and Overhead"][i] = h.rent
        R["Depreciation & Amortization"][i] = h.da
        R["Interest"][i] = h.interest
        R["Taxes"][i] = h.taxes
        R["Cash"][i] = h.cash
        R["Accounts Receivable"][i] = h.ar
        R["Inventory"][i] = h.inventory
        R["Property & Equipment"][i] = h.ppe
        R["Accounts Payable"][i] = h.ap
        R["Debt"][i] = h.debt
        R["Equity Capital"][i] = h.equity_capital
        R["Retained Earnings"][i] = h.retained_earnings
        R["Plus Capex"][i] = h.capex
        R["Investments in Property & Equipment"][i] = h.capex
        R["Issuance (repayment)"][i] = h.debt_issued
        R["Issuance (repayment) of debt"][i] = h.debt_issued
        R["Issuance (repayment) of equity"][i] = h.equity_issued
        R["Less Depreciation"][i] = h.da
        R["Interest Expense"][i] = h.interest

    if ppe_opening0 is None:
        ppe_opening0 = hist[0].ppe - hist[0].capex + hist[0].da
    if debt_opening0 is None:
        debt_opening0 = hist[0].debt - hist[0].debt_issued

    # ---------- year loop ----------
    prev_nwc = 0.0
    for i in range(N):
        f = i - n_h  # forecast index (>=0 in forecast years)
        is_fc = f >= 0
        # schedules: PP&E
        R["PPE Opening"][i] = ppe_opening0 if i == 0 else R["PPE Closing"][i - 1]
        if is_fc:
            R["Plus Capex"][i] = A["capex"][f]
            R["Investments in Property & Equipment"][i] = A["capex"][f]
            R["Less Depreciation"][i] = R["PPE Opening"][i] * A["da_pct_ppe"][f]
            R["Depreciation & Amortization"][i] = R["Less Depreciation"][i]
        R["PPE Closing"][i] = R["PPE Opening"][i] + R["Plus Capex"][i] - R["Less Depreciation"][i]
        # schedules: debt
        R["Debt Opening"][i] = debt_opening0 if i == 0 else R["Debt Closing"][i - 1]
        if is_fc:
            R["Issuance (repayment)"][i] = A["debt_issued"][f]
            R["Issuance (repayment) of debt"][i] = A["debt_issued"][f]
            R["Issuance (repayment) of equity"][i] = A["equity_issued"][f]
        R["Debt Closing"][i] = R["Debt Opening"][i] + R["Issuance (repayment)"][i]
        if is_fc:
            R["Interest Expense"][i] = (R["Debt Opening"][i] + R["Debt Closing"][i]) / 2 * A["interest_pct_debt"][f]
            R["Interest"][i] = R["Interest Expense"][i]
            # income statement
            R["Revenue"][i] = R["Revenue"][i - 1] * (1 + A["revenue_growth"][f])
            R["Cost of Goods Sold"][i] = R["Revenue"][i] * A["cogs_pct"][f]
            R["Salaries and Benefits"][i] = R["Revenue"][i] * A["salaries_pct"][f]
            R["Rent and Overhead"][i] = A["rent"][f]
        R["Gross Profit"][i] = R["Revenue"][i] - R["Cost of Goods Sold"][i]
        R["Total Expenses"][i] = (R["Salaries and Benefits"][i] + R["Rent and Overhead"][i]
                                  + R["Depreciation & Amortization"][i] + R["Interest"][i])
        R["Earnings Before Tax"][i] = R["Gross Profit"][i] - R["Total Expenses"][i]
        if is_fc:
            R["Taxes"][i] = R["Earnings Before Tax"][i] * A["tax_rate"][f]
        R["Net Earnings"][i] = R["Earnings Before Tax"][i] - R["Taxes"][i]
        # balance sheet (forecast working capital)
        if is_fc:
            d = A["days_in_period"][f]
            R["Accounts Receivable"][i] = R["Revenue"][i] * A["ar_days"][f] / d
            R["Inventory"][i] = R["Cost of Goods Sold"][i] * A["inventory_days"][f] / d
            R["Accounts Payable"][i] = R["Cost of Goods Sold"][i] * A["ap_days"][f] / d
            R["Property & Equipment"][i] = R["PPE Closing"][i]
            R["Debt"][i] = R["Debt Closing"][i]
            R["Equity Capital"][i] = R["Equity Capital"][i - 1] + R["Issuance (repayment) of equity"][i]
            R["Retained Earnings"][i] = R["Retained Earnings"][i - 1] + R["Net Earnings"][i]
        # NWC schedule
        R["NWC: Accounts Receivable"][i] = R["Accounts Receivable"][i]
        R["NWC: Inventory"][i] = R["Inventory"][i]
        R["NWC: Accounts Payable"][i] = R["Accounts Payable"][i]
        nwc = R["Accounts Receivable"][i] + R["Inventory"][i] - R["Accounts Payable"][i]
        R["Net Working Capital (NWC)"][i] = nwc
        R["Change in NWC"][i] = nwc - prev_nwc
        prev_nwc = nwc
        # cash flow statement
        R["Net Earnings (CF)"][i] = R["Net Earnings"][i]
        R["Plus: Depreciation & Amortization"][i] = R["Depreciation & Amortization"][i]
        R["Less: Changes in Working Capital"][i] = R["Change in NWC"][i]
        R["Cash from Operations"][i] = (R["Net Earnings (CF)"][i] + R["Plus: Depreciation & Amortization"][i]
                                        - R["Less: Changes in Working Capital"][i])
        R["Cash from Investing"][i] = R["Investments in Property & Equipment"][i]
        R["Cash from Financing"][i] = R["Issuance (repayment) of debt"][i] + R["Issuance (repayment) of equity"][i]
        R["Net Increase (decrease) in Cash"][i] = (R["Cash from Operations"][i] - R["Cash from Investing"][i]
                                                   + R["Cash from Financing"][i])
        R["Opening Cash Balance"][i] = 0.0 if i == 0 else R["Closing Cash Balance"][i - 1]
        R["Closing Cash Balance"][i] = R["Opening Cash Balance"][i] + R["Net Increase (decrease) in Cash"][i]
        if is_fc:
            R["Cash"][i] = R["Closing Cash Balance"][i]
        # totals + check
        R["Total Assets"][i] = (R["Cash"][i] + R["Accounts Receivable"][i] + R["Inventory"][i]
                                + R["Property & Equipment"][i])
        R["Total Liabilities"][i] = R["Accounts Payable"][i] + R["Debt"][i]
        R["Shareholder's Equity"][i] = R["Equity Capital"][i] + R["Retained Earnings"][i]
        R["Total Liabilities & Shareholder's Equity"][i] = R["Total Liabilities"][i] + R["Shareholder's Equity"][i]
        R["Balance Sheet Check"][i] = R["Total Liabilities & Shareholder's Equity"][i] - R["Total Assets"][i]

    # implied assumptions (historical) + used assumptions (forecast), CFI 'Key Assumptions' block
    asm: Dict[str, List[float]] = {k: [0.0] * N for k in (
        "Revenue Growth", "COGS % Revenue", "Salaries % Revenue", "Rent and Overhead", "D&A % PP&E",
        "Interest % Debt", "Tax Rate", "AR Days", "Inventory Days", "AP Days", "Capex", "Debt Issued", "Equity Issued")}
    for i in range(N):
        d = 365.0 if i < n_h else A["days_in_period"][i - n_h]
        asm["Revenue Growth"][i] = safe_div(R["Revenue"][i], R["Revenue"][i - 1]) - 1 if i > 0 else 0.0
        asm["COGS % Revenue"][i] = safe_div(R["Cost of Goods Sold"][i], R["Revenue"][i])
        asm["Salaries % Revenue"][i] = safe_div(R["Salaries and Benefits"][i], R["Revenue"][i])
        asm["Rent and Overhead"][i] = R["Rent and Overhead"][i]
        asm["D&A % PP&E"][i] = safe_div(R["Depreciation & Amortization"][i], R["Property & Equipment"][i]) if i < n_h else A["da_pct_ppe"][i - n_h]
        asm["Interest % Debt"][i] = safe_div(R["Interest"][i], R["Debt"][i]) if i < n_h else A["interest_pct_debt"][i - n_h]
        asm["Tax Rate"][i] = safe_div(R["Taxes"][i], R["Earnings Before Tax"][i])
        asm["AR Days"][i] = safe_div(R["Accounts Receivable"][i], R["Revenue"][i]) * d
        asm["Inventory Days"][i] = safe_div(R["Inventory"][i], R["Cost of Goods Sold"][i]) * d
        asm["AP Days"][i] = safe_div(R["Accounts Payable"][i], R["Cost of Goods Sold"][i]) * d
        asm["Capex"][i] = R["Plus Capex"][i]
        asm["Debt Issued"][i] = R["Issuance (repayment)"][i]
        asm["Equity Issued"][i] = R["Issuance (repayment) of equity"][i]
    return ThreeStatementResult(years=years, n_hist=n_h, rows=R, assumptions=asm)


def from_dict(d: Dict[str, Any]) -> ThreeStatementResult:
    """Run from a JSON-style dict: {"historical": [...], "forecast": {...}, "ppe_opening0":..., "debt_opening0":...}"""
    hist = [HistoricalYear(**{k: v for k, v in h.items() if not str(k).startswith("_")}) for h in d["historical"]]
    fc = ForecastAssumptions(**{k: v for k, v in d["forecast"].items() if not str(k).startswith("_")})
    return run(hist, fc, d.get("ppe_opening0"), d.get("debt_opening0"))
