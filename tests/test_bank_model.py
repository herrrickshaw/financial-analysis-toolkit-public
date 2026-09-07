"""finmodel.bank_model: NII/NIM and provision are checked by hand, the efficiency ratio and regulatory capital
ratios are checked against their exact definitions, and the real US Prompt Corrective Action "well capitalized"
thresholds are checked on both sides (a bank that clears them and one that doesn't)."""
import pytest

from finmodel import bank_model as B


def test_net_interest_income_matches_hand_calc():
    out = B.net_interest_income(avg_earning_assets=1000.0, asset_yield=0.06, avg_interest_bearing_liabilities=800.0, cost_of_funds=0.02)
    assert out["interest_income"] == 60.0
    assert out["interest_expense"] == 16.0
    assert out["nii"] == 44.0
    assert out["nim"] == pytest.approx(0.044)


def test_provision_for_credit_losses():
    out = B.provision_for_credit_losses(loans=700.0, expected_loss_rate=0.005)
    assert out["provision"] == 3.5


def test_efficiency_ratio_matches_exact_definition():
    assert B.efficiency_ratio(noninterest_expense=60.0, nii=44.0, noninterest_income=20.0) == pytest.approx(60.0 / 64.0)


def test_bank_income_statement_flows_through_to_net_income():
    out = B.bank_income_statement(avg_earning_assets=1000.0, asset_yield=0.06, avg_interest_bearing_liabilities=800.0,
                                  cost_of_funds=0.02, loans=700.0, expected_loss_rate=0.005, noninterest_income=20.0,
                                  noninterest_expense=35.0, tax_rate=0.21)
    pretax = 44.0 - 3.5 + 20.0 - 35.0
    assert out["pretax_income"] == pytest.approx(pretax)
    assert out["net_income"] == pytest.approx(pretax * 0.79)


def test_project_bank_grows_balance_sheet_each_year():
    rows = B.project_bank(years=3, avg_earning_assets_0=1000.0, asset_yield=0.06, avg_interest_bearing_liabilities_0=800.0,
                          cost_of_funds=0.02, loan_growth=0.10, loans_0=700.0, expected_loss_rate=0.005,
                          noninterest_income_0=20.0, noninterest_expense_0=35.0, tax_rate=0.21)
    assert len(rows) == 3
    assert rows[1]["nii"] > rows[0]["nii"]
    assert rows[2]["nii"] > rows[1]["nii"]


def test_regulatory_capital_ratios_well_capitalized():
    out = B.regulatory_capital_ratios(cet1_capital=90.0, tier1_capital=95.0, total_capital=110.0, risk_weighted_assets=900.0, average_total_assets=1100.0)
    assert out["well_capitalized"] is True


def test_regulatory_capital_ratios_undercapitalized_bank_fails_the_check():
    # a bank thinly capitalized relative to its risk-weighted assets should fail the real PCA thresholds
    out = B.regulatory_capital_ratios(cet1_capital=30.0, tier1_capital=32.0, total_capital=40.0, risk_weighted_assets=900.0, average_total_assets=1100.0)
    assert out["well_capitalized"] is False
    assert out["cet1_ratio"] < out["thresholds"]["cet1_ratio"]


def test_from_dict_bundles_everything():
    d = {"income_statement": {"avg_earning_assets": 1000.0, "asset_yield": 0.06, "avg_interest_bearing_liabilities": 800.0,
                              "cost_of_funds": 0.02, "loans": 700.0, "expected_loss_rate": 0.005, "noninterest_income": 20.0,
                              "noninterest_expense": 35.0, "tax_rate": 0.21},
         "regulatory_capital_ratios": {"cet1_capital": 90.0, "tier1_capital": 95.0, "total_capital": 110.0, "risk_weighted_assets": 900.0, "average_total_assets": 1100.0}}
    out = B.from_dict(d)
    assert "income_statement" in out and "regulatory_capital_ratios" in out
