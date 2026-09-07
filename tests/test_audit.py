from openpyxl import Workbook
from finmodel.audit import audit, to_markdown, _to_r1c1


def test_r1c1_normalisation():
    assert _to_r1c1("=B2*1.05", 2, 3) == _to_r1c1("=C3*1.05", 3, 4)
    assert _to_r1c1("=$B$2*C2", 2, 3) == _to_r1c1("=$B$2*D3", 3, 4)   # absolute ref stays put, relative ref shifts equally → same pattern
    assert _to_r1c1("=$B$2*C2", 2, 3) != _to_r1c1("=$B$3*C2", 2, 3)   # different absolute ref → different pattern
    assert _to_r1c1('="x"&B2', 2, 3) == _to_r1c1('="y"&C3', 3, 4)


def test_audit_detects_plugs_errors_and_inconsistency(tmp_path):
    wb = Workbook(); ws = wb.active; ws.title = "Model"
    ws.append(["Revenue", 100, "=B1*1.05", "=C1*1.05", "=D1*1.05", "=E1*1.05", "=F1*1.05"])     # 1.05 plug in each formula
    ws.append(["Cost", 60, "=B2*1", "=C2*1", 75, "=E2*1", "=F2*1"])                             # typed 75 inside a formula row
    ws.append(["Margin", "=B1-B2", "=C1-C2", "=D1-D2", "=E1-E2", "=F1-F2", "=G1-G2+1200"])      # inconsistent + plug
    ws.append(["Ratio", "=B1/0", "=C3/C1", "=D3/D1", "=E3/E1", "=F3/F1", "=G3/G1"])
    ws.append(["Link", "=[other.xlsx]Sheet1!A1"])
    h = wb.create_sheet("Hidden"); h.sheet_state = "hidden"
    p = tmp_path / "t.xlsx"; wb.save(p)
    res = audit(p)
    kinds = res["counts"]
    assert kinds.get("hardcode_in_formula", 0) >= 6 and kinds.get("hardcode_in_formula_row") == 1
    assert kinds.get("inconsistent_formula", 0) >= 1 and kinds.get("external_link") == 1 and kinds.get("hidden_sheet") == 1
    assert any(f["cell"] == "E2" for f in res["findings"] if f["kind"] == "hardcode_in_formula_row")
    assert any(f["cell"] == "G3" for f in res["findings"] if f["kind"] in ("inconsistent_formula", "hardcode_in_formula"))
    md = to_markdown(res); assert "Workbook audit" in md and "hardcode_in_formula" in md
