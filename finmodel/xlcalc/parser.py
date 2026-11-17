"""xlcalc: parser layer."""
from __future__ import annotations

from dataclasses import dataclass
import re
from typing import List

from .values import (XlError)
from .functions import (FUNCS)

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
