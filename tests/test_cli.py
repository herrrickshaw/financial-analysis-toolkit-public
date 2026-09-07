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


def test_cli_cycle_field_override_for_reit(capsys):
    # 'ffo' is precomputed into data/edgar/O.json (net_income + real-estate D&A) specifically so this real CLI
    # invocation — quoted verbatim in docs/FOOTBALL_FIELD_O.md — actually runs rather than dividing by a missing field.
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "O.json"), "--sector", "reit", "--field", "ffo", "--revenue-field", "revenue"])
    out = capsys.readouterr().out
    assert "ffo/revenue" in out and "REITs / real estate" in out and "near normal" in out


def test_cli_cycle_airline_periods5_avoids_the_covid_year(capsys):
    # unlike banking/REIT, the airline check needs no --field override (the default operating_income/revenue is
    # correct here) — but it DOES need --periods 5 instead of the CLI's default 8, since the usual 8-year window
    # pulls in FY2020's pandemic collapse as a "bear case." This is the exact command docs/FOOTBALL_FIELD_ALK.md
    # cites for the fix.
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "ALK.json"), "--sector", "airline", "--periods", "5"])
    out = capsys.readouterr().out
    assert "Airlines / air transport" in out and "margin" in out  # default fields (no --field override) are correct here
    assert "-49.8%" not in out and "bear -49" not in out  # FY2020's collapse must not leak into a periods=5 scenario target


def test_cli_cycle_field_override_for_insurance(capsys):
    # same ROE override as banking (field=net_income, revenue_field=equity), a different sector, confirming the
    # override generalizes rather than being a banking-only special case.
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "TRV.json"), "--sector", "insurance", "--field", "net_income", "--revenue-field", "equity"])
    out = capsys.readouterr().out
    assert "net_income/equity" in out and "Property & casualty insurance" in out


def test_cli_cycle_semiconductor_no_override_needed(capsys):
    # like airlines, the semiconductor sector needs no --field/--revenue-field override -- the default
    # operating_income/revenue is already correct here (a real, useful contrast to banking/REIT/insurance).
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "TXN.json"), "--sector", "semiconductor"])
    out = capsys.readouterr().out
    assert "Semiconductors / analog" in out and "margin" in out


def test_cli_cycle_utility_no_override_needed(capsys):
    # like airlines and semiconductors, the utility sector needs no --field/--revenue-field override -- the
    # default operating_income/revenue is correct, but (unlike airlines/semis) the real finding is a genuine
    # secular improving trend (rate-base growth), not mean-reverting cyclicality -- see docs/FOOTBALL_FIELD_DUK.md.
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "DUK.json"), "--sector", "utility"])
    out = capsys.readouterr().out
    assert "Regulated utilities" in out and "margin" in out


def test_cli_cycle_pharma_no_override_needed_but_needs_adjustment(capsys):
    # like airlines/semiconductors/utilities, pharma needs no --field/--revenue-field override -- but see
    # test_sectors.py for the real finding that the field's history still needs an IPR&D adjustment before its
    # trend can be trusted (a third distinct pattern from "wrong field" and "right field, no fix needed").
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cycle", str(root / "data" / "edgar" / "ABBV.json"), "--sector", "pharma"])
    out = capsys.readouterr().out
    assert "Pharmaceuticals" in out and "margin" in out


def test_cli_startup(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["startup", str(root / "examples" / "startup_saas.json"), "--json-out", str(tmp_path / "s.json")])
    out = capsys.readouterr().out
    assert "Balance sheet balances: True" in out and "DCF: enterprise value" in out and "Benchmark vs real software peers" in out
    saved = json.loads((tmp_path / "s.json").read_text())
    assert saved["three_statement"]["balanced"] is True and saved["benchmark"]["sector"] == "software"


def test_cli_startup_benchmark_sector_override(capsys):
    # --benchmark-sector on the CLI should override whatever (if anything) the input file specifies
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["startup", str(root / "examples" / "startup_saas.json"), "--benchmark-sector", "airline"])
    out = capsys.readouterr().out
    assert "Benchmark vs real airline peers" in out


def test_cli_cap_table(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cap-table", str(root / "examples" / "cap_table_series_ab.json"), "--json-out", str(tmp_path / "ct.json")])
    out = capsys.readouterr().out
    assert "Final ownership:" in out and "Exit waterfall on $60,000,000:" in out
    saved = json.loads((tmp_path / "ct.json").read_text())
    assert saved["cap_table"]["ownership"]["Founders"] == pytest.approx(0.49, abs=1e-6)
    assert sum(saved["exit_waterfall"]["payouts"].values()) == pytest.approx(60_000_000)


def test_cli_vc_fund(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["vc-fund", str(root / "examples" / "vc_fund_demo.json"), "--json-out", str(tmp_path / "vf.json")])
    out = capsys.readouterr().out
    assert "TVPI 1.30x" in out and "MOIC 4.00x" in out and "Carry waterfall" in out
    saved = json.loads((tmp_path / "vf.json").read_text())
    assert saved["fund_metrics"]["tvpi"] == pytest.approx(1.3)


def test_cli_cash_flow_forecast(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cash-flow-forecast", str(root / "examples" / "cash_flow_forecast_13wk.json"), "--json-out", str(tmp_path / "cf.json")])
    out = capsys.readouterr().out
    assert "BELOW COVENANT" in out and "Covenant breach weeks: 2026-02-06" in out
    saved = json.loads((tmp_path / "cf.json").read_text())
    assert len(saved["forecast"]["weeks"]) == 13
    assert len(saved["forecast"]["covenant_breach_weeks"]) == 3


def test_cli_impact(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["impact", str(root / "examples" / "impact_scoring_demo.json"), "--json-out", str(tmp_path / "ic.json")])
    out = capsys.readouterr().out
    assert "2X eligible: True" in out and "Impact classification: B" in out and "tCO2e/$M revenue" in out
    saved = json.loads((tmp_path / "ic.json").read_text())
    assert saved["ghg"]["scope1_2_tco2e"] == 2000


def test_cli_ppa(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["ppa", str(root / "examples" / "ppa_demo.json"), "--json-out", str(tmp_path / "ppa.json")])
    out = capsys.readouterr().out
    assert "relief_from_royalty" in out and "Allocation:" in out and "goodwill" in out
    saved = json.loads((tmp_path / "ppa.json").read_text())
    assert saved["allocation"]["goodwill"] > 0


def test_cli_impairment(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["impairment", str(root / "examples" / "impairment_demo.json"), "--json-out", str(tmp_path / "imp.json")])
    out = capsys.readouterr().out
    assert "ASC 350" in out and "ASC 360" in out
    saved = json.loads((tmp_path / "imp.json").read_text())
    assert saved["goodwill"]["capped_by_goodwill_balance"] is True


def test_cli_audit_analytics(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["audit-analytics", str(root / "examples" / "audit_analytics_demo.json"), "--json-out", str(tmp_path / "aa.json")])
    out = capsys.readouterr().out
    assert "Benford's Law" in out and "Journal entry testing" in out
    saved = json.loads((tmp_path / "aa.json").read_text())
    assert saved["journal_entries"]["n_flagged"] == 4


def test_cli_options(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["options", str(root / "examples" / "options_demo.json"), "--json-out", str(tmp_path / "opt.json")])
    out = capsys.readouterr().out
    assert "Call price: 10.4506" in out and "Greeks:" in out and "holds=True" in out
    saved = json.loads((tmp_path / "opt.json").read_text())
    assert saved["black_scholes"]["price"] == pytest.approx(10.4506, abs=1e-3)


def test_cli_project_finance(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["project-finance", str(root / "examples" / "project_finance_demo.json"), "--json-out", str(tmp_path / "pf.json")])
    out = capsys.readouterr().out
    assert "Fully repaid: True" in out and "Cap rate valuation:" in out and "Debt structure comparison:" in out
    saved = json.loads((tmp_path / "pf.json").read_text())
    assert saved["sculpted_amortization"]["fully_repaid"] is True
    cmp = saved["compare_debt_structures"]
    assert cmp["dscr_sculpted"]["total_interest"] < cmp["interest_only_bullet"]["total_interest"]


def test_cli_dcf_diagnostics(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["dcf-diagnostics", str(root / "examples" / "dcf_diagnostics_demo.json"), "--json-out", str(tmp_path / "dd.json")])
    out = capsys.readouterr().out
    assert "Likely uses levered" in out and "True" in out
    saved = json.loads((tmp_path / "dd.json").read_text())
    assert saved["total_gap_undiscounted"] == pytest.approx(41716, abs=1)


def test_cli_portfolio(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["portfolio", str(root / "examples" / "portfolio_demo.json"), "--json-out", str(tmp_path / "port.json")])
    out = capsys.readouterr().out
    assert "Global minimum-variance portfolio:" in out and "Tangency portfolio:" in out and "Capital Allocation Line:" in out
    saved = json.loads((tmp_path / "port.json").read_text())
    assert sum(saved["global_minimum_variance"]["weights"]) == pytest.approx(1.0)


def test_cli_restructuring(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["restructuring", str(root / "examples" / "restructuring_demo.json"), "--json-out", str(tmp_path / "rs.json")])
    out = capsys.readouterr().out
    assert "Fulcrum security: Senior Unsecured Notes" in out and "Absolute priority respected: True" in out
    saved = json.loads((tmp_path / "rs.json").read_text())
    assert saved["fulcrum_security"]["name"] == "Senior Unsecured Notes"
    assert saved["dip_financing_sizing"]["required_dip_facility"] == 4000000


def test_cli_bank_model(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["bank-model", str(root / "examples" / "bank_model_demo.json"), "--json-out", str(tmp_path / "bm.json")])
    out = capsys.readouterr().out
    assert "NII" in out and "well-capitalized=True" in out
    saved = json.loads((tmp_path / "bm.json").read_text())
    assert saved["regulatory_capital_ratios"]["well_capitalized"] is True
    assert len(saved["projection"]) == 5


def test_cli_cohort(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cohort", str(root / "examples" / "cohort_analysis_demo.json"), "--json-out", str(tmp_path / "co.json")])
    out = capsys.readouterr().out
    assert "LTV:CAC ratio:" in out and "CAC payback:" in out
    saved = json.loads((tmp_path / "co.json").read_text())
    assert saved["revenue_retention"]["net_revenue_retention"] == pytest.approx(1.0)


def test_cli_insurance_pricing(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["insurance-pricing", str(root / "examples" / "insurance_pricing_demo.json"), "--json-out", str(tmp_path / "ip.json")])
    out = capsys.readouterr().out
    assert "combined ratio 95.0%" in out
    saved = json.loads((tmp_path / "ip.json").read_text())
    assert saved["operating_ratio"]["overall_profitable"] is True


def test_cli_convertible(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["convertible", str(root / "examples" / "convertible_bonds_demo.json"), "--json-out", str(tmp_path / "cv.json")])
    out = capsys.readouterr().out
    assert "estimated value" in out and "Conversion premium:" in out
    saved = json.loads((tmp_path / "cv.json").read_text())
    assert saved["convertible_bond_value"]["estimated_value"] >= saved["convertible_bond_value"]["conversion_value"]


def test_cli_cmo(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cmo", str(root / "examples" / "cmo_demo.json"), "--json-out", str(tmp_path / "cmo.json")])
    out = capsys.readouterr().out
    assert "Tranche A: WAL" in out and "PSA sensitivity" in out
    saved = json.loads((tmp_path / "cmo.json").read_text())
    wal = saved["cmo_deal"]["weighted_average_life"]
    assert wal["A"] < wal["B"] < wal["C"]


def test_cli_strategy(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["strategy", str(root / "examples" / "strategy_frameworks_demo.json"), "--json-out", str(tmp_path / "sf.json")])
    out = capsys.readouterr().out
    assert "SOM = 1.50% of TAM" in out and "Flagship product" in out and "Star" in out and "Invest/Grow" in out
    saved = json.loads((tmp_path / "sf.json").read_text())
    assert saved["bcg_matrix"]["units"][0]["classification"] == "Star"
