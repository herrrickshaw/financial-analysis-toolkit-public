"""Excel formula parser, Python transpiler and evaluator.

Turns the formulas of any .xlsx workbook into Python callables (or a standalone Python module) and
evaluates them with Excel semantics for the function subset used by financial-model templates.
Every compiled workbook can be verified against the cached values Excel saved in the file.

    m = XlModel("lbo.xlsx"); m.verify() -> {'checked': 623, 'ok': 623, ...}
    m["LBO!J222"]                       -> 0.30687...
    m.set("LBO!J200", 8); m["LBO!J222"] -> recomputed
    to_python_source(m)                 -> str (importable module)

Supported: arithmetic / comparison / concatenation / percent, A1 and sheet-qualified refs, ranges,
defined names, ~80 functions (see FUNCS), lazy IF/IFERROR, iterative calculation for circular
references (Excel-style, capped), Excel serial dates.  Unsupported functions raise XlError('#NAME?').
"""
from __future__ import annotations

import calendar
import datetime as _dt
import math
import re
import statistics
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string, get_column_letter

from . import fin as _fin

# ----------------------------------------------------------------------------- values & errors
_EPOCH = _dt.datetime(1899, 12, 30)


class XlError(Exception):
    def __init__(self, code: str = "#VALUE!"):
        super().__init__(code); self.code = code
    def __repr__(self): return f"XlError({self.code})"
    def __eq__(self, o): return isinstance(o, XlError) and o.code == self.code
    def __hash__(self): return hash(self.code)


def to_serial(d) -> float:
    if isinstance(d, _dt.datetime):
        return (d - _EPOCH).total_seconds() / 86400.0
    if isinstance(d, _dt.date):
        return float((_dt.datetime(d.year, d.month, d.day) - _EPOCH).days)
    return d


def from_serial(x: float) -> _dt.date:
    return (_EPOCH + _dt.timedelta(days=float(x))).date()


def num(v) -> float:
    """Coerce to number the way Excel arithmetic does (blank->0, bool->0/1, numeric text->number)."""
    if isinstance(v, XlError):
        raise v
    if v is None or v == "":
        return 0.0
    if isinstance(v, bool):
        return 1.0 if v else 0.0
    if isinstance(v, (int, float)):
        return float(v)
    if isinstance(v, (_dt.datetime, _dt.date)):
        return float(to_serial(v))
    if isinstance(v, str):
        try:
            return float(v.replace(",", "")) if v.strip() else 0.0
        except ValueError:
            raise XlError("#VALUE!")
    if isinstance(v, Range):
        vals = v.flat()
        if len(vals) == 1:
            return num(vals[0])
        raise XlError("#VALUE!")
    raise XlError("#VALUE!")


def _scalar(v):
    if isinstance(v, Range):
        vals = v.flat_raw()
        return vals[0] if len(vals) == 1 else XlError("#VALUE!")
    return v


def truthy(v) -> bool:
    v = _scalar(v)
    if isinstance(v, XlError):
        raise v
    if isinstance(v, str):
        if v.upper() == "TRUE": return True
        if v.upper() == "FALSE": return False
        raise XlError("#VALUE!")
    return bool(num(v))


# ----------------------------------------------------------------------------- operators
def _snap(r, a, b):
    return 0.0 if abs(r) <= 1e-13 * max(abs(a), abs(b)) else r


def add(a, b):
    x, y = num(a), num(b); return _snap(x + y, x, y)


def sub(a, b):
    x, y = num(a), num(b); return _snap(x - y, x, y)
def mul(a, b): return num(a) * num(b)
def div(a, b):
    d = num(b)
    if d == 0: raise XlError("#DIV/0!")
    return num(a) / d
def pow_(a, b):
    try: return math.pow(num(a), num(b))
    except (ValueError, OverflowError): raise XlError("#NUM!")
def neg(a): return -num(a)
def pos(a):
    a = _scalar(a)
    if isinstance(a, XlError): raise a
    return a if isinstance(a, str) else num(a)
def pct(a): return num(a) / 100.0
def concat(a, b): return _text(a) + _text(b)


def _cmp_key(v):
    v = _scalar(v)
    if isinstance(v, XlError): raise v
    if v is None: return (0, 0.0)
    if isinstance(v, bool): return (2, float(v))
    if isinstance(v, (int, float)): return (0, float(v))
    if isinstance(v, (_dt.datetime, _dt.date)): return (0, float(to_serial(v)))
    return (1, str(v).upper())


def _cmp(a, b) -> int:
    ka, kb = _cmp_key(a), _cmp_key(b)
    if ka[0] == 0 and kb[0] == 1 and kb[1] == "": kb = (0, 0.0)   # number vs blank-string
    if kb[0] == 0 and ka[0] == 1 and ka[1] == "": ka = (0, 0.0)
    if ka[0] != kb[0]:
        return -1 if ka[0] < kb[0] else 1
    return (ka[1] > kb[1]) - (ka[1] < kb[1])


def _close(a, b) -> bool:
    ka, kb = _cmp_key(a), _cmp_key(b)
    return ka[0] == 0 and kb[0] == 0 and abs(ka[1] - kb[1]) <= 1e-9 * max(1.0, abs(ka[1]), abs(kb[1]))


def eq(a, b): return _cmp(a, b) == 0 or _close(a, b)
def ne(a, b): return not eq(a, b)
def lt(a, b): return _cmp(a, b) < 0
def le(a, b): return _cmp(a, b) <= 0
def gt(a, b): return _cmp(a, b) > 0
def ge(a, b): return _cmp(a, b) >= 0


def _text(v) -> str:
    v = _scalar(v)
    if isinstance(v, XlError): raise v
    if v is None: return ""
    if isinstance(v, bool): return "TRUE" if v else "FALSE"
    if isinstance(v, float):
        return str(int(v)) if v.is_integer() and abs(v) < 1e15 else repr(v)
    if isinstance(v, (_dt.datetime, _dt.date)): return str(to_serial(v))
    return str(v)


# ----------------------------------------------------------------------------- ranges
class Range:
    """Lazy rectangular reference; values are pulled from the model on demand."""
    __slots__ = ("model", "sheet", "r1", "c1", "r2", "c2")

    def __init__(self, model, sheet, r1, c1, r2, c2):
        self.model, self.sheet = model, sheet
        self.r1, self.c1, self.r2, self.c2 = min(r1, r2), min(c1, c2), max(r1, r2), max(c1, c2)

    @property
    def rows(self): return self.r2 - self.r1 + 1
    @property
    def cols(self): return self.c2 - self.c1 + 1

    def cell(self, i, j):
        return self.model.get(self.sheet, self.r1 + i, self.c1 + j)

    def grid(self) -> List[List[Any]]:
        return [[self.cell(i, j) for j in range(self.cols)] for i in range(self.rows)]

    def flat_raw(self) -> List[Any]:
        return [self.cell(i, j) for i in range(self.rows) for j in range(self.cols)]

    def flat(self) -> List[Any]:
        return self.flat_raw()

    def offset(self, dr, dc, h=None, w=None) -> "Range":
        h = self.rows if h is None else int(h); w = self.cols if w is None else int(w)
        r1, c1 = self.r1 + int(dr), self.c1 + int(dc)
        if r1 < 1 or c1 < 1: raise XlError("#REF!")
        return Range(self.model, self.sheet, r1, c1, r1 + h - 1, c1 + w - 1)

    def __repr__(self):
        return f"{self.sheet}!{get_column_letter(self.c1)}{self.r1}:{get_column_letter(self.c2)}{self.r2}"


def _numbers(args, include_text_args=True) -> List[float]:
    """Flatten args for SUM-like functions: ranges ignore text/bool/blank, direct args coerce."""
    out = []
    for a in args:
        if isinstance(a, Range):
            for v in a.flat_raw():
                if isinstance(v, XlError): raise v
                if isinstance(v, bool) or v is None or isinstance(v, str): continue
                out.append(num(v))
        elif isinstance(a, (list, tuple)):
            out.extend(_numbers(a))
        elif a is None or isinstance(a, (str, bool)):
            continue
        elif isinstance(a, XlError):
            raise a
        else:
            out.append(num(a))
    return out


def _numbers_all(args) -> List[float]:
    """Like _numbers but text counts as 0 and booleans as 0/1 (MAXA/MINA)."""
    out = []
    for a in args:
        vals = a.flat_raw() if isinstance(a, Range) else (a if isinstance(a, list) else [a])
        for v in vals:
            if v is None: continue
            if isinstance(v, XlError): raise v
            out.append(0.0 if isinstance(v, str) else num(v))
    return out


def _grid(a) -> List[List[Any]]:
    if isinstance(a, Range): return a.grid()
    if isinstance(a, list): return a if a and isinstance(a[0], list) else [a]
    return [[a]]


# ----------------------------------------------------------------------------- criteria (SUMIF/COUNTIF)
_CRIT = re.compile(r"^(<=|>=|<>|=|<|>)?(.*)$", re.S)


def _criterion(c) -> Callable[[Any], bool]:
    c = _scalar(c)
    if not isinstance(c, str):
        return lambda v: (not isinstance(v, (str, type(None), bool))) and num(v) == num(c) if c is not None else v is None
    op, rest = _CRIT.match(c).groups()
    op = op or "="
    try:
        target: Any = float(rest)
        is_num = True
    except ValueError:
        target = rest; is_num = False
    def test(v):
        if isinstance(v, XlError): return False
        if is_num:
            if v is None or isinstance(v, (str, bool)):
                return op == "<>" if not (op == "=" and False) else False
            x = num(v)
            return {"=": x == target, "<>": x != target, "<": x < target, "<=": x <= target, ">": x > target, ">=": x >= target}[op]
        s = "" if v is None else _text(v)
        if op == "=": return s.upper() == target.upper()
        if op == "<>": return s.upper() != target.upper()
        return {"<": s < target, "<=": s <= target, ">": s > target, ">=": s >= target}[op]
    return test


# ----------------------------------------------------------------------------- functions
def _xirr(values, dates):
    vs = _numbers([values]); ds = [num(x) for x in _grid(dates)[0]] if isinstance(dates, Range) and dates.rows == 1 else [num(x) for x in (dates.flat_raw() if isinstance(dates, Range) else _grid(dates)[0])]
    if len(vs) != len(ds):
        # values may include blanks that were dropped; realign by raw
        raw = values.flat_raw() if isinstance(values, Range) else list(values)
        pairs = [(num(v), d) for v, d in zip(raw, ds) if not (v is None or isinstance(v, str))]
        vs, ds = [p[0] for p in pairs], [p[1] for p in pairs]
    if not (any(v > 0 for v in vs) and any(v < 0 for v in vs)):
        raise XlError("#NUM!")
    try:
        return _fin.xirr(vs, [from_serial(d) for d in ds])
    except (ValueError, ZeroDivisionError, OverflowError):
        raise XlError("#NUM!")


def _xnpv(rate, values, dates):
    vs = _numbers([values]); ds = [num(x) for x in (dates.flat_raw() if isinstance(dates, Range) else _grid(dates)[0])]
    return _fin.xnpv(num(rate), vs, [from_serial(d) for d in ds])


def _irr(values, guess=0.1):
    try: return _fin.irr(_numbers([values]), num(guess))
    except (ValueError, ZeroDivisionError, OverflowError): raise XlError("#NUM!")


def _npv(rate, *args): return _fin.npv(num(rate), _numbers(args))


def _eomonth(d, months):
    return float(to_serial(_fin.eomonth(from_serial(num(d)), int(num(months)))))


def _edate(d, months):
    return float(to_serial(_fin.edate(from_serial(num(d)), int(num(months)))))


def _date(y, m, d):
    y, m, d = int(num(y)), int(num(m)), int(num(d))
    base = _dt.date(y + (m - 1) // 12, (m - 1) % 12 + 1, 1)
    return float(to_serial(base) + d - 1)


def _round(x, n=0):
    x, n = num(x), int(num(n))
    q = 10 ** n
    return math.floor(abs(x) * q + 0.5) / q * (1 if x >= 0 else -1)


def _roundup(x, n=0):
    x, n = num(x), int(num(n)); q = 10 ** n
    return math.ceil(abs(x) * q - 1e-12) / q * (1 if x >= 0 else -1)


def _rounddown(x, n=0):
    x, n = num(x), int(num(n)); q = 10 ** n
    return math.floor(abs(x) * q + 1e-12) / q * (1 if x >= 0 else -1)


def _choose(i, *opts):
    i = int(num(i))
    if not 1 <= i <= len(opts): raise XlError("#VALUE!")
    return opts[i - 1]


def _index(rng, r, c=None):
    g = _grid(rng); r = int(num(r)); c = 1 if c is None else int(num(c))
    if r == 0 and c == 0: return rng
    if r == 0: return [row[c - 1] for row in g]
    if c == 0: return g[r - 1]
    try: return g[r - 1][c - 1]
    except IndexError: raise XlError("#REF!")


def _match(val, rng, mtype=1):
    vals = _grid(rng); vals = vals[0] if len(vals) == 1 else [row[0] for row in vals]
    mtype = int(num(mtype)); key = _scalar(val)
    if mtype == 0:
        for i, v in enumerate(vals):
            if isinstance(key, str) and isinstance(v, str):
                if v.upper() == key.upper(): return i + 1
            elif not isinstance(v, (str, type(None))) and not isinstance(key, (str, type(None))) and num(v) == num(key):
                return i + 1
        raise XlError("#N/A")
    best = None
    for i, v in enumerate(vals):
        if v is None: continue
        try:
            if (mtype == 1 and _cmp(v, key) <= 0) or (mtype == -1 and _cmp(v, key) >= 0): best = i + 1
            elif best is not None: break
        except XlError: continue
    if best is None: raise XlError("#N/A")
    return best


def _vlookup(val, table, col, approx=True):
    g = _grid(table); col = int(num(col)); first = [row[0] for row in g]
    i = _match(val, [first], 1 if truthy(approx) else 0)
    try: return g[i - 1][col - 1]
    except IndexError: raise XlError("#REF!")


def _hlookup(val, table, row, approx=True):
    g = _grid(table); row = int(num(row))
    i = _match(val, [g[0]], 1 if truthy(approx) else 0)
    try: return g[row - 1][i - 1]
    except IndexError: raise XlError("#REF!")


def _rjoin(a, b):
    if not isinstance(a, Range) or not isinstance(b, Range): raise XlError("#VALUE!")
    return Range(a.model, a.sheet, min(a.r1, b.r1), min(a.c1, b.c1), max(a.r2, b.r2), max(a.c2, b.c2))


def _offset(ref, r, c, h=None, w=None):
    if not isinstance(ref, Range): raise XlError("#VALUE!")
    return ref.offset(num(r), num(c), None if h is None else num(h), None if w is None else num(w))


def _sumproduct(*ranges):
    grids = [_grid(r) for r in ranges]
    total = 0.0
    for i in range(len(grids[0])):
        for j in range(len(grids[0][0])):
            p = 1.0
            for g in grids:
                v = g[i][j]
                p *= 0.0 if (v is None or isinstance(v, (str, bool))) else num(v)
            total += p
    return total


def _sumif(rng, crit, sum_rng=None):
    test = _criterion(crit); g = _grid(rng); s = _grid(sum_rng) if sum_rng is not None else g
    total = 0.0
    for i, row in enumerate(g):
        for j, v in enumerate(row):
            if test(v):
                try: sv = s[i][j]
                except IndexError: continue
                if not (sv is None or isinstance(sv, (str, bool))): total += num(sv)
    return total


def _countif(rng, crit):
    test = _criterion(crit)
    return float(sum(1 for row in _grid(rng) for v in row if test(v)))


def _count(*args):
    n = 0
    for a in args:
        if isinstance(a, Range):
            n += sum(1 for v in a.flat_raw() if isinstance(v, (int, float, _dt.date)) and not isinstance(v, bool))
        elif a is not None and not isinstance(a, str): n += 1
        elif isinstance(a, str):
            try: float(a); n += 1
            except ValueError: pass
    return float(n)


def _counta(*args):
    n = 0
    for a in args:
        if isinstance(a, Range): n += sum(1 for v in a.flat_raw() if v is not None and v != "")
        elif a is not None: n += 1
    return float(n)


def _average(*args):
    xs = _numbers(args)
    if not xs: raise XlError("#DIV/0!")
    return sum(xs) / len(xs)


def _min(*args):
    xs = _numbers(args); return min(xs) if xs else 0.0


def _max(*args):
    xs = _numbers(args); return max(xs) if xs else 0.0


_DATE_TOK = re.compile(r"yyyy|yy|mmmm|mmm|mm|m|dddd|ddd|dd|d", re.I)


def _text_fn(v, fmt):
    if isinstance(v, Range):
        return [[_text_fn(x, fmt) for x in row] for row in v.grid()]
    v = _scalar(v); fmt = _text(fmt)
    if isinstance(v, str) and not fmt: return v
    x = num(v)
    f = fmt.lower()
    if "%" in f:
        dec = sum(1 for ch in (f.split(".")[1] if "." in f else "") if ch == "0")
        return f"{x*100:.{dec}f}%"
    if re.search(r"[ymd]", f) and not any(ch in f for ch in "0#"):
        d = from_serial(x)
        rep = {"yyyy": f"{d.year:04d}", "yy": f"{d.year%100:02d}", "mmmm": d.strftime("%B"), "mmm": d.strftime("%b"), "mm": f"{d.month:02d}",
               "m": str(d.month), "dddd": d.strftime("%A"), "ddd": d.strftime("%a"), "dd": f"{d.day:02d}", "d": str(d.day)}
        return _DATE_TOK.sub(lambda m: rep[m.group(0).lower()], fmt)
    if "0" in f or "#" in f:
        dec = sum(1 for ch in (f.split(".")[1] if "." in f else "") if ch == "0")
        return f"{x:,.{dec}f}" if "," in f else f"{x:.{dec}f}"
    return _text(x)


def _sln(cost, salvage, life):
    life = num(life)
    if life == 0: raise XlError("#DIV/0!")
    return (num(cost) - num(salvage)) / life


def _syd(cost, salvage, life, per):
    life, per = num(life), num(per)
    if life <= 0 or per < 1 or per > life: raise XlError("#NUM!")
    return (num(cost) - num(salvage)) * (life - per + 1) * 2 / (life * (life + 1))


def _pmt(rate, nper, pv, fv=0, type_=0):
    return _fin.pmt(num(rate), int(num(nper)), num(pv), num(fv), int(num(type_)))


def _quartile(rng, q):
    xs = sorted(_numbers([rng])); q = int(num(q))
    if not xs or not 0 <= q <= 4: raise XlError("#NUM!")
    pos = (len(xs) - 1) * q / 4.0; lo = int(math.floor(pos)); hi = int(math.ceil(pos))
    return xs[lo] + (xs[hi] - xs[lo]) * (pos - lo)


def _median(*args):
    xs = _numbers(args)
    if not xs: raise XlError("#NUM!")
    return float(statistics.median(xs))


def _stdev(*args):
    xs = _numbers(args)
    if len(xs) < 2: raise XlError("#DIV/0!")
    return float(statistics.stdev(xs))


def _days360(d1, d2, method=False):
    a, b = from_serial(num(d1)), from_serial(num(d2))
    if truthy(method):
        return float(360 * (b.year - a.year) + 30 * (b.month - a.month) + (min(b.day, 30) - min(a.day, 30)))
    return float(_fin.days360_us(a, b))


def _yearfrac(d1, d2, basis=0):
    return _fin.yearfrac(from_serial(num(d1)), from_serial(num(d2)), int(num(basis)))


def _iferror(value_thunk, alt_thunk):
    try:
        v = value_thunk()
        if isinstance(v, XlError): raise v
        if isinstance(v, Range):
            vals = v.flat_raw()
            if len(vals) == 1 and isinstance(vals[0], XlError): raise vals[0]
        return v
    except XlError:
        return alt_thunk()
    except ZeroDivisionError:
        return alt_thunk()


def _iserror(v):
    try:
        v = _scalar(v); return isinstance(v, XlError)
    except XlError: return True


def _isnumber(v):
    v = _scalar(v); return isinstance(v, (int, float, _dt.date)) and not isinstance(v, bool)


def _and(*args):
    vals = []
    for a in args:
        vals.extend(a.flat_raw() if isinstance(a, Range) else [a])
    vals = [v for v in vals if not (v is None or isinstance(v, str))]
    return all(truthy(v) for v in vals) if vals else XlError("#VALUE!")


def _or(*args):
    vals = []
    for a in args:
        vals.extend(a.flat_raw() if isinstance(a, Range) else [a])
    vals = [v for v in vals if not (v is None or isinstance(v, str))]
    return any(truthy(v) for v in vals) if vals else XlError("#VALUE!")


def _mid(s, start, n): s = _text(s); i = int(num(start)) - 1; return s[i:i + int(num(n))]
def _year(d): return float(from_serial(num(d)).year)
def _month(d): return float(from_serial(num(d)).month)
def _day(d): return float(from_serial(num(d)).day)
def _today(): return float(to_serial(_dt.date.today()))
def _value(v):
    v = _scalar(v)
    if isinstance(v, str):
        s = v.strip().replace(",", "")
        if s.endswith("%"): return float(s[:-1]) / 100
        try: return float(s)
        except ValueError: raise XlError("#VALUE!")
    return num(v)


FUNCS: Dict[str, Callable] = {
    "SUM": lambda *a: sum(_numbers(a)), "AVERAGE": _average, "MIN": _min, "MAX": _max, "COUNT": _count, "COUNTA": _counta,
    "PRODUCT": lambda *a: math.prod(_numbers(a)) if _numbers(a) else 0.0, "SUMPRODUCT": _sumproduct, "SUMIF": _sumif,
    "COUNTIF": _countif, "ABS": lambda x: abs(num(x)), "ROUND": _round, "ROUNDUP": _roundup, "ROUNDDOWN": _rounddown,
    "INT": lambda x: float(math.floor(num(x))), "MOD": lambda a, b: math.fmod(num(a), num(b)) if num(b) else XlError("#DIV/0!"),
    "SQRT": lambda x: math.sqrt(num(x)), "LN": lambda x: math.log(num(x)), "LOG": lambda x, b=10: math.log(num(x), num(b)),
    "EXP": lambda x: math.exp(num(x)), "POWER": pow_, "SIGN": lambda x: float((num(x) > 0) - (num(x) < 0)),
    "NORMSDIST": lambda x: 0.5 * (1 + math.erf(num(x) / math.sqrt(2))), "NORM.S.DIST": lambda x, c=True: 0.5 * (1 + math.erf(num(x) / math.sqrt(2))) if truthy(c) else math.exp(-num(x) ** 2 / 2) / math.sqrt(2 * math.pi),
    "NORMDIST": lambda x, mu, sd, c=True: 0.5 * (1 + math.erf((num(x) - num(mu)) / (num(sd) * math.sqrt(2)))) if truthy(c) else math.exp(-((num(x) - num(mu)) / num(sd)) ** 2 / 2) / (num(sd) * math.sqrt(2 * math.pi)),
    "NORMSINV": lambda p: statistics.NormalDist().inv_cdf(num(p)), "NORM.S.INV": lambda p: statistics.NormalDist().inv_cdf(num(p)),
    "TRANSPOSE": lambda r: [list(col) for col in zip(*_grid(r))],
    "MAXA": lambda *a: max(_numbers_all(a)) if _numbers_all(a) else 0.0, "MINA": lambda *a: min(_numbers_all(a)) if _numbers_all(a) else 0.0,
    "MEDIAN": _median, "QUARTILE": _quartile, "STDEV": _stdev, "STDEV.S": _stdev,
    "AND": _and, "OR": _or, "NOT": lambda x: not truthy(x), "TRUE": lambda: True, "FALSE": lambda: False,
    "ISNUMBER": _isnumber, "ISERROR": _iserror, "ISERR": _iserror, "ISBLANK": lambda v: _scalar(v) is None,
    "ISTEXT": lambda v: isinstance(_scalar(v), str), "NA": lambda: XlError("#N/A"),
    "CHOOSE": _choose, "INDEX": _index, "ROWS": lambda r: float(len(_grid(r))), "COLUMNS": lambda r: float(len(_grid(r)[0])), "MATCH": _match, "VLOOKUP": _vlookup, "HLOOKUP": _hlookup, "OFFSET": _offset,
    "XIRR": _xirr, "XNPV": _xnpv, "IRR": _irr, "NPV": _npv, "PMT": _pmt, "SLN": _sln, "SYD": _syd,
    "EOMONTH": _eomonth, "EDATE": _edate, "DATE": _date, "YEAR": _year, "MONTH": _month, "DAY": _day,
    "DAYS360": _days360, "YEARFRAC": _yearfrac, "TODAY": _today, "NOW": _today,
    "TEXT": _text_fn, "VALUE": _value, "UPPER": lambda s: _text(s).upper(), "LOWER": lambda s: _text(s).lower(),
    "PROPER": lambda s: _text(s).title(), "LEN": lambda s: float(len(_text(s))), "TRIM": lambda s: " ".join(_text(s).split()),
    "LEFT": lambda s, n=1: _text(s)[:int(num(n))], "RIGHT": lambda s, n=1: _text(s)[-int(num(n)):] if int(num(n)) else "",
    "MID": _mid, "CONCATENATE": lambda *a: "".join(_text(x) for x in a), "CONCAT": lambda *a: "".join(_text(x) for x in a),
    "N": lambda v: num(v) if not isinstance(_scalar(v), str) else 0.0, "T": lambda v: _text(v) if isinstance(_scalar(v), str) else "",
    "AVERAGEIF": lambda r, c, s=None: (lambda t, g, sg: (lambda xs: sum(xs) / len(xs) if xs else XlError("#DIV/0!"))(
        [num(sg[i][j]) for i, row in enumerate(g) for j, v in enumerate(row) if t(v) and not (sg[i][j] is None or isinstance(sg[i][j], (str, bool)))]))(_criterion(c), _grid(r), _grid(s if s is not None else r)),
}

# ----------------------------------------------------------------------------- tokenizer / parser
_TOKEN = re.compile(r"""
    (?P<ws>\s+)
  | (?P<str>"(?:[^"]|"")*")
  | (?P<num>\d+\.?\d*(?:[eE][+-]?\d+)?|\.\d+(?:[eE][+-]?\d+)?)
  | (?P<ref>(?:'(?:[^']|'')+'|[A-Za-z0-9_\.]+)!\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?
           |\$?[A-Za-z]{1,3}\$?\d+(?::\$?[A-Za-z]{1,3}\$?\d+)?(?![A-Za-z0-9_\(]))
  | (?P<colrange>(?:'(?:[^']|'')+'|[A-Za-z0-9_\.]+)!\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3}|\$?[A-Za-z]{1,3}:\$?[A-Za-z]{1,3}(?![A-Za-z0-9_\(]))
  | (?P<err>\#(?:REF!|N/A|VALUE!|DIV/0!|NAME\?|NUM!|NULL!))
  | (?P<func>[A-Za-z_][A-Za-z0-9_\.]*\()
  | (?P<bool>TRUE|FALSE)(?![A-Za-z0-9_\(])
  | (?P<name>[A-Za-z_\\][A-Za-z0-9_\.\\]*)
  | (?P<op><>|<=|>=|[-+*/^&=<>%(),:;{}])
""", re.X)


@dataclass
class Tok:
    kind: str
    text: str


def tokenize(formula: str) -> List[Tok]:
    s = formula[1:] if formula.startswith("=") else formula
    pos, out = 0, []
    while pos < len(s):
        m = _TOKEN.match(s, pos)
        if not m:
            raise XlError("#NAME?")
        pos = m.end()
        kind = m.lastgroup
        if kind == "ws":
            continue
        out.append(Tok(kind, m.group(kind)))
    return out


class Parser:
    """Recursive-descent parser producing Python expression source."""

    def __init__(self, toks: List[Tok], sheet: str):
        self.toks, self.i, self.sheet = toks, 0, sheet

    def peek(self, k=0): return self.toks[self.i + k] if self.i + k < len(self.toks) else None
    def take(self):
        t = self.toks[self.i]; self.i += 1; return t
    def expect(self, text):
        t = self.take()
        if t.text != text: raise XlError("#NAME?")

    def parse(self) -> str:
        e = self.comparison()
        if self.i != len(self.toks): raise XlError("#NAME?")
        return e

    def comparison(self):
        left = self.concat()
        while self.peek() and self.peek().kind == "op" and self.peek().text in ("=", "<>", "<", "<=", ">", ">="):
            op = self.take().text; right = self.concat()
            fn = {"=": "eq", "<>": "ne", "<": "lt", "<=": "le", ">": "gt", ">=": "ge"}[op]
            left = f"{fn}({left},{right})"
        return left

    def concat(self):
        left = self.additive()
        while self.peek() and self.peek().text == "&":
            self.take(); left = f"concat({left},{self.additive()})"
        return left

    def additive(self):
        left = self.term()
        while self.peek() and self.peek().kind == "op" and self.peek().text in "+-" and len(self.peek().text) == 1:
            op = self.take().text; right = self.term()
            left = f"{'add' if op == '+' else 'sub'}({left},{right})"
        return left

    def term(self):
        left = self.power()
        while self.peek() and self.peek().kind == "op" and self.peek().text in ("*", "/"):
            op = self.take().text; right = self.power()
            left = f"{'mul' if op == '*' else 'div'}({left},{right})"
        return left

    def power(self):
        left = self.unary()
        while self.peek() and self.peek().text == "^":
            self.take(); left = f"pow_({left},{self.unary()})"
        return left

    def unary(self):
        t = self.peek()
        if t and t.kind == "op" and t.text in ("-", "+"):
            self.take(); inner = self.unary()
            return f"neg({inner})" if t.text == "-" else f"pos({inner})"
        return self.postfix()

    def postfix(self):
        e = self.primary()
        while self.peek() and self.peek().text in ("%", ":"):
            t = self.take()
            if t.text == "%":
                e = f"pct({e})"
            else:
                rhs = self.primary()
                e = f"RJOIN({self._as_range(e)},{self._as_range(rhs)})"
        return e

    @staticmethod
    def _as_range(src: str) -> str:
        if src.startswith("C("):
            inner = src[2:-1]; cell = inner.rsplit(",", 1)[1]
            return f"R({inner},{cell})"
        return src

    def primary(self):
        t = self.take()
        if t.kind == "num": return repr(float(t.text))
        if t.kind == "str": return repr(t.text[1:-1].replace('""', '"'))
        if t.kind == "bool": return "True" if t.text.upper() == "TRUE" else "False"
        if t.kind == "err": return f"XlError({t.text!r})"
        if t.kind == "ref": return self.ref(t.text)
        if t.kind == "colrange": return self.colrange(t.text)
        if t.kind == "name": return f"N({self._q(t.text)})"
        if t.kind == "func": return self.func(t.text[:-1].upper())
        if t.text == "(":
            e = self.comparison(); self.expect(")"); return e
        if t.text == "{":
            rows, row = [], []
            while True:
                row.append(self.comparison())
                nt = self.take()
                if nt.text in (",", ):
                    continue
                if nt.text == ";":
                    rows.append(row); row = []; continue
                if nt.text == "}":
                    rows.append(row); break
            return "[" + ",".join("[" + ",".join(r) + "]" for r in rows) + "]"
        raise XlError("#NAME?")

    @staticmethod
    def _q(s): return repr(s)

    def _split_sheet(self, text):
        if "!" in text:
            sh, ref = text.rsplit("!", 1)
            sh = sh[1:-1].replace("''", "'") if sh.startswith("'") else sh
            return sh, ref
        return self.sheet, text

    def ref(self, text):
        sh, ref = self._split_sheet(text)
        ref = ref.replace("$", "")
        if ":" in ref:
            a, b = ref.split(":")
            return f"R({self._q(sh)},{self._q(a)},{self._q(b)})"
        return f"C({self._q(sh)},{self._q(ref)})"

    def colrange(self, text):
        sh, ref = self._split_sheet(text)
        a, b = ref.replace("$", "").split(":")
        return f"R({self._q(sh)},{self._q(a + '1')},{self._q(b + '1048576')})"

    def func(self, name):
        args: List[str] = []
        if self.peek() and self.peek().text == ")":
            self.take()
        else:
            while True:
                if self.peek() and self.peek().text in (",", ")"):
                    args.append("None")
                else:
                    args.append(self.comparison())
                t = self.take()
                if t.text == ")": break
                if t.text != ",": raise XlError("#NAME?")
        if name == "IF":
            a = args + ["None"] * (3 - len(args))
            return f"({a[1]} if truthy({a[0]}) else {a[2] if a[2] != 'None' else 'False'})"
        if name == "IFERROR":
            return f"IFERROR(lambda: {args[0]}, lambda: {args[1]})"
        if name in ("OFFSET", "INDEX", "ROWS", "COLUMNS") and args and args[0].startswith("C("):
            args[0] = "R(" + args[0][2:-1] + "," + args[0][2:-1].rsplit(",", 1)[1] + ")"
        if name not in FUNCS:
            return f"NOFUNC({self._q(name)})"
        return f"F[{self._q(name)}](" + ",".join(args) + ")"


def transpile_formula(formula: str, sheet: str) -> str:
    """Excel formula text -> Python expression source (uses C, R, N, F, truthy, IFERROR, operators)."""
    return Parser(tokenize(formula), sheet).parse()


# ----------------------------------------------------------------------------- model
_CELL = re.compile(r"^([A-Z]{1,3})(\d+)$")


def _split(coord: str) -> Tuple[int, int]:
    m = _CELL.match(coord.upper())
    if not m: raise XlError("#REF!")
    return int(m.group(2)), column_index_from_string(m.group(1))


class XlModel:
    """A compiled workbook: values + formulas, lazily evaluated with memoisation."""

    MAX_ITER = 100

    def __init__(self, path: str | Path, sheets: Optional[Sequence[str]] = None):
        self.path = Path(path)
        wb_f = load_workbook(self.path, data_only=False)
        wb_v = load_workbook(self.path, data_only=True)
        self.sheets: List[str] = [s for s in wb_f.sheetnames if sheets is None or s in sheets]
        self.inputs: Dict[Tuple[str, int, int], Any] = {}
        self.formulas: Dict[Tuple[str, int, int], str] = {}
        self.cached: Dict[Tuple[str, int, int], Any] = {}
        self.compiled: Dict[Tuple[str, int, int], Callable] = {}
        self.src: Dict[Tuple[str, int, int], str] = {}
        self.names: Dict[str, str] = {}
        self._values: Dict[Tuple[str, int, int], Any] = {}
        self._stack: List[Tuple[str, int, int]] = []
        self._circular: set = set()
        for ws in wb_f.worksheets:
            if ws.title not in self.sheets: continue
            wv = wb_v[ws.title]
            for row in ws.iter_rows():
                for c in row:
                    if c.value is None: continue
                    key = (ws.title, c.row, c.column)
                    v = c.value
                    if not isinstance(v, (str, int, float, bool, _dt.datetime, _dt.date)):
                        txt = getattr(v, "text", None)          # ArrayFormula -> its formula text
                        if isinstance(txt, str) and txt.startswith("="):
                            v = txt
                        else:                                    # DataTableFormula etc. -> keep Excel's cached result
                            cv = wv.cell(row=c.row, column=c.column).value
                            self.inputs[key] = to_serial(cv) if isinstance(cv, (_dt.datetime, _dt.date)) else cv
                            continue
                    if isinstance(v, str) and v.strip() == "=":
                        self.inputs[key] = v; continue
                    if isinstance(v, str) and v.startswith("="):
                        cv = wv.cell(row=c.row, column=c.column).value
                        if cv == v:                               # stored as text, not a formula
                            self.inputs[key] = v; continue
                        self.formulas[key] = v
                        self.cached[key] = to_serial(cv) if isinstance(cv, (_dt.datetime, _dt.date)) else cv
                    else:
                        self.inputs[key] = to_serial(v) if isinstance(v, (_dt.datetime, _dt.date)) else v
        try:
            items = wb_f.defined_names.items()
        except AttributeError:
            items = [(d.name, d) for d in wb_f.defined_names.definedName]
        for name, dn in items:
            if dn.attr_text and "!" in dn.attr_text:
                self.names[name.upper()] = dn.attr_text
        self._compile_all()

    # ---- compilation
    def _env(self):
        return {"C": self._cell_ref, "R": self._range_ref, "N": self._name_ref, "F": FUNCS, "truthy": truthy,
                "IFERROR": _iferror, "RJOIN": _rjoin, "NOFUNC": lambda n: (_ for _ in ()).throw(XlError("#NAME?")),
                "add": add, "sub": sub, "mul": mul, "div": div, "pow_": pow_, "neg": neg, "pos": pos, "pct": pct,
                "concat": concat, "eq": eq, "ne": ne, "lt": lt, "le": le, "gt": gt, "ge": ge, "XlError": XlError}

    def _compile_all(self):
        env = self._env()
        self.compile_errors: Dict[Tuple[str, int, int], str] = {}
        for key, f in self.formulas.items():
            try:
                src = transpile_formula(f, key[0])
                self.src[key] = src
                self.compiled[key] = eval("lambda: " + src, env)
            except Exception as e:  # noqa: BLE001
                self.compile_errors[key] = f"{type(e).__name__}: {e}"

    # ---- references
    def _cell_ref(self, sheet, coord):
        r, c = _split(coord)
        return self.get(sheet, r, c)

    def _range_ref(self, sheet, a, b):
        r1, c1 = _split(a); r2, c2 = _split(b)
        return Range(self, sheet, r1, c1, r2, c2)

    def _name_ref(self, name):
        ref = self.names.get(name.upper())
        if ref is None: raise XlError("#NAME?")
        sh, rng = ref.rsplit("!", 1)
        sh = sh[1:-1].replace("''", "'") if sh.startswith("'") else sh
        rng = rng.replace("$", "")
        if ":" in rng:
            a, b = rng.split(":"); return self._range_ref(sh, a, b)
        return self._cell_ref(sh, rng)

    # ---- evaluation
    def get(self, sheet: str, r: int, c: int):
        key = (sheet, r, c)
        if key in self._values:
            return self._values[key]
        fn = self.compiled.get(key)
        if fn is None:
            if key in self.formulas:            # compile error -> fall back to cached
                return self.cached.get(key)
            return self.inputs.get(key)
        if key in self._stack:                  # circular reference: use last known value
            self._circular.add(key)
            return self._iter_value.get(key, self.cached.get(key, 0.0))
        self._stack.append(key)
        try:
            v = fn()
            if isinstance(v, Range):
                vals = v.flat_raw()
                v = vals[0] if len(vals) == 1 else XlError("#VALUE!")
            elif isinstance(v, list):
                v = v[0][0] if v and isinstance(v[0], list) else (v[0] if v else None)
        except XlError as e:
            v = e
        except ZeroDivisionError:
            v = XlError("#DIV/0!")
        except (ValueError, OverflowError, TypeError, IndexError, RecursionError) as e:
            v = XlError("#VALUE!")
        finally:
            self._stack.pop()
        self._values[key] = v
        return v

    _iter_value: Dict[Tuple[str, int, int], Any] = {}

    def recalc(self) -> None:
        """Evaluate every formula; iterate for circular references until values stop moving."""
        self._values.clear(); self._circular.clear(); self._iter_value = {}
        for _ in range(self.MAX_ITER):
            self._values.clear()
            for key in self.formulas:
                self.get(*key)
            if not self._circular:
                return
            delta = 0.0
            for key in self._circular:
                new, old = self._values.get(key), self._iter_value.get(key, self.cached.get(key, 0.0))
                if isinstance(new, (int, float)) and isinstance(old, (int, float)):
                    delta = max(delta, abs(new - old))
                self._iter_value[key] = new
            if delta < 1e-7:
                return

    def __getitem__(self, ref: str):
        sheet, coord = ref.rsplit("!", 1) if "!" in ref else (self.sheets[0], ref)
        if not self._values:
            self.recalc()
        r, c = _split(coord.replace("$", ""))
        return self.get(sheet, r, c)

    def set(self, ref: str, value) -> None:
        sheet, coord = ref.rsplit("!", 1) if "!" in ref else (self.sheets[0], ref)
        r, c = _split(coord.replace("$", ""))
        key = (sheet, r, c)
        self.formulas.pop(key, None); self.compiled.pop(key, None)
        self.inputs[key] = to_serial(value) if isinstance(value, (_dt.datetime, _dt.date)) else value
        self._values.clear()

    # ---- verification
    def verify(self, tol: float = 1e-6, rel: float = 1e-9, limit_examples: int = 12) -> Dict[str, Any]:
        self.recalc()
        ok = bad = skipped = 0; examples = []
        for key, cached in self.cached.items():
            got = self._values.get(key)
            if key in self.compile_errors:
                bad += 1
                if len(examples) < limit_examples: examples.append((self._ref(key), self.formulas[key][:80], "COMPILE: " + self.compile_errors[key][:60], cached))
                continue
            if cached is None:
                skipped += 1; continue
            if _match_value(got, cached, tol, rel):
                ok += 1
            else:
                bad += 1
                if len(examples) < limit_examples: examples.append((self._ref(key), self.formulas[key][:80], got, cached))
        return {"file": self.path.name, "checked": ok + bad, "ok": ok, "mismatch": bad, "no_cached": skipped,
                "compile_errors": len(self.compile_errors), "circular": len(self._circular),
                "match_rate": ok / (ok + bad) if ok + bad else 1.0, "examples": examples}

    @staticmethod
    def _ref(key): return f"{key[0]}!{get_column_letter(key[2])}{key[1]}"


def _match_value(got, cached, tol, rel) -> bool:
    if isinstance(cached, str) and cached.startswith("#"):
        return isinstance(got, XlError)
    if isinstance(got, XlError):
        return False
    if isinstance(cached, bool) or isinstance(got, bool):
        try: return bool(truthy(got)) == bool(cached)
        except XlError: return False
    if isinstance(cached, (int, float)):
        try: g = num(got)
        except XlError: return False
        return abs(g - cached) <= max(tol, rel * abs(cached))
    if isinstance(cached, str):
        return _text(got) == cached if got is not None else cached == ""
    return got == cached


# ----------------------------------------------------------------------------- code generation
def to_python_source(model: XlModel, name: str = "workbook") -> str:
    """Emit a standalone module: inputs, transpiled formulas, and an `evaluate()` helper."""
    lines = [f'"""Generated from {model.path.name} by finmodel.xlcalc — every formula rewritten as Python."""',
             "from finmodel.xlcalc import FUNCS as F, XlError, truthy, add, sub, mul, div, pow_, neg, pos, pct, concat, eq, ne, lt, le, gt, ge, _iferror as IFERROR",
             "from finmodel.xlcalc import Range as _Range, _rjoin as RJOIN", "", f"SHEETS = {model.sheets!r}", "", "INPUTS = {"]
    for (sh, r, c), v in sorted(model.inputs.items()):
        lines.append(f"    {sh + '!' + get_column_letter(c) + str(r)!r}: {v!r},")
    lines += ["}", "", "NAMES = {"]
    for k, v in sorted(model.names.items()):
        lines.append(f"    {k!r}: {v!r},")
    lines += ["}", "", "# key -> (original Excel formula, python expression using C(sheet,cell) / R(sheet,a,b) / N(name))", "FORMULAS = {"]
    for key, f in sorted(model.formulas.items()):
        src = model.src.get(key, "NOFUNC('UNCOMPILED')")
        lines.append(f"    {key[0] + '!' + get_column_letter(key[2]) + str(key[1])!r}: ({f!r}, {src!r}),")
    lines += ["}", "", '''

class Workbook:
    """Evaluate the transpiled formulas (memoised, supports overrides via .set)."""

    def __init__(self):
        from finmodel.xlcalc import XlModel
        self._m = XlModel.__new__(XlModel)
        m = self._m
        m.path = __import__("pathlib").Path(%r); m.sheets = list(SHEETS); m.names = dict(NAMES)
        m.inputs = {}; m.formulas = {}; m.cached = {}; m.compiled = {}; m.src = {}; m._values = {}; m._stack = []; m._circular = set(); m._iter_value = {}; m.compile_errors = {}
        for k, v in INPUTS.items():
            sh, cell = k.rsplit("!", 1); m.inputs[(sh,) + _rc(cell)] = v
        env = m._env()
        for k, (f, src) in FORMULAS.items():
            sh, cell = k.rsplit("!", 1); key = (sh,) + _rc(cell)
            m.formulas[key] = f; m.src[key] = src; m.compiled[key] = eval("lambda: " + src, env)

    def __getitem__(self, ref): return self._m[ref]
    def set(self, ref, value): self._m.set(ref, value)
    def recalc(self): self._m.recalc()


def _rc(cell):
    from finmodel.xlcalc import _split
    return _split(cell)
''' % str(model.path)]
    return "\n".join(lines)
