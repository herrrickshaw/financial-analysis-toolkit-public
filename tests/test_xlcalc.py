"""Tests for finmodel.xlcalc — the Excel formula transpiler/evaluator.

Expected values are the worked examples in Microsoft's Excel function documentation (support.microsoft.com,
one per function) or hand-computed Excel semantics, so each assertion is "what Excel shows"."""
import datetime as dt

import pytest
from openpyxl import Workbook

from finmodel import xlcalc as X
from finmodel.xlcalc import FUNCS as F, XlError, XlModel


def S(y, m, d):
    return X.to_serial(dt.date(y, m, d))


# ---------------------------------------------------------------- coercion & operators
def test_num_coercion_like_excel_arithmetic():
    assert X.num(None) == 0 and X.num("") == 0
    assert X.num(True) == 1 and X.num("1,234.5") == 1234.5
    assert X.num(dt.date(1900, 1, 1)) == 2           # 1899-12-30 epoch (Excel's 1900 leap-bug offset)
    with pytest.raises(XlError):
        X.num("abc")


def test_operators():
    assert X.add("2", 3) == 5 and X.sub(0.3, 0.1 + 0.2) == 0.0      # snapped to 0
    with pytest.raises(XlError) as e:
        X.div(1, 0)
    assert e.value.code == "#DIV/0!"
    assert X.pct(50) == 0.5 and X.concat(1.0, "x") == "1x" and X.concat(True, None) == "TRUE"
    assert X.eq("abc", "ABC")                         # case-insensitive text compare
    assert X.lt(10, "a") and X.lt("z", True)          # numbers < text < logicals
    assert X.eq(None, 0) and X.eq("", 0)


def test_truthy():
    assert X.truthy("true") and not X.truthy(0) and X.truthy(2)
    with pytest.raises(XlError):
        X.truthy("maybe")


# ---------------------------------------------------------------- math
def test_mod_takes_sign_of_divisor():
    # Excel docs: MOD(3,2)=1, MOD(-3,2)=1, MOD(3,-2)=-1, MOD(-3,-2)=-1
    assert F["MOD"](3, 2) == 1
    assert F["MOD"](-3, 2) == 1
    assert F["MOD"](3, -2) == -1
    assert F["MOD"](-3, -2) == -1


def test_round_family():
    assert F["ROUND"](2.15, 1) == pytest.approx(2.2)            # Excel docs
    assert F["ROUND"](-1.475, 2) == pytest.approx(-1.48)        # Excel docs
    assert F["ROUND"](21.5, -1) == pytest.approx(20)            # Excel docs
    assert F["ROUND"](626.3, -3) == pytest.approx(1000)         # Excel docs
    assert F["ROUND"](2.5, 0) == 3 and F["ROUND"](-2.5, 0) == -3
    assert F["ROUNDUP"](3.2, 0) == 4 and F["ROUNDUP"](-3.14159, 1) == pytest.approx(-3.2)
    assert F["ROUNDUP"](31415.92654, -2) == pytest.approx(31500)
    assert F["ROUNDDOWN"](3.14159, 3) == pytest.approx(3.141)
    assert F["ROUNDDOWN"](-3.14159, 1) == pytest.approx(-3.1)
    assert F["INT"](-8.9) == -9 and F["INT"](8.9) == 8


def test_round_half_up_on_decimal_ties_like_excel():
    # Excel rounds the decimal value it displays: ROUND(1.005,2)=1.01, ROUND(2.675,2)=2.68
    # (binary 1.005 is 1.00499999999999989..., which naive floor(x*100+0.5) rounds down)
    assert F["ROUND"](1.005, 2) == pytest.approx(1.01)
    assert F["ROUND"](2.675, 2) == pytest.approx(2.68)
    assert F["ROUND"](-1.005, 2) == pytest.approx(-1.01)


def test_stats():
    assert F["MEDIAN"](1, 2, 3, 4, 5, 6) == 3.5
    assert F["QUARTILE"]([[1, 2, 4, 7, 8, 9, 10, 12]], 1) == pytest.approx(3.5)   # Excel docs
    assert F["STDEV"](1345, 1301, 1368, 1322, 1310, 1370, 1318, 1350, 1303, 1299) == pytest.approx(27.46391572)
    assert F["SUM"](1, 2, None, "x") == 3 and F["PRODUCT"]() == 0.0
    with pytest.raises(XlError):
        F["AVERAGE"]()
    assert F["SIGN"](-0.0001) == -1


def test_maxa_mina_accept_array_constants():
    # ={1,"t",TRUE} transpiles to [[1.0,'t',True]]; text counts 0, TRUE 1
    assert F["MAXA"]([[1, "t", True]]) == 1
    assert F["MINA"]([[1, "t", True]]) == 0


# ---------------------------------------------------------------- finance
def test_pmt_sln_syd_from_excel_docs():
    assert F["PMT"](0.08 / 12, 10, 10000) == pytest.approx(-1037.03, abs=0.005)
    assert F["PMT"](0.06 / 12, 18 * 12, 0, 50000) == pytest.approx(-129.08, abs=0.005)
    assert F["SLN"](30000, 7500, 10) == 2250
    assert F["SYD"](30000, 7500, 10, 1) == pytest.approx(4090.91, abs=0.005)
    assert F["SYD"](30000, 7500, 10, 10) == pytest.approx(409.09, abs=0.005)
    with pytest.raises(XlError):
        F["SYD"](1, 0, 5, 6)


def test_npv_xnpv_xirr_from_excel_docs():
    assert F["NPV"](0.10, -10000, 3000, 4200, 6800) == pytest.approx(1188.44, abs=0.005)
    vals = [[-10000, 2750, 4250, 3250, 2750]]
    dates = [[S(2008, 1, 1), S(2008, 3, 1), S(2008, 10, 30), S(2009, 2, 15), S(2009, 4, 1)]]
    assert F["XNPV"](0.09, vals, dates) == pytest.approx(2086.65, abs=0.005)
    assert F["XIRR"](vals, dates) == pytest.approx(0.373362535, abs=1e-6)
    assert F["IRR"]([[-70000, 12000, 15000, 18000, 21000, 26000]]) == pytest.approx(0.0866, abs=5e-5)
    with pytest.raises(XlError):
        F["XIRR"]([[100, 200]], [[S(2020, 1, 1), S(2021, 1, 1)]])   # no sign change -> #NUM!


# ---------------------------------------------------------------- dates
def test_date_functions_from_excel_docs():
    assert F["DATE"](2008, 14, 2) == S(2009, 2, 2)
    assert F["DATE"](2008, -3, 2) == S(2007, 9, 2)
    assert F["DATE"](2008, 1, 35) == S(2008, 2, 4)
    assert F["EOMONTH"](S(2011, 1, 1), 1) == 40602         # 28-Feb-2011
    assert F["EOMONTH"](S(2011, 1, 1), -3) == 40482        # 31-Oct-2010
    assert F["EDATE"](S(2011, 1, 15), 1) == 40589
    assert F["EDATE"](S(2011, 1, 15), -1) == 40527
    assert F["EDATE"](S(2011, 1, 31), 1) == S(2011, 2, 28)
    assert F["DAYS360"](S(2011, 1, 30), S(2011, 2, 1)) == 1
    assert F["DAYS360"](S(2011, 1, 1), S(2011, 12, 31)) == 360
    assert F["YEARFRAC"](S(2012, 1, 1), S(2012, 7, 30)) == pytest.approx(0.58055556, abs=1e-8)
    assert F["YEARFRAC"](S(2012, 1, 1), S(2012, 7, 30), 1) == pytest.approx(0.57650273, abs=1e-8)
    assert F["YEARFRAC"](S(2012, 1, 1), S(2012, 7, 30), 3) == pytest.approx(0.57808219, abs=1e-8)
    assert (F["YEAR"](40602), F["MONTH"](40602), F["DAY"](40602)) == (2011, 2, 28)


# ---------------------------------------------------------------- lookup / criteria / text
def test_lookup_functions():
    col = [[25], [38], [40], [41]]
    assert F["MATCH"](39, col, 1) == 2 and F["MATCH"](41, col, 0) == 4   # Excel docs
    with pytest.raises(XlError):
        F["MATCH"](24, col, 1)
    assert F["MATCH"]("b", [["A", "B", "C"]], 0) == 2
    table = [[1, "one"], [5, "five"], [10, "ten"]]
    assert F["VLOOKUP"](7, table, 2) == "five"
    assert F["VLOOKUP"](10, table, 2, False) == "ten"
    with pytest.raises(XlError):
        F["VLOOKUP"](7, table, 2, False)
    assert F["HLOOKUP"](5, [[1, 5, 10], ["a", "b", "c"]], 2) == "b"
    assert F["INDEX"]([[1, 2], [3, 4]], 2, 1) == 3
    assert F["CHOOSE"](2, "a", "b") == "b"


def test_sumif_countif_operators():
    rng = [[1, 5, 10, "x", None]]
    assert F["SUMIF"](rng, ">4") == 15
    assert F["COUNTIF"](rng, "<=5") == 2
    assert F["COUNTIF"](rng, "x") == 1
    assert F["SUMIF"]([["a", "b", "a"]], "a", [[1, 2, 3]]) == 4
    assert F["AVERAGEIF"](rng, ">0") == pytest.approx(16 / 3)


def test_criteria_wildcards_like_excel():
    # Excel criteria support * (any run) and ? (one char); ~ escapes them
    names = [["apple", "apricot", "banana", "a?c"]]
    assert F["COUNTIF"](names, "ap*") == 2
    assert F["SUMIF"](names, "ap*", [[1, 2, 3, 4]]) == 3
    assert F["COUNTIF"](names, "?pple") == 1
    assert F["COUNTIF"](names, "a~?c") == 1
    assert F["COUNTIF"](names, "<>ap*") == 2


def test_text_functions():
    assert F["TEXT"](0.285, "0.0%") == "28.5%"
    assert F["TEXT"](1234.567, "#,##0.00") == "1,234.57"
    assert F["TEXT"](S(2011, 3, 14), "yyyy-mm-dd") == "2011-03-14"
    assert F["VALUE"]("12%") == 0.12 and F["LEN"]("abc") == 3
    assert F["TRIM"]("  a   b ") == "a b" and F["MID"]("Fluid Flow", 7, 20) == "Flow"
    assert F["RIGHT"]("Sale Price", 5) == "Price" and F["LEFT"]("Sweden") == "S"


def test_logical_and_errors():
    assert F["AND"](True, 1) is True and F["OR"](False, 0) is False
    assert X._iferror(lambda: X.div(1, 0), lambda: "alt") == "alt"
    assert F["ISERROR"](XlError("#N/A")) and not F["ISNUMBER"]("1")


# ---------------------------------------------------------------- tokenizer / transpiler
def test_transpile_precedence_and_refs():
    src = X.transpile_formula("=-A1^2+B1*2%", "S")
    assert src == "add(pow_(neg(C('S','A1')),2.0),mul(C('S','B1'),pct(2.0)))"
    assert X.transpile_formula("='My Sheet'!$A$1:B2", "S") == "R('My Sheet','A1','B2')"
    assert X.transpile_formula('=IF(A1>1,"big")', "S") == "('big' if truthy(gt(C('S','A1'),1.0)) else False)"
    assert X.transpile_formula("=NOSUCH(1)", "S") == "NOFUNC('NOSUCH')"


def test_transpile_quotes_strings_safely():
    # string literals are emitted with repr(): a formula cannot inject Python
    src = X.transpile_formula('="__import__(\'os\')"&A1', "S")
    assert src == "concat(\"__import__('os')\",C('S','A1'))"
    assert eval(src, {"concat": X.concat, "C": lambda s, c: "!"}) == "__import__('os')!"


# ---------------------------------------------------------------- whole workbook
@pytest.fixture
def book(tmp_path):
    wb = Workbook()
    ws = wb.active; ws.title = "Calc"
    ws["A1"], ws["A2"], ws["A3"] = 10, 20, 30
    ws["A4"] = "=SUM(A1:A3)"
    ws["A5"] = '=IF(A4>50,"big","small")'
    ws["A6"] = '=IFERROR(A1/0,"div0")'
    ws["A7"] = "=A1/0"
    ws["B1"] = "=B2*0.5+1"             # circular with B2: converges to B1 = 2
    ws["B2"] = "=B1"
    ws["C1"] = "=Other!A1*2"
    ws["C2"] = "=Rate*100"
    o = wb.create_sheet("Other"); o["A1"] = 21; o["A2"] = 0.07
    from openpyxl.workbook.defined_name import DefinedName
    dn = DefinedName("Rate", attr_text="Other!$A$2")
    try:
        wb.defined_names["Rate"] = dn
    except TypeError:                   # openpyxl < 3.1
        wb.defined_names.append(dn)
    p = tmp_path / "b.xlsx"; wb.save(p)
    return p


def test_model_evaluates_formulas(book):
    m = XlModel(book)
    assert m["Calc!A4"] == 60 and m["Calc!A5"] == "big" and m["Calc!A6"] == "div0"
    assert m["Calc!A7"] == XlError("#DIV/0!")
    assert m["Calc!C1"] == 42 and m["Calc!C2"] == pytest.approx(7.0)


def test_model_iterates_circular_references(book):
    m = XlModel(book)
    assert m["Calc!B1"] == pytest.approx(2.0, abs=1e-6)


def test_model_set_recomputes(book):
    m = XlModel(book)
    assert m["Calc!A5"] == "big"
    m.set("Calc!A1", -100)
    assert m["Calc!A4"] == -50 and m["Calc!A5"] == "small"


def test_generated_module_reproduces_model(book):
    m = XlModel(book)
    ns = {}
    exec(compile(X.to_python_source(m), "gen", "exec"), ns)
    w = ns["Workbook"]()
    assert w["Calc!A4"] == 60 and w["Calc!C1"] == 42


def test_verify_without_cached_values_skips(book):
    r = XlModel(book).verify()          # openpyxl-written files carry no Excel cached results
    assert r["checked"] == 0 and r["no_cached"] > 0 and r["compile_errors"] == 0
