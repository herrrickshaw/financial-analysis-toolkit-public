"""Regression tests from the 2026-10-25 static-analysis sweep (ruff F821 / invalid-syntax on 3.10-3.11)."""
import ast
import pathlib
import shutil
import subprocess
import typing

import pytest

PKG = pathlib.Path(__file__).resolve().parents[1] / "finmodel"


def _fstring_backslashes(path: pathlib.Path):
    """Return (lineno, segment) for every f-string replacement field whose source contains a backslash.
    Python 3.10 and 3.11 reject these with SyntaxError (PEP 701 only landed in 3.12), so a single one makes
    the whole module unimportable on the oldest interpreters the package claims to support."""
    src = path.read_text()
    tree = ast.parse(src)
    hits = []
    for node in ast.walk(tree):
        if isinstance(node, ast.FormattedValue):
            seg = ast.get_source_segment(src, node.value) or ""
            if "\\" in seg:
                hits.append((node.lineno, seg))
    return hits


def test_no_backslash_inside_fstring_expression():
    # pyproject says requires-python >= 3.10; audit.py:110 used `.replace('|', '\\|')` inside an f-string.
    bad = {p.name: _fstring_backslashes(p) for p in PKG.glob("*.py")}
    bad = {k: v for k, v in bad.items() if v}
    assert bad == {}, bad


@pytest.mark.skipif(shutil.which("python3.11") is None, reason="python3.11 not installed")
def test_audit_module_compiles_on_python311():
    code = f"import sys; compile(open({str(PKG / 'audit.py')!r}).read(), 'audit.py', 'exec')"
    r = subprocess.run(["python3.11", "-I", "-c", code], capture_output=True, text=True, timeout=30)
    assert r.returncode == 0, r.stderr


def test_implied_growth_annotations_resolve():
    # dcf.py used `Optional[float]` in a signature without importing Optional; with `from __future__ import
    # annotations` the module imports, but anything that resolves the hints (dataclasses, docs, typing tools) fails.
    from finmodel import dcf
    hints = typing.get_type_hints(dcf.implied_growth)
    assert hints["target_price"] == typing.Optional[float]
