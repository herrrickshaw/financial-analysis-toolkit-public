"""Excel-compatible finance maths, pure Python (no numpy).

Every function here mirrors the Excel function the CFI templates use, so
engine outputs reconcile to the spreadsheets cell-for-cell.
"""
from __future__ import annotations

import calendar
from datetime import date, datetime, timedelta
from typing import Iterable, Sequence


def to_date(d) -> date:
    """Accept date, datetime, or ISO string 'YYYY-MM-DD'."""
    if isinstance(d, datetime):
        return d.date()
    if isinstance(d, date):
        return d
    if isinstance(d, str):
        return datetime.strptime(d[:10], "%Y-%m-%d").date()
    raise TypeError(f"cannot convert {d!r} to date")


def _last_day_of_feb(d: date) -> bool:
    return d.month == 2 and d.day == calendar.monthrange(d.year, 2)[1]


def days360_us(d1: date, d2: date) -> int:
    """US (NASD) 30/360 day count, as used by Excel DAYS360 / YEARFRAC basis 0."""
    d1, d2 = to_date(d1), to_date(d2)
    dd1, dd2 = d1.day, d2.day
    if _last_day_of_feb(d1) and _last_day_of_feb(d2):
        dd2 = 30
    if _last_day_of_feb(d1):
        dd1 = 30
    if dd2 == 31 and dd1 >= 30:
        dd2 = 30
    if dd1 == 31:
        dd1 = 30
    return 360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (dd2 - dd1)


def yearfrac(d1, d2, basis: int = 0) -> float:
    """Excel YEARFRAC. basis 0 = US 30/360 (Excel default, used by the CFI DCF), 1 = actual/actual
    (approximated as actual/365.25 for multi-year spans), 2 = actual/360, 3 = actual/365, 4 = EU 30/360."""
    d1, d2 = to_date(d1), to_date(d2)
    if d2 < d1:
        d1, d2 = d2, d1
    if basis == 0:
        return days360_us(d1, d2) / 360.0
    actual = (d2 - d1).days
    if basis == 1:
        if d1.year == d2.year:
            return actual / (366.0 if calendar.isleap(d1.year) else 365.0)
        # Excel: average year length across the span
        years = range(d1.year, d2.year + 1)
        avg = sum(366 if calendar.isleap(y) else 365 for y in years) / len(years)
        return actual / avg
    if basis == 2:
        return actual / 360.0
    if basis == 3:
        return actual / 365.0
    if basis == 4:
        dd1 = min(d1.day, 30)
        dd2 = min(d2.day, 30)
        return (360 * (d2.year - d1.year) + 30 * (d2.month - d1.month) + (dd2 - dd1)) / 360.0
    raise ValueError("basis must be 0..4")


def eomonth(d, months: int = 0) -> date:
    d = to_date(d)
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    m += 1
    return date(y, m, calendar.monthrange(y, m)[1])


def edate(d, months: int) -> date:
    d = to_date(d)
    y, m = divmod(d.month - 1 + months, 12)
    y += d.year
    m += 1
    return date(y, m, min(d.day, calendar.monthrange(y, m)[1]))


def networkdays(start, end, holidays: Iterable = ()) -> int:
    """Excel NETWORKDAYS: whole weekdays between start and end inclusive, minus holidays."""
    start, end = to_date(start), to_date(end)
    if end < start:
        return -networkdays(end, start, holidays)
    hol = {to_date(h) for h in holidays}
    n = 0
    d = start
    while d <= end:
        if d.weekday() < 5 and d not in hol:
            n += 1
        d += timedelta(days=1)
    return n


def npv(rate: float, cashflows: Sequence[float]) -> float:
    """Excel NPV: first cash flow discounted one full period."""
    return sum(cf / (1 + rate) ** (i + 1) for i, cf in enumerate(cashflows))


def xnpv(rate: float, cashflows: Sequence[float], dates: Sequence) -> float:
    """Excel XNPV: discount each flow by actual days / 365 from the first date."""
    if len(cashflows) != len(dates):
        raise ValueError("cashflows and dates must be the same length")
    ds = [to_date(d) for d in dates]
    d0 = ds[0]
    return sum(cf / (1 + rate) ** ((d - d0).days / 365.0) for cf, d in zip(cashflows, ds))


def _solve_rate(f, guess: float = 0.1, lo: float = -0.9999, hi: float = 10.0, tol: float = 1e-10) -> float:
    """Newton with bisection fallback on a monotone-ish NPV function."""
    r = guess
    for _ in range(100):
        v = f(r)
        h = 1e-6
        dv = (f(r + h) - f(r - h)) / (2 * h)
        if dv == 0:
            break
        nr = r - v / dv
        if not (lo < nr < hi):
            break
        if abs(nr - r) < tol:
            return nr
        r = nr
    # bisection
    flo, fhi = f(lo), f(hi)
    if flo * fhi > 0:
        raise ValueError("IRR not bracketed; cash flows may not change sign")
    for _ in range(300):
        mid = (lo + hi) / 2
        fm = f(mid)
        if abs(fm) < tol:
            return mid
        if flo * fm < 0:
            hi, fhi = mid, fm
        else:
            lo, flo = mid, fm
    return (lo + hi) / 2


def irr(cashflows: Sequence[float], guess: float = 0.1) -> float:
    return _solve_rate(lambda r: sum(cf / (1 + r) ** i for i, cf in enumerate(cashflows)), guess)


def xirr(cashflows: Sequence[float], dates: Sequence, guess: float = 0.1) -> float:
    return _solve_rate(lambda r: xnpv(r, cashflows, dates), guess)


def pmt(rate: float, nper: int, pv: float, fv: float = 0.0, when: int = 0) -> float:
    """Excel PMT (returns a negative number for a positive pv, like Excel)."""
    if rate == 0:
        return -(pv + fv) / nper
    f = (1 + rate) ** nper
    return -(pv * f + fv) * rate / ((1 + rate * when) * (f - 1))


def cagr(begin: float, end: float, periods: float) -> float:
    return (end / begin) ** (1.0 / periods) - 1


def safe_div(a: float, b: float, default: float = 0.0) -> float:
    """IFERROR(a/b, default)."""
    try:
        return a / b
    except ZeroDivisionError:
        return default
