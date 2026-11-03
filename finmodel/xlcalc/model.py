"""xlcalc: model layer."""
from __future__ import annotations

from openpyxl import load_workbook
from openpyxl.utils import column_index_from_string
from openpyxl.utils import get_column_letter
from pathlib import Path
import datetime as _dt
import re
from typing import Any, Callable, Dict, List, Optional, Sequence, Tuple

from .values import (Range, XlError, _text, add, concat, div, eq, ge, gt, le, lt, mul, ne, neg, num, pct, pos, pow_, sub, to_serial, truthy)
from .functions import (FUNCS, _iferror, _rjoin)
from .parser import (transpile_formula)

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
