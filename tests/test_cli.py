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
    assert "TVPI 1.30x" in out and "MOIC 4.00x" in out and "Carry waterfall" in out and "American waterfall" in out and "CLAWBACK" in out
    saved = json.loads((tmp_path / "vf.json").read_text())
    assert saved["fund_metrics"]["tvpi"] == pytest.approx(1.3)
    assert saved["american_waterfall"]["final_clawback_owed"] == pytest.approx(160_000.0, rel=1e-3)


def test_cli_percentage_of_completion(tmp_path, capsys):
    from finmodel.cli import main
    main(["percentage-of-completion", str(EX / "percentage_of_completion_demo.json"), "--json-out", str(tmp_path / "poc.json")])
    out = capsys.readouterr().out
    assert "revenue to date" in out and "Total revenue recognized:" in out
    saved = json.loads((tmp_path / "poc.json").read_text())
    assert saved["completion_schedule"]["total_revenue_recognized"] == pytest.approx(1_200_000.0)


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
    assert "Call price: 10.4506" in out and "Greeks:" in out and "holds=True" in out and "Geometric Asian call:" in out
    saved = json.loads((tmp_path / "opt.json").read_text())
    assert saved["black_scholes"]["price"] == pytest.approx(10.4506, abs=1e-3)
    assert saved["geometric_asian_option"]["price"] > 0


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


def test_cli_variance_analysis(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["variance-analysis", str(root / "examples" / "variance_analysis_demo.json"), "--json-out", str(tmp_path / "va.json")])
    out = capsys.readouterr().out
    assert "total variance" in out
    saved = json.loads((tmp_path / "va.json").read_text())
    assert saved["budget_vs_actual_variance"]["reconciles"] is True


def test_cli_fpa_planning(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["fpa-planning", str(root / "examples" / "fpa_planning_demo.json"), "--json-out", str(tmp_path / "fp.json")])
    out = capsys.readouterr().out
    assert "Headcount monthly cost" in out and "Rolling forecast" in out
    saved = json.loads((tmp_path / "fp.json").read_text())
    assert saved["headcount_cost_schedule"]["total_cost"] > 0


def test_cli_breakeven(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["breakeven", str(root / "examples" / "breakeven_demo.json"), "--json-out", str(tmp_path / "be.json")])
    out = capsys.readouterr().out
    assert "Break-even:" in out and "Degree of operating leverage:" in out
    saved = json.loads((tmp_path / "be.json").read_text())
    assert saved["break_even_point"]["break_even_units"] == pytest.approx(25000.0)


def test_cli_cap_table_vc_method(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["cap-table", str(root / "examples" / "vc_method_demo.json"), "--json-out", str(tmp_path / "vc.json")])
    out = capsys.readouterr().out
    assert "VC method:" in out
    saved = json.loads((tmp_path / "vc.json").read_text())
    assert "cap_table" not in saved
    assert saved["vc_method_valuation"]["required_multiple"] > 1.0


def test_cli_strategy(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["strategy", str(root / "examples" / "strategy_frameworks_demo.json"), "--json-out", str(tmp_path / "sf.json")])
    out = capsys.readouterr().out
    assert "SOM = 1.50% of TAM" in out and "Flagship product" in out and "Star" in out and "Invest/Grow" in out
    saved = json.loads((tmp_path / "sf.json").read_text())
    assert saved["bcg_matrix"]["units"][0]["classification"] == "Star"


def test_cli_loss_reserving(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["loss-reserving", str(root / "examples" / "loss_reserving_demo.json"), "--json-out", str(tmp_path / "lr.json")])
    out = capsys.readouterr().out
    assert "Total IBNR:" in out and "Total BF ultimate:" in out
    saved = json.loads((tmp_path / "lr.json").read_text())
    assert saved["chain_ladder"]["total_ibnr"] > 0
    assert saved["bornhuetter_ferguson"]["total_bf_ultimate"] > 0


def test_cli_tax_provision(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["tax-provision", str(root / "examples" / "tax_provision_demo.json"), "--json-out", str(tmp_path / "tp.json")])
    out = capsys.readouterr().out
    assert "Effective tax rate:" in out and "Valuation allowance: required" in out
    saved = json.loads((tmp_path / "tp.json").read_text())
    assert saved["valuation_allowance"]["valuation_allowance_required"] is True


def test_cli_real_estate_development(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["real-estate-development", str(root / "examples" / "real_estate_development_demo.json"), "--json-out", str(tmp_path / "red.json")])
    out = capsys.readouterr().out
    assert "Development pro forma:" in out
    saved = json.loads((tmp_path / "red.json").read_text())
    assert saved["development_pro_forma"]["development_profit"] > 0
    assert saved["development_pro_forma"]["development_spread_bps"] > 0


def test_cli_working_capital_financing(tmp_path, capsys):
    from finmodel.cli import main
    root = Path(__file__).resolve().parent.parent
    main(["working-capital-financing", str(root / "examples" / "working_capital_financing_demo.json"), "--json-out", str(tmp_path / "wcf.json")])
    out = capsys.readouterr().out
    assert "Factoring:" in out and "Early-payment discount APR:" in out and "ABL availability:" in out
    saved = json.loads((tmp_path / "wcf.json").read_text())
    assert saved["asset_based_lending_availability"]["available_to_draw"] > 0


def test_cli_retail_loans(tmp_path, capsys):
    from finmodel.cli import main
    main(["retail-loans", str(EX / "retail_loans_demo.json"), "--json-out", str(tmp_path / "rl.json")])
    out = capsys.readouterr().out
    assert "Amortization:" in out and "Prepayment" in out and "Foreclosure payoff:" in out and "Step-up EMI:" in out
    saved = json.loads((tmp_path / "rl.json").read_text())
    assert saved["prepayment_impact"]["interest_saved"] > 0
    assert saved["loan_eligibility_foir"]["max_eligible_principal"] > 0
    assert saved["step_up_emi_schedule"]["closing_balance"] == pytest.approx(0.0, abs=1.0)


def test_cli_earnout_valuation(tmp_path, capsys):
    from finmodel.cli import main
    main(["earnout-valuation", str(EX / "earnout_valuation_demo.json"), "--json-out", str(tmp_path / "eo.json")])
    out = capsys.readouterr().out
    assert "Scenario-weighted earnout:" in out and "Binary metric earnout:" in out
    saved = json.loads((tmp_path / "eo.json").read_text())
    assert saved["scenario_weighted_earnout"]["present_value"] > 0
    assert 0.0 < saved["binary_metric_earnout"]["risk_neutral_probability_achieved"] < 1.0


def test_cli_retail_deposits(tmp_path, capsys):
    from finmodel.cli import main
    main(["retail-deposits", str(EX / "retail_deposits_demo.json"), "--json-out", str(tmp_path / "rd.json")])
    out = capsys.readouterr().out
    assert "FD maturity:" in out and "RD maturity:" in out and "TDS:" in out
    saved = json.loads((tmp_path / "rd.json").read_text())
    assert saved["tds_on_interest"]["tds_applicable"] is True


def test_cli_carry_trade(tmp_path, capsys):
    from finmodel.cli import main
    main(["carry-trade", str(EX / "carry_trade_demo.json"), "--json-out", str(tmp_path / "ct.json")])
    out = capsys.readouterr().out
    assert "CIP forward rate:" in out and "Uncovered carry return:" in out and "Break-even depreciation:" in out
    saved = json.loads((tmp_path / "ct.json").read_text())
    assert saved["break_even_depreciation"]["break_even_depreciation_pct"] == pytest.approx(
        saved["covered_interest_rate_parity"]["forward_premium_pct"])


def test_cli_revolving_credit(tmp_path, capsys):
    from finmodel.cli import main
    main(["revolving-credit", str(EX / "revolving_credit_demo.json"), "--json-out", str(tmp_path / "rc.json")])
    out = capsys.readouterr().out
    assert "Daily-balance interest:" in out and "Minimum-payment schedule:" in out
    saved = json.loads((tmp_path / "rc.json").read_text())
    assert saved["credit_card_minimum_payment_schedule"]["paid_off"] is True


def test_cli_npa_classification(tmp_path, capsys):
    from finmodel.cli import main
    main(["npa-classification", str(EX / "npa_classification_demo.json"), "--json-out", str(tmp_path / "npa.json")])
    out = capsys.readouterr().out
    assert "Total provision required:" in out and "commercial_real_estate" in out
    saved = json.loads((tmp_path / "npa.json").read_text())
    assert saved["total_provision_required"] > 0
    assert len(saved["loan_book"]) == 5
    assert saved["npa_provisioning"]["segment"] == "commercial_real_estate"


def test_cli_credit_risk(tmp_path, capsys):
    from finmodel.cli import main
    main(["credit-risk", str(EX / "credit_risk_demo.json"), "--json-out", str(tmp_path / "cr.json")])
    out = capsys.readouterr().out
    assert "Expected loss:" in out and "Basel IRB:" in out
    saved = json.loads((tmp_path / "cr.json").read_text())
    assert 0.0 < saved["basel_irb_corporate"]["risk_weight_pct"] < 5.0


def test_cli_interest_rate_risk(tmp_path, capsys):
    from finmodel.cli import main
    main(["interest-rate-risk", str(EX / "interest_rate_risk_demo.json"), "--json-out", str(tmp_path / "irr.json")])
    out = capsys.readouterr().out
    assert "Total gap:" in out and "NII sensitivity" in out
    saved = json.loads((tmp_path / "irr.json").read_text())
    assert saved["repricing_gap"]["total_gap"] == pytest.approx(saved["nii_sensitivity"]["total_gap"])


def test_cli_fixed_income_risk(tmp_path, capsys):
    from finmodel.cli import main
    main(["fixed-income-risk", str(EX / "fixed_income_risk_demo.json"), "--json-out", str(tmp_path / "fir.json")])
    out = capsys.readouterr().out
    assert "Macaulay duration" in out
    saved = json.loads((tmp_path / "fir.json").read_text())
    assert saved["bond_price_and_duration"]["price"] > 0


def test_cli_pipeline(tmp_path, capsys):
    from finmodel.cli import main
    main(["pipeline", str(EX / "pipeline_retail_lending_demo.json"), "--json-out", str(tmp_path / "pl.json")])
    out = capsys.readouterr().out
    assert "Step 'eligibility':" in out and "Step 'schedule':" in out and "Step 'delinquency':" in out
    saved = json.loads((tmp_path / "pl.json").read_text())
    assert saved["order"] == ["eligibility", "schedule", "delinquency"]
    principal = saved["steps"]["eligibility"]["loan_eligibility_foir"]["max_eligible_principal"]
    outstanding = saved["steps"]["schedule"]["amortization_schedule"]["schedule"][23]["closing_balance"]
    assert outstanding < principal
    assert saved["steps"]["delinquency"]["npa_provisioning"]["outstanding_amount"] == pytest.approx(outstanding)


def test_cli_credit_card_abs(tmp_path, capsys):
    from finmodel.cli import main
    main(["credit-card-abs", str(EX / "credit_card_abs_demo.json"), "--json-out", str(tmp_path / "cca.json")])
    out = capsys.readouterr().out
    assert "Excess spread:" in out and "Early amortization: triggered" in out and "Master trust:" in out
    saved = json.loads((tmp_path / "cca.json").read_text())
    assert saved["master_trust_cash_flows"]["fully_paid_down"] is True
    assert saved["early_amortization_trigger"]["triggered_month"] == 6


def test_cli_sales_capacity_planning(tmp_path, capsys):
    from finmodel.cli import main
    main(["sales-capacity-planning", str(EX / "sales_capacity_planning_demo.json"), "--json-out", str(tmp_path / "scp.json")])
    out = capsys.readouterr().out
    assert "Total capacity:" in out and "Reps needed:" in out
    saved = json.loads((tmp_path / "scp.json").read_text())
    assert saved["reps_needed_for_target"]["reps_needed"] == pytest.approx(5.0)


def test_cli_lease_accounting(tmp_path, capsys):
    from finmodel.cli import main
    main(["lease-accounting", str(EX / "lease_accounting_demo.json"), "--json-out", str(tmp_path / "la.json")])
    out = capsys.readouterr().out
    assert "Lease classification: finance" in out and "Finance lease:" in out and "Operating lease:" in out
    saved = json.loads((tmp_path / "la.json").read_text())
    assert saved["classify_lease"]["classification"] == "finance"
    assert saved["operating_lease_schedule"]["schedule"][0]["straight_line_expense"] == pytest.approx(100_000.0)


def test_cli_fx_hedging(tmp_path, capsys):
    from finmodel.cli import main
    main(["fx-hedging", str(EX / "fx_hedging_demo.json"), "--json-out", str(tmp_path / "fxh.json")])
    out = capsys.readouterr().out
    assert "Forward hedge" in out and "Money-market hedge" in out and "Unhedged" in out
    saved = json.loads((tmp_path / "fxh.json").read_text())
    assert saved["fx_hedge_comparison"]["forward_hedge_value"] == pytest.approx(
        saved["fx_hedge_comparison"]["money_market_hedge_value"])


def test_cli_stock_based_compensation(tmp_path, capsys):
    from finmodel.cli import main
    main(["stock-based-compensation", str(EX / "stock_based_compensation_demo.json"), "--json-out", str(tmp_path / "sbc.json")])
    out = capsys.readouterr().out
    assert "RSU grant fair value:" in out and "Option grant fair value:" in out and "Graded vesting:" in out
    saved = json.loads((tmp_path / "sbc.json").read_text())
    assert saved["graded_vesting_expense_schedule"]["schedule"][-1]["cumulative_expense"] == pytest.approx(1_000_000.0)


def test_cli_bond_amortization(tmp_path, capsys):
    from finmodel.cli import main
    main(["bond-amortization", str(EX / "bond_amortization_demo.json"), "--json-out", str(tmp_path / "ba.json")])
    out = capsys.readouterr().out
    assert "Bond issued at discount:" in out
    saved = json.loads((tmp_path / "ba.json").read_text())
    assert saved["bond_amortization_schedule"]["schedule"][-1]["carrying_value"] == pytest.approx(1_000_000.0, abs=1e-2)


def test_cli_fx_translation(tmp_path, capsys):
    from finmodel.cli import main
    main(["fx-translation", str(EX / "fx_translation_demo.json"), "--json-out", str(tmp_path / "fct.json")])
    out = capsys.readouterr().out
    assert "Translated net income:" in out and "CTA" in out
    saved = json.loads((tmp_path / "fct.json").read_text())
    r = saved["current_rate_translation"]
    assert r["translated_assets"] == pytest.approx(r["translated_liabilities"] + r["total_translated_equity"])


def test_cli_inventory_costing(tmp_path, capsys):
    from finmodel.cli import main
    main(["inventory-costing", str(EX / "inventory_costing_demo.json"), "--json-out", str(tmp_path / "ic.json")])
    out = capsys.readouterr().out
    assert "Total cost available:" in out and "fifo" in out and "lifo" in out
    saved = json.loads((tmp_path / "ic.json").read_text())
    r = saved["compare_costing_methods"]
    assert r["fifo"]["cogs"] < r["weighted_average"]["cogs"] < r["lifo"]["cogs"]


def test_cli_pension_accounting(tmp_path, capsys):
    from finmodel.cli import main
    main(["pension-accounting", str(EX / "pension_accounting_demo.json"), "--json-out", str(tmp_path / "pa.json")])
    out = capsys.readouterr().out
    assert "Funded status:" in out and "underfunded" in out and "Net periodic pension cost:" in out
    saved = json.loads((tmp_path / "pa.json").read_text())
    assert saved["funded_status"]["classification"] == "underfunded"


def test_cli_nwc_peg(tmp_path, capsys):
    from finmodel.cli import main
    main(["nwc-peg", str(EX / "nwc_peg_demo.json"), "--json-out", str(tmp_path / "nwc.json")])
    out = capsys.readouterr().out
    assert "NWC true-up:" in out and "increase to seller" in out
    saved = json.loads((tmp_path / "nwc.json").read_text())
    assert saved["working_capital_adjustment"]["purchase_price_adjustment"] == pytest.approx(1_000_000.0)


def test_cli_eps(tmp_path, capsys):
    from finmodel.cli import main
    main(["eps", str(EX / "eps_demo.json"), "--json-out", str(tmp_path / "eps.json")])
    out = capsys.readouterr().out
    assert "Diluted EPS:" in out and "2 dilutive securities included" in out
    saved = json.loads((tmp_path / "eps.json").read_text())
    assert saved["diluted_eps"]["diluted_eps"] < saved["diluted_eps"]["basic_eps"]


def test_cli_investment_securities(tmp_path, capsys):
    from finmodel.cli import main
    main(["investment-securities", str(EX / "investment_securities_demo.json"), "--json-out", str(tmp_path / "is.json")])
    out = capsys.readouterr().out
    assert "available_for_sale:" in out and "Realized gain/loss:" in out
    saved = json.loads((tmp_path / "is.json").read_text())
    assert saved["classify_and_measure"]["oci_impact"] == pytest.approx(15_000.0)


def test_cli_consolidation(tmp_path, capsys):
    from finmodel.cli import main
    main(["consolidation", str(EX / "consolidation_demo.json"), "--json-out", str(tmp_path / "cons.json")])
    out = capsys.readouterr().out
    assert "Consolidated NI:" in out and "NCI balance:" in out
    saved = json.loads((tmp_path / "cons.json").read_text())
    assert saved["consolidated_net_income"]["net_income_attributable_to_parent"] == pytest.approx(5_800_000.0)


def test_cli_debt_covenants(tmp_path, capsys):
    from finmodel.cli import main
    main(["debt-covenants", str(EX / "debt_covenants_demo.json"), "--json-out", str(tmp_path / "dc.json")])
    out = capsys.readouterr().out
    assert "BREACH" in out and "Covenant summary:" in out
    saved = json.loads((tmp_path / "dc.json").read_text())
    assert saved["covenant_compliance_summary"]["all_compliant"] is False
    assert len(saved["covenant_compliance_summary"]["breaches"]) == 1


def test_cli_aro(tmp_path, capsys):
    from finmodel.cli import main
    main(["aro", str(EX / "aro_demo.json"), "--json-out", str(tmp_path / "aro.json")])
    out = capsys.readouterr().out
    assert "Initial ARO liability:" in out and "Accretion schedule:" in out and "Settlement:" in out
    saved = json.loads((tmp_path / "aro.json").read_text())
    assert saved["accretion_schedule"]["final_aro_liability"] == pytest.approx(1_000_000.0, abs=1.0)


def test_cli_warranty_receivables(tmp_path, capsys):
    from finmodel.cli import main
    main(["warranty-receivables", str(EX / "warranty_receivables_demo.json"), "--json-out", str(tmp_path / "wra.json")])
    out = capsys.readouterr().out
    assert "Warranty reserve:" in out and "Total allowance:" in out
    saved = json.loads((tmp_path / "wra.json").read_text())
    assert saved["receivables_allowance_aging_method"]["total_allowance"] == pytest.approx(43_000.0)


def test_cli_investment_incentives(tmp_path, capsys):
    from finmodel.cli import main
    main(["investment-incentives", str(EX / "investment_incentives_demo.json"), "--json-out", str(tmp_path / "inc.json")])
    out = capsys.readouterr().out
    assert "Capital subsidy:" in out and "Total incentive package:" in out
    saved = json.loads((tmp_path / "inc.json").read_text())
    assert saved["net_tax_reimbursement_schedule"]["total_reimbursement"] == pytest.approx(10.0)
    assert saved["net_tax_reimbursement_schedule"]["overall_cap_exhausted"] is True
    assert saved["combined_incentive_package"]["total_incentive_value"] == pytest.approx(13.5)


def test_cli_sector_investment_model(tmp_path, capsys):
    from finmodel.cli import main
    main(["sector-investment-model", str(EX / "sector_investment_model_demo.json"), "--json-out", str(tmp_path / "sim.json")])
    out = capsys.readouterr().out
    assert "Sample project: Pharmaceuticals in Telangana" in out and "Net effective investment:" in out
    saved = json.loads((tmp_path / "sim.json").read_text())["sample_project_model"]
    assert saved["capex"]["total_capex"] == pytest.approx(70.0)
    expected_pv = 8.0 + sum(2.0 / (1.10 ** year) for year in range(1, 6))
    assert saved["incentives"]["total_present_value"] == pytest.approx(expected_pv)


def test_cli_project_bankability_flags_incentive_enabled_states(tmp_path, capsys):
    from finmodel.cli import main
    main(["project-bankability", str(EX / "project_bankability_demo.json"), "--json-out", str(tmp_path / "bank.json")])
    out = capsys.readouterr().out
    assert "Ranked by IRR without incentives" in out and "Incentive-enabled projects" in out
    saved = json.loads((tmp_path / "bank.json").read_text())["rank_projects"]
    assert len(saved["projects"]) == 12
    enabled_states = {p["state"] for p in saved["incentive_enabled_projects"]}
    assert enabled_states == {"Gujarat", "Odisha", "Karnataka"}
    # every project's IRR-with-incentives must be >= its IRR-without (incentives never hurt bankability)
    for p in saved["projects"]:
        assert p["irr_with_incentives"] >= p["irr_without_incentives"]


def test_cli_dscr_matrix_demo_flags_conservative_bank_case_breaches(tmp_path, capsys):
    from finmodel.cli import main
    main(["project-bankability", str(EX / "dscr_matrix_demo.json"), "--json-out", str(tmp_path / "dscr.json")])
    out = capsys.readouterr().out
    assert "BREACH" in out and "OK" in out
    saved = json.loads((tmp_path / "dscr.json").read_text())["dscr_matrix"]
    assert len(saved) == 12
    compliant_states = {r["state"] for r in saved if r["compliant"]}
    assert compliant_states == {"Tamil Nadu", "Odisha", "Uttar Pradesh", "Karnataka", "Madhya Pradesh"}


def test_cli_state_sector_matrix_demo_covers_all_12_states(tmp_path, capsys):
    from finmodel.cli import main
    main(["sector-investment-model", str(EX / "state_sector_matrix_demo.json"), "--json-out", str(tmp_path / "matrix.json")])
    out = capsys.readouterr().out
    assert "Total capex across projects:" in out
    saved = json.loads((tmp_path / "matrix.json").read_text())["sample_project_matrix"]
    assert len(saved["projects"]) == 12
    assert {p["state"] for p in saved["projects"]} == {
        "Gujarat", "Uttar Pradesh", "Rajasthan", "Telangana", "Odisha", "Haryana",
        "Tamil Nadu", "Karnataka", "Andhra Pradesh", "Madhya Pradesh", "Maharashtra", "Punjab",
    }
    recomputed_capex = sum(p["capex"]["total_capex"] for p in saved["projects"])
    assert saved["total_capex_across_projects"] == pytest.approx(recomputed_capex)
    recomputed_pv = sum(p["incentives"]["total_present_value"] for p in saved["projects"])
    assert saved["total_incentive_present_value_across_projects"] == pytest.approx(recomputed_pv)
