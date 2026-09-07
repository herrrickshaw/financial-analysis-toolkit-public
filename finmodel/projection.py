"""Bottom-up financial projection, distilled from CFI 'Financial Projection Template'.

Base year is built from monthly detail (products x units, employees x hours, opex by category);
later years roll forward from growth assumptions.  Output: sales, payroll, opex schedules ->
income statement -> balance sheet (working capital, PP&E, debt schedules) -> cash flow -> ratios.

Deviations from the CFI workbook (all are corrections of template bugs, see README):
  * forecast wages include hours/day (template omits the factor);
  * D&A rate = base D&A / opening PP&E (template points at interest / debt by mistake);
  * bonuses are deducted before tax (template shows but never deducts them);
  * prepaid and accrued expenses are part of working capital (otherwise the BS cannot balance);
  * wage expense defaults to GROSS wages (template books net pay); set wage_expense_basis="net_pay" to match.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date
from typing import Any, Dict, List, Optional

from .fin import networkdays, eomonth, safe_div, to_date
from . import ratios as _ratios


@dataclass
class Product:
    name: str
    price: float                 # sales price per unit (base year)
    cogs_per_unit: float
    units_by_month: List[float]  # 12 values, base year
    unit_growth: List[float]     # one per forecast year
    price_growth: Any = 0.0      # scalar or list per forecast year
    cogs_growth: Any = 0.0


@dataclass
class Employee:
    name: str
    type: str                    # key of ProjectionInputs.employee_types
    hourly_wage: float
    hours_per_month: Optional[List[float]] = None   # override (12 values); default = hours/day * workdays for FT


@dataclass
class EmployeeType:
    hours_per_day: float = 8.0
    benefits: bool = True        # insurance + pension deducted
    bonus: bool = True           # shares the bonus pool


@dataclass
class ProjectionInputs:
    base_year: int
    forecast_years: int
    products: List[Product]
    employees: List[Employee]
    opex_by_month: Dict[str, List[float]]          # category -> 12 monthly values (base year)
    opex_growth: Dict[str, Any]                    # category -> scalar or list per forecast year
    employee_types: Dict[str, EmployeeType] = field(default_factory=lambda: {
        "Full-Time": EmployeeType(8, True, True), "Part-Time": EmployeeType(0, False, False),
        "Contractors": EmployeeType(0, False, False)})
    headcount_growth: Dict[str, Any] = field(default_factory=dict)   # type -> scalar/list per forecast year
    wage_growth: Dict[str, Any] = field(default_factory=dict)        # type -> scalar/list
    deductions: Dict[str, float] = field(default_factory=lambda: {"federal_tax": 0.094, "state_tax": 0.036,
                                                                   "insurance": 0.016, "pension": 0.045})
    bonus_pct_ebit: float = 0.10
    wage_expense_basis: str = "gross"           # "gross" | "net_pay"
    tax_rate: float = 0.20
    holidays: List[str] = field(default_factory=list)
    # opening balance sheet (start of base year)
    opening_cash: float = 0.0
    opening_ar: float = 0.0
    opening_prepaid: float = 0.0
    opening_inventory: float = 0.0
    opening_ppe: float = 0.0
    opening_ap: float = 0.0
    opening_accrued: float = 0.0
    opening_debt: float = 0.0
    opening_equity_capital: float = 0.0
    opening_retained_earnings: float = 0.0
    # base-year flows / rates
    base_capex_by_month: List[float] = field(default_factory=lambda: [0.0] * 12)
    base_debt_issued_by_month: List[float] = field(default_factory=lambda: [0.0] * 12)
    base_equity_issued_by_month: List[float] = field(default_factory=lambda: [0.0] * 12)
    da_pct_ppe: Optional[float] = None          # default: base-year D&A (opex 'Depreciation & Amortization') / opening PP&E
    interest_pct_debt: Optional[float] = None   # default: base-year interest / opening debt
    base_interest_by_month: List[float] = field(default_factory=lambda: [0.0] * 12)
    ar_days: Optional[float] = None             # default: derived from base-year closing AR
    inventory_days: Optional[float] = None
    ap_days: Optional[float] = None
    prepaid_growth: Any = 0.02
    accrued_growth: Any = 0.01
    forecast_capex: Any = None                  # default: base-year capex
    forecast_debt_issued: Any = 0.0
    forecast_equity_issued: Any = 0.0
    da_category: str = "Depreciation & Amortization"


def _exp(v, n: int, default=0.0) -> List[float]:
    if v is None:
        v = default
    if isinstance(v, (int, float)):
        return [float(v)] * n
    v = [float(x) for x in v]
    if len(v) != n:
        raise ValueError(f"expected {n} values, got {len(v)}")
    return v


def _months(year: int):
    return [(date(year, m, 1), eomonth(date(year, m, 1))) for m in range(1, 13)]


def run(inp: ProjectionInputs) -> Dict[str, Any]:
    n_f = inp.forecast_years
    years = [inp.base_year + i for i in range(n_f + 1)]
    N = n_f + 1
    hol = [to_date(h) for h in inp.holidays]
    workdays = [networkdays(date(y, 1, 1), date(y, 12, 31), hol) for y in years]
    month_workdays = [networkdays(s, e, hol) for s, e in _months(inp.base_year)]

    # ---------------- sales ----------------
    sales: Dict[str, Dict[str, List[float]]] = {}
    for p in sales_products(inp):
        pass
    for p in inp.products:
        ug = _exp(p.unit_growth, n_f); pg = _exp(p.price_growth, n_f); cg = _exp(p.cogs_growth, n_f)
        units = [sum(p.units_by_month)]; price = [p.price]; cpu = [p.cogs_per_unit]
        for f in range(n_f):
            units.append(units[-1] * (1 + ug[f])); price.append(price[-1] * (1 + pg[f])); cpu.append(cpu[-1] * (1 + cg[f]))
        rev = [price[i] * units[i] for i in range(N)]
        cogs = [cpu[i] * units[i] for i in range(N)]
        sales[p.name] = {"price": price, "units": units, "revenue": rev, "cogs_per_unit": cpu,
                         "cogs": cogs, "gross_margin": [rev[i] - cogs[i] for i in range(N)]}
    revenue = [sum(s["revenue"][i] for s in sales.values()) for i in range(N)]
    cogs = [sum(s["cogs"][i] for s in sales.values()) for i in range(N)]

    # ---------------- payroll ----------------
    types = inp.employee_types
    base_hours = {t: 0.0 for t in types}; base_wages = {t: 0.0 for t in types}; heads = {t: 0 for t in types}
    for e in inp.employees:
        et = types[e.type]
        if e.hours_per_month is not None:
            hrs = list(e.hours_per_month)
        else:
            hrs = [et.hours_per_day * wd for wd in month_workdays]
        base_hours[e.type] += sum(hrs); base_wages[e.type] += sum(h * e.hourly_wage for h in hrs); heads[e.type] += 1
    payroll: Dict[str, Any] = {"types": {}}
    wages_total = [0.0] * N; ins_base = [0.0] * N  # insurance/pension base (benefit types)
    bonus_base_by_type = {}
    for t, et in types.items():
        hg = _exp(inp.headcount_growth.get(t), n_f); wg = _exp(inp.wage_growth.get(t), n_f)
        hc = [float(heads[t])]; avg_wage = [safe_div(base_wages[t], base_hours[t])]
        hrs_per_head = safe_div(base_hours[t], heads[t])
        wages = [base_wages[t]]
        for f in range(n_f):
            hc.append(hc[-1] * (1 + hg[f])); avg_wage.append(avg_wage[-1] * (1 + wg[f]))
            wages.append(avg_wage[-1] * hrs_per_head * hc[-1] * workdays[f + 1] / workdays[0] if workdays[0] else 0.0)
        payroll["types"][t] = {"headcount": hc, "avg_hourly_wage": avg_wage, "wages": wages,
                               "hours_per_head_base": hrs_per_head}
        for i in range(N):
            wages_total[i] += wages[i]
            if et.benefits:
                ins_base[i] += wages[i]
        if et.bonus:
            bonus_base_by_type[t] = wages
    d = inp.deductions
    fed = [w * d.get("federal_tax", 0) for w in wages_total]
    state = [w * d.get("state_tax", 0) for w in wages_total]
    ins = [w * d.get("insurance", 0) for w in ins_base]
    pen = [w * d.get("pension", 0) for w in ins_base]
    net_pay = [wages_total[i] - fed[i] - state[i] - ins[i] - pen[i] for i in range(N)]
    payroll.update({"work_days": workdays, "total_wages": wages_total, "federal_tax": fed, "state_tax": state,
                    "insurance": ins, "pension": pen, "net_pay": net_pay})
    wage_expense = net_pay if inp.wage_expense_basis == "net_pay" else wages_total

    # ---------------- operating expenses ----------------
    opex: Dict[str, List[float]] = {}
    for cat, months in inp.opex_by_month.items():
        if cat == inp.da_category:
            continue
        g = _exp(inp.opex_growth.get(cat), n_f)
        vals = [sum(months)]
        for f in range(n_f):
            vals.append(vals[-1] * (1 + g[f]))
        opex[cat] = vals
    base_da = sum(inp.opex_by_month.get(inp.da_category, [0.0] * 12))
    da_rate = inp.da_pct_ppe if inp.da_pct_ppe is not None else safe_div(base_da, inp.opening_ppe)
    base_interest = sum(inp.base_interest_by_month)
    int_rate = inp.interest_pct_debt if inp.interest_pct_debt is not None else safe_div(base_interest, inp.opening_debt)

    # ---------------- schedules + statements ----------------
    capex = [sum(inp.base_capex_by_month)] + _exp(inp.forecast_capex, n_f, default=sum(inp.base_capex_by_month))
    debt_iss = [sum(inp.base_debt_issued_by_month)] + _exp(inp.forecast_debt_issued, n_f)
    eq_iss = [sum(inp.base_equity_issued_by_month)] + _exp(inp.forecast_equity_issued, n_f)
    pre_g = _exp(inp.prepaid_growth, n_f); acc_g = _exp(inp.accrued_growth, n_f)

    ppe_open = [0.0] * N; da = [0.0] * N; ppe_close = [0.0] * N
    debt_open = [0.0] * N; debt_close = [0.0] * N; interest = [0.0] * N
    for i in range(N):
        ppe_open[i] = inp.opening_ppe if i == 0 else ppe_close[i - 1]
        da[i] = base_da if i == 0 else ppe_open[i] * da_rate
        ppe_close[i] = ppe_open[i] + capex[i] - da[i]
        debt_open[i] = inp.opening_debt if i == 0 else debt_close[i - 1]
        debt_close[i] = debt_open[i] + debt_iss[i]
        interest[i] = base_interest if i == 0 else debt_open[i] * int_rate

    IS: Dict[str, List[float]] = {"Revenue": revenue, "COGS": cogs, "Gross Margin": [revenue[i] - cogs[i] for i in range(N)]}
    IS["Operating Expenses"] = {}  # type: ignore[assignment]
    opex_lines: Dict[str, List[float]] = dict(opex)
    opex_lines["Depreciation & Amortization"] = da
    opex_lines["Wages and Benefits"] = wage_expense
    total_opex = [sum(v[i] for v in opex_lines.values()) for i in range(N)]
    ebit = [IS["Gross Margin"][i] - total_opex[i] for i in range(N)]
    bonus_pool = [max(ebit[i], 0.0) * inp.bonus_pct_ebit for i in range(N)]
    ebt = [ebit[i] - bonus_pool[i] - interest[i] for i in range(N)]
    taxes = [ebt[i] * inp.tax_rate if ebt[i] > 0 else 0.0 for i in range(N)]
    ni = [ebt[i] - taxes[i] for i in range(N)]
    IS = {"Revenue": revenue, "COGS": cogs, "Gross Margin": IS["Gross Margin"], **opex_lines,
          "Total Operating Expenses": total_opex, "EBIT": ebit, "Employee Bonuses": bonus_pool,
          "Interest Expense": interest, "EBT": ebt, "Income Taxes": taxes, "Net Earnings": ni}
    payroll["bonus_pool"] = bonus_pool

    # balance sheet
    ar_days = inp.ar_days; inv_days = inp.inventory_days; ap_days = inp.ap_days
    ar = [0.0] * N; inv = [0.0] * N; ap = [0.0] * N; pre = [0.0] * N; acc = [0.0] * N
    # base year closing: opening balances rolled by days assumptions if provided, else held at opening
    ar[0] = revenue[0] * ar_days / 365 if ar_days is not None else inp.opening_ar
    inv[0] = cogs[0] * inv_days / 365 if inv_days is not None else inp.opening_inventory
    ap[0] = cogs[0] * ap_days / 365 if ap_days is not None else inp.opening_ap
    pre[0] = inp.opening_prepaid; acc[0] = inp.opening_accrued
    ar_days_eff = ar_days if ar_days is not None else safe_div(ar[0], revenue[0]) * 365
    inv_days_eff = inv_days if inv_days is not None else safe_div(inv[0], cogs[0]) * 365
    ap_days_eff = ap_days if ap_days is not None else safe_div(ap[0], cogs[0]) * 365
    for i in range(1, N):
        ar[i] = revenue[i] * ar_days_eff / 365; inv[i] = cogs[i] * inv_days_eff / 365; ap[i] = cogs[i] * ap_days_eff / 365
        pre[i] = pre[i - 1] * (1 + pre_g[i - 1]); acc[i] = acc[i - 1] * (1 + acc_g[i - 1])
    nwc = [ar[i] + inv[i] + pre[i] - ap[i] - acc[i] for i in range(N)]
    nwc_open = inp.opening_ar + inp.opening_inventory + inp.opening_prepaid - inp.opening_ap - inp.opening_accrued
    d_nwc = [nwc[i] - (nwc_open if i == 0 else nwc[i - 1]) for i in range(N)]

    cfo = [ni[i] + da[i] - d_nwc[i] for i in range(N)]
    cfi = capex
    cff = [debt_iss[i] + eq_iss[i] for i in range(N)]
    net_cash = [cfo[i] - cfi[i] + cff[i] for i in range(N)]
    cash_open = [0.0] * N; cash_close = [0.0] * N
    for i in range(N):
        cash_open[i] = inp.opening_cash if i == 0 else cash_close[i - 1]
        cash_close[i] = cash_open[i] + net_cash[i]
    eq_cap = [0.0] * N; re = [0.0] * N
    for i in range(N):
        eq_cap[i] = (inp.opening_equity_capital if i == 0 else eq_cap[i - 1]) + eq_iss[i]
        re[i] = (inp.opening_retained_earnings if i == 0 else re[i - 1]) + ni[i]
    tca = [cash_close[i] + ar[i] + pre[i] + inv[i] for i in range(N)]
    ta = [tca[i] + ppe_close[i] for i in range(N)]
    tcl = [ap[i] + acc[i] for i in range(N)]
    tl = [tcl[i] + debt_close[i] for i in range(N)]
    eq = [eq_cap[i] + re[i] for i in range(N)]
    BS = {"Cash": cash_close, "Accounts Receivable": ar, "Prepaid expenses": pre, "Inventory": inv,
          "Total current assets": tca, "Property & Equipment": ppe_close, "Total Assets": ta,
          "Accounts Payable": ap, "Accrued expenses": acc, "Total current liabilities": tcl,
          "Long-term debt": debt_close, "Total Liabilities": tl, "Equity Capital": eq_cap,
          "Retained Earnings": re, "Shareholder's Equity": eq,
          "Total Liabilities & Shareholder's Equity": [tl[i] + eq[i] for i in range(N)],
          "Check": [tl[i] + eq[i] - ta[i] for i in range(N)]}
    CF = {"Net Earnings": ni, "Plus: Depreciation & Amortization": da, "Less: Changes in Working Capital": d_nwc,
          "Cash from Operations": cfo, "Investments in Property & Equipment": cfi, "Cash from Investing": cfi,
          "Issuance (repayment) of debt": debt_iss, "Issuance (repayment) of equity": eq_iss,
          "Cash from Financing": cff, "Net Increase (decrease) in Cash": net_cash,
          "Opening Cash Balance": cash_open, "Closing Cash Balance": cash_close}
    schedules = {"working_capital": {"AR": ar, "Inventory": inv, "Prepaid": pre, "AP": ap, "Accrued": acc,
                                     "NWC": nwc, "Change in NWC": d_nwc,
                                     "ar_days": ar_days_eff, "inventory_days": inv_days_eff, "ap_days": ap_days_eff},
                 "ppe": {"Opening": ppe_open, "Capex": capex, "Depreciation": da, "Closing": ppe_close, "da_pct_ppe": da_rate},
                 "debt": {"Opening": debt_open, "Issuance": debt_iss, "Closing": debt_close, "Interest": interest,
                          "interest_pct_debt": int_rate}}
    rat = []
    for i in range(N):
        rat.append(_ratios.compute(
            {"revenue": revenue[i], "cogs": cogs[i], "gross_profit": IS["Gross Margin"][i], "ebit": ebit[i],
             "interest": interest[i], "ebt": ebt[i], "taxes": taxes[i], "net_income": ni[i]},
            {"total_assets": ta[i], "current_assets": tca[i], "current_liabilities": tcl[i], "inventory": inv[i],
             "ar": ar[i], "ap": ap[i], "ppe": ppe_close[i], "long_term_debt": debt_close[i],
             "total_liabilities": tl[i], "equity": eq[i]}))
    return {"years": years, "sales": sales, "payroll": payroll, "opex": opex, "income_statement": IS,
            "balance_sheet": BS, "cash_flow": CF, "schedules": schedules, "ratios": rat,
            "balanced": all(abs(c) <= 1.0 for c in BS["Check"])}


def sales_products(inp):  # small hook kept for extension (e.g. seasonality); returns nothing today
    return []


def from_dict(d: Dict[str, Any]) -> Dict[str, Any]:
    d = {k: v for k, v in d.items() if not str(k).startswith("_")}
    d["products"] = [Product(**p) for p in d["products"]]
    d["employees"] = [Employee(**e) for e in d["employees"]]
    if "employee_types" in d:
        d["employee_types"] = {k: EmployeeType(**v) for k, v in d["employee_types"].items()}
    return run(ProjectionInputs(**d))
