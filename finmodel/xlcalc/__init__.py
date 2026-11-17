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

from .values import (  # noqa: F401
    Range,
    XlError,
    _CRIT,
    _EPOCH,
    _close,
    _cmp,
    _cmp_key,
    _criterion,
    _grid,
    _numbers,
    _numbers_all,
    _scalar,
    _snap,
    _text,
    add,
    concat,
    div,
    eq,
    from_serial,
    ge,
    gt,
    le,
    lt,
    mul,
    ne,
    neg,
    num,
    pct,
    pos,
    pow_,
    sub,
    to_serial,
    truthy,
)
from .functions import (  # noqa: F401
    FUNCS,
    _DATE_TOK,
    _and,
    _average,
    _choose,
    _count,
    _counta,
    _countif,
    _date,
    _day,
    _days360,
    _edate,
    _eomonth,
    _hlookup,
    _iferror,
    _index,
    _irr,
    _iserror,
    _isnumber,
    _match,
    _max,
    _median,
    _mid,
    _min,
    _month,
    _npv,
    _offset,
    _or,
    _pmt,
    _quartile,
    _rjoin,
    _round,
    _rounddown,
    _roundup,
    _sln,
    _stdev,
    _sumif,
    _sumproduct,
    _syd,
    _text_fn,
    _today,
    _value,
    _vlookup,
    _xirr,
    _xnpv,
    _year,
    _yearfrac,
)
from .parser import (  # noqa: F401
    Parser,
    Tok,
    _TOKEN,
    tokenize,
    transpile_formula,
)
from .model import (  # noqa: F401
    XlModel,
    _CELL,
    _match_value,
    _split,
    to_python_source,
)
