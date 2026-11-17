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


def _project_sales(inp: ProjectionInputs, n_f: int, N: int) -> Dict[str, Dict[str, List[float]]]:
    """Per-product price / units / COGS paths over base year + forecast years."""
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
    return sales


def _project_payroll(inp: ProjectionInputs, n_f: int, N: int, workdays: List[int], month_workdays: List[int]) -> Dict[str, Any]:
    """Wages by employee type, payroll deductions and net pay; returns the payroll dict (bonus_pool is added later)."""
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
    d = inp.deductions
    fed = [w * d.get("federal_tax", 0) for w in wages_total]
    state = [w * d.get("state_tax", 0) for w in wages_total]
    ins = [w * d.get("insurance", 0) for w in ins_base]
    pen = [w * d.get("pension", 0) for w in ins_base]
    net_pay = [wages_total[i] - fed[i] - state[i] - ins[i] - pen[i] for i in range(N)]
    payroll.update({"work_days": workdays, "total_wages": wages_total, "federal_tax": fed, "state_tax": state,
                    "insurance": ins, "pension": pen, "net_pay": net_pay})
    return payroll


def _project_opex(inp: ProjectionInputs, n_f: int) -> Dict[str, List[float]]:
    """Operating-expense categories (excluding D&A) grown from their base-year monthly totals."""
    opex: Dict[str, List[float]] = {}
    for cat, months in inp.opex_by_month.items():
        if cat == inp.da_category:
            continue
        g = _exp(inp.opex_growth.get(cat), n_f)
        vals = [sum(months)]
        for f in range(n_f):
            vals.append(vals[-1] * (1 + g[f]))
        opex[cat] = vals
    return opex


def _asset_debt_schedules(inp: ProjectionInputs, n_f: int, N: int) -> Dict[str, Any]:
    """PP&E (capex, D&A) and debt (issuance, interest) roll-forwards plus the equity-issuance path."""
    base_da = sum(inp.opex_by_month.get(inp.da_category, [0.0] * 12))
    da_rate = inp.da_pct_ppe if inp.da_pct_ppe is not None else safe_div(base_da, inp.opening_ppe)
    base_interest = sum(inp.base_interest_by_month)
    int_rate = inp.interest_pct_debt if inp.interest_pct_debt is not None else safe_div(base_interest, inp.opening_debt)
    capex = [sum(inp.base_capex_by_month)] + _exp(inp.forecast_capex, n_f, default=sum(inp.base_capex_by_month))
    debt_iss = [sum(inp.base_debt_issued_by_month)] + _exp(inp.forecast_debt_issued, n_f)
    eq_iss = [sum(inp.base_equity_issued_by_month)] + _exp(inp.forecast_equity_issued, n_f)
    ppe_open = [0.0] * N; da = [0.0] * N; ppe_close = [0.0] * N
    debt_open = [0.0] * N; debt_close = [0.0] * N; interest = [0.0] * N
    for i in range(N):
        ppe_open[i] = inp.opening_ppe if i == 0 else ppe_close[i - 1]
        da[i] = base_da if i == 0 else ppe_open[i] * da_rate
        ppe_close[i] = ppe_open[i] + capex[i] - da[i]
        debt_open[i] = inp.opening_debt if i == 0 else debt_close[i - 1]
        debt_close[i] = debt_open[i] + debt_iss[i]
        interest[i] = base_interest if i == 0 else debt_open[i] * int_rate
    return {"capex": capex, "debt_iss": debt_iss, "eq_iss": eq_iss, "ppe_open": ppe_open, "da": da, "ppe_close": ppe_close,
            "debt_open": debt_open, "debt_close": debt_close, "interest": interest, "da_rate": da_rate, "int_rate": int_rate}


def _working_capital(inp: ProjectionInputs, n_f: int, N: int, revenue: List[float], cogs: List[float]) -> Dict[str, Any]:
    """Receivables / inventory / payables / prepaid / accrued balances and the change in net working capital."""
    ar_days = inp.ar_days; inv_days = inp.inventory_days; ap_days = inp.ap_days
    pre_g = _exp(inp.prepaid_growth, n_f); acc_g = _exp(inp.accrued_growth, n_f)
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
    return {"ar": ar, "inv": inv, "ap": ap, "pre": pre, "acc": acc, "nwc": nwc, "d_nwc": d_nwc,
            "ar_days_eff": ar_days_eff, "inv_days_eff": inv_days_eff, "ap_days_eff": ap_days_eff}


def _income_statement(inp: ProjectionInputs, N: int, revenue, cogs, opex, wage_expense, sched) -> Dict[str, List[float]]:
    """Income statement lines; D&A and interest come from the asset/debt schedules."""
    gross = [revenue[i] - cogs[i] for i in range(N)]
    opex_lines: Dict[str, List[float]] = dict(opex)
    opex_lines["Depreciation & Amortization"] = sched["da"]
    opex_lines["Wages and Benefits"] = wage_expense
    total_opex = [sum(v[i] for v in opex_lines.values()) for i in range(N)]
    ebit = [gross[i] - total_opex[i] for i in range(N)]
    bonus_pool = [max(ebit[i], 0.0) * inp.bonus_pct_ebit for i in range(N)]
    ebt = [ebit[i] - bonus_pool[i] - sched["interest"][i] for i in range(N)]
    taxes = [ebt[i] * inp.tax_rate if ebt[i] > 0 else 0.0 for i in range(N)]
    ni = [ebt[i] - taxes[i] for i in range(N)]
    return {"Revenue": revenue, "COGS": cogs, "Gross Margin": gross, **opex_lines,
            "Total Operating Expenses": total_opex, "EBIT": ebit, "Employee Bonuses": bonus_pool,
            "Interest Expense": sched["interest"], "EBT": ebt, "Income Taxes": taxes, "Net Earnings": ni}


def _statements(inp: ProjectionInputs, N: int, IS, sched, wc) -> tuple:
    """Cash flow, equity roll-forward and balance sheet; returns (BS, CF, cash_close, cash_open, tca, tcl, ta, tl, eq)."""
    ni, da = IS["Net Earnings"], sched["da"]
    capex, debt_iss, eq_iss = sched["capex"], sched["debt_iss"], sched["eq_iss"]
    cfo = [ni[i] + da[i] - wc["d_nwc"][i] for i in range(N)]
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
    ar, pre, inv, ap, acc = wc["ar"], wc["pre"], wc["inv"], wc["ap"], wc["acc"]
    ppe_close, debt_close = sched["ppe_close"], sched["debt_close"]
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
    CF = {"Net Earnings": ni, "Plus: Depreciation & Amortization": da, "Less: Changes in Working Capital": wc["d_nwc"],
          "Cash from Operations": cfo, "Investments in Property & Equipment": cfi, "Cash from Investing": cfi,
          "Issuance (repayment) of debt": debt_iss, "Issuance (repayment) of equity": eq_iss,
          "Cash from Financing": cff, "Net Increase (decrease) in Cash": net_cash,
          "Opening Cash Balance": cash_open, "Closing Cash Balance": cash_close}
    return BS, CF, tca, tcl, ta, tl, eq


def _ratio_rows(N: int, IS, BS, tca, tcl, ta, tl, eq) -> List[Any]:
    """Per-year ratio analysis from the statement lines."""
    rat = []
    for i in range(N):
        rat.append(_ratios.compute(
            {"revenue": IS["Revenue"][i], "cogs": IS["COGS"][i], "gross_profit": IS["Gross Margin"][i], "ebit": IS["EBIT"][i],
             "interest": IS["Interest Expense"][i], "ebt": IS["EBT"][i], "taxes": IS["Income Taxes"][i], "net_income": IS["Net Earnings"][i]},
            {"total_assets": ta[i], "current_assets": tca[i], "current_liabilities": tcl[i], "inventory": BS["Inventory"][i],
             "ar": BS["Accounts Receivable"][i], "ap": BS["Accounts Payable"][i], "ppe": BS["Property & Equipment"][i],
             "long_term_debt": BS["Long-term debt"][i], "total_liabilities": tl[i], "equity": eq[i]}))
    return rat


def run(inp: ProjectionInputs) -> Dict[str, Any]:
    """Run the bottom-up projection: sales -> payroll -> opex -> schedules -> statements -> ratios."""
    n_f = inp.forecast_years
    years = [inp.base_year + i for i in range(n_f + 1)]
    N = n_f + 1
    hol = [to_date(h) for h in inp.holidays]
    workdays = [networkdays(date(y, 1, 1), date(y, 12, 31), hol) for y in years]
    month_workdays = [networkdays(s, e, hol) for s, e in _months(inp.base_year)]

    sales = _project_sales(inp, n_f, N)
    revenue = [sum(s["revenue"][i] for s in sales.values()) for i in range(N)]
    cogs = [sum(s["cogs"][i] for s in sales.values()) for i in range(N)]
    payroll = _project_payroll(inp, n_f, N, workdays, month_workdays)
    wage_expense = payroll["net_pay"] if inp.wage_expense_basis == "net_pay" else payroll["total_wages"]
    opex = _project_opex(inp, n_f)
    sched = _asset_debt_schedules(inp, n_f, N)
    IS = _income_statement(inp, N, revenue, cogs, opex, wage_expense, sched)
    payroll["bonus_pool"] = IS["Employee Bonuses"]
    wc = _working_capital(inp, n_f, N, revenue, cogs)
    BS, CF, tca, tcl, ta, tl, eq = _statements(inp, N, IS, sched, wc)
    schedules = {"working_capital": {"AR": wc["ar"], "Inventory": wc["inv"], "Prepaid": wc["pre"], "AP": wc["ap"], "Accrued": wc["acc"],
                                     "NWC": wc["nwc"], "Change in NWC": wc["d_nwc"],
                                     "ar_days": wc["ar_days_eff"], "inventory_days": wc["inv_days_eff"], "ap_days": wc["ap_days_eff"]},
                 "ppe": {"Opening": sched["ppe_open"], "Capex": sched["capex"], "Depreciation": sched["da"], "Closing": sched["ppe_close"],
                         "da_pct_ppe": sched["da_rate"]},
                 "debt": {"Opening": sched["debt_open"], "Issuance": sched["debt_iss"], "Closing": sched["debt_close"],
                          "Interest": sched["interest"], "interest_pct_debt": sched["int_rate"]}}
    return {"years": years, "sales": sales, "payroll": payroll, "opex": opex, "income_statement": IS,
            "balance_sheet": BS, "cash_flow": CF, "schedules": schedules, "ratios": _ratio_rows(N, IS, BS, tca, tcl, ta, tl, eq),
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
