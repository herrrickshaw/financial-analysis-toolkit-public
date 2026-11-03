"""xlcalc: functions layer."""
from __future__ import annotations

import datetime as _dt
import math
import re
import statistics
from typing import Callable, Dict

from .. import fin as _fin
from .values import (Range, XlError, _cmp, _criterion, _grid, _numbers, _numbers_all, _scalar, _text, from_serial, num, pow_, to_serial, truthy)

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
