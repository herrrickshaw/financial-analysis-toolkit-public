import json
from pathlib import Path
import pytest
from finmodel.cli import main

EX = Path(__file__).resolve().parent.parent / "examples"


def test_cli_roundtrips(tmp_path, capsys):
    main(["dcf", str(EX / "cfi_dcf.json"), "--json-out", str(tmp_path / "d.json"), "--sensitivity"])
    d = json.loads((tmp_path / "d.json").read_text())
    assert abs(d["equity_value_per_share"] - 33.6266) < 1e-3 and "sensitivity" in d
    main(["three-statement", str(EX / "cfi_three_statement.json"), "--table", "balance_sheet"])
    out = capsys.readouterr().out
    assert "balance sheet OK" in out and "Total Assets" in out
    main(["projection", str(EX / "projection_demo.json"), "--xlsx", str(tmp_path / "p.xlsx")])
    assert (tmp_path / "p.xlsx").exists()
    main(["ratios", str(EX / "ratios_demo.json")])
    assert "gross_margin" in capsys.readouterr().out
    main(["catalog", "list", "--source", "asimplemodel"])
    assert "asimplemodel" in capsys.readouterr().out


def test_cli_comps_scores_costing(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["comps", str(root / "examples" / "comps_stld.json"), "--json-out", str(tmp_path / "c.json")])
    out = capsys.readouterr().out
    assert "Football field" in out and "EV / EBITDA LTM" in out and (tmp_path / "c.json").exists()
    main(["scores", str(root / "examples" / "scores_stld.json")]); assert "Altman Z" in capsys.readouterr().out
    main(["costing", str(root / "examples" / "costing_university.json")]); assert "HHI" in capsys.readouterr().out
    main(["charts", "comps", str(root / "examples" / "comps_stld.json"), "-o", str(tmp_path / "ch.html")])
    html = (tmp_path / "ch.html").read_text(); assert "Football field" in html and "<svg" in html


def test_cli_wacc_residual_income_sotp(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["wacc", str(root / "examples" / "wacc_stld.json"), "--json-out", str(tmp_path / "w.json")])
    out = capsys.readouterr().out
    assert "WACC" in out and (tmp_path / "w.json").exists()
    main(["residual-income", str(root / "examples" / "residual_income_stld.json")])
    assert "Residual income" in capsys.readouterr().out
    main(["sotp", str(root / "examples" / "sotp_conglomerate.json")])
    assert "Equity value" in capsys.readouterr().out


AUDIT_FILE = Path(__file__).resolve().parent.parent / "downloads" / "asimplemodel" / "DCF_A Basic Discounted Cash Flow Model.xlsx"


@pytest.mark.skipif(not AUDIT_FILE.exists(), reason="downloaded template not on this machine")
def test_cli_audit(tmp_path, capsys):
    from finmodel.cli import main
    main(["audit", str(AUDIT_FILE), "--json-out", str(tmp_path / "a.json"), "--markdown-out", str(tmp_path / "a.md")])
    out = capsys.readouterr().out
    assert "sheets" in out and (tmp_path / "a.json").exists() and "Workbook audit" in (tmp_path / "a.md").read_text()


def test_cli_cycle(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "STLD.json"), "--sector", "steel", "--json-out", str(tmp_path / "c.json")])
    out = capsys.readouterr().out
    assert "trough" in out and "Data-driven scenario targets" in out and (tmp_path / "c.json").exists()


def test_cli_cycle_field_override_for_banking(capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "USB.json"), "--sector", "banking", "--field", "net_income", "--revenue-field", "equity"])
    out = capsys.readouterr().out
    assert "net_income/equity" in out and "Banks / financial institutions" in out
