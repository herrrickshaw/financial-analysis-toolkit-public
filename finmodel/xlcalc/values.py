"""xlcalc: values layer."""
from __future__ import annotations

from openpyxl.utils import get_column_letter
import datetime as _dt
import math
import re
from typing import Any, Callable, List


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
