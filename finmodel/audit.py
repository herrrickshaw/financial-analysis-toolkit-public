"""Workbook audit: the quality checks that model-review checklists (CFI modelling guidelines, 3-statement-ultra's QC list,
agentii's audit-xls) apply before a model is trusted:

  * error values cached in cells (#REF!, #DIV/0!, #VALUE!, #N/A, #NAME?, #NUM!)
  * hard-coded numbers inside formulas ("plugs": =B5*1.05, =SUM(B2:B9)+1200) — constants other than 0, 1, −1, 100, 12, 365
  * hard-coded values in a formula row: a row whose cells are mostly formulas but some are typed numbers
  * inconsistent formulas across a row: R1C1-relative pattern differs from the row's dominant pattern
  * external workbook links, hidden sheets, very hidden sheets, merged-cell formulas
  * (optional) recomputation check via finmodel.xlcalc.verify — every formula reproduces its cached value

Output is a findings list with severity, sheet, cell, and message, plus counts; `finmodel audit book.xlsx`."""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence

from openpyxl import load_workbook
from openpyxl.utils import get_column_letter

ERRORS = {"#REF!", "#DIV/0!", "#VALUE!", "#N/A", "#NAME?", "#NUM!", "#NULL!"}
ALLOWED_CONSTANTS = {0.0, 1.0, -1.0, 100.0, 12.0, 365.0, 360.0, 1000.0, 2.0, 4.0, 52.0}
_NUM = re.compile(r'(?<![A-Za-z0-9_$".!])(?<!\$)(-?\d+(?:\.\d+)?)(?![A-Za-z0-9_(:!])')
_STR = re.compile(r'"[^"]*"')
_REF = re.compile(r"(\$?)([A-Z]{1,3})(\$?)(\d+)")
_EXT = re.compile(r"\[[^\]]+\]")


def _to_r1c1(formula: str, row: int, col: int) -> str:
    """Rewrite A1 refs relative to (row, col) so shifted copies of the same formula compare equal."""
    def rep(m):
        cabs, cl, rabs, rw = m.group(1), m.group(2), m.group(3), int(m.group(4))
        from openpyxl.utils import column_index_from_string
        c = column_index_from_string(cl)
        cs = f"C{c}" if cabs else f"C[{c - col}]"; rs = f"R{rw}" if rabs else f"R[{rw - row}]"
        return rs + cs
    return _REF.sub(rep, _STR.sub('""', formula))


def audit(path: str | Path, recompute: bool = False, min_row_cells: int = 4) -> Dict[str, Any]:
    p = Path(path)
    wb_f = load_workbook(p, data_only=False); wb_v = load_workbook(p, data_only=True)
    findings: List[Dict[str, Any]] = []
    add = lambda sev, sheet, cell, kind, msg: findings.append({"severity": sev, "sheet": sheet, "cell": cell, "kind": kind, "message": msg})
    n_formulas = n_cells = 0
    for ws in wb_f.worksheets:
        if ws.sheet_state != "visible":
            add("info", ws.title, "", "hidden_sheet", f"sheet is {ws.sheet_state}")
        wv = wb_v[ws.title]
        merged = {c for rng in ws.merged_cells.ranges for row in ws.iter_rows(min_row=rng.min_row, max_row=rng.max_row, min_col=rng.min_col, max_col=rng.max_col) for c in row}
        for row in ws.iter_rows():
            kinds = []; patterns = []
            for c in row:
                v = c.value
                if v is None: kinds.append(None); patterns.append(None); continue
                n_cells += 1
                if isinstance(v, str) and v.startswith("="):
                    n_formulas += 1; kinds.append("f")
                    f = v
                    patterns.append(_to_r1c1(f, c.row, c.column))
                    cached = wv[c.coordinate].value
                    if isinstance(cached, str) and cached in ERRORS:
                        add("error", ws.title, c.coordinate, "error_value", f"{f[:60]} → {cached}")
                    if _EXT.search(f):
                        add("warning", ws.title, c.coordinate, "external_link", f[:80])
                    consts = [float(x) for x in _NUM.findall(_STR.sub('""', f))]
                    plugs = [x for x in consts if x not in ALLOWED_CONSTANTS]
                    if plugs:
                        add("warning", ws.title, c.coordinate, "hardcode_in_formula", f"{f[:70]} contains {plugs[:3]}")
                    if c in merged:
                        add("info", ws.title, c.coordinate, "formula_in_merged_cell", f[:60])
                elif isinstance(v, (int, float)) and not isinstance(v, bool):
                    kinds.append("n"); patterns.append(None)
                else:
                    kinds.append("t"); patterns.append(None)
            nf = kinds.count("f"); nn = kinds.count("n")
            if nf >= min_row_cells and nn:
                # numbers sitting inside a formula row (excluding the leftmost label/first-year input column region)
                first_f = kinds.index("f")
                for i, k in enumerate(kinds):
                    if k == "n" and i > first_f:
                        cell = row[i]
                        add("warning", ws.title, cell.coordinate, "hardcode_in_formula_row", f"typed value {cell.value} in a row of {nf} formulas")
            pats = [x for x in patterns if x]
            if len(pats) >= min_row_cells:
                dom, cnt = Counter(pats).most_common(1)[0]
                if cnt >= 0.6 * len(pats):
                    for i, x in enumerate(patterns):
                        if x and x != dom:
                            add("info", ws.title, row[i].coordinate, "inconsistent_formula", f"differs from the row's dominant pattern ({cnt}/{len(pats)} cells)")
    out = {"file": str(p), "sheets": len(wb_f.worksheets), "cells": n_cells, "formulas": n_formulas, "findings": findings,
           "counts": dict(Counter(f["kind"] for f in findings)), "by_severity": dict(Counter(f["severity"] for f in findings))}
    if recompute:
        try:
            from . import xlcalc
            m = xlcalc.XlModel(p); r = m.verify()
            out["recompute"] = {k: r[k] for k in r if k in ("checked", "matched", "mismatched", "match_rate")} if isinstance(r, dict) else r
        except Exception as e:  # pragma: no cover
            out["recompute"] = {"error": str(e)}
    return out


def to_markdown(res: Dict[str, Any], limit: int = 200) -> str:
    md = [f"# Workbook audit — {Path(res['file']).name}", "", f"{res['sheets']} sheets, {res['cells']:,} non-empty cells, {res['formulas']:,} formulas. Findings: {res['by_severity']}", ""]
    if res.get("recompute"): md += [f"Recomputation: {res['recompute']}", ""]
    if res["counts"]: md += ["| kind | count |", "|---|---|"] + [f"| {k} | {v} |" for k, v in sorted(res["counts"].items(), key=lambda kv: -kv[1])] + [""]
    md += ["| severity | sheet | cell | kind | message |", "|---|---|---|---|---|"]
    for f in sorted(res["findings"], key=lambda f: {"error": 0, "warning": 1, "info": 2}[f["severity"]])[:limit]:
        md.append(f"| {f['severity']} | {f['sheet']} | {f['cell']} | {f['kind']} | {f['message'].replace('|', '\\|')} |")
    if len(res["findings"]) > limit: md.append(f"| … | | | | {len(res['findings']) - limit} more |")
    return "\n".join(md)
